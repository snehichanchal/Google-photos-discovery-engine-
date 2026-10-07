#!/usr/bin/env python3
"""
Phase 5 — Task 5.3 & 5.4: Full Ingestion Orchestrator

Reads the embedded corpus generated in Phase 4 and ingests it into:
  1. ChromaDB (Dense Vector Store)
  2. BM25 (Sparse Keyword Index)

Implements idempotent indexing: skips documents whose `chunk_id` is already
present in the vector store.

Usage:
    python indexing/ingest.py
"""

import json
import os
import sys
import time

# Ensure the project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from indexing.vector_store import VectorStore
from indexing.bm25_index import SparseIndex


def ingest_corpus(embedded_json_path: str):
    """
    Reads the embedded JSON corpus and ingests it into ChromaDB and BM25.
    """
    if not os.path.exists(embedded_json_path):
        print(f"✗ Error: Embedded corpus not found — {embedded_json_path}")
        print("  Did you run Phase 4 (`indexing/run_phase4.py`) first?")
        sys.exit(1)

    print("=" * 60)
    print("  Phase 5 — Ingestion Orchestrator")
    print("=" * 60)
    print(f"\n│  Loading corpus from {embedded_json_path} ...")
    
    with open(embedded_json_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)
        
    print(f"│  Loaded {len(corpus):,} embedded chunks.\n")
    
    # ── Initialize Stores ─────────────────────────────────────────────────
    
    vstore = VectorStore().connect()
    sparse = SparseIndex()
    
    # ── Deduplication (Task 5.4) ──────────────────────────────────────────
    
    print("─" * 60)
    print("  Deduplication Check")
    print("─" * 60)
    
    existing_ids = vstore.get_existing_ids()
    print(f"│  Found {len(existing_ids):,} existing IDs in ChromaDB.")
    
    chunks_to_ingest = []
    for chunk in corpus:
        if chunk["chunk_id"] not in existing_ids:
            chunks_to_ingest.append(chunk)
            
    skipped = len(corpus) - len(chunks_to_ingest)
    print(f"│  Skipping {skipped:,} already-indexed chunks.")
    print(f"│  Chunks to ingest: {len(chunks_to_ingest):,}\n")
    
    if not chunks_to_ingest:
        print("│  No new chunks to ingest. Exiting.")
        return

    # ── Prepare Data ──────────────────────────────────────────────────────
    
    chunk_ids = [c["chunk_id"] for c in chunks_to_ingest]
    documents = [c["text"] for c in chunks_to_ingest]
    embeddings = [c["embedding"] for c in chunks_to_ingest]
    metadatas = [c["metadata"] for c in chunks_to_ingest]
    
    overall_start = time.time()
    
    # ── 1. ChromaDB Upsert ────────────────────────────────────────────────
    
    print("─" * 60)
    print("  1. Ingesting to ChromaDB (Dense Vector Store)")
    print("─" * 60)
    
    vstore.upsert_chunks(
        chunk_ids=chunk_ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    
    # ── 2. BM25 Rebuild ───────────────────────────────────────────────────
    
    print("\n" + "─" * 60)
    print("  2. Rebuilding BM25 (Sparse Keyword Index)")
    print("─" * 60)
    print("│  Note: BM25 must be rebuilt over the ENTIRE corpus, not just new chunks.")
    
    # For BM25, we need the full corpus. Since the file contains everything, we just use it.
    all_chunk_ids = [c["chunk_id"] for c in corpus]
    all_documents = [c["text"] for c in corpus]
    all_metadatas = [c["metadata"] for c in corpus]
    
    sparse.build(
        chunk_ids=all_chunk_ids,
        documents=all_documents,
        metadatas=all_metadatas
    )
    sparse.save()
    
    # ── Summary ───────────────────────────────────────────────────────────
    
    total_time = time.time() - overall_start
    print("\n" + "=" * 60)
    print("  Phase 5 Ingestion Complete ✓")
    print(f"  Total ingestion time: {total_time:.1f}s")
    print("=" * 60)
    print(f"  ChromaDB Total Documents: {vstore.count():,}")
    print(f"  BM25 Total Documents:     {sparse.count():,}")
    print("=" * 60)


if __name__ == "__main__":
    embedded_json = os.path.join(PROJECT_ROOT, "indexing", "embedded_corpus.json")
    ingest_corpus(embedded_json)
