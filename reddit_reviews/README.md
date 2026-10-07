# Reddit Reviews Scraper for Google Photos

This directory contains Python scripts and generated datasets for scraping user reviews, feedback, and community discussions about the **Google Photos** application from **Reddit**.

## Directory Structure

- `scrape_reviews.py`: Main Python script to scrape the 100 latest reviews/discussions from Reddit.
- `requirements.txt`: Python dependencies required to run the script (`requests`, `beautifulsoup4`).
- `google_photos_reddit_reviews.json`: Saved JSON dataset containing 100 Reddit reviews with rich metadata.
- `google_photos_reddit_reviews.csv`: Saved CSV dataset formatted for spreadsheet analysis.

## Setup & Execution

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Scraper
```bash
python3 scrape_reviews.py
```

## Scraped Fields

Each review record contains:
- `review_id`: Unique post ID from Reddit (e.g. `t3_1wo2345`)
- `title`: Title of the Reddit post / discussion
- `review`: Full body text / content of the review
- `author`: Author username (e.g. `/u/username`)
- `subreddit`: Subreddit name (e.g. `r/googlephotos`)
- `url`: Direct link to the Reddit post
- `published_date`: Timestamp in ISO 8601 format
- `source`: Source platform (`Reddit`)

## Features & Robustness
- Automatically parses Atom XML RSS feeds (`r/googlephotos` and global Reddit search).
- Handles HTTP 429 rate limits gracefully with dynamic backoff retry logic (`x-ratelimit-reset`).
- Extracts clean body text using `BeautifulSoup` by stripping HTML wrapper tags.
- Outputs summary statistics including total review count, average word count, and top subreddits.
