import os
import json
import re
import argparse
import pandas as pd
from datetime import datetime
from google_play_scraper import Sort, reviews

APP_ID = "com.google.android.apps.photos"
DEFAULT_TARGET_COUNT = 500

def is_relevant_review(content):
    """
    Classifies if a review is relevant to:
    1. How people remember old visual information (memories, finding old photos/videos, searching past moments).
    2. Where the existing retrieval experience breaks down (search failures, inability to locate pictures,
       sorting/filtering issues, broken face tags, missing memories, loss/inaccessibility of backed-up photos).
    """
    if not content or len(str(content).strip()) < 12:
        return False

    text = str(content).lower()

    # Core photo & memory domain terms
    photo_terms = [
        'photo', 'photos', 'pic', 'pics', 'picture', 'pictures', 'image', 'images', 
        'video', 'videos', 'album', 'albums', 'gallery', 'memory', 'memories', 
        'media', 'snapshot', 'snapshots'
    ]

    # Search, retrieval, & organization terms
    retrieval_terms = [
        'search', 'searching', 'find', 'finding', 'found', 'locate', 'locating', 
        'retrieve', 'retrieving', 'retrieval', 'filter', 'filtering', 'sort', 
        'sorting', 'organize', 'organizing', 'organized', 'organization', 'timeline', 
        'scroll', 'scrolling', 'date', 'dates', 'year', 'years', 'face', 'faces', 
        'tag', 'tags', 'tagging', 'grouping', 'look for', 'looking for', 'lost', 
        'missing', 'disappear', 'disappeared', 'gone', 'delete', 'deleted', 'restore', 
        'restoring', 'backup', 'back up', 'backed up', 'old', 'past', 'remember', 
        'remembering', 'recollect', 'recollection', 'archive', 'unarchive', 'history', 
        'nostalgia', 'childhood', 'reminisce', 'relive', 'throwback', 'access', 'accessible'
    ]

    # Explicit retrieval breakdown patterns
    breakdown_terms = [
        "can't find", "cannot find", "hard to find", "unable to find", "difficult to find", 
        "impossible to find", "where are my", "where did my", "where have my", "lost my", 
        "lost all", "missing photos", "missing pictures", "disappeared", "gone", 
        "can't search", "search is broken", "search doesn't work", "search not working", 
        "bad search", "worst search", "can't sort", "cannot sort", "sorting broken", 
        "face recognition", "face tagging", "wrong date", "wrong dates", "wrong order", 
        "scrambled", "mixed up", "hard to navigate", "confusing layout", "ruined gallery", 
        "bring back", "bring back old", "memory feature", "memories feature"
    ]

    # High-value domain specific phrases
    key_phrases = [
        'old photo', 'old picture', 'old memory', 'old photos', 'old pictures', 'old memories',
        'find photo', 'find picture', 'find video', 'find photos', 'find pictures', 'find videos',
        'search feature', 'search bar', 'search option', 'face recognition', 'people and pets',
        'years ago', 'back in', 'way back', 'reminisce', 'reminiscing', 'relive'
    ]

    has_photo = any(re.search(r'\b' + re.escape(pt) + r'\b', text) for pt in photo_terms)
    has_retrieval = any(re.search(r'\b' + re.escape(rt) + r'\b', text) for rt in retrieval_terms)
    has_breakdown = any(bt in text for bt in breakdown_terms)
    has_key_phrase = any(kp in text for kp in key_phrases)

    # Exclude common irrelevant phrases (e.g., pure update complaints, billing, ads, app crash on open without photo context)
    irrelevant_patterns = ['bad update', 'worst update', 'cannot download', "won't open", 'app crashing', 'pay for storage', 'too many ads']
    if any(ip in text for ip in irrelevant_patterns) and not (has_breakdown or 'search' in text or 'memory' in text or 'find' in text or 'old' in text):
        return False

    return bool(has_breakdown or has_key_phrase or (has_photo and has_retrieval))


def update_and_scrape_reviews(target_count=DEFAULT_TARGET_COUNT, output_dir=None):
    """
    Scans existing dataset in output_dir, removes irrelevant reviews,
    scrapes new Play Store reviews, filters for domain relevance,
    and updates existing google_photos_reviews.json & csv in place.
    """
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    json_filepath = os.path.join(output_dir, "google_photos_reviews.json")
    csv_filepath = os.path.join(output_dir, "google_photos_reviews.csv")

    existing_reviews = []
    if os.path.exists(json_filepath):
        try:
            with open(json_filepath, "r", encoding="utf-8") as f:
                existing_reviews = json.load(f)
            print(f"📖 Loaded {len(existing_reviews)} existing reviews from {json_filepath}")
        except Exception as e:
            print(f"⚠️ Warning reading existing JSON: {e}")

    # 1. Filter existing dataset
    filtered_existing = []
    removed_count = 0
    for r in existing_reviews:
        if is_relevant_review(r.get("content", "")):
            filtered_existing.append(r)
        else:
            removed_count += 1

    print(f"🧹 Existing Dataset Scan Complete:")
    print(f"   - Retained relevant: {len(filtered_existing)}")
    print(f"   - Removed irrelevant: {removed_count}")

    # Track seen review IDs
    seen_ids = {r["review_id"] for r in filtered_existing if r.get("review_id")}
    combined_relevant = list(filtered_existing)

    # 2. Fetch new reviews from Play Store until target_count relevant reviews is reached
    print(f"\n🌐 Scraping Google Play Store to reach {target_count} relevant reviews...")

    sort_modes = [Sort.NEWEST, Sort.MOST_RELEVANT]
    countries = ['us', 'gb', 'ca', 'au', 'in']

    scraped_raw_count = 0
    new_relevant_count = 0

    for sort_mode in sort_modes:
        if len(combined_relevant) >= target_count:
            break
        for country in countries:
            if len(combined_relevant) >= target_count:
                break
            
            print(f"   Fetching reviews (Sort: {sort_mode}, Country: '{country}')...")
            try:
                scraped, _ = reviews(
                    APP_ID,
                    lang="en",
                    country=country,
                    sort=sort_mode,
                    count=1500
                )
                scraped_raw_count += len(scraped)

                for item in scraped:
                    rid = item.get("reviewId")
                    if rid and rid not in seen_ids:
                        content = item.get("content", "")
                        if is_relevant_review(content):
                            seen_ids.add(rid)
                            review_dict = {
                                "review_id": rid,
                                "user_name": item.get("userName"),
                                "user_image": item.get("userImage"),
                                "content": content,
                                "score": item.get("score"),
                                "thumbs_up_count": item.get("thumbsUpCount"),
                                "review_created_version": item.get("reviewCreatedVersion"),
                                "at": item.get("at").isoformat() if isinstance(item.get("at"), datetime) else str(item.get("at")),
                                "reply_content": item.get("replyContent"),
                                "replied_at": item.get("repliedAt").isoformat() if isinstance(item.get("repliedAt"), datetime) else str(item.get("repliedAt")) if item.get("repliedAt") else None
                            }
                            combined_relevant.append(review_dict)
                            new_relevant_count += 1

                            if len(combined_relevant) >= target_count:
                                break
            except Exception as e:
                print(f"   ⚠️ Warning while scraping ({sort_mode}, {country}): {e}")

    print(f"\n📊 Scraping Summary:")
    print(f"   - Total raw reviews inspected: {scraped_raw_count}")
    print(f"   - New relevant reviews added: {new_relevant_count}")
    print(f"   - Total relevant reviews collected: {len(combined_relevant)}")

    # Sort reviews by 'at' date descending
    def get_date(r):
        return r.get("at") or ""

    combined_relevant.sort(key=get_date, reverse=True)

    # Trim to target count if exceeded
    final_reviews = combined_relevant[:target_count]

    # Save directly into existing JSON & CSV files
    print(f"\n💾 Updating existing dataset files in place ({len(final_reviews)} reviews)...")

    # Update JSON
    with open(json_filepath, "w", encoding="utf-8") as f:
        json.dump(final_reviews, f, indent=2, ensure_ascii=False)
    print(f"✅ Updated JSON: {json_filepath}")

    # Update CSV
    df = pd.DataFrame(final_reviews)
    df.to_csv(csv_filepath, index=False, encoding="utf-8-sig")
    print(f"✅ Updated CSV: {csv_filepath}")

    return final_reviews

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape and filter Play Store reviews for Google Photos regarding photo memory retrieval.")
    parser.add_argument("--count", type=int, default=DEFAULT_TARGET_COUNT, help=f"Number of relevant reviews to collect (default: {DEFAULT_TARGET_COUNT})")

    args = parser.parse_args()
    update_and_scrape_reviews(target_count=args.count)
