import json
import os

def filter_dataset():
    input_file = "data_processing/enriched_corpus.json"
    output_file = "data_processing/enriched_corpus.json"
    backup_file = "data_processing/enriched_corpus_backup.json"
    
    if not os.path.exists(input_file):
        print("Error: Input file not found.")
        return
        
    with open(input_file, 'r', encoding='utf-8') as f:
        corpus = json.load(f)
        
    # Create backup
    if not os.path.exists(backup_file):
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(corpus, f, indent=2)
            
    # Keywords strongly associated with visual memory and retrieval breakdowns
    strong_keywords = [
        "search", "find", "retrieve", "locate", "look for", "looking for", 
        "can't find", "couldn't find", "missing", "remember", "forgot",
        "scroll", "album", "filter", "face", "ocr", "date", "year"
    ]
    
    relevant_corpus = []
    
    for record in corpus:
        text = (record.get('title', '') + " " + record.get('review', '')).lower()
        tax = record.get('taxonomy', {})
        
        # Condition 1: Has strong search/memory keywords
        has_keyword = any(kw in text for kw in strong_keywords)
        
        # Condition 2: LLM identified a retrieval failure or specific search behavior or user memory
        mem = tax.get('user_memory', 'Not specified')
        beh = tax.get('search_behavior', 'Not specified')
        fail = tax.get('retrieval_failure', 'Not specified')
        
        has_taxonomy = False
        if mem not in ['Not specified', 'N/A', 'None']:
            has_taxonomy = True
        if beh not in ['Not specified', 'N/A', 'None']:
            has_taxonomy = True
        if fail not in ['Not specified', 'N/A', 'None']:
            has_taxonomy = True
            
        # We keep the record if it discusses retrieval/memory AND isn't completely generic
        if has_keyword and has_taxonomy:
            relevant_corpus.append(record)
            
    print(f"Total reviews before strict filtering: {len(corpus)}")
    print(f"Total relevant reviews after strict filtering: {len(relevant_corpus)}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(relevant_corpus, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    filter_dataset()
