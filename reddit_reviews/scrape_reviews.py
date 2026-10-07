#!/usr/bin/env python3
"""
Reddit Reviews Scraper for Google Photos Application
Scrapes the 100 latest user reviews, discussions, and feedback about Google Photos from Reddit
and saves the structured output into JSON and CSV formats.
"""

import requests
import json
import csv
import os
import sys
import time
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime

TARGET_COUNT = 100
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'

# RSS feed endpoints to fetch Google Photos reviews/discussions
SOURCES = [
    {
        'name': 'r/googlephotos',
        'url_template': 'https://www.reddit.com/r/googlephotos/new.rss?limit=100'
    },
    {
        'name': 'Reddit Search ("Google Photos")',
        'url_template': 'https://www.reddit.com/search.rss?q=%22Google+Photos%22&sort=new&limit=100'
    }
]

def fetch_rss_content(url, max_retries=5):
    """
    Fetches XML content from Reddit RSS feed with rate-limit backoff handling.
    """
    headers = {'User-Agent': DEFAULT_USER_AGENT}
    
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200 and response.content:
                return response.content
            elif response.status_code == 429:
                reset_seconds = int(response.headers.get('x-ratelimit-reset', 5)) + 1
                print(f"[Rate Limit 429] Waiting {reset_seconds} seconds before retrying (Attempt {attempt}/{max_retries})...")
                time.sleep(reset_seconds)
            else:
                print(f"[HTTP {response.status_code}] Failed to fetch RSS from {url}. Retrying in 3s...")
                time.sleep(3)
        except Exception as e:
            print(f"[Error] Attempt {attempt}/{max_retries} for {url}: {e}")
            time.sleep(3)
            
    return None

def parse_rss_entries(rss_content):
    """
    Parses Atom XML entries from Reddit RSS content and returns clean review objects.
    """
    reviews = []
    if not rss_content:
        return reviews
        
    try:
        root = ET.fromstring(rss_content)
    except ET.ParseError as e:
        print(f"XML Parsing Error: {e}")
        return reviews
        
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    entries = root.findall('atom:entry', ns)
    
    for entry in entries:
        title_elem = entry.find('atom:title', ns)
        title = title_elem.text.strip() if title_elem is not None and title_elem.text else ''
        
        updated_elem = entry.find('atom:updated', ns)
        published_date = updated_elem.text.strip() if updated_elem is not None and updated_elem.text else ''
        
        author_elem = entry.find('atom:author/atom:name', ns)
        author = author_elem.text.strip() if author_elem is not None and author_elem.text else 'Anonymous'
        
        link_elem = entry.find('atom:link', ns)
        url = link_elem.attrib.get('href', '').strip() if link_elem is not None else ''
        
        id_elem = entry.find('atom:id', ns)
        raw_id = id_elem.text.strip() if id_elem is not None and id_elem.text else ''
        review_id = raw_id.split(',')[-1] if ',' in raw_id else raw_id
        
        category_elem = entry.find('atom:category', ns)
        subreddit = category_elem.attrib.get('term', '') if category_elem is not None else 'googlephotos'
        if subreddit.startswith('r/'):
            subreddit = subreddit[2:]
            
        content_elem = entry.find('atom:content', ns)
        raw_html = content_elem.text if content_elem is not None and content_elem.text else ''
        
        # Clean HTML content to extract review body
        review_body = ''
        if raw_html:
            soup = BeautifulSoup(raw_html, 'html.parser')
            
            # Reddit RSS HTML contains tables with metadata & post body
            # Look for post content in div with class 'md' or paragraphs
            post_div = soup.find('div', class_='md')
            if post_div:
                review_body = post_div.get_text(separator=' ', strip=True)
            else:
                # Fallback: extract text from paragraphs excluding submitted footer
                paras = [p.get_text(strip=True) for p in soup.find_all('p') if 'submitted by' not in p.get_text().lower()]
                review_body = ' '.join(paras).strip()
                
            if not review_body:
                # Standard text fallback
                text_all = soup.get_text(separator=' ', strip=True)
                if 'submitted by' in text_all:
                    text_all = text_all.split('submitted by')[0].strip()
                review_body = text_all
                
        review_item = {
            'review_id': review_id,
            'title': title,
            'review': review_body if review_body else title,
            'author': author,
            'subreddit': f"r/{subreddit}",
            'url': url,
            'published_date': published_date,
            'source': 'Reddit'
        }
        reviews.append(review_item)
        
    return reviews

def fetch_reddit_reviews(target_count=TARGET_COUNT):
    """
    Collects 100 latest reviews and feedback posts across Reddit RSS sources.
    """
    reviews = []
    seen_ids = set()
    
    print(f"Starting Reddit scraper for Google Photos (Target: {target_count} reviews)...")
    
    # Primary fetch from r/googlephotos
    primary_source = SOURCES[0]
    print(f"\nFetching from primary source: {primary_source['name']}...")
    rss_data = fetch_rss_content(primary_source['url_template'])
    items = parse_rss_entries(rss_data)
    
    for item in items:
        if item['review_id'] not in seen_ids:
            seen_ids.add(item['review_id'])
            reviews.append(item)
            if len(reviews) >= target_count:
                break
                
    print(f"Collected {len(reviews)} reviews from {primary_source['name']}.")
    
    # If more needed, fetch from Reddit Search
    if len(reviews) < target_count:
        search_source = SOURCES[1]
        print(f"\nFetching additional posts from: {search_source['name']}...")
        time.sleep(3)  # Respect rate limit
        search_rss = fetch_rss_content(search_source['url_template'])
        search_items = parse_rss_entries(search_rss)
        
        for item in search_items:
            if item['review_id'] not in seen_ids:
                seen_ids.add(item['review_id'])
                reviews.append(item)
                if len(reviews) >= target_count:
                    break
                    
    # If pagination needed to hit exact count
    while len(reviews) < target_count:
        last_item = reviews[-1] if reviews else None
        if not last_item:
            break
        last_id = last_item['review_id']
        url = f"https://www.reddit.com/r/googlephotos/new.rss?limit=100&after={last_id}"
        print(f"\nFetching additional page after {last_id}...")
        time.sleep(4)
        rss_data = fetch_rss_content(url)
        more_items = parse_rss_entries(rss_data)
        
        added = 0
        for item in more_items:
            if item['review_id'] not in seen_ids:
                seen_ids.add(item['review_id'])
                reviews.append(item)
                added += 1
                if len(reviews) >= target_count:
                    break
        if added == 0:
            print("No more new entries returned by pagination.")
            break
            
    print(f"\nTotal unique Reddit reviews scraped: {len(reviews)}")
    return reviews[:target_count]

def save_to_json(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON data ({len(data)} items) to {filepath}")

def save_to_csv(data, filepath):
    if not data:
        return
    fieldnames = list(data[0].keys())
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Saved CSV data ({len(data)} items) to {filepath}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, 'google_photos_reddit_reviews.json')
    csv_path = os.path.join(script_dir, 'google_photos_reddit_reviews.csv')
    
    reviews = fetch_reddit_reviews(target_count=TARGET_COUNT)
    
    if reviews:
        save_to_json(reviews, json_path)
        save_to_csv(reviews, csv_path)
        
        # Summary metrics
        subreddits = {}
        total_words = 0
        for r in reviews:
            sub = r.get('subreddit', 'r/unknown')
            subreddits[sub] = subreddits.get(sub, 0) + 1
            total_words += len(r.get('review', '').split())
            
        avg_words = total_words / len(reviews) if reviews else 0
        
        print("\n" + "="*40)
        print("         SCRAPING SUMMARY")
        print("="*40)
        print(f"Total Reviews Scraped : {len(reviews)}")
        print(f"Average Words / Review: {avg_words:.1f} words")
        print("\nSubreddit Breakdown:")
        for sub, count in sorted(subreddits.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {sub}: {count} reviews ({count/len(reviews)*100:.1f}%)")
        print("="*40)
    else:
        print("No reviews were scraped.")

if __name__ == '__main__':
    main()
