import json
import os
import hashlib
import pandas as pd
from dateutil import parser
from datetime import timezone

INPUT_FILES = {
    'app_store': '../app_store/google_photos_app_store_reviews.json',
    'play_store': '../play_store/google_photos_reviews.json',
    'reddit': '../reddit_reviews/google_photos_reddit_reviews.json',
    'community': '../community_reviews/google_photos_community_reviews.json',
    'youtube': '../youtube_reviews/google_photos_youtube_reviews.json',
    'socialmedia': '../socialmedia_reviews/google_photos_socialmedia_reviews.json'
}

OUTPUT_JSON = 'unified_corpus.json'
OUTPUT_CSV = 'unified_corpus.csv'
AUDIT_REPORT = 'schema_audit_report.md'

def generate_hash(source, author, date_str, review_text):
    author_str = str(author) if author else "Anonymous"
    text_str = str(review_text) if review_text else ""
    # Use the edge-case specified hashing strategy
    hash_input = f"{source}{author_str}{date_str}{text_str[:250]}{len(text_str)}"
    return hashlib.md5(hash_input.encode('utf-8', errors='ignore')).hexdigest()

def parse_date(date_string):
    if not date_string:
        return None
    try:
        dt = parser.parse(str(date_string))
        # Ensure UTC timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        return None

def sanitize_text(text):
    if pd.isna(text) or text is None:
        return ""
    # Basic sanitization, convert to string and handle edge cases
    text = str(text)
    # Strip null bytes and non-printable characters that might break JSON/CSV
    text = text.replace('\x00', '')
    return text.strip()

def normalize_data():
    unified_records = []
    seen_hashes = set()
    audit_stats = {}

    for source_key, file_path in INPUT_FILES.items():
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} not found. Skipping.")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"Error decoding JSON from {file_path}")
                continue
                
        audit_stats[source_key] = {"total": len(data), "processed": 0, "duplicates": 0, "errors": 0}
        
        for item in data:
            try:
                record = {
                    "source": "",
                    "author": "Anonymous",
                    "rating": None,
                    "title": "",
                    "review": "",
                    "app_version": "",
                    "date": "",
                    "url": "",
                    "metadata": {
                        "country": "",
                        "upvotes": 0,
                        "reply_count": 0
                    }
                }

                # Source-specific mapping
                if source_key == 'app_store':
                    record['source'] = "Apple App Store"
                    record['author'] = item.get('author', 'Anonymous')
                    record['rating'] = item.get('rating')
                    record['title'] = item.get('title', '')
                    record['review'] = item.get('review', '')
                    record['app_version'] = item.get('app_version', '')
                    record['date'] = parse_date(item.get('date'))
                
                elif source_key == 'play_store':
                    record['source'] = "Google Play Store"
                    record['author'] = item.get('user_name', 'Anonymous')
                    record['rating'] = item.get('score')
                    record['title'] = ''
                    record['review'] = item.get('content', '')
                    record['app_version'] = item.get('review_created_version', '')
                    record['date'] = parse_date(item.get('at'))
                    record['metadata']['upvotes'] = item.get('thumbs_up_count', 0)
                
                elif source_key == 'reddit':
                    record['source'] = "Reddit"
                    record['author'] = item.get('author', 'Anonymous')
                    record['title'] = item.get('title', '')
                    record['review'] = item.get('review', '')
                    record['date'] = parse_date(item.get('published_date'))
                    record['url'] = item.get('url', '')
                
                elif source_key == 'community':
                    record['source'] = "Google Photos Help Community"
                    record['title'] = item.get('title', '')
                    record['review'] = item.get('snippet', '')
                    record['date'] = parse_date(item.get('scraped_at'))
                    record['url'] = item.get('url', '')
                    record['metadata']['upvotes'] = item.get('upvotes_count', 0)
                    record['metadata']['reply_count'] = item.get('replies_count', 0)
                
                elif source_key == 'youtube':
                    record['source'] = "YouTube"
                    record['author'] = item.get('author', 'Anonymous')
                    record['title'] = item.get('video_title', '')
                    record['review'] = item.get('comment_text', '')
                    record['date'] = parse_date(item.get('published_date'))
                    record['url'] = item.get('video_url', '')
                    try:
                        record['metadata']['upvotes'] = int(item.get('like_count', 0))
                    except (ValueError, TypeError):
                        record['metadata']['upvotes'] = 0
                
                elif source_key == 'socialmedia':
                    record['source'] = item.get('platform', 'Social Media')
                    record['author'] = item.get('author', 'Anonymous')
                    record['title'] = item.get('topic_title', '')
                    record['review'] = item.get('content', '')
                    record['date'] = parse_date(item.get('date'))
                    record['url'] = item.get('source_url', '')

                # Sanitize text fields
                record['title'] = sanitize_text(record['title'])
                record['review'] = sanitize_text(record['review'])
                record['author'] = sanitize_text(record['author'])
                if not record['author']:
                    record['author'] = "Anonymous"
                    
                # Truncate review length if extremely long to avoid mega-thread issues
                if len(record['review']) > 5000:
                    record['review'] = record['review'][:5000] + "... [TRUNCATED]"

                # Generate Hash ID
                review_id = generate_hash(record['source'], record['author'], record['date'], record['review'])
                record['review_id'] = review_id

                # Deduplication
                if review_id not in seen_hashes:
                    seen_hashes.add(review_id)
                    unified_records.append(record)
                    audit_stats[source_key]["processed"] += 1
                else:
                    audit_stats[source_key]["duplicates"] += 1
                    
            except Exception as e:
                audit_stats[source_key]["errors"] += 1
                print(f"Error processing item in {source_key}: {e}")
                
    return unified_records, audit_stats

def write_audit_report(stats):
    with open(AUDIT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Schema Audit & Normalization Report\n\n")
        f.write("| Source | Total Raw | Processed | Duplicates | Errors |\n")
        f.write("|--------|-----------|-----------|------------|--------|\n")
        for source, s in stats.items():
            f.write(f"| {source} | {s['total']} | {s['processed']} | {s['duplicates']} | {s['errors']} |\n")
        f.write(f"\n**Total Unified Records**: {sum(s['processed'] for s in stats.values())}\n")

if __name__ == '__main__':
    print("Starting data unification and normalization...")
    
    # Change dir to the script's dir so output files are in data_processing/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    unified_data, stats = normalize_data()
    
    # Write JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(unified_data, f, indent=2, ensure_ascii=False)
        
    # Write CSV
    # Flatten metadata for CSV
    flat_data = []
    for row in unified_data:
        flat_row = row.copy()
        meta = flat_row.pop('metadata', {})
        flat_row['meta_country'] = meta.get('country')
        flat_row['meta_upvotes'] = meta.get('upvotes')
        flat_row['meta_reply_count'] = meta.get('reply_count')
        flat_data.append(flat_row)
        
    df = pd.DataFrame(flat_data)
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    
    write_audit_report(stats)
    
    print(f"Normalization complete. Generated {len(unified_data)} records.")
    print(f"Saved to {OUTPUT_JSON} and {OUTPUT_CSV}")
