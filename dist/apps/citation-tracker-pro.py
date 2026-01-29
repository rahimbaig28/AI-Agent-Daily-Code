# Auto-generated via Perplexity on 2026-01-29T20:47:08.793100Z
#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import shutil
import webbrowser

DATA_FILE = Path.home() / ".citations.json"
SAMPLES = [
    {
        "id": "a1b2c3d4e5f6",
        "title": "Sample Paper 1",
        "authors": "Author1, Author2",
        "year": 2023,
        "url": "https://doi.org/10.1234/sample1",
        "notes": "",
        "tags": "",
        "added_date": "2023-01-01T00:00:00"
    },
    {
        "id": "f6e5d4c3b2a1",
        "title": "Sample Paper 2",
        "authors": "Author3",
        "year": 2022,
        "url": "https://doi.org/10.1234/sample2",
        "notes": "Important notes",
        "tags": "ml,ai",
        "added_date": "2023-01-02T00:00:00"
    },
    {
        "id": "123456789abc",
        "title": "Sample Paper 3",
        "authors": "Author4, Author5",
        "year": 2021,
        "url": "https://doi.org/10.1234/sample3",
        "notes": "",
        "tags": "stats",
        "added_date": "2023-01-03T00:00:00"
    }
]

BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_colored(text, color=RESET):
    print(f"{color}{text}{RESET}")

def load_data():
    if DATA_FILE.exists():
        with DATA_FILE.open('r') as f:
            return json.load(f)
    return []

def save_data(data):
    temp_file = DATA_FILE.with_suffix('.tmp')
    with temp_file.open('w') as f:
        json.dump(data, f, indent=2)
    temp_file.rename(DATA_FILE)

def generate_id(title, year):
    h = hashlib.md5(f"{title.lower()}-{year}".encode()).hexdigest()[:12]
    return h

def validate_year(year):
    year = int(year)
    if not 1900 <= year <= 2030:
        raise ValueError("Year must be between 1900 and 2030")
    return year

def validate_url(url):
    parsed = urlparse(url)
    if not all([parsed.scheme, parsed.netloc]):
        raise ValueError("Invalid URL")
    return url

def add_citation(data, title, authors, year, url, notes="", tags=""):
    year = validate_year(year)
    url = validate_url(url)
    citation = {
        "id": generate_id(title, year),
        "title": title,
        "authors": authors,
        "year": year,
        "url": url,
        "notes": notes,
        "tags": tags,
        "added_date": datetime.now().isoformat()
    }
    
    # Check for duplicate
    for c in data:
        if c["title"].lower() == title.lower() and c["year"] == year:
            print_colored("Citation already exists!", RED)
            return data
    
    data.append(citation)
    print_colored("Citation added successfully!", GREEN)
    return data

def list_citations(data, search="", year=None):
    filtered = []
    for c in data:
        if search and search.lower() not in c["title"].lower() and search.lower() not in c["authors"].lower():
            continue
        if year and c["year"] != year:
            continue
        filtered.append(c)
    
    # Sort by year desc, then authors
    filtered.sort(key=lambda x: (-x["year"], x["authors"]))
    
    if not filtered:
        print_colored("No citations found.", YELLOW)
        return
    
    print_colored(f"\n{BOLD}Found {len(filtered)} citation(s):{RESET}")
    for i, c in enumerate(filtered, 1):
        tags = f"[{c['tags']}]" if c['tags'] else ""
        print_colored(f"{BLUE}{i:2d}.{RESET} {c['authors']} ({c['year']}) - {c['title']} {tags}")

def export_csv(data, filename):
    if not data:
        print_colored("No citations to export.", YELLOW)
        return
    
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["title", "authors", "year", "url", "notes", "tags", "added_date"])
        writer.writeheader()
        writer.writerows(data)
    print_colored(f"Exported {len(data)} citations to {filename}", GREEN)

def import_json(data, filename):
    try:
        with open(filename, 'r') as f:
            new_data = json.load(f)
        
        imported = 0
        for item in new_data:
            if isinstance(item, dict):
                # Use title+year hash for dedup
                title_hash = generate_id(item.get("title", ""), item.get("year", 0))
                if not any(c["id"] == title_hash for c in data):
                    data.append(item)
                    imported += 1
        
        print_colored(f"Imported {imported} new citations from {filename}", GREEN)
        return data
    except Exception as e:
        print_colored(f"Import error: {e}", RED)
        return data

def open_url(data, index):
    if not 1 <= index <= len(data):
        print_colored("Invalid citation index.", RED)
        return
    url = data[index-1]["url"]
    webbrowser.open(url)
    print_colored(f"Opened: {url}", GREEN)

def interactive_mode():
    data = load_data()
    print_colored("Citation Tracker Pro - Interactive Mode", BLUE)
    print("Commands: a=add, l=list, s=search, e=export, o=open #, q=quit")
    
    while True:
        try:
            cmd = input("\n> ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 'a':
                title = input("Title: ").strip()
                authors = input("Authors (comma sep): ").strip()
                year = input("Year: ").strip()
                url = input("URL: ").strip()
                notes = input("Notes (optional): ").strip()
                tags = input("Tags (optional): ").strip()
                
                if title and authors and year and url:
                    data = add_citation(data, title, authors, year, url, notes, tags)
                    save_data(data)
            
            elif cmd == 'l':
                list_citations(data)
            
            elif cmd == 's':
                keyword = input("Search keyword: ").strip()
                list_citations(data, search=keyword)
            
            elif cmd.startswith('o '):
                try:
                    idx = int(cmd.split()[1])
                    open_url(data, idx)
                except:
                    print_colored("Usage: o <number>", RED)
            
            elif cmd.startswith('e '):
                filename = cmd.split(maxsplit=1)[1] if len(cmd.split()) > 1 else "citations.csv"
                export_csv(data, filename)
            
            else:
                print_colored("Unknown command. Type 'h' for help.", YELLOW)
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print_colored(f"Error: {e}", RED)

def main():
    parser = argparse.ArgumentParser(description="Citation Tracker Pro - Academic citation manager")
    parser.add_argument('--test', action='store_true', help="Show sample data without saving")
    
    subparsers = parser.add_subparsers(dest='command', required=not sys.stdin.isatty())
    
    # Add command
    add_parser = subparsers.add_parser('add')
    add_parser.add_argument('--title', required=True)
    add_parser.add_argument('--authors', required=True)
    add_parser.add_argument('--year', required=True, type=int)
    add_parser.add_argument('--url', required=True)
    add_parser.add_argument('--notes', default='')
    add_parser.add_argument('--tags', default='')
    
    # List command
    list_parser = subparsers.add_parser('list')
    list_parser.add_argument('--search', default='')
    list_parser.add_argument('--year', type=int)
    
    # Export command
    export_parser = subparsers.add_parser('export')
    export_parser.add_argument('filename', nargs='?', default='citations.csv')
    
    # Import command
    import_parser = subparsers.add_parser('import')
    import_parser.add_argument('filename')
    
    # Open command
    open_parser = subparsers.add_parser('open')
    open_parser.add_argument('index', type=int)
    
    # Interactive
    subparsers.add_parser('interactive')
    
    args = parser.parse_args()
    
    if args.test:
        print_colored("Sample data:", BLUE)
        list_citations(SAMPLES)
        return
    
    data = load_data()
    
    try:
        if args.command == 'add':
            data = add_citation(data, args.title, args.authors, args.year, args.url, args.notes, args.tags)
            save_data(data)
        
        elif args.command == 'list':
            list_citations(data, args.search, args.year)
        
        elif args.command == 'export':
            export_csv(data, args.filename)
        
        elif args.command == 'import':
            data = import_json(data, args.filename)
            save_data(data)
        
        elif args.command == 'open':
            open_url(data, args.index)
        
        elif args.command == 'interactive':
            interactive_mode()
        
        else:
            parser.print_help()
    
    except ValueError as e:
        print_colored(f"Validation error: {e}", RED)
    except Exception as e:
        print_colored(f"Error: {e}", RED)

if __name__ == "__main__":
    main()