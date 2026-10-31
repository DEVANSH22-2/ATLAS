import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv
from pypdf import PdfReader
from typing import Annotated, TypedDict

from langchain_community.utilities import SQLDatabase
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

def create_agent(csv_file, doc_files):
    tools = []

    # 1. Structured Data: CSV to In-Memory SQLite
    if csv_file is not None:
        df = pd.read_csv(csv_file)
        engine = create_engine("sqlite:///:memory:",connect_args={"check_same_thread": False},poolclass=StaticPool)
        df.to_sql("company_metrics", engine, index=False)
        db = SQLDatabase(engine)
        schema = db.get_table_info(["company_metrics"])

        @tool(description=  f"Execute SQLite read queries on company_metrics table to get financial numbers.Table schema:\n{schema},RULE: When asked for 'recent', 'latest', or 'last N' periods, ALWAYS sort in descending order (`ORDER BY month DESC`) before applying LIMIT.\n")
        def run_sql(query: str) -> str:
            try:
                if any(word in query.upper() for word in ["DROP", "DELETE", "UPDATE", "INSERT"]):
                    return "Only SELECT queries are allowed."
                output = db.run(query)
                return str(output) if output else "No results found."
            except Exception as e:
                return f"Error: {e}"

        tools.append(run_sql)

    # 2. Unstructured Data: Docs/PDFs to ChromaDB
    if doc_files:
        docs = []
        for file in doc_files:
            name = file.name.lower()
            if name.endswith(".pdf"):
                reader = PdfReader(file)
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        docs.append(Document(page_content=text, metadata={"source": file.name, "page": page_num + 1}))
            elif name.endswith((".txt", ".md")):
                content = file.read().decode("utf-8")
                if content:
                    docs.append(Document(page_content=content, metadata={"source": file.name}))

        if docs:
            splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
            splits = splitter.split_documents(docs)
            
            embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")
            vectorstore = Chroma.from_documents(splits, embeddings)
            retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

            @tool
            def search_playbook(query: str) -> str:
                """Search company playbooks, SOPs, and guidelines for rules and policies."""
                results = retriever.invoke(query)
                if not results:
                    return "No relevant SOP or policy found in the company documentation for this topic."
                content="\n\n".join([doc.page_content for doc in results])
                return content if content.strip() else "No relevant SOP or policy found in the company documentation for this topic."

            tools.append(search_playbook)

    if not tools:
        return None

    # 3. LangGraph Setup
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    model_with_tools = model.bind_tools(tools)

    class State(TypedDict):
        messages: Annotated[list[BaseMessage], add_messages]

    def chat_node(state: State):
        query=state["messages"]
        result = model_with_tools.invoke(query)
        
        # If the model produced final content as a list of blocks, flatten it to a string
        if isinstance(result.content, list):
            clean_str = "".join(b["text"] for b in result.content if isinstance(b, dict) and "text" in b)
            result.content = clean_str
            
        return {"messages": [result]}

    workflow = StateGraph(State)
    workflow.add_node("agent", chat_node)
    workflow.add_node("tools", ToolNode(tools))

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    save = MemorySaver()
    app = workflow.compile(checkpointer=save)
    return app