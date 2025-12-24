# Auto-generated via Perplexity on 2025-12-24T01:26:32.796663Z
#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
import webbrowser
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from urllib.parse import quote

DATA_FILE = 'literature_gaps.json'
DEMO_DATA = {
    "searches": [
        {
            "query": "Machine Learning Survey",
            "timestamp": "2025-12-24T01:00:00",
            "papers": [
                {
                    "title": "Deep Learning for Computer Vision",
                    "abstract": "survey of deep learning methods in computer vision including CNNs and transformers",
                    "url": "https://arxiv.org/abs/2301.00001"
                },
                {
                    "title": "Natural Language Processing Advances",
                    "abstract": "overview of NLP techniques including BERT transformers and language models",
                    "url": "https://arxiv.org/abs/2301.00002"
                },
                {
                    "title": "Reinforcement Learning Applications",
                    "abstract": "applications of RL in robotics and game playing with policy gradients",
                    "url": "https://arxiv.org/abs/2301.00003"
                },
                {
                    "title": "Graph Neural Networks",
                    "abstract": "survey of GNN architectures for node classification and link prediction",
                    "url": "https://arxiv.org/abs/2301.00004"
                },
                {
                    "title": "Federated Learning Systems",
                    "abstract": "distributed machine learning with privacy preservation across devices",
                    "url": "https://arxiv.org/abs/2301.00005"
                }
            ],
            "gaps": [
                {"gap": "Limited research on ML interpretability in medical diagnosis", "score": 0.85, "context": "healthcare"},
                {"gap": "Few studies on energy efficiency of large language models", "score": 0.78, "context": "sustainability"},
                {"gap": "Underexplored: fairness in federated learning systems", "score": 0.72, "context": "ethics"}
            ]
        }
    ]
}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"searches": []}
    return {"searches": []}

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Error saving data: {e}")

def extract_keywords(text, limit=15):
    text = text.lower()
    words = re.findall(r'\b[a-z]{4,}\b', text)
    stop_words = {'that', 'this', 'with', 'from', 'have', 'been', 'were', 'their', 'which', 'using', 'based', 'paper', 'study', 'research', 'method', 'approach', 'model', 'system', 'data', 'analysis'}
    words = [w for w in words if w not in stop_words]
    counter = Counter(words)
    return [word for word, _ in counter.most_common(limit)]

def fetch_arxiv(query, max_results=5):
    try:
        search_url = f"http://export.arxiv.org/api/query?search_query=all:{quote(query)}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"
        with urllib.request.urlopen(search_url, timeout=5) as response:
            content = response.read().decode('utf-8')
        
        papers = []
        entries = re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL)
        for entry in entries[:max_results]:
            title_match = re.search(r'<title>(.*?)</title>', entry)
            summary_match = re.search(r'<summary>(.*?)</summary>', entry)
            id_match = re.search(r'<id>(.*?)</id>', entry)
            
            if title_match and summary_match and id_match:
                title = title_match.group(1).strip()
                abstract = summary_match.group(1).strip()
                arxiv_id = id_match.group(1).strip().split('/abs/')[-1]
                url = f"https://arxiv.org/abs/{arxiv_id}"
                papers.append({"title": title, "abstract": abstract, "url": url})
        
        return papers
    except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
        print(f"Warning: Could not fetch from arXiv: {e}")
        return []

def fetch_crossref(query, max_results=3):
    try:
        search_url = f"https://api.crossref.org/works?query={quote(query)}&rows={max_results}"
        with urllib.request.urlopen(search_url, timeout=5) as response:
            content = response.read().decode('utf-8')
        
        papers = []
        items = re.findall(r'"title":\s*\[(.*?)\]', content)
        abstracts = re.findall(r'"abstract":\s*"(.*?)"', content)
        dois = re.findall(r'"DOI":\s*"(.*?)"', content)
        
        for i, title in enumerate(items[:max_results]):
            title = title.strip('"').replace('\\"', '"')
            abstract = abstracts[i] if i < len(abstracts) else "No abstract available"
            doi = dois[i] if i < len(dois) else ""
            url = f"https://doi.org/{doi}" if doi else ""
            papers.append({"title": title, "abstract": abstract, "url": url})
        
        return papers
    except Exception as e:
        print(f"Warning: Could not fetch from CrossRef: {e}")
        return []

def compute_gap_scores(all_keywords, paper_keywords_list):
    gap_scores = {}
    
    for i, keywords in enumerate(paper_keywords_list):
        for keyword in keywords:
            if keyword not in gap_scores:
                gap_scores[keyword] = 0
            gap_scores[keyword] += 1
    
    total_papers = len(paper_keywords_list)
    gaps = []
    
    for keyword, count in gap_scores.items():
        frequency = count / total_papers
        gap_score = 1 - frequency
        
        if gap_score > 0.4:
            gaps.append({"keyword": keyword, "score": round(gap_score, 2), "frequency": count})
    
    gaps.sort(key=lambda x: x['score'], reverse=True)
    return gaps[:8]

def identify_gaps(papers):
    if not papers:
        return []
    
    all_keywords = []
    paper_keywords_list = []
    
    for paper in papers:
        abstract = paper.get('abstract', '')
        title = paper.get('title', '')
        combined_text = f"{title} {abstract}"
        keywords = extract_keywords(combined_text)
        paper_keywords_list.append(keywords)
        all_keywords.extend(keywords)
    
    gaps = compute_gap_scores(all_keywords, paper_keywords_list)
    
    contexts = ["healthcare", "sustainability", "ethics", "education", "industry", "developing regions"]
    formatted_gaps = []
    
    for i, gap in enumerate(gaps):
        context = contexts[i % len(contexts)]
        gap_text = f"Limited research on {gap['keyword']} in {context} context"
        formatted_gaps.append({
            "gap": gap_text,
            "score": gap['score'],
            "context": context
        })
    
    return formatted_gaps

def display_papers(papers):
    print("\n" + "="*70)
    print("RELATED PAPERS")
    print("="*70)
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper['title']}")
        print(f"   URL: {paper['url']}")
        abstract = paper['abstract'][:150] + "..." if len(paper['abstract']) > 150 else paper['abstract']
        print(f"   Abstract: {abstract}")

def display_gaps(gaps):
    print("\n" + "="*70)
    print("IDENTIFIED RESEARCH GAPS")
    print("="*70)
    for i, gap in enumerate(gaps, 1):
        print(f"\n{i}. {gap['gap']}")
        print(f"   Gap Score: {gap['score']:.2f} | Context: {gap['context']}")

def open_papers_in_browser(papers):
    if not papers:
        print("No papers to open.")
        return
    
    print("\nOpening top papers in browser...")
    for paper in papers[:3]:
        if paper['url']:
            try:
                webbrowser.open(paper['url'])
            except Exception as e:
                print(f"Could not open {paper['url']}: {e}")

def interactive_mode():
    data = load_data()
    
    while True:
        print("\n" + "="*70)
        print("LITERATURE GAP FINDER - Interactive Mode")
        print("="*70)
        print("Commands:")
        print("  search <query>  - Search for papers by title")
        print("  doi <doi>       - Search by DOI")
        print("  history         - Show search history")
        print("  open            - Open top papers in browser")
        print("  q               - Quit")
        print("-"*70)
        
        user_input = input("\nEnter command: ").strip()
        
        if user_input.lower() == 'q':
            print("Goodbye!")
            break
        elif user_input.lower().startswith('search '):
            query = user_input[7:].strip()
            if query:
                perform_search(query, data)
        elif user_input.lower().startswith('doi '):
            doi = user_input[4:].strip()
            if doi:
                perform_search(doi, data)
        elif user_input.lower() == 'history':
            show_history(data)
        elif user_input.lower() == 'open':
            if data['searches']:
                last_search = data['searches'][-1]
                open_papers_in_browser(last_search.get('papers', []))
            else:
                print("No searches in history.")
        else:
            print("Unknown command. Try again.")

def perform_search(query, data):
    print(f"\nSearching for: {query}")
    print("Fetching papers...")
    
    arxiv_papers = fetch_arxiv(query, max_results=5)
    crossref_papers = fetch_crossref(query, max_results=3)
    
    papers = arxiv_papers + crossref_papers
    
    if not papers:
        print("No papers found. Check your query or network connection.")
        return
    
    gaps = identify_gaps(papers)
    
    search_entry = {
        "query": query,
        "timestamp": datetime.utcnow().isoformat(),
        "papers": papers,
        "gaps": gaps
    }
    
    data['searches'].append(search_entry)
    save_data(data)
    
    display_papers(papers)
    display_gaps(gaps)
    
    print("\nPress 'o' to open top papers in browser, or any other key to continue...")
    try:
        choice = input().strip().lower()
        if choice == 'o':
            open_papers_in_browser(papers)
    except EOFError:
        pass

def show_history(data):
    if not data['searches']:
        print("No search history.")
        return
    
    print("\n" + "="*70)
    print("SEARCH HISTORY")
    print("="*70)
    for i, search in enumerate(data['searches'][-10:], 1):
        print(f"\n{i}. Query: {search['query']}")
        print(f"   Time: {search['timestamp']}")
        print(f"   Papers found: {len(search.get('papers', []))}")
        print(f"   Gaps identified: {len(search.get('gaps', []))}")

def main():
    parser = argparse.ArgumentParser(
        description='Literature Gap Finder - Identify research gaps from paper abstracts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py --title "Machine Learning Survey"
  python app.py --doi "10.1234/abc"
  python app.py --demo
  python app.py --interactive
        """
    )
    
    parser.add_argument('--title', type=str, help='Search by paper title')
    parser.add_argument('--doi', type=str, help='Search by DOI')
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--history', action='store_true', help='Show search history')
    
    args = parser.parse_args()
    
    if args.demo:
        print("Running DEMO mode with sample data...\n")
        demo_search = DEMO_DATA['searches'][0]
        display_papers(demo_search['papers'])
        display_gaps(demo_search['gaps'])
        print("\n(Demo mode - no network requests made)")
    elif args.history:
        data = load_data()
        show_history(data)
    elif args.interactive:
        interactive_mode()
    elif args.title or args.doi:
        query = args.title or args.doi
        data = load_data()
        perform_search(query, data)
    else:
        interactive_mode()

if __name__ == '__main__':
    main()