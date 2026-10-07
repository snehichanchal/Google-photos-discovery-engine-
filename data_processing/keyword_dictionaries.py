import re

# Keywords indicating relevance to domain (Google Photos, finding memories, searching, etc.)
DOMAIN_KEYWORDS = [
    "search", "find", "photo", "memory", "retrieve", "album", 
    "scroll", "filter", "face", "ocr", "screenshot", "remember",
    "locate", "look for", "looking for", "tag", "sort", "date",
    "year", "month", "keyword", "type", "text in image",
    "recognize", "can't find", "couldn't find", "missing",
    "people", "places", "things", "old", "years ago", "receipt"
]

# Patterns or keywords indicating generic spam, noise, or purely account/storage issues
SPAM_PATTERNS = [
    re.compile(r"^\s*(great|good|nice|best|worst|bad|terrible|awesome|cool)\s+app\s*$", re.IGNORECASE),
    re.compile(r"^\s*(love|hate)\s+it\s*$", re.IGNORECASE),
    re.compile(r"too many ads", re.IGNORECASE),
    re.compile(r"keeps crashing", re.IGNORECASE),
    re.compile(r"won'?t open", re.IGNORECASE),
    re.compile(r"can'?t open", re.IGNORECASE),
    re.compile(r"billing", re.IGNORECASE),
    re.compile(r"subscription", re.IGNORECASE),
    re.compile(r"refund", re.IGNORECASE),
    re.compile(r"scam\b", re.IGNORECASE),
    re.compile(r"storage full", re.IGNORECASE),
    re.compile(r"buy storage", re.IGNORECASE),
    re.compile(r"google one", re.IGNORECASE)
]
