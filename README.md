# AORTA: Assay Ontology & Retrieval Translation Architect

AORTA is an advanced, LLM-powered tool designed to autonomously ingest unstructured scientific literature (PDFs, PubMed abstracts, raw text) and transform it into a structured, semantic **Knowledge Graph**. By leveraging Databricks Foundation Models, AORTA extracts critical biomedical entities (Targets, Compounds, Assays, Pathways, Measurements) and maps them against the standard **BioAssay Ontology (BAO)**.

Beyond extraction, AORTA features a **Hybrid GraphRAG Chatbot** that allows you to chat directly with your ingested documents, utilizing both a FAISS Vector Database for nuanced semantic search and the Ontology Graph for structured relationship queries.

## 🌟 Key Features

- **Native PDF Parsing:** High-performance, multi-column text extraction using `PyMuPDF`.
- **Intelligent Knowledge Extraction:** Uses Databricks LLMs (e.g., Llama-3 70B) to deterministically extract entities and relationships.
- **Entity Normalization:** Automatically deduplicates synonyms and assigns canonical database IDs (NCBI, PubChem, ChEMBL).
- **Interactive Semantic Graph:** Constructs a W3C standard RDF/OWL graph visualized interactively in the browser via `pyvis`.
- **Hybrid GraphRAG Chatbot:** Dual-retrieval chatbot architecture. Queries either the FAISS vector index or the Ontology Graph based on your question.
- **Citation Highlighting:** Transparently displays the exact source text chunks and similarity scores used by the LLM to generate its answers.
- **Session Persistence:** Automatically saves chat histories, vector indices, and graph states to a local SQLite database for seamless session switching.

---

## 🛠️ Prerequisites

To run AORTA, you will need the following API keys configured:

1. **Databricks Workspace:** A host URL and Personal Access Token (PAT) to access Databricks Foundation Model APIs.
2. **NCBI API Key (Optional but recommended):** For accelerated PubMed abstract fetching.

---

## 💻 Local Installation

1. **Clone the repository or extract the ZIP file.**

2. **Install dependencies:**
   Ensure you have Python 3.10+ installed.
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys:**
   Create a `.streamlit/secrets.toml` file in the root directory and add your credentials:
   ```toml
   DATABRICKS_HOST = "https://<your-workspace>.cloud.databricks.com"
   DATABRICKS_TOKEN = "dapi..."
   DATABRICKS_MODEL = "databricks-meta-llama-3-1-70b-instruct"
   NCBI_API_KEY = "your-ncbi-key"
   ```
   *(Note: AORTA also supports reading these directly from OS Environment Variables).*

4. **Run the Application:**
   ```bash
   streamlit run app.py
   ```
   The app will launch in your default web browser at `http://localhost:8501`.

---

## ☁️ Cloud Deployment (Replit)

AORTA is optimized for quick deployment on cloud platforms like **Replit**.

1. Create a new Python workspace on [Replit](https://replit.com/).
2. Upload the project files directly into the Replit file explorer.
3. Open the **Secrets** tool in Replit and add your keys (`DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `NCBI_API_KEY`) as environment variables.
4. Click **Run**. Replit will automatically read the provided `replit.nix` file to install necessary C-libraries (like `freetype` and `rustc`), install `requirements.txt`, and launch the Streamlit app.

---

## 📂 Architecture Overview

- `app.py`: The main Streamlit UI and core extraction pipeline.
- `chatbot_llm.py`: Manages the LLM conversation loop and tool routing.
- `chatbot_tools.py`: Defines the tools (Vector DB Search, Graph Query) that the chatbot can invoke.
- `chat_storage.py`: Handles SQLite operations for persisting chats, graphs, and UI state.
- `vector_db.py`: Manages the FAISS index and sentence-transformers for semantic search.
- `bao_complete.owl`: The base BioAssay Ontology used for mapping semantic relationships.
