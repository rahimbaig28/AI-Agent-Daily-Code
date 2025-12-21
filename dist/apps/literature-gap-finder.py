# Auto-generated via Perplexity on 2025-12-21T01:41:14.038000Z
#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from collections import defaultdict, Counter
from pathlib import Path

STOP_WORDS = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been'}

def read_sentences(file_path):
    """Read file and extract sentences using simple punctuation splitting."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        sentences = re.split(r'[.!?]+', content)
        return [s.strip() for s in sentences if s.strip()]
    except Exception:
        return []

def extract_phrases(sentence, min_words):
    """Extract n-gram phrases from sentence."""
    words = re.findall(r'\b\w+\b', sentence)
    words = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    phrases = []
    for length in range(min_words, min(6, len(words) + 1)):
        for i in range(len(words) - length + 1):
            phrase = ' '.join(words[i:i + length])
            phrases.append(phrase)
    return phrases

def compute_tfidf(docs, phrases):
    """Compute TF-IDF scores for phrases across documents."""
    doc_phrase_count = defaultdict(lambda: defaultdict(int))
    phrase_doc_count = Counter()
    
    for doc_id, doc_phrases in docs.items():
        phrase_count = Counter(doc_phrases)
        for phrase, count in phrase_count.items():
            doc_phrase_count[doc_id][phrase] = count
            phrase_doc_count[phrase] += 1
    
    tfidf_scores = {}
    N = len(docs)
    for phrase in phrases:
        total_docs_with_phrase = phrase_doc_count[phrase]
        if total_docs_with_phrase == 0:
            continue
        idf = max(1.0 / total_docs_with_phrase, 0.01)
        
        # Average TF across documents
        avg_tf = 0
        doc_count = 0
        for doc_id in docs:
            tf = doc_phrase_count[doc_id].get(phrase, 0)
            max_doc_len = len(docs[doc_id])
            if max_doc_len > 0:
                avg_tf += tf / max_doc_len
                doc_count += 1
        if doc_count > 0:
            avg_tf /= doc_count
            tfidf_scores[phrase] = avg_tf * idf
    
    return tfidf_scores

def find_example_sentences(docs, phrase):
    """Find example sentences containing the phrase."""
    examples = []
    for doc_id, doc_data in docs.items():
        for sent_id, sentence in doc_data['sentences']:
            if phrase in sentence:
                examples.append({
                    'sentence': sentence[:100] + '...' if len(sentence) > 100 else sentence,
                    'file': doc_id,
                    'sent_id': sent_id
                })
                if len(examples) >= 3:
                    return examples
    return examples

def load_cache():
    """Load previous analysis from cache."""
    try:
        if os.path.exists('gapfinder_cache.json'):
            with open('gapfinder_cache.json', 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_cache(data):
    """Save analysis to cache."""
    try:
        with open('gapfinder_cache.json', 'w') as f:
            json.dump(data, f, indent=2)
    except:
        pass

def print_table(gaps, print_friendly):
    """Print results in table format."""
    if print_friendly:
        print("\n" + "="*80)
        print("LITERATURE GAPS (Lowest Coverage First)")
        print("="*80)
        print(f"{'Rank':<4} {'Topic':<30} {'Coverage':<10} {'Files':<6} {'Examples'}")
        print("-"*80)
        
        for i, (topic, data) in enumerate(gaps[:10], 1):
            score = f"{data['score']:.4f}"
            files = f"{len(data['files'])}/{len(data['docs'])}"
            examples = data['examples'][0]['sentence'][:50] + "..." if data['examples'] else ""
            print(f"{i:<4} {topic:<30} {score:<10} {files:<6} {examples}")
        
        print("\n" + "="*80)
        print("Coverage Score: Lower = Bigger Gap (TF-IDF based)")
        print("="*80)
    else:
        print(json.dumps(gaps, indent=2))

def main():
    parser = argparse.ArgumentParser(
        description='Literature Gap Finder: Identifies underrepresented topics in research papers/notes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python gapfinder.py paper1.txt paper2.txt notes.txt
  python gapfinder.py *.txt --min-words 4 --output gaps.json
  python gapfinder.py files/*.txt --print-friendly
        """
    )
    parser.add_argument('files', nargs='+', help='Input .txt files to analyze')
    parser.add_argument('--min-words', type=int, default=3, help='Minimum words per topic phrase (default: 3)')
    parser.add_argument('--output', help='Save results as JSON (default: stdout)')
    parser.add_argument('--print-friendly', action='store_true', help='Format output for terminal printing')
    
    args = parser.parse_args()
    
    # Validate files
    valid_files = []
    for file_path in args.files:
        path = Path(file_path)
        if not path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            continue
        if not path.suffix.lower() == '.txt':
            print(f"Warning: Skipping non-txt file: {file_path}", file=sys.stderr)
            continue
        valid_files.append(str(path.absolute()))
    
    if not valid_files:
        print("Error: No valid .txt files provided", file=sys.stderr)
        sys.exit(1)
    
    print(f"Analyzing {len(valid_files)} files...")
    
    # Load cache
    cache = load_cache()
    cache_key = '_'.join(sorted(valid_files))
    
    if cache_key in cache:
        print("Using cached analysis...")
        results = cache[cache_key]
    else:
        # Process documents
        docs = {}
        all_phrases = set()
        
        for i, file_path in enumerate(valid_files):
            print(f"  Reading {Path(file_path).name}...")
            sentences = read_sentences(file_path)
            if not sentences:
                print(f"  Warning: Empty file {file_path}", file=sys.stderr)
                continue
            
            doc_phrases = []
            doc_sentences = []
            for sent_id, sentence in enumerate(sentences):
                phrases = extract_phrases(sentence, args.min_words)
                doc_phrases.extend(phrases)
                doc_sentences.append((sent_id, sentence))
            
            docs[file_path] = {
                'phrases': doc_phrases,
                'sentences': doc_sentences
            }
            all_phrases.update(doc_phrases)
        
        if not docs:
            print("Error: No valid content found in files", file=sys.stderr)
            sys.exit(1)
        
        # Compute TF-IDF
        print("Computing TF-IDF scores...")
        tfidf_scores = compute_tfidf(docs, all_phrases)
        
        # Find gaps (lowest coverage)
        gaps = []
        for phrase, score in sorted(tfidf_scores.items(), key=lambda x: x[1]):
            examples = find_example_sentences(docs, phrase)
            files_mentioned = [f for f in docs if any(phrase in s for _, s in docs[f]['sentences'][:10])]
            
            gaps.append({
                'topic': phrase,
                'score': score,
                'examples': examples,
                'files': files_mentioned,
                'docs': list(docs.keys())
            })
        
        # Take top gaps
        results = sorted(gaps[:50], key=lambda x: x['score'])
        
        # Cache results
        cache[cache_key] = results
        save_cache(cache)
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print_table(results, args.print_friendly)

if __name__ == '__main__':
    main()