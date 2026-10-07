"""
Phase 6 — Task 6.2: Hybrid Retriever with Reciprocal Rank Fusion (RRF)

Combines dense vector similarity search (ChromaDB) and sparse keyword search (BM25)
using Reciprocal Rank Fusion (RRF) to retrieve the top candidate document chunks.

Formula:
  RRF_Score(d) = (w_dense / (k + rank_dense(d))) + (w_sparse / (k + rank_sparse(d)))

Architecture Reference: Layer 4 — RAG Query Engine & LLM Synthesis Layer (Section 5)
"""

import os
import sys
from typing import List, Dict, Any, Optional

# Ensure workspace root is in path for imports
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from indexing.vector_store import VectorStore
from indexing.bm25_index import SparseIndex
from indexing.embedder import EmbeddingPipeline
from rag_engine.query_parser import QueryParser


class HybridRetriever:
    """
    Hybrid retriever combining ChromaDB (dense) and BM25 (sparse) indices.
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        sparse_index: Optional[SparseIndex] = None,
        embedder: Optional[EmbeddingPipeline] = None,
        query_parser: Optional[QueryParser] = None,
        k_rrf: int = 60,
        dense_weight: float = 1.0,
        sparse_weight: float = 1.0,
    ):
        self.vector_store = vector_store
        self.sparse_index = sparse_index
        self.embedder = embedder
        self.query_parser = query_parser or QueryParser()
        self.k_rrf = k_rrf
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight

    def load_stores(self):
        """Initialises and connects to vector and sparse indices if not already done."""
        if self.vector_store is None:
            self.vector_store = VectorStore().connect()

        if self.sparse_index is None:
            sparse_path = os.path.join(workspace_root, "indexing", "bm25_index.pkl")
            self.sparse_index = SparseIndex(index_path=sparse_path).load()

        if self.embedder is None:
            self.embedder = EmbeddingPipeline()
            self.embedder.load_model()

    def retrieve(
        self,
        query: str,
        top_k: int = 25,
        candidate_pool_size: int = 50,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval:
          1. Parses and expands query
          2. Dense vector search in ChromaDB
          3. Sparse keyword search in BM25
          4. Reciprocal Rank Fusion (RRF)
          5. Returns top_k candidate chunks

        Returns:
            List of candidate dictionaries sorted by RRF score descending.
            Each dictionary contains:
              - "chunk_id": str
              - "document": str
              - "metadata": dict
              - "rrf_score": float
              - "dense_rank": int or None
              - "sparse_rank": int or None
              - "dense_distance": float or None
              - "sparse_score": float or None
        """
        self.load_stores()

        parsed = self.query_parser.parse(query)
        expanded_query = parsed["expanded_query"] or query

        # ── 1. Dense Search ───────────────────────────────────────────────────
        query_emb = self.embedder.embed_texts([expanded_query], show_progress=False)[0].tolist()
        dense_results = self.vector_store.query(
            query_embedding=query_emb,
            n_results=candidate_pool_size,
            where=where_filter,
        )

        dense_map: Dict[str, Dict[str, Any]] = {}
        for rank, (cid, doc, meta, dist) in enumerate(
            zip(
                dense_results["ids"],
                dense_results["documents"],
                dense_results["metadatas"],
                dense_results["distances"],
            ),
            start=1,
        ):
            dense_map[cid] = {
                "chunk_id": cid,
                "document": doc,
                "metadata": meta,
                "dense_rank": rank,
                "dense_distance": dist,
            }

        # ── 2. Sparse Search ──────────────────────────────────────────────────
        sparse_results = self.sparse_index.query(expanded_query, n_results=candidate_pool_size)

        sparse_map: Dict[str, Dict[str, Any]] = {}
        for rank, (cid, doc, meta, score) in enumerate(
            zip(
                sparse_results["ids"],
                sparse_results["documents"],
                sparse_results["metadatas"],
                sparse_results["scores"],
            ),
            start=1,
        ):
            sparse_map[cid] = {
                "chunk_id": cid,
                "document": doc,
                "metadata": meta,
                "sparse_rank": rank,
                "sparse_score": score,
            }

        # ── 3. Reciprocal Rank Fusion (RRF) ──────────────────────────────────
        all_chunk_ids = set(dense_map.keys()).union(set(sparse_map.keys()))
        fused_candidates: List[Dict[str, Any]] = []

        for cid in all_chunk_ids:
            dense_info = dense_map.get(cid)
            sparse_info = sparse_map.get(cid)

            # Document & metadata from whichever source captured it
            doc = (dense_info or sparse_info)["document"]
            meta = (dense_info or sparse_info)["metadata"]

            rrf_score = 0.0

            dense_rank = dense_info["dense_rank"] if dense_info else None
            if dense_rank is not None:
                rrf_score += self.dense_weight / (self.k_rrf + dense_rank)

            sparse_rank = sparse_info["sparse_rank"] if sparse_info else None
            if sparse_rank is not None:
                rrf_score += self.sparse_weight / (self.k_rrf + sparse_rank)

            fused_candidates.append(
                {
                    "chunk_id": cid,
                    "document": doc,
                    "metadata": meta,
                    "rrf_score": rrf_score,
                    "dense_rank": dense_rank,
                    "sparse_rank": sparse_rank,
                    "dense_distance": dense_info["dense_distance"] if dense_info else None,
                    "sparse_score": sparse_info["sparse_score"] if sparse_info else None,
                }
            )

        # Sort by RRF score descending
        fused_candidates.sort(key=lambda x: x["rrf_score"], reverse=True)

        return fused_candidates[:top_k]


# ── Quick CLI Test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    retriever = HybridRetriever()
    test_q = "photos disappearing after backup and sync failure"
    print(f"=== Hybrid Retriever Test ===")
    print(f"Query: {test_q}")

    results = retriever.retrieve(test_q, top_k=5)
    print(f"\nTop {len(results)} RRF Candidates:")
    for i, res in enumerate(results, 1):
        print(f"\n[{i}] ID: {res['chunk_id']} | RRF Score: {res['rrf_score']:.5f}")
        print(f"    Dense Rank: {res['dense_rank']} | Sparse Rank: {res['sparse_rank']}")
        print(f"    Source: {res['metadata'].get('source')} | Review ID: {res['metadata'].get('review_id')}")
        print(f"    Doc Snippet: {res['document'][:120]}...")
