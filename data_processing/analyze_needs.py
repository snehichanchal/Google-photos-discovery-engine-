import json
import os
from collections import defaultdict

def analyze_needs():
    corpus_path = "data_processing/enriched_corpus.json"
    with open(corpus_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Barrier categories based on keywords
    problems = {
        'Search Engine Failing / Zero Results': {
            'keywords': ['search', 'find', 'result', 'looking for'],
            'need': 'Reliable, contextual, and accurate natural language search',
            'behavior': 'Keyword / Natural language search'
        },
        'Incorrect Date/Timeline Sorting': {
            'keywords': ['date', 'year', 'month', 'sort', 'order', 'timeline'],
            'need': 'Accurate chronological timeline and sorting controls',
            'behavior': 'Manual scrolling and sorting'
        },
        'Missing/Lost Photos after Backup': {
            'keywords': ['missing', 'lost', 'deleted', 'backup', 'sync'],
            'need': 'Transparent and reliable backup syncing status',
            'behavior': 'Checking backed up folders / retrieving old photos'
        },
        'App Crashing/Freezing during Retrieval': {
            'keywords': ['crash', 'slow', 'freeze', 'load', 'bug'],
            'need': 'Fast and stable app performance during search/scroll',
            'behavior': 'Opening the app / scrolling fast'
        },
        'Missing or Unrecognized Faces': {
            'keywords': ['face', 'person', 'recognize', 'tag'],
            'need': 'Accurate facial recognition and manual tagging controls',
            'behavior': 'Searching for specific people / checking face groups'
        },
        'Inability to find Screenshots/Documents': {
            'keywords': ['screenshot', 'receipt', 'document', 'text'],
            'need': 'Automatic categorization of documents and screenshots',
            'behavior': 'Searching for receipts/documents'
        }
    }
    
    records_with_needs = 0
    results = defaultdict(int)
    
    for row in data:
        text = f"{row.get('title', '')} {row.get('review', '')}".lower()
        has_need = False
        
        for prob, info in problems.items():
            if any(kw in text for kw in info['keywords']):
                results[prob] += 1
                has_need = True
                
        if has_need:
            records_with_needs += 1

    md_lines = []
    md_lines.append("# Unmet Consumer Needs Analysis")
    md_lines.append(f"**Total Records Analyzed**: {len(data)}")
    md_lines.append(f"**Total Matching Records with Identified Needs**: {records_with_needs}")
    md_lines.append(f"*(Percentage: {(records_with_needs/len(data))*100:.1f}%)*\n")
    
    md_lines.append("| Unmet Consumer Need | Associated Barrier | Associated Behavior | Record Count |")
    md_lines.append("|---|---|---|---|")
    
    # Sort by count
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    
    for prob, count in sorted_results:
        info = problems[prob]
        md_lines.append(f"| {info['need']} | {prob} | {info['behavior']} | {count} |")
        
    out_path = os.environ.get("ARTIFACT_DIR", ".") + "/unmet_needs_analysis.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
        
    print(f"Generated report at {out_path}")
    print(f"Total matching records: {records_with_needs}")

if __name__ == "__main__":
    analyze_needs()
