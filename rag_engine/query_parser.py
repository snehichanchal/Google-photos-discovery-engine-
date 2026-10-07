"""
Phase 6 — Task 6.1: Query Parser & Expansion Module

Parses natural language user queries and expands them using a domain-specific
synonym dictionary tailored for Google Photos retrieval, search, memory, and UX pain points.

Features:
  - Query cleaning and normalization
  - Domain synonym expansion (e.g., photo ↔ image ↔ picture, find ↔ search ↔ retrieve)
  - Extraction of query intent & keywords
  - Returns parsed query object ready for hybrid retrieval

Architecture Reference: Layer 4 — RAG Query Engine & LLM Synthesis Layer (Section 5)
"""

import re
from typing import Dict, List, Set, Any


# ── Domain Synonym Map ────────────────────────────────────────────────────────

DOMAIN_SYNONYMS: Dict[str, List[str]] = {
    # Media items
    "photo": ["image", "picture", "snapshot", "media", "pic", "shot"],
    "picture": ["photo", "image", "pic", "snapshot", "media"],
    "image": ["photo", "picture", "pic", "snapshot", "media"],
    "screenshot": ["receipt", "doc", "document", "capture", "text image", "scan"],
    "video": ["recording", "clip", "movie", "media"],

    # Actions & Intent
    "find": ["search", "retrieve", "locate", "lookup", "fetch", "get"],
    "search": ["find", "retrieve", "locate", "lookup", "query", "filter"],
    "retrieve": ["find", "search", "locate", "fetch", "recover"],
    "delete": ["erase", "remove", "trash", "lost", "missing", "disappeared", "gone"],
    "remove": ["delete", "erase", "trash", "clear"],
    "hide": ["lock", "passcode", "private", "locked folder", "secure", "hidden"],
    "lock": ["hide", "passcode", "private", "locked folder", "secure"],
    "backup": ["sync", "cloud", "upload", "storage", "save", "drive"],
    "organize": ["album", "folder", "sort", "categorize", "tag", "group"],

    # Concepts & Features
    "album": ["folder", "gallery", "collection", "group", "tag"],
    "folder": ["album", "gallery", "directory", "storage"],
    "date": ["time", "year", "month", "timestamp", "chronological", "sort"],
    "year": ["date", "time", "timeframe", "period"],
    "face": ["person", "people", "recognition", "tag", "label", "facial"],
    "person": ["face", "people", "individual", "contact"],
    "location": ["place", "map", "gps", "geotag", "city", "country"],
    "ocr": ["text", "receipt", "document", "screenshot", "font", "reading"],
    "text": ["ocr", "words", "receipt", "screenshot", "writing"],
    "memory": ["flashback", "highlight", "story", "recap", "old photo"],
    "storage": ["space", "quota", "gigabyte", "gb", "google one", "cloud"],
}


class QueryParser:
    """
    Parses and expands user queries for the RAG engine.
    """

    def __init__(self, synonym_map: Dict[str, List[str]] = None):
        self.synonym_map = synonym_map or DOMAIN_SYNONYMS

    def parse(self, raw_query: str) -> Dict[str, Any]:
        """
        Parses a raw query string into a structured representation with synonym expansions.

        Returns:
            Dict containing:
              - "original_query": str
              - "cleaned_query": str
              - "expanded_query": str
              - "detected_terms": List[str]
              - "synonyms_added": List[str]
        """
        if not raw_query or not raw_query.strip():
            return {
                "original_query": "",
                "cleaned_query": "",
                "expanded_query": "",
                "detected_terms": [],
                "synonyms_added": [],
            }

        cleaned = re.sub(r'\s+', ' ', raw_query.strip().lower())
        words = re.findall(r'\b\w+\b', cleaned)

        detected_terms: List[str] = []
        synonyms_added_set: Set[str] = set()

        for word in words:
            if word in self.synonym_map:
                detected_terms.append(word)
                for syn in self.synonym_map[word]:
                    if syn not in words and syn not in synonyms_added_set:
                        synonyms_added_set.add(syn)

        synonyms_added = list(synonyms_added_set)

        if synonyms_added:
            expanded_query = f"{cleaned} {' '.join(synonyms_added)}"
        else:
            expanded_query = cleaned

        return {
            "original_query": raw_query.strip(),
            "cleaned_query": cleaned,
            "expanded_query": expanded_query,
            "detected_terms": detected_terms,
            "synonyms_added": synonyms_added,
        }


# ── Quick CLI Test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = QueryParser()
    test_queries = [
        "How do users search for old photos by date or face?",
        "Why can't people find screenshots or receipts?",
        "Issues with locked folder and private photos disappearing",
    ]

    print("=== Query Parser Test ===")
    for q in test_queries:
        res = parser.parse(q)
        print(f"\nOriginal:  {res['original_query']}")
        print(f"Expanded:  {res['expanded_query']}")
        print(f"Detected:  {res['detected_terms']}")
        print(f"Synonyms:  {res['synonyms_added']}")
