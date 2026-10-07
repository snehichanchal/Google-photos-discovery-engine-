# Google Photos Community Reviews Scraper

A Python utility to scrape user reviews, discussions, and support threads for **Google Photos** from the official [Google Photos Help Community](https://support.google.com/photos/threads).

---

## 📌 Features

- Scrapes the latest **200+ community discussions & reviews**.
- Extracts critical data fields:
  - `thread_id`: Unique Google Community Thread ID
  - `title`: Subject/Headline of the user's issue or feedback
  - `snippet`: Summary text of the issue/review
  - `category`: Discussion topic tag (e.g. `FIX_PROBLEM`, `BACKUP_SYNC`, etc.)
  - `recommended_answers`: Count of official/recommended solutions
  - `replies_count`: Total number of user replies
  - `upvotes_count`: Number of user upvotes ("I have the same question")
  - `url`: Direct link to the thread on Google Support
  - `scraped_at`: ISO UTC timestamp of extraction
- Exports scraped data in both **CSV** (`google_photos_community_reviews.csv`) and **JSON** (`google_photos_community_reviews.json`) formats.

---

## ⚙️ Installation

Make sure you have Python 3.8+ installed. Install the required packages:

```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

### 1. Run default (scrapes 200 latest reviews):

```bash
python scrape_reviews.py
```

### 2. Specify custom count or output directory:

```bash
python scrape_reviews.py --count 200 --output-dir .
```

### 3. Fetch detailed pages (author info and full content body):

```bash
python scrape_reviews.py --count 200 --fetch-details
```

---

## 📁 Output Files

- `google_photos_community_reviews.csv`: Clean tabular dataset (UTF-8 SIG encoded).
- `google_photos_community_reviews.json`: Structured JSON formatted dataset.
