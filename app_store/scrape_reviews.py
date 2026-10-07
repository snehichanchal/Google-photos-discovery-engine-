import requests
import json
import csv
import os
import sys
import re

# App Store Details for Google Photos
APP_ID = '962194608'  # Google Photos: Backup & Edit on Apple App Store
APP_NAME = 'Google Photos'
TARGET_COUNT = 500

# Major English & Global App Store Country Codes to ensure rich review coverage
COUNTRIES = [
    'us', 'gb', 'ca', 'au', 'in', 'ie', 'nz', 'sg', 'ph', 'za',
    'my', 'ng', 'ke', 'de', 'nl', 'se', 'no', 'dk', 'fi', 'gh', 'jm', 'tt'
]

# Relevance keywords related to visual memory, photo retrieval experience, and breakdown points
RELEVANCE_KEYWORDS = [
    'photo', 'picture', 'image', 'video', 'media', 'memory', 'memories',
    'search', 'find', 'found', 'looking', 'scroll', 'album', 'date', 'year',
    'old', 'backup', 'back up', 'sync', 'store', 'storage', 'lost', 'missing',
    'delete', 'disappear', 'retrieve', 'retrieval', 'face', 'people', 'tag',
    'organize', 'timeline', 'ui', 'update', 'layout', 'access', 'restore',
    'cloud', 'google photos', 'gallery', 'drive', 'paywall', 'quality', 'duplicate',
    'locate', 'sort', 'folder', 'recover', 'space'
]

def is_relevant_review(review_text, title=''):
    """
    Filters out short, non-substantive, or generic spam reviews.
    Checks if review is relevant to photo retrieval, memories, storage, search, UI/UX, or app features.
    """
    combined = (title + ' ' + review_text).strip()
    clean_text = review_text.strip()
    
    # Filter out empty or extremely short/generic responses (< 25 characters or < 5 words)
    if len(clean_text) < 25 or len(clean_text.split()) < 5:
        return False
    
    # Exclude common single-word/generic praise or spam patterns
    spam_pattern = r'^(good|great|nice|awesome|love it|best app|bad|ok|thanks|cool|super|top|bad app)[\.!\s]*$'
    if re.match(spam_pattern, combined.lower()):
        return False

    # Ensure text contains domain-relevant keywords
    combined_lower = combined.lower()
    return any(kw in combined_lower for kw in RELEVANCE_KEYWORDS)

def filter_existing_dataset(json_path):
    """
    Scans existing dataset and removes reviews that are not relevant.
    Returns filtered list of relevant reviews and set of seen IDs.
    """
    if not os.path.exists(json_path):
        return [], set()

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    except Exception as e:
        print(f"Error reading existing JSON file: {e}")
        return [], set()

    relevant_existing = []
    seen_ids = set()

    for item in existing_data:
        r_id = item.get('review_id')
        if not r_id or r_id in seen_ids:
            continue
        
        title = item.get('title', '')
        text = item.get('review', '')
        
        if is_relevant_review(text, title):
            seen_ids.add(r_id)
            # Ensure store field is present
            item['store'] = 'Apple App Store'
            relevant_existing.append(item)

    print(f"Scanned existing dataset: Retained {len(relevant_existing)} relevant reviews, removed {len(existing_data) - len(relevant_existing)} non-relevant reviews.")
    return relevant_existing, seen_ids

def scrape_app_store_reviews(target_count=TARGET_COUNT, existing_reviews=None, seen_ids=None):
    """
    Scrapes Apple App Store RSS customer reviews across storefronts to reach target count of relevant reviews.
    """
    if existing_reviews is None:
        existing_reviews = []
    if seen_ids is None:
        seen_ids = set()

    reviews = list(existing_reviews)
    print(f"Starting scraping to collect target of {target_count} relevant reviews (currently have {len(reviews)})...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    for country in COUNTRIES:
        if len(reviews) >= target_count:
            break

        for page in range(1, 11):
            if len(reviews) >= target_count:
                break

            url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={APP_ID}/sortby=mostrecent/json"
            
            try:
                response = requests.get(url, headers=headers, timeout=8)
                if response.status_code != 200:
                    continue

                data = response.json()
                entries = data.get('feed', {}).get('entry', [])

                for entry in entries:
                    review_id = entry.get('id', {}).get('label')
                    if not review_id or 'im:rating' not in entry or review_id in seen_ids:
                        continue

                    title = entry.get('title', {}).get('label', '')
                    content = entry.get('content', {}).get('label', '')

                    if is_relevant_review(content, title):
                        seen_ids.add(review_id)
                        
                        review_data = {
                            'review_id': review_id,
                            'author': entry.get('author', {}).get('name', {}).get('label', 'Anonymous'),
                            'rating': int(entry.get('im:rating', {}).get('label', 0)),
                            'title': title,
                            'review': content,
                            'app_version': entry.get('im:version', {}).get('label', ''),
                            'date': entry.get('updated', {}).get('label', ''),
                            'store': 'Apple App Store'
                        }
                        
                        reviews.append(review_data)
                        
                        if len(reviews) >= target_count:
                            break

            except Exception as e:
                pass

    print(f"Total relevant reviews assembled: {len(reviews)}")
    return reviews[:target_count]

def save_to_json(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Updated existing JSON file: {filepath}")

def save_to_csv(data, filepath):
    if not data:
        return
    fieldnames = list(data[0].keys())
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Updated existing CSV file: {filepath}")

def analyze_review_themes(reviews):
    """
    Categorizes reviews by key visual memory & retrieval themes for quick insights.
    """
    themes = {
        'Memories & Timeline (Throwbacks, Remembering Old Photos)': 0,
        'Photo Search & Retrieval Experience': 0,
        'Lost / Missing Photos & Backup Breakdowns': 0,
        'UI, Navigation & Layout Changes': 0,
        'Storage, Cloud Sync & Paywall Issues': 0
    }
    
    for r in reviews:
        text = (r.get('title', '') + ' ' + r.get('review', '')).lower()
        if any(k in text for k in ['memory', 'memories', 'throwback', 'remember', 'old photo', 'years ago']):
            themes['Memories & Timeline (Throwbacks, Remembering Old Photos)'] += 1
        if any(k in text for k in ['search', 'find', 'found', 'locate', 'filter', 'sort', 'tag', 'face']):
            themes['Photo Search & Retrieval Experience'] += 1
        if any(k in text for k in ['lost', 'missing', 'deleted', 'disappear', 'vanish', 'erase']):
            themes['Lost / Missing Photos & Backup Breakdowns'] += 1
        if any(k in text for k in ['ui', 'update', 'layout', 'navigation', 'tab', 'design', 'interface']):
            themes['UI, Navigation & Layout Changes'] += 1
        if any(k in text for k in ['storage', 'paywall', 'space', 'cloud', 'backup', 'back up', 'sync']):
            themes['Storage, Cloud Sync & Paywall Issues'] += 1

    return themes

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, 'google_photos_app_store_reviews.json')
    csv_path = os.path.join(script_dir, 'google_photos_app_store_reviews.csv')

    # Step 1: Scan and filter existing dataset
    relevant_existing, seen_ids = filter_existing_dataset(json_path)

    # Step 2: Scrape new reviews to reach 500 relevant items
    final_reviews = scrape_app_store_reviews(
        target_count=TARGET_COUNT,
        existing_reviews=relevant_existing,
        seen_ids=seen_ids
    )

    if final_reviews:
        # Step 3: Overwrite/update existing files with new 500 filtered reviews
        save_to_json(final_reviews, json_path)
        save_to_csv(final_reviews, csv_path)

        # Step 4: Summary Statistics & Theme Analysis
        ratings = [r['rating'] for r in final_reviews]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        print("\n================ DATASET SUMMARY ================")
        print(f"Total Relevant Reviews in Dataset: {len(final_reviews)}")
        print(f"Average Rating: {avg_rating:.2f} / 5.0")
        print("\nRating Distribution:")
        for star in range(5, 0, -1):
            count_star = ratings.count(star)
            print(f"  {star} Stars: {count_star} ({count_star/len(ratings)*100:.1f}%)")
        
        print("\nKey User Experience Themes Identified:")
        theme_counts = analyze_review_themes(final_reviews)
        for theme, count in theme_counts.items():
            print(f"  - {theme}: {count} reviews ({count/len(final_reviews)*100:.1f}%)")
        print("=================================================\n")
    else:
        print("No relevant reviews were found.")

if __name__ == '__main__':
    main()
