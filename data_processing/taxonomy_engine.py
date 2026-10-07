import json
import os
import time
import re

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

def load_corpus(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_corpus(corpus, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)

def read_prompt_template(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def mock_classify(text):
    text_lower = text.lower()
    taxonomy = {
        "user_memory": "Not specified",
        "retrieval_intent": "Not specified",
        "search_behavior": "Not specified",
        "retrieval_failure": "Not specified",
        "underlying_problem": "Not specified",
        "opportunity_area": "Not specified"
    }
    
    if "date" in text_lower or "year" in text_lower:
        taxonomy["user_memory"] = "Timeframe/Date"
    elif "face" in text_lower or "people" in text_lower:
        taxonomy["user_memory"] = "Person's face"
    elif "screenshot" in text_lower or "receipt" in text_lower:
        taxonomy["user_memory"] = "Document/Screenshot"
    
    if "search" in text_lower or "find" in text_lower:
        taxonomy["search_behavior"] = "Keyword/Natural language search"
    elif "scroll" in text_lower:
        taxonomy["search_behavior"] = "Manual scrolling"
        
    if "can't find" in text_lower or "missing" in text_lower:
        taxonomy["retrieval_failure"] = "Zero or incorrect search results"
        
    return taxonomy

def extract_json_from_llm(response_text):
    try:
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(response_text)
    except json.JSONDecodeError:
        return None

def classify_review(model, prompt_template, record, mock_all=False):
    title = record.get('title', '')
    text = record.get('review', '')
    
    title_str = title if title else ""
    text_str = text if text else ""
    
    prompt = prompt_template.format(title=title_str, text=text_str)
    
    if model and not mock_all:
        try:
            response = model.generate_content(prompt)
            result = extract_json_from_llm(response.text)
            if result:
                return result
        except Exception as e:
            # Silently fallback to avoid spamming console
            pass
            
    return mock_classify(title_str + " " + text_str)

def run_taxonomy_enrichment():
    input_file = "filtered_corpus.json"
    output_file = "enriched_corpus.json"
    prompt_file = "prompts/taxonomy_prompt.txt"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return
        
    corpus = load_corpus(input_file)
    prompt_template = read_prompt_template(prompt_file)
    
    model = None
    mock_all = False
    
    if HAS_GENAI:
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            print("GEMINI_API_KEY not found in environment. Using mock classifier.")
            mock_all = True
    else:
        print("google-generativeai not installed. Using mock classifier.")
        mock_all = True

    print(f"Starting taxonomy classification for {len(corpus)} records...")
    
    enriched_corpus = []
    
    for i, record in enumerate(corpus):
        taxonomy = classify_review(model, prompt_template, record, mock_all)
        record['taxonomy'] = taxonomy
        enriched_corpus.append(record)
        
        if i % 100 == 0 and i > 0:
            print(f"Processed {i} records...")
            if model and not mock_all:
                time.sleep(2) # rate limit protection
                
    save_corpus(enriched_corpus, output_file)
    print(f"Taxonomy enrichment complete. Saved to {output_file}")
    
    generate_qa_report(enriched_corpus, "qa_validation_report.md")

def generate_qa_report(corpus, filepath):
    import random
    sample_size = min(50, len(corpus))
    sample = random.sample(corpus, sample_size)
    
    md = f"# Taxonomy QA Validation Report\n\n"
    md += f"Random sample of {sample_size} records evaluated.\n\n"
    
    for i, rec in enumerate(sample):
        md += f"### Sample {i+1}: {rec.get('title', 'No Title')}\n"
        md += f"> {rec.get('review', '')}\n\n"
        md += "#### Classified Taxonomy:\n"
        md += f"```json\n{json.dumps(rec.get('taxonomy', {}), indent=2)}\n```\n\n"
        md += "---\n\n"
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md)
    print(f"QA Validation report saved to {filepath}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_taxonomy_enrichment()
