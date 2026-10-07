import json
import os
from collections import defaultdict
from textblob import TextBlob

def analyze_barriers():
    corpus_path = "data_processing/enriched_corpus.json"
    
    with open(corpus_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Barrier categories based on keywords
    problems = {
        'Search Engine Failing / Zero Results': ['search', 'find', 'result', 'looking for'],
        'Incorrect Date/Timeline Sorting': ['date', 'year', 'month', 'sort', 'order', 'timeline'],
        'Missing/Lost Photos after Backup': ['missing', 'lost', 'deleted', 'backup', 'sync'],
        'App Crashing/Freezing during Retrieval': ['crash', 'slow', 'freeze', 'load', 'bug'],
        'Missing or Unrecognized Faces': ['face', 'person', 'recognize', 'tag'],
        'Inability to find Screenshots/Documents': ['screenshot', 'receipt', 'document', 'text']
    }
    
    barrier_records = []
    
    for row in data:
        text = f"{row.get('title', '')} {row.get('review', '')}".lower()
        matched_categories = []
        
        # Check taxonomy (if available)
        tax = row.get('taxonomy', {})
        failure = tax.get('retrieval_failure', 'Not specified')
        if failure != 'Not specified' and failure not in matched_categories:
            matched_categories.append(failure)
            
        # Check keywords
        for prob, keywords in problems.items():
            if any(kw in text for kw in keywords):
                matched_categories.append(prob)
                
        if matched_categories:
            row['barriers'] = list(set(matched_categories))
            
            # Sentiment Analysis
            full_text = f"{row.get('title', '')}. {row.get('review', '')}"
            blob = TextBlob(full_text)
            polarity = blob.sentiment.polarity
            
            if polarity > 0.1:
                sentiment = "Positive"
            elif polarity < -0.1:
                sentiment = "Negative"
            else:
                sentiment = "Neutral"
                
            row['sentiment_score'] = polarity
            row['sentiment_category'] = sentiment
            barrier_records.append(row)
            
    # Compile Stats
    total_barriers = len(barrier_records)
    
    category_counts = defaultdict(int)
    sentiment_counts = defaultdict(int)
    category_sentiment = defaultdict(lambda: defaultdict(int))
    
    for row in barrier_records:
        sentiment = row['sentiment_category']
        sentiment_counts[sentiment] += 1
        
        for cat in row['barriers']:
            category_counts[cat] += 1
            category_sentiment[cat][sentiment] += 1

    # Format Markdown
    md_lines = []
    md_lines.append("# Retrieval Barriers Analysis")
    md_lines.append(f"**Total Records Analyzed**: {len(data)}")
    md_lines.append(f"**Records with Retrieval Barriers**: {total_barriers}")
    md_lines.append(f"*(Percentage: {(total_barriers/len(data))*100:.1f}%)*\n")
    
    md_lines.append("## Barrier Categories")
    md_lines.append("| Barrier Category | Count | % of Barrier Records |")
    md_lines.append("|---|---|---|")
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_barriers) * 100
        md_lines.append(f"| {cat} | {count} | {pct:.1f}% |")
    md_lines.append("\n*Note: A single record may belong to multiple barrier categories.*\n")
    
    md_lines.append("## Sentiment Analysis")
    md_lines.append("Sentiment distribution across the records facing barriers:")
    md_lines.append("| Sentiment | Count | % of Barrier Records |")
    md_lines.append("|---|---|---|")
    for sent in ["Negative", "Neutral", "Positive"]:
        count = sentiment_counts.get(sent, 0)
        pct = (count / total_barriers) * 100 if total_barriers > 0 else 0
        md_lines.append(f"| {sent} | {count} | {pct:.1f}% |")
        
    md_lines.append("\n## Sentiment by Barrier Category")
    md_lines.append("| Barrier Category | Negative | Neutral | Positive |")
    md_lines.append("|---|---|---|---|")
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        neg = category_sentiment[cat]["Negative"]
        neu = category_sentiment[cat]["Neutral"]
        pos = category_sentiment[cat]["Positive"]
        md_lines.append(f"| {cat} | {neg} | {neu} | {pos} |")

    md_lines.append("\n## Examples of Negative Sentiment Records")
    # Get top 5 most negative
    negative_records = sorted([r for r in barrier_records if r['sentiment_category'] == 'Negative'], key=lambda x: x['sentiment_score'])
    for i, rec in enumerate(negative_records[:5]):
        md_lines.append(f"**{i+1}. Source**: {rec.get('source', 'Unknown')} | **Rating**: {rec.get('rating', 'N/A')}")
        md_lines.append(f"**Barriers**: {', '.join(rec['barriers'])}")
        md_lines.append(f"**Review**: *{rec.get('review', '')}*")
        md_lines.append(f"**Sentiment Score**: {rec['sentiment_score']:.2f}")
        md_lines.append("---")

    # Save to artifacts
    # The script should be run in a way that generates the markdown file in the right location.
    out_path = os.environ.get("ARTIFACT_DIR", ".") + "/retrieval_barriers_analysis.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

if __name__ == "__main__":
    analyze_barriers()
