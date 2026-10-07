# Google Photos Social Media Reviews & Memory Retrieval Analysis

This directory contains the scraper script, dataset, and analysis of **200 latest social media reviews and discussions** regarding how users remember old visual information and where the current retrieval experience in Google Photos breaks down.

---

## 📁 Directory Structure

```
socialmedia_reviews/
├── scrape_socialmedia_reviews.py        # Python scraper script
├── google_photos_socialmedia_reviews.json # JSON output (200 structured reviews)
├── google_photos_socialmedia_reviews.csv  # CSV dataset for tabular analysis
├── requirements.txt                      # Python dependencies
└── README.md                             # Documentation & research insights
```

---

## 🛠️ Installation & Usage

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Execute the scraper script:**
   ```bash
   python scrape_socialmedia_reviews.py --count 200
   ```

---

## 📊 Dataset Schema

Each entry in `google_photos_socialmedia_reviews.json` / `google_photos_socialmedia_reviews.csv` contains:

| Field | Type | Description |
|---|---|---|
| `id` | String | Unique review identifier (e.g. `sm_rev_001` to `sm_rev_200`) |
| `platform` | String | Social media platform / community source (e.g., `HackerNews Social`) |
| `author` | String | Anonymized or public user handle |
| `date` | String | Date of post/discussion (`YYYY-MM-DD`) |
| `topic_title` | String | Title of the social media discussion thread |
| `content` | String | User review / post content detailing Google Photos experience |
| `visual_memory_pattern` | String | Classification of how the user remembers old visual info |
| `retrieval_breakdown_point` | String | Classification of where the search/retrieval failed |
| `user_workaround` | String | Action taken by the user (e.g., manual scroll, switching apps) |
| `sentiment` | String | Sentiment (`Frustrated`, `Mixed / Neutral`, `Satisfied`) |
| `source_url` | String | Direct link to the social media thread |

---

## 💡 Key Research Insights

### 1. How People Remember Old Visual Information
- **Temporal & Spatial Cues (~66%)**: Users remember *when* or *where* an event took place (e.g. "summer 2019 trip to Italy", "around my daughter's 2nd birthday").
- **Visual Attributes & Objects (~11%)**: Users remember specific visual cues (e.g. "wearing a blue jacket", "red vintage car", "dog near a lake").
- **Person & Social Context (~10%)**: Users remember who was in the picture or the group dynamic.
- **Event & Episodic Memory**: Memory is bound to events (weddings, parties, trips) rather than isolated keywords.
- **Text & OCR Cues**: Users remember specific text printed on signs, receipts, or documents captured in screenshots.

### 2. Where the Retrieval Experience Breaks Down
- **Lack of Custom Tagging & Manual Captions**: Users express frustration over being unable to add custom tags or edit EXIF metadata easily to make photos findable by custom memory anchors.
- **Semantic & Natural Language Mismatch**: Current search struggles with complex multi-attribute queries (e.g. "cat sitting on yellow rug near bookshelf") and yields irrelevant results or omits matching photos.
- **Album & Folder Retrieval Failure**: Search often bypasses album structures or fails to search within manually curated albums effectively.
- **High Cognitive Load**: When search fails, users are forced into manual infinite scrolling across tens of thousands of photos in the main grid timeline.
- **Loss of Context on Export**: Users face breakdown when backing up or exporting photos via Google Takeout, losing metadata and album hierarchy.
