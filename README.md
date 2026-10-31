## ATLAS — Autonomous Tactical & Logistical Assistant for Startups
An operations assistant built for startup leadership that connects business metrics with company playbooks. Instead of switching between spreadsheets and policy documents, ATLAS runs deterministic SQL queries on financial data and retrieves company rules using RAG, handling multi-step scenario questions through a stateful LangGraph workflow.

The Problem It Solves
Startup founders and leadership teams handle questions that frequently require two completely different sources of truth:

The Numbers (Structured Data): Live runway, monthly burn rate, revenue growth, churn, and CAC.

The Rules (Unstructured Data): Employee spending limits, hiring freeze guidelines, SLAs, and customer refund policies.

Standard LLM chatbots hallucinate when doing math on raw financial data, while basic SQL scripts cannot read governance documents. ATLAS routes each question to the right engine—or combines both—so founders can test scenarios like:

"If revenue drops by 20% next month, does our projected runway breach our minimum cash reserve policy?"

System Architecture

                    ┌───────────────────────────────┐
                    │     User Business Question    │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │    LangGraph State Router     │
                    └───────┬───────────────┬───────┘
                            │               │
        [Quantitative Data] │               │ [Policy / SOP Question]
                            ▼               ▼
             ┌─────────────────────┐ ┌─────────────────────┐
             │ In-Memory SQLite DB │ │ ChromaDB Vector Retr│
             │ Dynamic Text-to-SQL │ │ Semantic RAG Search │
             └──────────────┬──────┘ └──────┬──────────────┘
                            │               │
                            └───────┬───────┘
                                    ▼
                    ┌───────────────────────────────┐
                    │      Gemini LLM Reasoning     │
                    │   (Calculations + Synthesis)  │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │ Chat Response / Founder Memo  │
                    └───────────────────────────────┘
                    
Key Features
Deterministic Financial SQL: Loads structured CSV metrics directly into an in-memory SQLite database (SQLAlchemy with StaticPool). Uses schema inspection and strict read-only execution to calculate metrics like runway and burn rate accurately without guessing.

Policy Retrieval with ChromaDB: Parses and chunks internal documents (PDF, TXT, MD) into embeddings to answer questions on internal SOPs and rules.

Cross-Domain Scenario Testing: Synthesizes metrics and policies together. For example, it calculates new runway figures after a hypothetical hire and checks if the new number violates active hiring-freeze thresholds.

Founder Memo Generator: Generates a clean markdown briefing summarizing active KPIs, runway trajectory, and operational alerts with a single click.

Streamlit Interface: Clean dashboard featuring data upload controls, executive actions, and chat interaction.

Tech Stack
Workflow Orchestration: LangGraph, LangChain Core

LLM: Google Gemini (gemini-1.5-flash / gemini-1.5-pro)

Databases: In-Memory SQLite, ChromaDB

Data Processing: Pandas, PyPDF

Frontend: Streamlit
