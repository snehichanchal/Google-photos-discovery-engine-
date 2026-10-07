"""
Phase 4 — Task 4.2: Dense Embedding Pipeline

Converts chunked documents into 384-dimensional dense vector embeddings
using the `all-MiniLM-L6-v2` model from SentenceTransformers.

Features:
  - Batch embedding with configurable batch size
  - Progress reporting with ETA
  - Outputs a JSON file containing chunk data + embedding vectors
  - Also outputs a standalone .npy file for fast numpy-based loading

Input:  indexing/chunked_corpus.json
Output: indexing/embedded_corpus.json
        indexing/embeddings.npy  (numpy array of shape [N, 384])
"""

import json
import os
import sys
import time
import numpy as np
from sentence_transformers import SentenceTransformer


# ── Constants ─────────────────────────────────────────────────────────────────

MODEL_NAME         = "all-MiniLM-L6-v2"
EMBEDDING_DIM      = 384
DEFAULT_BATCH_SIZE = 128


# ── Embedding Pipeline ────────────────────────────────────────────────────────

class EmbeddingPipeline:
    """
    Wraps SentenceTransformer to produce dense embeddings
    for chunked review documents.
    """

    def __init__(self, model_name: str = MODEL_NAME, batch_size: int = DEFAULT_BATCH_SIZE):
        self.model_name = model_name
        self.batch_size = batch_size
        self.model = None
        self._embedding_dim = EMBEDDING_DIM

    def load_model(self):
        """Load the SentenceTransformer model (lazy initialization)."""
        if self.model is None:
            print(f"│  Loading model: {self.model_name} ...")
            self.model = SentenceTransformer(self.model_name)
            # Use the newer API name; fall back to legacy if unavailable
            if hasattr(self.model, "get_embedding_dimension"):
                self._embedding_dim = self.model.get_embedding_dimension()
            else:
                self._embedding_dim = self.model.get_sentence_embedding_dimension()
            print(f"│  Model loaded — Embedding dim: {self._embedding_dim}")
        return self.model

    @property
    def embedding_dim(self) -> int:
        return self._embedding_dim

    def embed_texts(self, texts: list[str], show_progress: bool = True) -> np.ndarray:
        """
        Embed a list of texts into dense vectors.

        Args:
            texts: List of document strings to embed.
            show_progress: Whether to print batch progress.

        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        model = self.load_model()
        total = len(texts)
        num_batches = (total + self.batch_size - 1) // self.batch_size

        all_embeddings = []
        start_time = time.time()

        for batch_idx in range(num_batches):
            batch_start = batch_idx * self.batch_size
            batch_end = min(batch_start + self.batch_size, total)
            batch_texts = texts[batch_start:batch_end]

            batch_embeddings = model.encode(
                batch_texts,
                show_progress_bar=False,
                normalize_embeddings=True,    # L2-normalize for cosine similarity
                convert_to_numpy=True,
            )
            all_embeddings.append(batch_embeddings)

            if show_progress:
                elapsed = time.time() - start_time
                progress = batch_end / total
                eta = (elapsed / progress - elapsed) if progress > 0 else 0
                print(
                    f"│  Batch {batch_idx + 1}/{num_batches}  "
                    f"[{batch_end:,}/{total:,}]  "
                    f"{progress * 100:.1f}%  "
                    f"ETA: {eta:.0f}s",
                    flush=True,
                )

        embeddings = np.vstack(all_embeddings)
        total_time = time.time() - start_time
        print(f"│  Embedding complete in {total_time:.1f}s  "
              f"({total / total_time:.0f} docs/sec)")

        return embeddings


# ── Corpus-Level Embedding ────────────────────────────────────────────────────

def embed_corpus(
    input_path: str,
    output_json_path: str,
    output_npy_path: str,
    model_name: str = MODEL_NAME,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> tuple[list[dict], np.ndarray]:
    """
    Reads the chunked corpus, embeds every chunk, and saves outputs.

    Args:
        input_path:       Path to chunked_corpus.json
        output_json_path: Path to write embedded_corpus.json
        output_npy_path:  Path to write embeddings.npy
        model_name:       SentenceTransformer model name
        batch_size:       Batch size for encoding

    Returns:
        (chunks, embeddings) — the chunk list and embedding numpy array
    """
    if not os.path.exists(input_path):
        print(f"✗ Error: Input file not found — {input_path}")
        sys.exit(1)

    print(f"╭─ Phase 4.2 — Dense Embedding Pipeline")
    print(f"│  Input:       {input_path}")
    print(f"│  Output JSON: {output_json_path}")
    print(f"│  Output NPY:  {output_npy_path}")
    print(f"│  Model:       {model_name}")
    print(f"│")

    # ── Load chunks ───────────────────────────────────────────────────────
    with open(input_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"│  Loaded {len(chunks):,} chunks")
    print(f"│")

    # ── Extract texts & embed ─────────────────────────────────────────────
    texts = [chunk["text"] for chunk in chunks]

    pipeline = EmbeddingPipeline(model_name=model_name, batch_size=batch_size)
    embeddings = pipeline.embed_texts(texts)

    # ── Attach embeddings to chunks (as lists for JSON serialization) ─────
    embedded_chunks = []
    for chunk, emb_vec in zip(chunks, embeddings):
        embedded_chunk = dict(chunk)
        embedded_chunk["embedding"] = emb_vec.tolist()
        embedded_chunks.append(embedded_chunk)

    # ── Save outputs ──────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(output_json_path) or ".", exist_ok=True)

    print(f"│")
    print(f"│  Saving embedded corpus JSON ...")
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(embedded_chunks, f, indent=2, ensure_ascii=False)
    json_size = os.path.getsize(output_json_path)
    print(f"│  Saved: {output_json_path}  ({json_size / 1024 / 1024:.1f} MB)")

    print(f"│  Saving embeddings numpy array ...")
    np.save(output_npy_path, embeddings)
    npy_size = os.path.getsize(output_npy_path)
    print(f"│  Saved: {output_npy_path}  ({npy_size / 1024:.1f} KB)")

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"│")
    print(f"│  ── Summary ──────────────────────────────")
    print(f"│  Total chunks embedded:  {len(chunks):,}")
    print(f"│  Embedding dimensions:   {pipeline.embedding_dim}")
    print(f"│  Embeddings matrix:      {embeddings.shape}")
    print(f"│  Normalized (L2):        Yes")
    print(f"╰─ ✓ Embedding generation complete")
    print()

    return embedded_chunks, embeddings


# ── CLI Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    input_file = os.path.join(project_root, "indexing", "chunked_corpus.json")
    output_json = os.path.join(project_root, "indexing", "embedded_corpus.json")
    output_npy  = os.path.join(project_root, "indexing", "embeddings.npy")

    embed_corpus(input_file, output_json, output_npy)
