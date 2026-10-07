"""
Phase 4 — Task 4.1: Document Chunking Strategy

Converts the enriched, taxonomy-tagged corpus into chunked documents
suitable for dense embedding. Each chunk is a self-contained "rich document"
that prepends populated metadata + taxonomy fields to the review text.

Strategy:
  - Reviews ≤ 300 words → single rich document (vast majority, ~97%)
  - Reviews > 300 words → sliding window (250 words, 50 word overlap)
  - Taxonomy fields with "Not specified" are excluded from the header
  - Each chunk carries its own metadata dict for vector store ingestion

Input:  data_processing/enriched_corpus.json
Output: indexing/chunked_corpus.json
"""

import json
import os
import sys
import hashlib
from datetime import datetime


# ── Constants ─────────────────────────────────────────────────────────────────

MAX_SINGLE_DOC_WORDS = 300   # Reviews at or under this → single chunk
SLIDING_WINDOW_SIZE  = 250   # Words per window for long reviews
SLIDING_OVERLAP      = 50    # Overlap between consecutive windows

TAXONOMY_DISPLAY_ORDER = [
    "user_memory",
    "retrieval_intent",
    "search_behavior",
    "retrieval_failure",
    "underlying_problem",
    "opportunity_area",
]

TAXONOMY_LABELS = {
    "user_memory":          "User Memory",
    "retrieval_intent":     "Retrieval Intent",
    "search_behavior":      "Search Behavior",
    "retrieval_failure":    "Retrieval Failure",
    "underlying_problem":   "Underlying Problem",
    "opportunity_area":     "Opportunity Area",
}


# ── Rich Document Builder ─────────────────────────────────────────────────────

def build_rich_header(record: dict) -> str:
    """
    Builds the metadata + taxonomy header block for a record.

    Format:
        Source: Google Play | Rating: 4/5 | Date: 2026-09-21
        Taxonomy: User Memory: Event/Occasion | Search Behavior: Natural Language Search
    """
    parts = []

    # ── Core metadata line ────────────────────────────────────────────────
    meta_tokens = []

    source = record.get("source", "Unknown")
    meta_tokens.append(f"Source: {source}")

    rating = record.get("rating")
    if rating is not None:
        meta_tokens.append(f"Rating: {rating}/5")

    date_str = record.get("date", "")
    if date_str:
        # Extract just the date portion for brevity
        try:
            dt = datetime.fromisoformat(date_str)
            meta_tokens.append(f"Date: {dt.strftime('%Y-%m-%d')}")
        except (ValueError, TypeError):
            meta_tokens.append(f"Date: {date_str}")

    parts.append(" | ".join(meta_tokens))

    # ── Taxonomy line (only populated dimensions) ─────────────────────────
    taxonomy = record.get("taxonomy", {})
    populated = []
    for key in TAXONOMY_DISPLAY_ORDER:
        value = taxonomy.get(key, "")
        if value and value.lower() != "not specified":
            label = TAXONOMY_LABELS.get(key, key.replace("_", " ").title())
            populated.append(f"{label}: {value}")

    if populated:
        parts.append("Taxonomy: " + " | ".join(populated))

    return "\n".join(parts)


def build_review_body(record: dict) -> str:
    """
    Combines the review title and body text into a single string.
    """
    title = (record.get("title") or "").strip()
    review = (record.get("review") or "").strip()

    if title and review:
        return f"{title}\n{review}"
    return title or review


def build_chunk_metadata(record: dict) -> dict:
    """
    Extracts the flat metadata dict stored alongside each chunk for
    vector store filtering & retrieval.
    """
    taxonomy = record.get("taxonomy", {})

    meta = {
        "review_id": record.get("review_id", ""),
        "source": record.get("source", ""),
        "date": record.get("date", ""),
        "rating": record.get("rating"),
        "author": record.get("author", ""),
        "url": record.get("url", ""),
    }

    # Flatten taxonomy into metadata for filterable retrieval
    for key in TAXONOMY_DISPLAY_ORDER:
        value = taxonomy.get(key, "Not specified")
        meta[f"taxonomy_{key}"] = value

    return meta


# ── Chunking Logic ────────────────────────────────────────────────────────────

def chunk_record(record: dict) -> list[dict]:
    """
    Chunks a single enriched record into one or more rich documents.

    Returns a list of chunk dicts:
        {
            "chunk_id":   "<review_id>_<idx>",
            "review_id":  "<review_id>",
            "text":       "<rich document text>",
            "word_count": int,
            "metadata":   { ... }
        }
    """
    header = build_rich_header(record)
    body = build_review_body(record)
    words = body.split()
    review_id = record.get("review_id", "unknown")
    meta = build_chunk_metadata(record)
    chunks = []

    if len(words) <= MAX_SINGLE_DOC_WORDS:
        # ── Single chunk ──────────────────────────────────────────────────
        rich_text = f"{header}\n\n{body}"
        chunks.append({
            "chunk_id":   f"{review_id}_0",
            "review_id":  review_id,
            "text":       rich_text,
            "word_count": len(rich_text.split()),
            "metadata":   meta,
        })
    else:
        # ── Sliding window for long reviews ───────────────────────────────
        idx = 0
        start = 0
        total_windows = _count_windows(len(words))
        while start < len(words):
            end = min(start + SLIDING_WINDOW_SIZE, len(words))
            window_text = " ".join(words[start:end])
            part_label = f"(Part {idx + 1}/{total_windows})"

            rich_text = f"{header}\n\n{part_label}\n{window_text}"

            chunk_meta = dict(meta)
            chunk_meta["chunk_part"] = idx + 1
            chunk_meta["chunk_total"] = total_windows

            chunks.append({
                "chunk_id":   f"{review_id}_{idx}",
                "review_id":  review_id,
                "text":       rich_text,
                "word_count": len(rich_text.split()),
                "metadata":   chunk_meta,
            })

            if end >= len(words):
                break

            start += (SLIDING_WINDOW_SIZE - SLIDING_OVERLAP)
            idx += 1

    return chunks


def _count_windows(total_words: int) -> int:
    """Pre-calculates the total number of sliding windows."""
    if total_words <= SLIDING_WINDOW_SIZE:
        return 1
    step = SLIDING_WINDOW_SIZE - SLIDING_OVERLAP
    count = 1
    pos = 0
    while pos + SLIDING_WINDOW_SIZE < total_words:
        pos += step
        count += 1
    return count


# ── Corpus-Level Processing ───────────────────────────────────────────────────

def process_corpus(input_path: str, output_path: str) -> list[dict]:
    """
    Reads the enriched corpus, chunks every record, and writes
    the chunked corpus to disk.

    Returns the list of all chunks.
    """
    if not os.path.exists(input_path):
        print(f"✗ Error: Input file not found — {input_path}")
        sys.exit(1)

    print(f"╭─ Phase 4.1 — Chunking Pipeline")
    print(f"│  Input:  {input_path}")
    print(f"│  Output: {output_path}")
    print(f"│")

    with open(input_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    total_records = len(corpus)
    all_chunks: list[dict] = []
    single_chunk_count = 0
    multi_chunk_count = 0

    for record in corpus:
        record_chunks = chunk_record(record)
        if len(record_chunks) == 1:
            single_chunk_count += 1
        else:
            multi_chunk_count += 1
        all_chunks.extend(record_chunks)

    # ── Write output ──────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    # ── Summary statistics ────────────────────────────────────────────────
    word_counts = [c["word_count"] for c in all_chunks]
    avg_words = sum(word_counts) / len(word_counts) if word_counts else 0

    print(f"│  Records processed:  {total_records:,}")
    print(f"│  Total chunks:       {len(all_chunks):,}")
    print(f"│  Single-chunk docs:  {single_chunk_count:,}")
    print(f"│  Multi-chunk docs:   {multi_chunk_count:,}")
    print(f"│  Avg words/chunk:    {avg_words:.1f}")
    print(f"│  Min words/chunk:    {min(word_counts)}")
    print(f"│  Max words/chunk:    {max(word_counts)}")
    print(f"╰─ ✓ Chunking complete")
    print()

    return all_chunks


# ── CLI Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    input_file = os.path.join(project_root, "data_processing", "enriched_corpus.json")
    output_file = os.path.join(project_root, "indexing", "chunked_corpus.json")

    process_corpus(input_file, output_file)
