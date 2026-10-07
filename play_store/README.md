# Google Photos Play Store Review Scraper & Relevance Analyzer

This directory contains scripts and datasets for scraping and analyzing **Google Play Store reviews for Google Photos**, specifically focusing on:
1. **How people remember old visual information** (searching for past memories, finding old photos/videos, timeline browsing, nostalgia, album organization).
2. **Where the existing retrieval experience breaks down** (search failures, inability to locate pictures, sorting/filtering bugs, broken face tagging, lost/inaccessible backed-up photos).

## Features
- **Dataset Cleaning & In-Place Updating**: Scans existing dataset (`google_photos_reviews.json` & `google_photos_reviews.csv`), removes generic/irrelevant reviews, and updates existing files in place without creating separate files.
- **Domain Relevance Filter**: Uses natural language keyword and breakdown pattern matching to isolate reviews specifically addressing visual memory retrieval and search breakdown.
- **Multi-Sort & Regional Fetching**: Aggregates reviews across multiple Play Store sort modes (`NEWEST`, `MOST_RELEVANT`) and regions (`US`, `GB`, `CA`, `AU`, `IN`) to compile 500 high-quality relevant reviews.
- **Dual Export**: Saves clean structured dataset to both `CSV` (`google_photos_reviews.csv`) and `JSON` (`google_photos_reviews.json`).

## Requirements
- Python 3.8+
- `google-play-scraper`
- `pandas`

Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the script to scan existing files, remove irrelevant reviews, fetch new relevant Play Store reviews, and update `google_photos_reviews.json` and `google_photos_reviews.csv` in place:
```bash
python scrape_reviews.py
```

### Optional Arguments:
- `--count`: Target number of relevant reviews to collect (default: `500`)

Example:
```bash
python scrape_reviews.py --count 500
```

## Dataset Fields
The resulting `google_photos_reviews.json` and `google_photos_reviews.csv` files contain:
- `review_id`: Unique ID of the review
- `user_name`: Name of the reviewer
- `user_image`: Profile picture URL of reviewer
- `content`: Review body text
- `score`: Star rating (1 to 5)
- `thumbs_up_count`: Number of thumbs up / helpful votes
- `review_created_version`: App version when review was submitted
- `at`: ISO Datetime timestamp of review
- `reply_content`: Developer response text (if applicable)
- `replied_at`: Developer response timestamp (if applicable)
