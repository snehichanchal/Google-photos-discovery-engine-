#!/usr/bin/env python3
"""
Phase 5 — Task 5.5: Validate Retrieval Quality

Runs a set of test queries against both the dense (ChromaDB) and
sparse (BM25) indices. Generates a markdown report with the top 3
results from each index to verify retrieval quality.

Usage:
    python indexing/test_queries.py
"""

import os
import sys

# Ensure the project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from indexing.vector_store import VectorStore
from indexing.bm25_index import SparseIndex
from indexing.embedder import EmbeddingPipeline


TEST_QUERIES = [
    "I want to find a picture of my dog but the search doesn't work",
    "App crashes when I try to scroll through old photos from years ago",
    "How can I search for text inside a screenshot?",
    "Lost my vacation album from last summer",
    "Facial recognition is grouping two different people together",
    "Can't find downloaded images, they disappear from the gallery",
    "Sorting by date is broken, pictures show up in the wrong year",
    "Is there a way to filter videos only without photos?",
    "Need to recover deleted photos from trash but it's empty",
    "Cannot upload high quality images anymore"
]


def generate_report():
    print("=" * 60)
    print("  Phase 5.5 — Retrieval Quality Validation")
    print("=" * 60)

    # 1. Init pipeline
    print("│  Loading Embedding Model...")
    embedder = EmbeddingPipeline()
    embedder.load_model()
    
    print("│  Connecting to ChromaDB...")
    vstore = VectorStore().connect()
    
    print("│  Loading BM25 Index...")
    sparse = SparseIndex().load()

    report_lines = [
        "# Retrieval Quality Test Report",
        "",
        "This report contains the top 3 results from both the Dense Vector Index (ChromaDB) and Sparse Keyword Index (BM25) for a set of 10 test queries.",
        ""
    ]

    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n│  Testing Query {i}/{len(TEST_QUERIES)}: '{query}'")
        
        report_lines.append(f"## Query {i}: `{query}`\n")
        
        # Dense Query
        query_emb = embedder.model.encode(query, normalize_embeddings=True).tolist()
        dense_results = vstore.query(query_embedding=query_emb, n_results=3)
        
        # Sparse Query
        sparse_results = sparse.query(query_text=query, n_results=3)
        
        # Format Dense
        report_lines.append("### Dense Search (ChromaDB)")
        for j, (doc, meta, dist) in enumerate(zip(
            dense_results["documents"], 
            dense_results["metadatas"], 
            dense_results["distances"]
        ), 1):
            source = meta.get("source", "Unknown")
            rating = meta.get("rating", "")
            rating_str = f" ({rating}/5)" if rating else ""
            # Clean up doc for preview (take first 150 chars of body)
            parts = doc.split("\n\n")
            body = parts[-1].replace("\n", " ")[:150] + "..."
            report_lines.append(f"{j}. **Distance**: {dist:.4f} | **Source**: {source}{rating_str}")
            report_lines.append(f"   > {body}")
        
        # Format Sparse
        report_lines.append("\n### Sparse Search (BM25)")
        for j, (doc, meta, score) in enumerate(zip(
            sparse_results["documents"], 
            sparse_results["metadatas"], 
            sparse_results["scores"]
        ), 1):
            source = meta.get("source", "Unknown")
            rating = meta.get("rating", "")
            rating_str = f" ({rating}/5)" if rating else ""
            parts = doc.split("\n\n")
            body = parts[-1].replace("\n", " ")[:150] + "..."
            report_lines.append(f"{j}. **Score**: {score:.4f} | **Source**: {source}{rating_str}")
            report_lines.append(f"   > {body}")
            
        report_lines.append("\n---\n")
        
    # Write report
    report_path = os.path.join(PROJECT_ROOT, "indexing", "test_queries.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"\n│  Validation complete. Report saved to {report_path}")

if __name__ == "__main__":
    generate_report()
