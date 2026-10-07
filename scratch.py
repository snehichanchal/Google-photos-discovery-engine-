import json

data = json.load(open("data_processing/enriched_corpus.json"))
needs = {}
for r in data:
    tax = r.get('taxonomy', {})
    need = tax.get('opportunity_area', 'Not specified')
    barrier = tax.get('retrieval_failure', 'Not specified')
    behavior = tax.get('search_behavior', 'Not specified')
    
    if need != 'Not specified' or barrier != 'Not specified' or behavior != 'Not specified':
        key = (need, barrier, behavior)
        needs[key] = needs.get(key, 0) + 1

print(f"Total records: {len(data)}")
for k, v in needs.items():
    print(f"Count: {v} | Need: {k[0]} | Barrier: {k[1]} | Behavior: {k[2]}")

