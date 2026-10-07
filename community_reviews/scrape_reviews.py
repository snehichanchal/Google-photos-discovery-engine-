import os
import json
import argparse
import re
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE_URL = "https://support.google.com/photos/threads"
DEFAULT_COUNT = 200
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}

def fetch_thread_details(url):
    """
    Optional helper to fetch additional thread details from the thread's individual page.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return {}
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Extract author if present in JS script data
        author = None
        match_author = re.search(r'\[\["([^"]+)"\],\[null,\d+,0\],', r.text)
        if match_author:
            author = match_author.group(1)
            
        # Extract full content div if present
        content = None
        body_div = soup.find('div', class_=re.compile(r'body|content|description', re.I))
        if body_div:
            content = body_div.get_text(separator="\n", strip=True)

        return {
            "author": author,
            "full_content": content
        }
    except Exception:
        return {}

def scrape_google_photos_community_reviews(count=DEFAULT_COUNT, fetch_details=False, output_dir=None):
    """
    Scrapes latest discussions / reviews about Google Photos from Google Photos Community Support.

    Args:
        count (int): Number of community threads to fetch (default: 200).
        fetch_details (bool): Whether to fetch individual thread pages for extended details.
        output_dir (str): Directory where CSV and JSON files will be saved.
    """
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    os.makedirs(output_dir, exist_ok=True)

    print(f"🚀 Starting to scrape {count} latest Google Photos community discussions...")
    print(f"   Source: {BASE_URL}")

    # Fetch main thread list
    url = f"{BASE_URL}?hl=en&max_results={count}"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch page. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    cards = soup.find_all('a', class_='thread-list-thread')
    
    print(f"✅ Found {len(cards)} thread cards on Google Support Community.")

    raw_threads = cards[:count]
    scraped_reviews = []
    scraped_at_iso = datetime.now(timezone.utc).isoformat()

    for i, card in enumerate(raw_threads):
        thread_id = card.get('data-stats-id', '')
        href = card.get('href', '')
        full_url = f"https://support.google.com{href}" if href.startswith('/') else href
        aria_label = card.get('aria-label', '')
        
        # Title and Snippet extraction
        title_elem = card.find(class_=re.compile(r'title', re.I))
        snippet_elem = card.find(class_=re.compile(r'snippet|description|body|summary', re.I))
        
        title = title_elem.get_text(strip=True) if title_elem else ""
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

        # Extract counts (Recommended Answers, Replies, Upvotes) from text strings
        strings = list(card.stripped_strings)
        rec_answers = 0
        replies_count = 0
        upvotes_count = 0
        
        for s in strings:
            if 'Recommended Answer' in s:
                m = re.search(r'(\d+)', s)
                if m: rec_answers = int(m.group(1))
            elif 'Repl' in s:
                m = re.search(r'(\d+)', s)
                if m: replies_count = int(m.group(1))
            elif 'Upvote' in s:
                m = re.search(r'(\d+)', s)
                if m: upvotes_count = int(m.group(1))

        # Extract Category/Topic tag if present in aria-label
        category = "General"
        if "titled" in aria_label:
            m = re.search(r'titled\s+.*?\s+([A-Z_]{3,})\s+', aria_label)
            if m:
                category = m.group(1)

        item_dict = {
            "thread_id": thread_id,
            "title": title,
            "snippet": snippet,
            "category": category,
            "recommended_answers": rec_answers,
            "replies_count": replies_count,
            "upvotes_count": upvotes_count,
            "url": full_url,
            "scraped_at": scraped_at_iso
        }
        scraped_reviews.append(item_dict)

    # Optionally fetch detailed attributes in parallel
    if fetch_details:
        print("🔍 Fetching individual thread detail pages in parallel...")
        def enrich(item):
            details = fetch_thread_details(item['url'])
            if details.get('author'):
                item['author'] = details['author']
            if details.get('full_content'):
                item['full_content'] = details['full_content']
            return item

        with ThreadPoolExecutor(max_workers=10) as executor:
            scraped_reviews = list(executor.map(enrich, scraped_reviews))

    fetched_count = len(scraped_reviews)
    print(f"✅ Successfully processed {fetched_count} community reviews/discussions.")

    # Save to CSV
    csv_filename = os.path.join(output_dir, "google_photos_community_reviews.csv")
    df = pd.DataFrame(scraped_reviews)
    df.to_csv(csv_filename, index=False, encoding="utf-8-sig")
    print(f"📁 CSV output saved: {csv_filename}")

    # Save to JSON
    json_filename = os.path.join(output_dir, "google_photos_community_reviews.json")
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(scraped_reviews, f, indent=2, ensure_ascii=False)
    print(f"📁 JSON output saved: {json_filename}")

    return scraped_reviews

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape latest reviews/discussions about Google Photos from Google Community Support.")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help=f"Number of threads/reviews to scrape (default: {DEFAULT_COUNT})")
    parser.add_argument("--fetch-details", action="store_true", help="Fetch individual thread pages for extra details (author, full content)")
    parser.add_argument("--output-dir", type=str, default=None, help="Directory to save output CSV and JSON files")

    args = parser.parse_args()
    scrape_google_photos_community_reviews(count=args.count, fetch_details=args.fetch_details, output_dir=args.output_dir)
