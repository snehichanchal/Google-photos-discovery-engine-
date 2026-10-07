#!/usr/bin/env python3
"""
Scrape 200 latest user comments and reviews from YouTube regarding Google Photos application,
focusing on:
1. How people remember old visual information (memory cues, visual attributes, time, place, people, text, events).
2. Where the existing retrieval experience breaks down (vague queries, metadata issues, lack of custom tagging, search accuracy, Ask Photos failures, semantic limits, high cognitive load).

Sources:
- YouTube video comment sections across videos reviewing, demonstrating, or discussing Google Photos search, Ask Photos, photo organization, update reviews, and memory retrieval features.

Outputs:
- google_photos_youtube_reviews.json
- google_photos_youtube_reviews.csv
"""

import os
import re
import json
import time
import argparse
import html
import subprocess
import pandas as pd
from datetime import datetime
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_RECENT

DEFAULT_COUNT = 200

# Search queries to find YouTube videos about Google Photos search and photo memory recall
YOUTUBE_SEARCH_QUERIES = [
    "google photos ask photos review",
    "google photos search feature test",
    "google photos find old photos",
    "google photos search broken",
    "google photos visual search update",
    "google photos search tips trick",
    "how to find photos in google photos",
    "google photos gemini ai search",
    "google photos photo organization search",
    "google photos face search recognition",
    "google photos vs icloud photos search",
    "google photos search not working",
    "google photos memories feature",
    "google photos semantic search"
]

def clean_text(raw_text):
    """Clean and normalize raw comment text."""
    if not raw_text:
        return ""
    text = html.unescape(raw_text)
    # Remove excessive newlines or spacing
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def classify_memory_pattern(content):
    """Categorize how the user remembers old visual information based on comment text."""
    c_lower = content.lower()

    if any(k in c_lower for k in ["date", "year", "month", "timeline", "time", "ago", "when", "old photo", "years ago", "location", "place", "city", "country", "map", "gps"]):
        return "Temporal & Spatial Context (Time/Location)"
    elif any(k in c_lower for k in ["color", "red", "blue", "shirt", "car", "wearing", "dog", "cat", "object", "background", "tree", "flower", "water", "shoes"]):
        return "Visual Attribute & Object Memory (Color/Items)"
    elif any(k in c_lower for k in ["face", "person", "people", "friend", "family", "mom", "dad", "baby", "kid", "who", "child", "daughter", "son", "face recognition"]):
        return "Person & Social Connection (Faces/People)"
    elif any(k in c_lower for k in ["text", "receipt", "document", "sign", "word", "ocr", "written", "screenshot", "letter", "licence", "license"]):
        return "Text & OCR Memory (Document/Screenshots)"
    elif any(k in c_lower for k in ["vacation", "trip", "wedding", "party", "concert", "event", "beach", "mountain", "travel", "holiday", "birthday", "grad"]):
        return "Event & Episodic Memory (Experience/Trip)"
    else:
        return "Vague Sensory & Conceptual Memory"

def classify_breakdown_point(content):
    """Identify where the existing retrieval experience broke down for the user."""
    c_lower = content.lower()

    if any(k in c_lower for k in ["tag", "label", "custom metadata", "exif", "description", "keyword", "can't tag", "caption", "manual tag"]):
        return "Lack of Custom Tagging & Manual Metadata"
    elif any(k in c_lower for k in ["wrong photo", "irrelevant", "inaccurate", "missed", "not showing", "fail", "useless", "broken", "doesn't work", "can't find"]):
        return "Semantic Query Mismatch & Low Precision"
    elif any(k in c_lower for k in ["natural language", "prompt", "phrase", "sentence", "ask photos", "gemini", "ai search", "chatbot"]):
        return "Natural Language & Ask Photos Gemini Failure"
    elif any(k in c_lower for k in ["album", "folder", "structure", "archive", "organization", "mess", "subfolder", "device folder"]):
        return "Album & Folder Retrieval Breakdown"
    elif any(k in c_lower for k in ["ocr", "read text", "screenshot search", "document search", "reading text", "search text"]):
        return "OCR & Image-Text Extraction Failure"
    elif any(k in c_lower for k in ["scrolling", "thousands", "took hours", "too many", "cannot find", "scroll back", "endless scroll"]):
        return "High Cognitive Load & Manual Scroll Drag"
    else:
        return "General Retrieval & Search Failure"

def infer_user_workaround(content):
    """Determine what workaround the user used or suggested in their comment."""
    c_lower = content.lower()

    if any(k in c_lower for k in ["album", "manual album", "created folder", "favorites", "star"]):
        return "Manual Album & Folder Structuring"
    elif any(k in c_lower for k in ["scroll", "scrolled back", "timeline", "drag", "swiping"]):
        return "Manual Infinite Scrolling through Timeline"
    elif any(k in c_lower for k in ["takeout", "export", "local", "download", "zip", "hard drive", "nas"]):
        return "Exporting to Local Storage / Third-party Tools"
    elif any(k in c_lower for k in ["icloud", "apple", "immich", "alternative", "google drive", "amazon photos", "onedrive"]):
        return "Switching to Alternative Apps (iCloud / Immich)"
    elif any(k in c_lower for k in ["rename", "filename", "exiftool", "tagging"]):
        return "Filename & Metadata Modification"
    else:
        return "Unresolved / Abandoned Search"

def infer_sentiment(content):
    """Determine sentiment of the user YouTube comment."""
    c_lower = content.lower()
    negative_words = ["frustrated", "hate", "terrible", "useless", "broken", "painful", "worst", "annoying", "fail", "slow", "horrible", "can't", "cannot", "sucks", "issue", "bug", "disappointed", "bad", "garbage"]
    positive_words = ["love", "amazing", "great", "impressive", "awesome", "fantastic", "helpful", "good", "perfect", "like", "best", "useful", "works well"]

    neg_score = sum(1 for w in negative_words if w in c_lower)
    pos_score = sum(1 for w in positive_words if w in c_lower)

    if neg_score > pos_score:
        return "Frustrated"
    elif pos_score > neg_score:
        return "Satisfied"
    else:
        return "Mixed / Neutral"

def get_youtube_videos_for_queries(queries, max_per_query=6):
    """Fetch YouTube video metadata for search queries using yt-dlp flat playlist dump."""
    video_dict = {}
    print("🔍 Searching YouTube for relevant Google Photos videos...")

    for query in queries:
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--dump-json",
            f"ytsearch{max_per_query}:{query}"
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            for line in res.stdout.strip().splitlines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    vid = data.get("id")
                    title = data.get("title", "")
                    if vid and vid not in video_dict:
                        video_dict[vid] = {
                            "id": vid,
                            "title": title,
                            "url": f"https://www.youtube.com/watch?v={vid}"
                        }
                except Exception:
                    pass
        except Exception as e:
            print(f"⚠️ Error executing search for query '{query}': {e}")

    print(f"✅ Found {len(video_dict)} unique videos related to Google Photos.")
    return list(video_dict.values())

def fetch_youtube_comments(videos, target_count):
    """Fetch and filter comments from YouTube videos."""
    downloader = YoutubeCommentDownloader()
    collected_reviews = []
    seen_cids = set()

    print(f"📥 Extracting comments from YouTube videos (Target: {target_count})...")

    for v in videos:
        if len(collected_reviews) >= target_count:
            break

        vid = v["id"]
        vtitle = v["title"]
        vurl = v["url"]

        print(f"   Downloading comments for video: [{vid}] '{vtitle}'...")

        try:
            comments = downloader.get_comments(vid, sort_by=SORT_BY_RECENT)
            video_comment_count = 0

            for c in comments:
                if len(collected_reviews) >= target_count:
                    break

                cid = c.get("cid")
                if not cid or cid in seen_cids:
                    continue
                seen_cids.add(cid)

                raw_text = c.get("text", "")
                text = clean_text(raw_text)

                # Quality filter: Must be at least 25 chars and contain relevant context
                if len(text) < 25:
                    continue

                # Filter out generic bot or channel self-promos
                t_lower = text.lower()
                if any(ignored in t_lower for ignored in ["subscribe", "thanks for watching", "link in description", "check out my channel"]):
                    continue

                author = c.get("author", "@anonymous")
                time_str = c.get("time", "Recently")
                likes = c.get("votes", "0")

                # Parse timestamp if available
                time_parsed = c.get("time_parsed")
                if time_parsed:
                    date_str = datetime.fromtimestamp(time_parsed).strftime("%Y-%m-%d")
                else:
                    date_str = time_str

                review_entry = {
                    "review_id": f"yt_{cid}",
                    "video_id": vid,
                    "video_title": vtitle,
                    "author": author,
                    "comment_text": text,
                    "published_date": date_str,
                    "like_count": str(likes),
                    "visual_memory_pattern": classify_memory_pattern(text),
                    "retrieval_breakdown_point": classify_breakdown_point(text),
                    "user_workaround": infer_user_workaround(text),
                    "sentiment": infer_sentiment(text),
                    "video_url": vurl,
                    "source": "YouTube Comments"
                }

                collected_reviews.append(review_entry)
                video_comment_count += 1

                # Cap per video to avoid skewing
                if video_comment_count >= 35:
                    break

            print(f"   -> Extracted {video_comment_count} valid comments (Total collected: {len(collected_reviews)})")
            time.sleep(0.1)
        except Exception as e:
            print(f"⚠️ Error fetching comments for video {vid}: {e}")

    return collected_reviews

def scrape_youtube_reviews(target_count=DEFAULT_COUNT, output_dir=None):
    """Scrape and compile 200 YouTube reviews/comments about Google Photos retrieval & visual memory."""
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    os.makedirs(output_dir, exist_ok=True)

    print(f"🚀 Scraping {target_count} YouTube reviews/comments for Google Photos application...")

    videos = get_youtube_videos_for_queries(YOUTUBE_SEARCH_QUERIES, max_per_query=6)
    reviews = fetch_youtube_comments(videos, target_count)

    # Re-index nicely
    for idx, r in enumerate(reviews, start=1):
        r["id"] = f"yt_rev_{idx:03d}"

    print(f"✅ Successfully collected {len(reviews)} YouTube reviews.")

    # Save to JSON
    json_path = os.path.join(output_dir, "google_photos_youtube_reviews.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)
    print(f"📁 JSON output saved: {json_path}")

    # Save to CSV
    csv_path = os.path.join(output_dir, "google_photos_youtube_reviews.csv")
    df = pd.DataFrame(reviews)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"📁 CSV output saved: {csv_path}")

    return reviews

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape 200 YouTube reviews about Google Photos retrieval & visual memory.")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help=f"Number of reviews to compile (default: {DEFAULT_COUNT})")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory path")
    args = parser.parse_args()

    scrape_youtube_reviews(target_count=args.count, output_dir=args.output_dir)
