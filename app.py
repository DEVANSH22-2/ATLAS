import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from agent_backend import create_agent

st.set_page_config(page_title="Founder's Assistant", layout="wide")
st.markdown("<h2 style='text-align: center;'>ATLAS — Autonomous Tactical & Logistical Assistant for Startups</h2><p style='text-align: center; color: gray;'>Real-Time Business Metrics & Compliance Intelligence</p>", unsafe_allow_html=True)
# Sidebar for file uploads
with st.sidebar:
    st.title("⚙️ Control Panel")
    st.header("Upload Data")
    csv_file = st.file_uploader("1. Company Metrics (CSV)", type=["csv"])
    doc_files = st.file_uploader("2. Playbooks/SOPs (PDF, TXT, MD)", type=["pdf", "txt", "md"], accept_multiple_files=True)

    if st.button("Start Assistant"):
        if not csv_file and not doc_files:
            st.error("Upload at least one file first!")
        else:
            with st.spinner("Setting up databases..."):
                st.session_state.agent = create_agent(csv_file, doc_files)
                st.session_state.messages = []
                st.session_state.memo_text = None
                st.success("Ready!")

    st.divider()
    memo_btn = st.button("Generate Founder Memo", disabled=("agent" not in st.session_state))

# Main chat logic
if "agent" not in st.session_state:
    st.info("👈 Upload your files in the sidebar and click **Start Assistant** to begin.")
else:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    config = {"configurable": {"thread_id": "session_1"}}

    # One-click Memo generation
    if memo_btn:
        memo_prompt = (
            "Analyze the latest financial metrics and check company policies. "
            "Write a concise Executive Memo with: "
            "1. KPI Summary, 2. Runway & Burn Analysis, 3. Policy & Risk Flags, 4. Action Items."
        )
        with st.spinner("Generating memo..."):
            res = st.session_state.agent.invoke(
                {"messages": [HumanMessage(content=memo_prompt)]}, 
                config=config
            )
            text = res["messages"][-1].content
            st.session_state.memo_text = text
            st.session_state.messages.append(AIMessage(content=text))

    # Download button for memo
    if st.session_state.get("memo_text"):
        with st.sidebar:
            st.download_button(
                label="Download Memo (.md)",
                data=st.session_state.memo_text,
                file_name="executive_memo.md"
            )
    with st.chat_message("assistant"):
        st.write("Hello,how may I help you today?")
    # Render history
    for msg in st.session_state.messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.write(msg.content)

    # Chat input
    if prompt := st.chat_input("Ask about revenue, runway, refund policy, etc..."):
        with st.chat_message("user"):
            st.write(prompt)
        st.session_state.messages.append(HumanMessage(content=prompt))

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                res = st.session_state.agent.invoke(
                    {"messages": [HumanMessage(content=prompt)]}, 
                    config=config
                )
                ans = res["messages"][-1].content
                st.write(ans)
                st.session_state.messages.append(AIMessage(content=ans))