"""
Phase 6 — Task 6.3: Cross-Encoder Reranker Module

Rescores and reranks the top-25 candidates retrieved by the HybridRetriever
down to the top-7 highest-relevance context chunks using a cross-encoder model.

Model: `cross-encoder/ms-marco-MiniLM-L-6-v2`

Architecture Reference: Layer 4 — RAG Query Engine & LLM Synthesis Layer (Section 5)
"""

import os
import sys
from typing import List, Dict, Any, Optional

from sentence_transformers import CrossEncoder

DEFAULT_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class Reranker:
    """
    Reranks candidate document chunks using a sentence-transformers CrossEncoder.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        self.model: Optional[CrossEncoder] = None

    def load_model(self):
        """Lazy loads the CrossEncoder model."""
        if self.model is None:
            print(f"│  Loading Reranker CrossEncoder: {self.model_name} ...")
            self.model = CrossEncoder(self.model_name)
            print(f"│  CrossEncoder loaded successfully.")
        return self.model

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_n: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Reranks a list of candidate chunk dictionaries for a given query.

        Args:
            query: User query string
            candidates: List of candidate chunk dicts (from HybridRetriever)
            top_n: Number of top reranked chunks to return (default 7)

        Returns:
            List of top_n candidate dicts sorted by cross_encoder_score descending.
        """
        if not candidates:
            return []

        model = self.load_model()

        # Build (query, text) pairs
        pairs = [(query, cand["document"]) for cand in candidates]

        # Predict cross-encoder relevance scores
        scores = model.predict(pairs)

        reranked: List[Dict[str, Any]] = []
        for cand, score in zip(candidates, scores):
            item = dict(cand)
            item["cross_encoder_score"] = float(score)
            reranked.append(item)

        # Sort descending by cross-encoder score
        reranked.sort(key=lambda x: x["cross_encoder_score"], reverse=True)

        # Assign rerank position
        for i, item in enumerate(reranked, start=1):
            item["rerank_position"] = i

        return reranked[:top_n]


# ── Quick CLI Test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from rag_engine.hybrid_retriever import HybridRetriever

    retriever = HybridRetriever()
    candidates = retriever.retrieve("photos disappearing after backup sync failure", top_k=25)

    reranker = Reranker()
    top7 = reranker.rerank("photos disappearing after backup sync failure", candidates, top_n=7)

    print("\n=== Cross-Encoder Reranker Test ===")
    print(f"Reranked top {len(top7)} chunks:")
    for item in top7:
        print(f"\n[Rank {item['rerank_position']}] ID: {item['chunk_id']} | Score: {item['cross_encoder_score']:.4f}")
        print(f"    Source: {item['metadata'].get('source')} | Review ID: {item['metadata'].get('review_id')}")
        print(f"    Snippet: {item['document'][:120]}...")
