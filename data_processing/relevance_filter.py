import json
import os
import re
from keyword_dictionaries import DOMAIN_KEYWORDS, SPAM_PATTERNS

def load_corpus(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_corpus(corpus, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)

def write_stats(stats, filepath):
    md_content = f"# Filtering Statistics\n\n"
    md_content += f"- **Total Records Processed**: {stats['total']}\n"
    md_content += f"- **Total Accepted**: {stats['accepted']}\n"
    md_content += f"- **Total Discarded**: {stats['discarded']}\n\n"
    md_content += f"## Discard Reasons\n\n"
    md_content += f"- **Too Short (Length Filter)**: {stats['reasons']['too_short']}\n"
    md_content += f"- **Generic Spam**: {stats['reasons']['spam']}\n"
    md_content += f"- **Off-Domain (No Keywords)**: {stats['reasons']['no_keywords']}\n"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)

def filter_corpus():
    input_file = "unified_corpus.json"
    output_file = "filtered_corpus.json"
    stats_file = "filter_stats_report.md"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    corpus = load_corpus(input_file)
    accepted_records = []
    
    stats = {
        'total': len(corpus),
        'accepted': 0,
        'discarded': 0,
        'reasons': {
            'too_short': 0,
            'spam': 0,
            'no_keywords': 0
        }
    }
    
    for record in corpus:
        text = record.get('review', '') or ''
        title = record.get('title', '') or ''
        
        full_text = f"{title} {text}".strip()
        
        # 1. Length filter (>=25 chars, >=5 words)
        if len(full_text) < 25 or len(full_text.split()) < 5:
            stats['discarded'] += 1
            stats['reasons']['too_short'] += 1
            continue
            
        # 2. Generic spam pattern matching
        is_spam = False
        for pattern in SPAM_PATTERNS:
            if pattern.search(full_text):
                is_spam = True
                break
        
        if is_spam:
            stats['discarded'] += 1
            stats['reasons']['spam'] += 1
            continue
            
        # 3. Domain & retrieval keyword matching
        has_keyword = False
        full_text_lower = full_text.lower()
        for kw in DOMAIN_KEYWORDS:
            if kw in full_text_lower:
                has_keyword = True
                break
                
        if not has_keyword:
            stats['discarded'] += 1
            stats['reasons']['no_keywords'] += 1
            continue
            
        # Accepted
        accepted_records.append(record)
        stats['accepted'] += 1
        
    save_corpus(accepted_records, output_file)
    write_stats(stats, stats_file)
    
    print(f"Filtering complete. Accepted {stats['accepted']} out of {stats['total']} records.")
    print(f"Results saved to {output_file} and stats to {stats_file}")

if __name__ == "__main__":
    # Move to the same directory as script to access local files if needed
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    filter_corpus()
