"""
Vector DB Layer
================
Implements an in-memory FAISS index backed by sentence-transformers
for semantic search over document text chunks.
"""
import logging
import pickle
import numpy as np
from pathlib import Path
from typing import Any

try:
    import faiss
    from sentence_transformers import SentenceTransformer
except ImportError:
    faiss = None
    SentenceTransformer = None

INDEX_PATH = Path(__file__).parent / "vector_index.pkl"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

class DocumentVectorDB:
    def __init__(self):
        self.chunks = []
        self.index = None
        self.model = None
        
        if faiss is not None and SentenceTransformer is not None:
            # We don't load the model until first use to save memory on startup
            pass

    def _lazy_init(self):
        if self.model is None:
            if SentenceTransformer is None:
                raise RuntimeError("sentence-transformers is not installed.")
            self.model = SentenceTransformer(EMBEDDING_MODEL)
            
        if self.index is None and self.chunks:
            # If we loaded chunks but haven't rebuilt the index yet
            self._rebuild_index()

    def _rebuild_index(self):
        if not self.chunks:
            self.index = None
            return
            
        dimension = len(self.chunks[0]["embedding"])
        self.index = faiss.IndexFlatL2(dimension)
        
        # Collect all embeddings
        embeddings = np.array([c["embedding"] for c in self.chunks], dtype=np.float32)
        self.index.add(embeddings)

    def load(self):
        if INDEX_PATH.exists():
            try:
                with open(INDEX_PATH, "rb") as f:
                    self.chunks = pickle.load(f)
                self.index = None # Will lazy init on query
            except Exception as e:
                logging.error(f"Failed to load vector index: {e}")
                self.chunks = []

    def set_chunks(self, chunks: list[dict[str, Any]]):
        """Restore vector chunks from storage and rebuild index."""
        self.chunks = chunks
        self._rebuild_index()

    def save(self):
        with open(INDEX_PATH, "wb") as f:
            pickle.dump(self.chunks, f)

    def chunk_text(self, text: str, max_tokens_approx: int = 400) -> list[str]:
        """Simple chunker splitting by double newlines or sentences, capping by length."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            # Roughly 1 token ~ 4 chars
            if len(current_chunk) + len(p) > max_tokens_approx * 4:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = p
            else:
                current_chunk += "\n" + p if current_chunk else p
                
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    def add_document(self, title: str, pmid: str, text: str):
        """Chunk, embed, and add a document to the index."""
        if SentenceTransformer is None:
            return  # Fail silently if dependencies aren't met
            
        self._lazy_init()
        doc_id = f"PMID_{pmid}" if pmid else "Document"
        
        raw_chunks = self.chunk_text(text)
        if not raw_chunks:
            return
            
        embeddings = self.model.encode(raw_chunks, convert_to_numpy=True)
        
        for i, (chunk_text, emb) in enumerate(zip(raw_chunks, embeddings)):
            self.chunks.append({
                "source_doc": doc_id,
                "title": title,
                "chunk_id": f"{doc_id}_chunk_{i}",
                "text": chunk_text,
                "embedding": emb.tolist()
            })
            
        self._rebuild_index()
        self.save()

    def query(self, query: str, top_k: int = 15) -> list[dict[str, Any]]:
        """Query the vector database semantically."""
        if SentenceTransformer is None:
            return [{"error": "sentence-transformers/faiss are not installed."}]
            
        if not self.chunks:
            return []
            
        self._lazy_init()
        
        q_emb = self.model.encode([query], convert_to_numpy=True).astype(np.float32)
        distances, indices = self.index.search(q_emb, min(top_k, len(self.chunks)))
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1: continue
            chunk = self.chunks[idx]
            # Convert L2 distance to an intuitive similarity score (1 = exact, 0 = distant)
            # Standard faiss L2 distance range varies; invert roughly for display
            sim_score = float(max(0.0, 1.0 - (distances[0][i] / 50.0)))
            results.append({
                "source_doc": chunk["title"] or chunk["source_doc"],
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "similarity_score": round(sim_score, 3)
            })
            
        return results

# Singleton instance
vector_db = DocumentVectorDB()
vector_db.load()

# Tool wrapper for chatbot
def query_vector_db(query: str, top_k: int = 15) -> list[dict[str, Any]]:
    """
    Search document text semantically for nuance, methodology, or qualitative 
    descriptions not captured as entities/relationships.
    """
    return vector_db.query(query, top_k=top_k)
