# Auto-generated via Perplexity on 2026-01-13T01:26:34.097079Z
#!/usr/bin/env python3
import json
import os
import sys
import readline
from datetime import datetime
from pathlib import Path

DATA_FILE = Path.home() / ".local" / "share" / "litreview.json"
BACKUP_FILE = DATA_FILE.with_stem("litreview_backup")
EXPORT_FILE = DATA_FILE.parent / "litreview_export.json"
UNDO_STACK = []
REDO_STACK = []
MAX_UNDO = 10
NEXT_ID = 0

def ensure_data_dir():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_data():
    global NEXT_ID
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            if data:
                NEXT_ID = max(p['id'] for p in data) + 1
            return data
    return []

def save_data(data):
    ensure_data_dir()
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r') as f:
            backup = f.read()
        with open(BACKUP_FILE, 'w') as f:
            f.write(backup)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def push_undo(data):
    global UNDO_STACK, REDO_STACK
    UNDO_STACK.append(json.dumps(data))
    if len(UNDO_STACK) > MAX_UNDO:
        UNDO_STACK.pop(0)
    REDO_STACK.clear()

def undo(data):
    global UNDO_STACK, REDO_STACK
    if UNDO_STACK:
        REDO_STACK.append(json.dumps(data))
        return json.loads(UNDO_STACK.pop())
    print("Nothing to undo.")
    return data

def redo(data):
    global UNDO_STACK, REDO_STACK
    if REDO_STACK:
        UNDO_STACK.append(json.dumps(data))
        return json.loads(REDO_STACK.pop())
    print("Nothing to redo.")
    return data

def add_paper(data):
    global NEXT_ID
    print("\n--- Add Paper ---")
    title = input("Title: ").strip()
    if not title:
        print("Title cannot be empty.")
        return data
    authors = input("Authors (comma-separated): ").strip()
    year_str = input("Year (1900-2030): ").strip()
    try:
        year = int(year_str)
        if not (1900 <= year <= 2030):
            raise ValueError
    except ValueError:
        print("Invalid year. Using current year.")
        year = datetime.now().year
    notes = input("Notes: ").strip()
    print("Status: 1=todo, 2=reading, 3=done")
    status_map = {'1': 'todo', '2': 'reading', '3': 'done'}
    status = status_map.get(input("Status (1-3): ").strip(), 'todo')
    
    push_undo(data)
    paper = {
        'id': NEXT_ID,
        'title': title,
        'authors': authors,
        'year': year,
        'notes': notes,
        'status': status,
        'added': datetime.now().strftime('%Y-%m-%d')
    }
    NEXT_ID += 1
    data.append(paper)
    save_data(data)
    print(f"Added: {title}")
    return data

def list_papers(data):
    print("\n--- Papers ---")
    status_filter = input("Filter by status (todo/reading/done) or press Enter for all: ").strip().lower()
    filtered = data
    if status_filter in ['todo', 'reading', 'done']:
        filtered = [p for p in data if p['status'] == status_filter]
    sorted_data = sorted(filtered, key=lambda x: x['added'], reverse=True)
    if not sorted_data:
        print("No papers found.")
        return
    for i, p in enumerate(sorted_data):
        status_icon = {'todo': '○', 'reading': '◐', 'done': '●'}.get(p['status'], '?')
        print(f"{i}: [{status_icon}] {p['title']} ({p['year']}) - {p['authors'][:30]}")

def edit_paper(data):
    print("\n--- Edit Paper ---")
    list_papers(data)
    try:
        idx = int(input("Select index: ").strip())
        if 0 <= idx < len(data):
            p = data[idx]
            push_undo(data)
            print(f"Editing: {p['title']}")
            p['title'] = input(f"Title [{p['title']}]: ").strip() or p['title']
            p['authors'] = input(f"Authors [{p['authors']}]: ").strip() or p['authors']
            year_str = input(f"Year [{p['year']}]: ").strip()
            if year_str:
                try:
                    p['year'] = int(year_str)
                except ValueError:
                    print("Invalid year, keeping original.")
            p['notes'] = input(f"Notes [{p['notes']}]: ").strip() or p['notes']
            print("Status: 1=todo, 2=reading, 3=done")
            status_map = {'1': 'todo', '2': 'reading', '3': 'done'}
            new_status = input(f"Status [{p['status']}]: ").strip()
            if new_status in status_map:
                p['status'] = status_map[new_status]
            save_data(data)
            print("Updated.")
        else:
            print("Invalid index.")
    except ValueError:
        print("Invalid input.")
    return data

def search_papers(data):
    print("\n--- Search ---")
    query = input("Search title or author: ").strip().lower()
    results = [p for p in data if query in p['title'].lower() or query in p['authors'].lower()]
    if results:
        for i, p in enumerate(results):
            status_icon = {'todo': '○', 'reading': '◐', 'done': '●'}.get(p['status'], '?')
            print(f"{i}: [{status_icon}] {p['title']} ({p['year']}) - {p['authors'][:30]}")
    else:
        print("No matches found.")

def stats(data):
    print("\n--- Stats ---")
    if not data:
        print("No papers.")
        return
    todo_count = sum(1 for p in data if p['status'] == 'todo')
    reading_count = sum(1 for p in data if p['status'] == 'reading')
    done_count = sum(1 for p in data if p['status'] == 'done')
    avg_year = sum(p['year'] for p in data) / len(data)
    recent = sorted(data, key=lambda x: x['added'], reverse=True)[0]
    print(f"Total: {len(data)} | Todo: {todo_count} | Reading: {reading_count} | Done: {done_count}")
    print(f"Average year: {avg_year:.0f}")
    print(f"Most recent: {recent['title']} ({recent['added']})")

def export_data(data):
    with open(EXPORT_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Exported to {EXPORT_FILE}")

def import_data(data):
    if not EXPORT_FILE.exists():
        print(f"Export file not found: {EXPORT_FILE}")
        return data
    with open(EXPORT_FILE, 'r') as f:
        imported = json.load(f)
    push_undo(data)
    data.extend(imported)
    save_data(data)
    print(f"Imported {len(imported)} papers.")
    return data

def show_help():
    print("\n--- Help ---")
    print("a: Add paper")
    print("l: List papers")
    print("e: Edit paper")
    print("s: Search papers")
    print("t: Stats")
    print("x: Export database")
    print("i: Import database")
    print("u: Undo")
    print("r: Redo")
    print("n: Add paper (shortcut)")
    print("h: Help")
    print("q: Quit")

def main():
    ensure_data_dir()
    data = load_data()
    print("Literature Review Tracker")
    show_help()
    while True:
        cmd = input("\nCommand (h for help): ").strip().lower()
        if cmd == 'q':
            print("Goodbye.")
            sys.exit(0)
        elif cmd == 'a' or cmd == 'n':
            data = add_paper(data)
        elif cmd == 'l':
            list_papers(data)
        elif cmd == 'e':
            data = edit_paper(data)
        elif cmd == 's':
            search_papers(data)
        elif cmd == 't':
            stats(data)
        elif cmd == 'x':
            export_data(data)
        elif cmd == 'i':
            data = import_data(data)
        elif cmd == 'u':
            data = undo(data)
        elif cmd == 'r':
            data = redo(data)
        elif cmd == 'h':
            show_help()
        else:
            print("Unknown command.")

if __name__ == '__main__':
    main()