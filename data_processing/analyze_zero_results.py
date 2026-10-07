import json
import re
from collections import Counter

def categorize_review(text):
    text_lower = text.lower()
    
    # 1. False Positives (Positive review, found missing items, survey questions)
    if re.search(r'(found.*missing)|(finally found)|(love.*search)|(what do you like)', text_lower):
        return "False Positive / Not a Failure"
        
    # 2. Missing Features / UI Elements
    if re.search(r'(missing.*sort)|(missing.*feature)|(can\'t find.*button)|(can\'t find.*video)|(can\'t find.*setting)|(ai features missing)|(can\'t find.*option)|(can\'t find.*way)', text_lower):
        return "Missing Feature/UI Element"
        
    # 3. Data Loss / Sync / Backup Issues
    if re.search(r'(backed.*up.*can\'t find)|(albums.*missing)|(pictures.*gone)|(photos.*missing)|(old.*missing)|(vanished)|(disappeared)|(pics are missing)|(photos from the year)|(phone was accid)|(pitchers.*can\'t find)', text_lower):
        return "Data Loss / Sync Issues"
        
    # 4. Poor Search Accuracy / Algorithm Issues (Censorship, Gemini, etc.)
    if re.search(r'(search.*terrible)|(search.*sucks)|(gemini)|(can\'t find.*search)|(search.*doesn\'t work)|(search.*censored)|(can\'t find tons of things)', text_lower):
        return "Poor Search Accuracy / Algorithm Limits"
        
    # 5. UX Confusion / Organization
    if re.search(r'(star.*can\'t find)|(folder)|(collections)|(rearrange photos)|(backs.*up.*can\'t find then again)|(navigate)', text_lower):
        return "UX/Organization Confusion"
        
    # Fallback for remaining true retrieval issues
    if re.search(r'can\'t find.*photo', text_lower) or re.search(r'missing.*photo', text_lower):
        return "General Retrieval/Finding Difficulty"
        
    return "Other / Irrelevant / General Complaints"

def main():
    try:
        with open('data_processing/enriched_corpus.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print("Error loading data:", e)
        return
        
    fail_data = [d for d in data if d.get('taxonomy', {}).get('retrieval_failure') == 'Zero or incorrect search results']
    print(f"Total reviews flagged as 'Zero or incorrect search results': {len(fail_data)}")
    
    categories = []
    for d in fail_data:
        cat = categorize_review(d['review'])
        categories.append(cat)
        
    c = Counter(categories)
    
    print("\nCategorization Breakdown:")
    print("-" * 50)
    for cat, count in c.most_common():
        percentage = (count / len(fail_data)) * 100
        print(f"{cat}: {count} ({percentage:.2f}%)")

if __name__ == "__main__":
    main()
