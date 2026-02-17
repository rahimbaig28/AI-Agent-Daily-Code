# Auto-generated via Perplexity on 2026-02-17T19:14:04.007840Z
#!/usr/bin/env python3
import json
import csv
import argparse
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).parent
DATA_FILE = SCRIPT_DIR / "papers.json"

def load_papers():
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_papers(papers):
    with open(DATA_FILE, 'w') as f:
        json.dump(papers, f, indent=2)

def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def add_paper(title, authors, pub_date, url, tags, notes):
    if not title or not authors or not url:
        print("Error: title, authors, and url are required")
        return
    if not validate_url(url):
        print("Error: invalid URL format")
        return
    if pub_date and not validate_date(pub_date):
        print("Error: publication date must be YYYY-MM-DD format")
        return
    
    papers = load_papers()
    paper = {
        "id": len(papers) + 1,
        "title": title,
        "authors": authors,
        "pub_date": pub_date or "",
        "url": url,
        "tags": tags.split(",") if tags else [],
        "notes": notes or "",
        "read": False,
        "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    papers.append(paper)
    save_papers(papers)
    print(f"Paper added: {title}")

def list_papers(sort_by="date_added", read_status=None):
    papers = load_papers()
    
    if read_status is not None:
        papers = [p for p in papers if p["read"] == read_status]
    
    if sort_by == "pub_date":
        papers.sort(key=lambda x: x["pub_date"] or "")
    elif sort_by == "title":
        papers.sort(key=lambda x: x["title"].lower())
    else:
        papers.sort(key=lambda x: x["date_added"], reverse=True)
    
    if not papers:
        print("No papers found")
        return
    
    print(f"\n{'ID':<4} {'Title':<40} {'Authors':<25} {'Date':<12} {'Status':<8} {'Tags':<20}")
    print("-" * 115)
    for p in papers:
        status = "Read" if p["read"] else "Unread"
        tags = ", ".join(p["tags"][:2]) if p["tags"] else "-"
        title = p["title"][:37] + "..." if len(p["title"]) > 40 else p["title"]
        authors = p["authors"][:22] + "..." if len(p["authors"]) > 25 else p["authors"]
        print(f"{p['id']:<4} {title:<40} {authors:<25} {p['pub_date']:<12} {status:<8} {tags:<20}")

def search_papers(query):
    papers = load_papers()
    query_lower = query.lower()
    results = [p for p in papers if 
               query_lower in p["title"].lower() or 
               query_lower in p["authors"].lower() or 
               any(query_lower in tag.lower() for tag in p["tags"])]
    
    if not results:
        print("No papers found matching query")
        return
    
    print(f"\nFound {len(results)} paper(s):")
    print(f"\n{'ID':<4} {'Title':<40} {'Authors':<25} {'Date':<12} {'Status':<8} {'Tags':<20}")
    print("-" * 115)
    for p in results:
        status = "Read" if p["read"] else "Unread"
        tags = ", ".join(p["tags"][:2]) if p["tags"] else "-"
        title = p["title"][:37] + "..." if len(p["title"]) > 40 else p["title"]
        authors = p["authors"][:22] + "..." if len(p["authors"]) > 25 else p["authors"]
        print(f"{p['id']:<4} {title:<40} {authors:<25} {p['pub_date']:<12} {status:<8} {tags:<20}")

def add_tags(paper_id, new_tags):
    papers = load_papers()
    paper = next((p for p in papers if p["id"] == paper_id), None)
    if not paper:
        print(f"Paper {paper_id} not found")
        return
    
    tags_list = [t.strip() for t in new_tags.split(",")]
    paper["tags"] = list(set(paper["tags"] + tags_list))
    save_papers(papers)
    print(f"Tags added to paper {paper_id}")

def remove_tags(paper_id, tags_to_remove):
    papers = load_papers()
    paper = next((p for p in papers if p["id"] == paper_id), None)
    if not paper:
        print(f"Paper {paper_id} not found")
        return
    
    remove_list = [t.strip() for t in tags_to_remove.split(",")]
    paper["tags"] = [t for t in paper["tags"] if t not in remove_list]
    save_papers(papers)
    print(f"Tags removed from paper {paper_id}")

def list_tags():
    papers = load_papers()
    all_tags = {}
    for p in papers:
        for tag in p["tags"]:
            all_tags[tag] = all_tags.get(tag, 0) + 1
    
    if not all_tags:
        print("No tags found")
        return
    
    print("\nTags (count):")
    for tag in sorted(all_tags.keys()):
        print(f"  {tag}: {all_tags[tag]}")

def mark_read(paper_id, read_status):
    papers = load_papers()
    paper = next((p for p in papers if p["id"] == paper_id), None)
    if not paper:
        print(f"Paper {paper_id} not found")
        return
    
    paper["read"] = read_status
    save_papers(papers)
    status = "marked as read" if read_status else "marked as unread"
    print(f"Paper {paper_id} {status}")

def export_csv(filename="papers_export.csv"):
    papers = load_papers()
    if not papers:
        print("No papers to export")
        return
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Title", "Authors", "Publication Date", "URL", "Tags", "Notes", "Read", "Date Added"])
        for p in papers:
            writer.writerow([
                p["id"],
                p["title"],
                p["authors"],
                p["pub_date"],
                p["url"],
                "; ".join(p["tags"]),
                p["notes"],
                "Yes" if p["read"] else "No",
                p["date_added"]
            ])
    print(f"Papers exported to {filename}")

def import_json(filename):
    try:
        with open(filename, 'r') as f:
            imported = json.load(f)
        
        papers = load_papers()
        max_id = max([p["id"] for p in papers], default=0)
        
        for p in imported:
            p["id"] = max_id + 1
            max_id += 1
            papers.append(p)
        
        save_papers(papers)
        print(f"Imported {len(imported)} paper(s)")
    except FileNotFoundError:
        print(f"File {filename} not found")
    except json.JSONDecodeError:
        print("Invalid JSON format")

def delete_by_tag(tag):
    papers = load_papers()
    original_count = len(papers)
    papers = [p for p in papers if tag not in p["tags"]]
    deleted = original_count - len(papers)
    save_papers(papers)
    print(f"Deleted {deleted} paper(s) with tag '{tag}'")

def delete_by_date_range(start_date, end_date):
    if not validate_date(start_date) or not validate_date(end_date):
        print("Error: dates must be YYYY-MM-DD format")
        return
    
    papers = load_papers()
    original_count = len(papers)
    papers = [p for p in papers if not (start_date <= p["pub_date"] <= end_date)]
    deleted = original_count - len(papers)
    save_papers(papers)
    print(f"Deleted {deleted} paper(s) in date range {start_date} to {end_date}")

def statistics():
    papers = load_papers()
    if not papers:
        print("No papers in database")
        return
    
    read_count = sum(1 for p in papers if p["read"])
    all_tags = {}
    all_authors = {}
    
    for p in papers:
        for tag in p["tags"]:
            all_tags[tag] = all_tags.get(tag, 0) + 1
        for author in p["authors"].split(","):
            author = author.strip()
            all_authors[author] = all_authors.get(author, 0) + 1
    
    print(f"\nStatistics:")
    print(f"  Total papers: {len(papers)}")
    print(f"  Read: {read_count}")
    print(f"  Unread: {len(papers) - read_count}")
    print(f"  Unique tags: {len(all_tags)}")
    
    if all_tags:
        top_tag = max(all_tags.items(), key=lambda x: x[1])
        print(f"  Most used tag: {top_tag[0]} ({top_tag[1]})")
    
    if all_authors:
        top_author = max(all_authors.items(), key=lambda x: x[1])
        print(f"  Most prolific author: {top_author[0]} ({top_author[1]})")

def show_help():
    help_text = """
Research Paper Tracker - Command Line Interface

USAGE: python script.py <command> [options]

COMMANDS:
  add              Add a new paper
    --title TEXT   Paper title (required)
    --authors TEXT Authors (required)
    --url URL      Paper URL (required)
    --pub-date YYYY-MM-DD  Publication date (optional)
    --tags TEXT    Comma-separated tags (optional)
    --notes TEXT   Notes (optional)
    Example: python script.py add --title "AI Paper" --authors "John Doe" --url "https://example.com/paper.pdf"

  list             List all papers
    --sort FIELD   Sort by: date_added (default), pub_date, title
    --read         Show only read papers
    --unread       Show only unread papers
    Example: python script.py list --sort title --unread

  search           Search papers by title, authors, or tags
    --query TEXT   Search query (required)
    Example: python script.py search --query "machine learning"

  tag              Manage tags
    --add ID,TAGS  Add tags to paper (ID and comma-separated tags)
    --remove ID,TAGS  Remove tags from paper
    --list         List all unique tags with counts
    Example: python script.py tag --add 1,ai,deep-learning

  mark-read        Mark paper as read/unread
    --id ID        Paper ID (required)
    --status BOOL  True for read, False for unread (required)
    Example: python script.py mark-read --id 1 --status True

  export           Export papers to CSV
    --file NAME    Output filename (default: papers_export.csv)
    Example: python script.py export --file my_papers.csv

  import           Import papers from JSON file
    --file NAME    Input filename (required)
    Example: python script.py import --file backup.json

  delete           Delete papers
    --tag TAG      Delete all papers with this tag
    --date-range START END  Delete papers in date range (YYYY-MM-DD)
    Example: python script.py delete --tag old-research

  stats            Show database statistics
    Example: python script.py stats

  help             Show this help message
"""
    print(help_text)

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('command', nargs='?', default='help')
    parser.add_argument('--title', type=str)
    parser.add_argument('--authors', type=str)
    parser.add_argument('--url', type=str)
    parser.add_argument('--pub-date', type=str)
    parser.add_argument('--tags', type=str)
    parser.add_argument('--notes', type=str)
    parser.add_argument('--query', type=str)
    parser.add_argument('--sort', type=str, default='date_added')
    parser.add_argument('--read', action='store_true')
    parser.add_argument('--unread', action='store_true')
    parser.add_argument('--id', type=int)
    parser.add_argument('--status', type=lambda x: x.lower() == 'true')
    parser.add_argument('--add', type=str)
    parser.add_argument('--remove', type=str)
    parser.add_argument('--file', type=str)
    parser.add_argument('--tag', type=str)
    parser.add_argument('--date-range', nargs=2, type=str)
    
    args = parser.parse_args()
    
    if args.command == 'add':
        add_paper(args.title, args.authors, args.pub_date, args.url, args.tags, args.notes)
    elif args.command == 'list':
        read_status = True if args.read else (False if args.unread else None)
        list_papers(args.sort, read_status)
    elif args.command == 'search':
        if not args.query:
            print("Error: --query required")
            return
        search_papers(args.query)
    elif args.command == 'tag':
        if args.add:
            parts = args.add.split(',', 1)
            if len(parts) != 2:
                print("Error: use --add ID,TAGS format")
                return
            add_tags(int(parts[0]), parts[1])
        elif args.remove:
            parts = args.remove.split(',', 1)
            if len(parts) != 2:
                print("Error: use --remove ID,TAGS format")
                return
            remove_tags(int(parts[0]), parts[1])
        else:
            list_tags()
    elif args.command == 'mark-read':
        if args.id is None or args.status is None:
            print("Error: --id and --status required")
            return
        mark_read(args.id, args.status)
    elif args.command == 'export':
        export_csv(args.file or "papers_export.csv")
    elif args.command == 'import':
        if not args.file:
            print("Error: --file required")
            return
        import_json(args.file)
    elif args.command == 'delete':
        if args.tag:
            delete_by_tag(args.tag)
        elif args.date_range:
            delete_by_date_range(args.date_range[0], args.date_range[1])
        else:
            print("Error: --tag or --date-range required")
    elif args.command == 'stats':
        statistics()
    else:
        show_help()

if __name__ == "__main__":
    main()