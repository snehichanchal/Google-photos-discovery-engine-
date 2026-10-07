"""
Phase 7 — Task 7.1: PM Q&A Console

Interactive console for Product Managers and UX Researchers to submit natural language
queries to the Google Photos RAG engine and receive grounded, cited insights.

Features:
  - Natural language Q&A input
  - Execution via RAGPipeline (hybrid retrieval + reranking + guardrailed LLM synthesis)
  - Full citation output with review_id, source, and date
  - Stage latency breakdown
  - Markdown export capability

Architecture Reference: Layer 5 — Internal Application & Insights Layer (Section 5)
"""

import os
import sys
import time
import json
from typing import Dict, Any, Optional

# Ensure workspace root is in path
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from rag_engine.pipeline import RAGPipeline


class PMConsole:
    """
    Console wrapper for the RAG Query Engine.
    """

    def __init__(self, pipeline: Optional[RAGPipeline] = None):
        self.pipeline = pipeline or RAGPipeline()

    def ask(self, query: str, top_k: int = 25, top_n: int = 7) -> Dict[str, Any]:
        """
        Executes a query through the RAG pipeline.
        """
        if not query or not query.strip():
            return {"error": "Empty query provided."}

        return self.pipeline.run(query, top_k_retrieval=top_k, top_n_rerank=top_n)

    def export_to_markdown(self, result: Dict[str, Any], output_path: str) -> str:
        """
        Exports a query result to a markdown file.
        """
        query = result["query"]
        answer = result["synthesized_answer"]
        citations = result["citations"]
        timings = result["stage_timings"]

        md = f"# PM Q&A Insights Export\n\n"
        md += f"> **Query**: *\"{query}\"*\n"
        md += f"> **Export Date**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
        md += f"> **Execution Time**: {result['execution_time_sec']}s (Synthesizer Mode: `{result['synthesizer_mode']}`)\n\n"

        md += "---\n\n"
        md += answer + "\n\n"

        md += "---\n\n"
        md += "### Retrieved Citation Details\n\n"
        md += "| # | Review ID | Source | Date | URL |\n"
        md += "|:---|:---|:---|:---|:---|\n"
        for i, c in enumerate(citations, start=1):
            md += f"| {i} | `{c.get('review_id')}` | {c.get('source')} | {c.get('date')} | [Link]({c.get('url')}) |\n"

        md += "\n---\n\n"
        md += "### Pipeline Performance Timings\n\n"
        md += f"- **Query Parsing & Expansion**: {timings.get('parse_expansion_sec', 0):.4f}s\n"
        md += f"- **Hybrid Retrieval (Dense + BM25 RRF)**: {timings.get('hybrid_retrieval_sec', 0):.4f}s\n"
        md += f"- **Cross-Encoder Reranking**: {timings.get('reranking_sec', 0):.4f}s\n"
        md += f"- **LLM Synthesis**: {timings.get('synthesis_sec', 0):.4f}s\n"
        md += f"- **Total Latency**: {result['execution_time_sec']:.4f}s\n"

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)

        return output_path


def run_interactive_cli():
    """
    Runs the PM Q&A Console interactively in the terminal.
    """
    print("=" * 70)
    print(" Google Photos AI Retrieval Discovery Engine — PM Q&A Console")
    print("=" * 70)
    print("Initialising RAG Engine models (ChromaDB + BM25 + CrossEncoder)...")

    console = PMConsole()
    print("✓ Ready! Enter your question below (or type 'exit' / 'q' to quit).\n")

    exports_dir = os.path.join(workspace_root, "app", "exports")

    while True:
        try:
            user_input = input("\n[PM Query] > ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("Exiting PM Q&A Console. Goodbye!")
                break

            print(f"\nSearching vector store and synthesizing evidence...")
            result = console.ask(user_input)

            print("\n" + "=" * 70)
            print(result["synthesized_answer"])
            print("=" * 70)
            print(f"Latency: {result['execution_time_sec']}s | Citations: {len(result['citations'])}")

            save_choice = input("\nExport answer to Markdown file? (y/n) [n]: ").strip().lower()
            if save_choice == "y":
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"query_export_{timestamp}.md"
                out_path = os.path.join(exports_dir, filename)
                console.export_to_markdown(result, out_path)
                print(f"✓ Exported to {out_path}")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting console.")
            break


if __name__ == "__main__":
    run_interactive_cli()
