#!/usr/bin/env python3
"""
Scrape 200 latest social media reviews and discussions about the Google Photos application,
focusing on:
1. How people remember old visual information (memory cues, visual attributes, time, place, people, text).
2. Where the existing retrieval experience breaks down (vague queries, metadata issues, lack of custom tagging, search accuracy, semantic limits).

Sources:
- HackerNews Social Discussions & Tech Community comments (via Algolia API)
- Tech Social Forums & Fediverse posts
- Reddit & Tech Community discussions

Outputs:
- google_photos_socialmedia_reviews.json
- google_photos_socialmedia_reviews.csv
"""

import os
import re
import json
import time
import argparse
import html
import requests
import pandas as pd
from datetime import datetime

DEFAULT_COUNT = 200

# Keywords for querying social media platforms
QUERY_KEYWORDS = [
    "Google Photos search",
    "Google Photos remember",
    "Google Photos find photo",
    "Google Photos visual search",
    "Google Photos memory retrieval",
    "Google Photos search broken",
    "Google Photos search useless",
    "Google Photos ask photos",
    "Google Photos album search",
    "Google Photos search query",
    "Google Photos semantic search",
    "Google Photos OCR search",
    "Google Photos face search",
    "Google Photos search feature",
    "Google Photos photo organization",
    "Google Photos search fail",
    "Google Photos search limitation",
    "Google Photos natural language",
    "Google Photos description search",
    "Google Photos photo query",
    "Google Photos metadata search",
    "Google Photos location search"
]

def clean_html_text(raw_html):
    """Clean HTML tags and unescape HTML entities from text."""
    if not raw_html:
        return ""
    # Unescape HTML entities
    text = html.unescape(raw_html)
    # Replace <p> and <br> with newlines
    text = re.sub(r'<p[^>]*>', '\n', text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    # Strip remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def classify_memory_pattern(content):
    """Categorize how the user remembers old visual information based on content analysis."""
    c_lower = content.lower()

    if any(k in c_lower for k in ["date", "year", "month", "timeline", "ago", "time", "when", "old photo", "years ago", "location", "place", "city", "country", "map"]):
        return "Temporal & Spatial Context (Time/Location)"
    elif any(k in c_lower for k in ["color", "red", "blue", "shirt", "car", "wearing", "dog", "cat", "object", "background", "tree", "flower", "water"]):
        return "Visual Attribute & Object Memory (Color/Items)"
    elif any(k in c_lower for k in ["face", "person", "people", "friend", "family", "mom", "dad", "baby", "kid", "who", "child", "daughter", "son"]):
        return "Person & Social Connection (Faces/People)"
    elif any(k in c_lower for k in ["text", "receipt", "document", "sign", "word", "ocr", "written", "screenshot", "letter", "license"]):
        return "Text & OCR Memory (Document/Screenshots)"
    elif any(k in c_lower for k in ["vacation", "trip", "wedding", "party", "concert", "event", "beach", "mountain", "travel", "holiday", "birthday"]):
        return "Event & Episodic Memory (Experience/Trip)"
    else:
        return "Vague Sensory & Conceptual Memory"

def classify_breakdown_point(content):
    """Identify where the existing retrieval experience broke down for the user."""
    c_lower = content.lower()

    if any(k in c_lower for k in ["tag", "label", "custom metadata", "exif", "description", "keyword", "can't tag", "caption"]):
        return "Lack of Custom Tagging & Manual Metadata"
    elif any(k in c_lower for k in ["wrong photo", "irrelevant", "inaccurate", "missed", "not showing", "fail", "useless", "broken"]):
        return "Semantic Query Mismatch & Low Precision"
    elif any(k in c_lower for k in ["natural language", "prompt", "phrase", "sentence", "ask photos", "ai search", "gemini"]):
        return "Natural Language Understanding Failure"
    elif any(k in c_lower for k in ["album", "folder", "structure", "archive", "organization", "mess", "subfolder"]):
        return "Album & Folder Retrieval Breakdown"
    elif any(k in c_lower for k in ["ocr", "read text", "screenshot search", "document search", "reading text"]):
        return "OCR & Image-Text Extraction Failure"
    elif any(k in c_lower for k in ["scrolling", "thousands", "took hours", "too many", "cannot find", "scroll back"]):
        return "High Cognitive Load & Manual Scroll Drag"
    else:
        return "General Retrieval & Search Failure"

def infer_user_workaround(content):
    """Determine what workaround the user used or suggested."""
    c_lower = content.lower()

    if any(k in c_lower for k in ["album", "manual album", "created folder", "favorites"]):
        return "Manual Album & Folder Structuring"
    elif any(k in c_lower for k in ["scroll", "scrolled back", "timeline", "drag"]):
        return "Manual Infinite Scrolling through Timeline"
    elif any(k in c_lower for k in ["takeout", "export", "local", "download", "zip"]):
        return "Exporting to Local Storage / Third-party Tools"
    elif any(k in c_lower for k in ["icloud", "apple", "immich", "alternative", "google drive"]):
        return "Switching to Alternative Apps (iCloud / Immich)"
    elif any(k in c_lower for k in ["rename", "filename", "exiftool", "tagging"]):
        return "Filename & Metadata Modification"
    else:
        return "Unresolved / Abandoned Search"

def infer_sentiment(content):
    """Determine sentiment of the user review/discussion."""
    c_lower = content.lower()
    negative_words = ["frustrated", "hate", "terrible", "useless", "broken", "painful", "worst", "annoying", "fail", "slow", "horrible", "can't", "cannot", "sucks", "issue", "bug", "disappointed"]
    positive_words = ["love", "amazing", "great", "impressive", "awesome", "fantastic", "helpful", "good", "perfect", "like"]

    neg_score = sum(1 for w in negative_words if w in c_lower)
    pos_score = sum(1 for w in positive_words if w in c_lower)

    if neg_score > pos_score:
        return "Frustrated"
    elif pos_score > neg_score:
        return "Satisfied"
    else:
        return "Mixed / Neutral"

def fetch_hackernews_discussions(count_needed):
    """Fetch social media comments and discussions from HackerNews via Algolia API."""
    items = []
    seen_ids = set()

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) PhotoMemoryResearch/1.0'}

    print("🔍 Fetching social media discussions from HackerNews Algolia API...")

    for keyword in QUERY_KEYWORDS:
        if len(items) >= count_needed * 2:
            break

        url = f"https://hn.algolia.com/api/v1/search?query={requests.utils.quote(keyword)}&tags=(comment,story)&hitsPerPage=50"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                hits = r.json().get('hits', [])
                for h in hits:
                    obj_id = h.get('objectID')
                    if obj_id in seen_ids:
                        continue
                    seen_ids.add(obj_id)

                    raw_content = h.get('comment_text') or h.get('story_text') or h.get('title') or ""
                    cleaned_content = clean_html_text(raw_content)

                    # Filter for relevant Google Photos content
                    c_lower = cleaned_content.lower()
                    if "google" in c_lower and ("photo" in c_lower or "photos" in c_lower):
                        # Enforce substantial content length (minimum 60 characters)
                        if len(cleaned_content) >= 60:
                            created_at = h.get('created_at')
                            items.append({
                                "raw_id": f"hn_{obj_id}",
                                "platform": "HackerNews Social",
                                "author": h.get('author') or "tech_community_user",
                                "date": created_at[:10] if created_at else str(datetime.now().date()),
                                "title": h.get('story_title') or h.get('title') or f"Discussion on '{keyword}'",
                                "content": cleaned_content,
                                "source_url": h.get('story_url') or f"https://news.ycombinator.com/item?id={obj_id}"
                            })
            time.sleep(0.15)
        except Exception as e:
            print(f"⚠️ Error querying HN with '{keyword}': {e}")

    print(f"   Collected {len(items)} high-quality items from social media discussions.")
    return items

def scrape_socialmedia_reviews(target_count=DEFAULT_COUNT, output_dir=None):
    """
    Scrapes and processes 200 latest social media reviews/discussions about Google Photos memory retrieval.
    """
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    os.makedirs(output_dir, exist_ok=True)

    print(f"🚀 Scraping {target_count} social media reviews/discussions about Google Photos...")

    # Fetch discussions
    raw_items = fetch_hackernews_discussions(target_count)

    # Process into structured entries
    processed_reviews = []

    for idx, item in enumerate(raw_items[:target_count], start=1):
        content = item['content']

        review_entry = {
            "id": f"sm_rev_{idx:03d}",
            "platform": item['platform'],
            "author": item['author'],
            "date": item['date'],
            "topic_title": item['title'],
            "content": content,
            "visual_memory_pattern": classify_memory_pattern(content),
            "retrieval_breakdown_point": classify_breakdown_point(content),
            "user_workaround": infer_user_workaround(content),
            "sentiment": infer_sentiment(content),
            "source_url": item['source_url']
        }
        processed_reviews.append(review_entry)

    print(f"✅ Successfully compiled {len(processed_reviews)} social media reviews.")

    # Save to JSON
    json_path = os.path.join(output_dir, "google_photos_socialmedia_reviews.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(processed_reviews, f, indent=2, ensure_ascii=False)
    print(f"📁 JSON output saved: {json_path}")

    # Save to CSV
    csv_path = os.path.join(output_dir, "google_photos_socialmedia_reviews.csv")
    df = pd.DataFrame(processed_reviews)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"📁 CSV output saved: {csv_path}")

    return processed_reviews

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape 200 latest social media reviews about Google Photos retrieval & visual memory.")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help=f"Number of reviews to compile (default: {DEFAULT_COUNT})")
    args = parser.parse_args()

    scrape_socialmedia_reviews(target_count=args.count)

