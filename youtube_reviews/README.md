# Google Photos YouTube Reviews Scraper

This folder contains the python script and dataset for scraping and analyzing 200 user reviews and comments from YouTube videos regarding the **Google Photos** application.

## Research Objectives
1. **Visual Memory Recall Patterns**: Analyze how users recall old photos using visual cues (colors, objects, time/location context, face recognition, text/OCR, events).
2. **Retrieval Experience Breakdown Points**: Identify pain points where Google Photos search fails (vague prompts, Ask Photos Gemini failures, metadata/tagging limitations, album/folder structure breakdowns, high cognitive load).

## Project Structure
- `scrape_youtube_reviews.py`: Python script to fetch YouTube comments from relevant Google Photos review & tutorial videos, classify visual memory patterns & breakdown points, and save datasets.
- `requirements.txt`: Python package dependencies.
- `google_photos_youtube_reviews.json`: JSON output containing 200 structured YouTube reviews/comments.
- `google_photos_youtube_reviews.csv`: CSV export of the dataset.

## Setup & Execution

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Scraper
To scrape 200 reviews/comments:
```bash
python3 scrape_youtube_reviews.py --count 200
```

## Schema Fields
- `id`: Unique review ID (e.g. `yt_rev_001`)
- `review_id`: Original YouTube comment CID
- `video_id`: YouTube video identifier
- `video_title`: Title of the YouTube video
- `author`: Commenter handle
- `comment_text`: Full body text of the comment
- `published_date`: Date or relative time of the comment
- `like_count`: Number of likes on the comment
- `visual_memory_pattern`: Categorized memory cue
- `retrieval_breakdown_point`: Categorized retrieval pain point
- `user_workaround`: Workaround strategy used by the user
- `sentiment`: Sentiment classification (Frustrated, Satisfied, Mixed / Neutral)
- `video_url`: Direct video link
- `source`: "YouTube Comments"
