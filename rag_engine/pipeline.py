"""
Phase 6 — Task 6.6: End-to-End RAG Pipeline Orchestrator

Orchestrates the full RAG query lifecycle:
  User Query ➔ Query Parsing & Synonym Expansion ➔ Hybrid Retrieval (Dense + BM25 RRF)
  ➔ Cross-Encoder Reranking (Top 25 ➔ Top 7) ➔ LLM Synthesis with Guardrails & Citations

Architecture Reference: Layer 4 — RAG Query Engine & LLM Synthesis Layer (Section 5)
"""

import os
import sys
import time
from typing import List, Dict, Any, Optional

# Ensure workspace root is in path
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from rag_engine.query_parser import QueryParser
from rag_engine.hybrid_retriever import HybridRetriever
from rag_engine.reranker import Reranker
from rag_engine.llm_synthesizer import LLMSynthesizer


class RAGPipeline:
    """
    End-to-End RAG Pipeline Orchestrator.
    """

    def __init__(
        self,
        query_parser: Optional[QueryParser] = None,
        retriever: Optional[HybridRetriever] = None,
        reranker: Optional[Reranker] = None,
        synthesizer: Optional[LLMSynthesizer] = None,
    ):
        self.query_parser = query_parser or QueryParser()
        self.retriever = retriever or HybridRetriever(query_parser=self.query_parser)
        self.reranker = reranker or Reranker()
        self.synthesizer = synthesizer or LLMSynthesizer()

    def run(
        self,
        query: str,
        top_k_retrieval: int = 25,
        top_n_rerank: int = 7,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes the end-to-end RAG pipeline for a given query.

        Args:
            query: Natural language question from stakeholder
            top_k_retrieval: Number of candidate chunks from hybrid retrieval (default 25)
            top_n_rerank: Number of reranked context chunks for LLM (default 7)
            where_filter: Optional metadata filter for ChromaDB retrieval

        Returns:
            Dict containing full pipeline execution output:
              - "query": str
              - "parsed_query": dict
              - "retrieved_candidates_count": int
              - "reranked_context": List[dict]
              - "synthesized_answer": str
              - "citations": List[dict]
              - "execution_time_sec": float
              - "stage_timings": dict
        """
        start_total = time.time()
        stage_timings = {}

        # ── Stage 1: Query Parsing & Expansion ────────────────────────────────
        t0 = time.time()
        parsed = self.query_parser.parse(query)
        stage_timings["parse_expansion_sec"] = round(time.time() - t0, 4)

        # ── Stage 2: Hybrid Retrieval (Dense + BM25 RRF) ──────────────────────
        t0 = time.time()
        candidates = self.retriever.retrieve(
            query=query,
            top_k=top_k_retrieval,
            where_filter=where_filter,
        )
        stage_timings["hybrid_retrieval_sec"] = round(time.time() - t0, 4)

        # ── Stage 3: Cross-Encoder Reranking ──────────────────────────────────
        t0 = time.time()
        reranked_context = self.reranker.rerank(
            query=query,
            candidates=candidates,
            top_n=top_n_rerank,
        )
        stage_timings["reranking_sec"] = round(time.time() - t0, 4)

        # ── Stage 4: LLM Synthesis with Guardrails ─────────────────────────────
        t0 = time.time()
        synthesis = self.synthesizer.synthesize(
            query=query,
            context_chunks=reranked_context,
        )
        stage_timings["synthesis_sec"] = round(time.time() - t0, 4)

        total_elapsed = round(time.time() - start_total, 4)

        return {
            "query": query,
            "parsed_query": parsed,
            "retrieved_candidates_count": len(candidates),
            "reranked_context": reranked_context,
            "synthesized_answer": synthesis["answer"],
            "citations": synthesis["citations"],
            "synthesizer_mode": synthesis["synthesizer_mode"],
            "execution_time_sec": total_elapsed,
            "stage_timings": stage_timings,
        }


# ── Quick CLI Test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== RAG Pipeline Orchestrator Test ===")
    pipeline = RAGPipeline()
    test_query = "Why are users complaining about missing screenshots and OCR text search?"
    
    print(f"\nSubmitting Query: '{test_query}' ...\n")
    result = pipeline.run(test_query)

    print(f"✓ Pipeline finished in {result['execution_time_sec']}s")
    print(f"  Stage Timings: {result['stage_timings']}")
    print(f"  Candidates Retrieved: {result['retrieved_candidates_count']}")
    print(f"  Reranked Context Size: {len(result['reranked_context'])}")
    print(f"  Synthesizer Mode: {result['synthesizer_mode']}")
    print(f"  Citations Count: {len(result['citations'])}")
    print("\n--- SYNTHESIZED ANSWER ---")
    print(result["synthesized_answer"][:800])
