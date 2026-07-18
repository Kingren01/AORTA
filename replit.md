# AORTA — Assay Ontology & Retrieval Translation Architect

A Streamlit-based biomedical knowledge graph tool that ingests scientific literature (PDFs, PubMed abstracts, raw text) and transforms it into a structured semantic knowledge graph using Databricks LLMs.

## How to run

```
streamlit run app.py
```

The workflow "Start application" handles this automatically. The app runs on **port 5000**.

## Required secrets

Set these in Replit Secrets (already configured):

- `DATABRICKS_HOST` — Databricks workspace URL
- `DATABRICKS_TOKEN` — Databricks Personal Access Token
- `DATABRICKS_MODEL` — Model name (e.g. `databricks-meta-llama-3-1-70b-instruct`)
- `NCBI_API_KEY` — Optional; accelerates PubMed abstract fetching

## Architecture

- `app.py` — Main Streamlit UI and extraction pipeline
- `chatbot_llm.py` — LLM conversation loop and tool routing
- `chatbot_tools.py` — Chatbot tools (Vector DB search, Graph query)
- `chat_storage.py` — SQLite persistence for chats, graphs, UI state
- `vector_db.py` — FAISS index and sentence-transformers for semantic search
- `bao_complete.owl` — Base BioAssay Ontology for semantic mapping

## Dependencies

Managed via `requirements.txt`: `streamlit`, `rdflib`, `pyvis`, `PyMuPDF`, `sentence-transformers`, `faiss-cpu`, `pandas`, `openpyxl`.

## User preferences

_None recorded yet._
