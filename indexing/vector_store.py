"""
Phase 5 — Task 5.1: ChromaDB Vector Store

Manages the persistent ChromaDB collection for dense vector retrieval.

Features:
  - Persistent local storage (indexing/chroma_db/)
  - Cosine similarity distance metric
  - Collection schema with full metadata fields for filtered retrieval
  - Batch upsert with review_id-based deduplication (Task 5.4)
  - Query interface returning ranked results with scores

Architecture Reference: Layer 3 — Vector Indexing & Knowledge Store (Section 4)
"""

import os
import sys
import chromadb
from chromadb.config import Settings


# ── Constants ─────────────────────────────────────────────────────────────────

COLLECTION_NAME = "google_photos_reviews"
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
UPSERT_BATCH_SIZE = 200   # ChromaDB recommends batches ≤ 5000


# ── ChromaDB Metadata Sanitiser ───────────────────────────────────────────────

def _sanitise_metadata(meta: dict) -> dict:
    """
    ChromaDB only accepts str, int, float, bool metadata values.
    Convert None → "" and ensure all values are primitive.
    """
    clean = {}
    for k, v in meta.items():
        if v is None:
            clean[k] = ""
        elif isinstance(v, (str, int, float, bool)):
            clean[k] = v
        else:
            clean[k] = str(v)
    return clean


# ── VectorStore Class ─────────────────────────────────────────────────────────

class VectorStore:
    """
    Wrapper around a persistent ChromaDB collection for the
    Google Photos Discovery Engine.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH, collection_name: str = COLLECTION_NAME):
        self.db_path = db_path
        self.collection_name = collection_name
        self._client = None
        self._collection = None

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def connect(self):
        """Initialise the persistent ChromaDB client and get/create the collection."""
        os.makedirs(self.db_path, exist_ok=True)

        self._client = chromadb.PersistentClient(path=self.db_path)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},   # cosine similarity
        )

        count = self._collection.count()
        print(f"│  ChromaDB connected — collection '{self.collection_name}'")
        print(f"│  DB path:  {self.db_path}")
        print(f"│  Existing documents: {count:,}")
        return self

    @property
    def collection(self):
        if self._collection is None:
            raise RuntimeError("Call .connect() before accessing the collection.")
        return self._collection

    @property
    def client(self):
        if self._client is None:
            raise RuntimeError("Call .connect() before accessing the client.")
        return self._client

    # ── Deduplication (Task 5.4) ──────────────────────────────────────────

    def get_existing_ids(self) -> set[str]:
        """Returns the set of chunk_ids already stored in the collection."""
        count = self.collection.count()
        if count == 0:
            return set()

        # Fetch all IDs (ChromaDB supports get with no filter to return all)
        result = self.collection.get(include=[])
        return set(result["ids"])

    # ── Upsert ────────────────────────────────────────────────────────────

    def upsert_chunks(
        self,
        chunk_ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
        batch_size: int = UPSERT_BATCH_SIZE,
    ) -> int:
        """
        Upserts chunks into the ChromaDB collection in batches.
        Uses chunk_id as the document ID for deduplication.

        Returns the number of documents upserted.
        """
        total = len(chunk_ids)
        upserted = 0

        for start in range(0, total, batch_size):
            end = min(start + batch_size, total)

            batch_ids = chunk_ids[start:end]
            batch_docs = documents[start:end]
            batch_embs = embeddings[start:end]
            batch_metas = [_sanitise_metadata(m) for m in metadatas[start:end]]

            self.collection.upsert(
                ids=batch_ids,
                documents=batch_docs,
                embeddings=batch_embs,
                metadatas=batch_metas,
            )
            upserted += len(batch_ids)

            progress = upserted / total * 100
            print(f"│  Upserted {upserted:,}/{total:,}  ({progress:.0f}%)", flush=True)

        return upserted

    # ── Query ─────────────────────────────────────────────────────────────

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 25,
        where: dict | None = None,
    ) -> dict:
        """
        Performs a dense vector similarity search.

        Args:
            query_embedding: 384-dim query vector
            n_results:       Number of results to return
            where:           Optional ChromaDB metadata filter

        Returns:
            Dict with keys: ids, documents, metadatas, distances
        """
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        results = self.collection.query(**kwargs)

        # Flatten from batch-of-1 to single lists
        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
        }

    def query_by_text(
        self,
        query_text: str,
        embedding_fn,
        n_results: int = 25,
        where: dict | None = None,
    ) -> dict:
        """
        Convenience method: embeds the query text then searches.

        Args:
            query_text:   Natural language query string
            embedding_fn: Callable(text) -> list[float]
            n_results:    Number of results
            where:        Optional metadata filter

        Returns:
            Same dict as .query()
        """
        query_emb = embedding_fn(query_text)
        return self.query(query_emb, n_results=n_results, where=where)

    # ── Stats ─────────────────────────────────────────────────────────────

    def count(self) -> int:
        """Returns the total number of documents in the collection."""
        return self.collection.count()

    def reset(self):
        """Deletes and recreates the collection. Use with caution."""
        self.client.delete_collection(self.collection_name)
        self._collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        print(f"│  ⚠ Collection '{self.collection_name}' reset")


# ── CLI Test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    store = VectorStore()
    store.connect()
    print(f"\nCollection count: {store.count()}")
