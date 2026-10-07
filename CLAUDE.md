# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A 7-phase batch pipeline + RAG system that mines public Google Photos user feedback (6 channels)
to answer product questions about **visual memory retrieval failures** — cases where a user knows
a photo exists but can't describe it precisely enough to find it.

Read `context.md` (problem framing) and `Architecture.md` (layer-by-layer design, with mermaid
diagrams and the unified data schema) before making structural changes. `play_store/docs/implementation_plan.md`
holds the phase/task breakdown that every module docstring references ("Phase 6 — Task 6.2", etc.).

## Pipeline: data flows through files, not services

Every phase reads a JSON file and writes the next one. There is no orchestrator for the whole
chain — you run phases in order, and each stage's artifact is committed to the repo:

```
<channel>/*.json          6 scrapers, each with its own schema
  → data_processing/unified_corpus.json     normalize.py       (1699 records)
  → data_processing/filtered_corpus.json    relevance_filter.py (1492)
  → data_processing/enriched_corpus.json    taxonomy_engine.py → filter_relevant.py (822)
  → indexing/chunked_corpus.json            chunker.py          (899 chunks)
  → indexing/embedded_corpus.json + embeddings.npy   embedder.py
  → indexing/chroma_db/ + indexing/bm25_index.pkl    ingest.py
```

`enriched_corpus.json` is the hub artifact: it feeds the indexing chain *and* is read directly
(bypassing retrieval) by the Streamlit dashboard, `app/taxonomy_report_generator.py`, and the
`data_processing/analyze_*.py` scripts. `enriched_corpus_backup.json` is the pre-`filter_relevant.py`
snapshot (that script rewrites its input in place).

### Running the phases

```bash
python data_processing/normalize.py          # Phase 2: unify 6 channel schemas
python data_processing/relevance_filter.py   # Phase 3a: length + spam + domain-keyword filter
python data_processing/taxonomy_engine.py    # Phase 3b: 6-tier taxonomy via Gemini (2s/record)
python data_processing/filter_relevant.py    # Phase 3c: keyword AND taxonomy strict cut
python indexing/run_phase4.py                # Phase 4: chunk + embed (both steps)
python indexing/ingest.py                    # Phase 5: upsert into ChromaDB + rebuild BM25
python indexing/test_queries.py              # Phase 5 validation → indexing/test_queries.md
python rag_engine/evaluate.py                # Phase 6 eval, 15 queries → rag_engine/evaluation_report.md
```

**Working directory matters and is inconsistent.** `normalize.py`, `relevance_filter.py`, and
`taxonomy_engine.py` `os.chdir()` into `data_processing/` and use bare filenames; `filter_relevant.py`
and the `analyze_*.py` scripts use `data_processing/...` paths and must be run **from the repo root**.
Everything under `indexing/`, `rag_engine/`, and `app/` resolves paths from `__file__` and works
from anywhere.

## Applications

```bash
python app/main.py              # interactive menu
python app/main.py console      # CLI PM Q&A console
python app/main.py frontend     # streamlit run app/unified_frontend.py
python app/main.py report       # regenerate app/taxonomy_report.md
```

`app/main.py` launches each app as a `subprocess` rather than importing it, so Streamlit's CLI and
the console's input loop stay isolated. `app/unified_frontend.py` wraps `PMConsole` in
`@st.cache_resource` — the embedder, cross-encoder, and Chroma client load once per Streamlit session.

## RAG query path

`RAGPipeline.run()` (`rag_engine/pipeline.py`) is the single entry point; the four stages are
injectable constructor args, so tests can substitute any of them:

1. `query_parser.py` — synonym expansion over a hand-built `DOMAIN_SYNONYMS` map (photo↔image↔pic,
   find↔search↔retrieve, ocr↔text↔receipt). This is the domain tuning knob; extend it rather than
   changing retrieval weights when a query class under-retrieves.
2. `hybrid_retriever.py` — dense (ChromaDB, cosine) + sparse (BM25Okapi) fused by Reciprocal Rank
   Fusion, `k_rrf=60`, equal weights. Calls `load_stores()` lazily on first retrieve.
3. `reranker.py` — `cross-encoder/ms-marco-MiniLM-L-6-v2`, top 25 → top 7.
4. `llm_synthesizer.py` — Gemini (`gemini-1.5-flash`) under `rag_engine/prompts/system_prompt.txt`.

### The synthesizer always answers

If `GEMINI_API_KEY`/`GOOGLE_API_KEY` is unset, `google-generativeai` is missing, or the API call
raises, `_generate_grounded_fallback()` produces a deterministic extractive answer from the same
context chunks, still enforcing all four guardrails (context-only, `[review_id: …, source: …]`
citations, 6-tier taxonomy framing, quantified counts). Check `result["synthesizer_mode"]`
(`"gemini"` vs `"deterministic_fallback"`) when a change to answer quality looks unexplained —
you may simply be in fallback. `data_processing/taxonomy_engine.py` has the parallel pattern:
no API key means `mock_classify()`, a keyword heuristic, silently tags the whole corpus.

## The 6-tier taxonomy

Every enriched record carries `taxonomy` with exactly these keys, in this order, defaulting to
`"Not specified"`:

```
user_memory → retrieval_intent → search_behavior → retrieval_failure → underlying_problem → opportunity_area
```

This ordering is load-bearing in three places: `chunker.py`'s `TAXONOMY_DISPLAY_ORDER` (which
prepends populated fields as a text header into the embedded document, so taxonomy is *semantically
searchable*, not just filterable), the synthesis guardrails, and the report/dashboard groupings.
Adding a tier means touching all of them plus re-running Phase 3 onward.

## Conventions

- **No dependency manifest at the repo root.** Only the six scraper directories have
  `requirements.txt`. The pipeline's own deps — `chromadb`, `sentence-transformers`, `rank-bm25`,
  `google-generativeai`, `streamlit`, `plotly`, `pandas`, `python-dateutil` — are undeclared;
  install them explicitly in a venv (`.gitignore` expects `venv/` or `.venv/`).
- Each pipeline module has a `if __name__ == "__main__":` block that runs it against the standard
  repo paths — that is how any single stage is exercised. There is no test framework, no linter,
  and no CI; `indexing/test_queries.py` and `rag_engine/evaluate.py` are report generators, not
  assertions, so validate changes by reading their markdown output.
- Modules insert the workspace root into `sys.path` from `__file__` before importing siblings
  (`from indexing.vector_store import VectorStore`). Keep that preamble when adding a module that
  crosses package boundaries.
- Deduplication keys: `review_id` is an MD5 of source+author+date+text-prefix+length
  (`normalize.py:generate_hash`); `chunk_id` identifies chunks and `ingest.py` skips chunk_ids
  already in Chroma, so re-ingesting is idempotent. `VectorStore.reset()` drops the collection.
- ChromaDB metadata only accepts primitives — `_sanitise_metadata()` in `vector_store.py` coerces
  `None` → `""`. New metadata fields must survive that.
- Progress output across the pipeline uses a `╭─ │ ╰─` box-drawing convention; match it in new stages.
