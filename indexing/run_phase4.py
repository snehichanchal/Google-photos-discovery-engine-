#!/usr/bin/env python3
"""
Phase 4 — Full Pipeline Runner

Orchestrates both Phase 4 tasks in sequence:
  1. Chunking  (enriched_corpus.json → chunked_corpus.json)
  2. Embedding (chunked_corpus.json  → embedded_corpus.json + embeddings.npy)

Usage:
    python indexing/run_phase4.py
"""

import os
import sys
import time

# Ensure the project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from indexing.chunker import process_corpus as run_chunking
from indexing.embedder import embed_corpus as run_embedding


def main():
    print("=" * 60)
    print("  Phase 4 — Chunking & Embedding Generation")
    print("=" * 60)
    print()

    # ── File paths ────────────────────────────────────────────────────────
    enriched_corpus = os.path.join(PROJECT_ROOT, "data_processing", "enriched_corpus.json")
    chunked_corpus  = os.path.join(PROJECT_ROOT, "indexing", "chunked_corpus.json")
    embedded_json   = os.path.join(PROJECT_ROOT, "indexing", "embedded_corpus.json")
    embeddings_npy  = os.path.join(PROJECT_ROOT, "indexing", "embeddings.npy")

    overall_start = time.time()

    # ── Step 1: Chunking ──────────────────────────────────────────────────
    print("─" * 60)
    print("  Step 1/2: Chunking Enriched Corpus")
    print("─" * 60)
    print()

    chunks = run_chunking(enriched_corpus, chunked_corpus)

    # ── Step 2: Embedding ─────────────────────────────────────────────────
    print("─" * 60)
    print("  Step 2/2: Generating Dense Embeddings")
    print("─" * 60)
    print()

    embedded_chunks, embeddings = run_embedding(
        chunked_corpus,
        embedded_json,
        embeddings_npy,
    )

    # ── Final Summary ─────────────────────────────────────────────────────
    total_time = time.time() - overall_start
    print("=" * 60)
    print("  Phase 4 Complete ✓")
    print(f"  Total time: {total_time:.1f}s")
    print()
    print(f"  Outputs:")
    print(f"    • {chunked_corpus}")
    print(f"    • {embedded_json}")
    print(f"    • {embeddings_npy}")
    print("=" * 60)


if __name__ == "__main__":
    main()
