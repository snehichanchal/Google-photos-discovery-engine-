"""
Phase 5 — Task 5.2: BM25 Sparse Index

Creates and manages a BM25 inverted index for keyword-based retrieval.
This complements the dense vector store for hybrid RRF retrieval (Phase 6).

Features:
  - Tokenization strategy for review text
  - BM25Okapi implementation via rank_bm25
  - Serialization to/from disk (pickle)
  - Keyword query interface

Architecture Reference: Layer 3 — Vector Indexing & Knowledge Store (Section 4)
"""

import os
import pickle
import string
from typing import List, Dict, Any

from rank_bm25 import BM25Okapi


# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_INDEX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bm25_index.pkl")


# ── Tokenizer ─────────────────────────────────────────────────────────────────

def tokenize(text: str) -> List[str]:
    """
    Basic tokenization for BM25: lowercase, remove punctuation, split on whitespace.
    For a production system, this might use NLTK or spaCy.
    """
    if not text:
        return []
    
    # Lowercase
    text = text.lower()
    
    # Remove punctuation
    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator)
    
    # Split
    return text.split()


# ── BM25Index Class ───────────────────────────────────────────────────────────

class SparseIndex:
    """
    Manages the BM25 keyword index over the chunked documents.
    Stores the BM25 model and a mapping back to the chunk metadata.
    """

    def __init__(self, index_path: str = DEFAULT_INDEX_PATH):
        self.index_path = index_path
        self.bm25: BM25Okapi | None = None
        
        # Parallel arrays mapping the bm25 corpus index to chunk details
        self.chunk_ids: List[str] = []
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []

    # ── Building ──────────────────────────────────────────────────────────

    def build(self, chunk_ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]):
        """
        Builds the BM25 index from a list of documents.
        """
        print(f"│  Building BM25 index over {len(documents):,} documents...")
        
        # Tokenize the corpus
        tokenized_corpus = [tokenize(doc) for doc in documents]
        
        # Build BM25 Okapi model
        self.bm25 = BM25Okapi(tokenized_corpus)
        
        # Store metadata mappings
        self.chunk_ids = chunk_ids
        self.documents = documents
        self.metadatas = metadatas
        
        print("│  BM25 index built successfully.")

    # ── I/O ───────────────────────────────────────────────────────────────

    def save(self):
        """Serializes the index and mappings to disk."""
        if self.bm25 is None:
            raise RuntimeError("Cannot save an empty index. Call .build() first.")
            
        print(f"│  Saving BM25 index to {self.index_path}...")
        
        data = {
            "bm25": self.bm25,
            "chunk_ids": self.chunk_ids,
            "documents": self.documents,
            "metadatas": self.metadatas
        }
        
        os.makedirs(os.path.dirname(self.index_path) or ".", exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump(data, f)
            
        file_size = os.path.getsize(self.index_path)
        print(f"│  Saved BM25 index ({file_size / 1024 / 1024:.1f} MB)")

    def load(self):
        """Loads the serialized index from disk."""
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(f"BM25 index file not found: {self.index_path}")
            
        print(f"│  Loading BM25 index from {self.index_path}...")
        
        with open(self.index_path, "rb") as f:
            data = pickle.load(f)
            
        self.bm25 = data["bm25"]
        self.chunk_ids = data["chunk_ids"]
        self.documents = data["documents"]
        self.metadatas = data["metadatas"]
        
        print(f"│  Loaded BM25 index with {len(self.chunk_ids):,} documents.")
        return self

    # ── Querying ──────────────────────────────────────────────────────────

    def query(self, query_text: str, n_results: int = 25) -> Dict[str, Any]:
        """
        Searches the BM25 index.
        
        Returns a dict matching the ChromaDB output format for easy fusion:
            { "ids": [...], "documents": [...], "metadatas": [...], "scores": [...] }
        """
        if self.bm25 is None:
            raise RuntimeError("Index not loaded. Call .load() or .build() first.")
            
        tokenized_query = tokenize(query_text)
        
        # Get raw scores
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top N indices
        # argsort sorts ascending, so we take the last N and reverse
        import numpy as np
        top_indices = np.argsort(scores)[-n_results:][::-1]
        
        # Filter out 0-score results (no keyword match)
        valid_indices = [idx for idx in top_indices if scores[idx] > 0]
        
        results = {
            "ids": [self.chunk_ids[i] for i in valid_indices],
            "documents": [self.documents[i] for i in valid_indices],
            "metadatas": [self.metadatas[i] for i in valid_indices],
            "scores": [float(scores[i]) for i in valid_indices]
        }
        
        return results

    def count(self) -> int:
        return len(self.chunk_ids)


# ── CLI Test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    idx = SparseIndex()
    if os.path.exists(idx.index_path):
        idx.load()
        print(f"\nIndex count: {idx.count()}")
    else:
        print("\nIndex not built yet.")
