#!/usr/bin/env python3
"""
Alias script for scrape_youtube_reviews.py
"""
import sys
from scrape_youtube_reviews import scrape_youtube_reviews, DEFAULT_COUNT

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scrape 200 YouTube reviews about Google Photos retrieval & visual memory.")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help=f"Number of reviews to compile (default: {DEFAULT_COUNT})")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory path")
    args = parser.parse_args()

    scrape_youtube_reviews(target_count=args.count, output_dir=args.output_dir)
