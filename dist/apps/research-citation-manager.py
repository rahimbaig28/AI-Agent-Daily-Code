# Auto-generated via Perplexity on 2026-01-29T14:57:38.556210Z
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import deque

class ResearchCitationManager:
    def __init__(self, config_path=None):
        if config_path:
            self.library_path = Path(config_path)
        else:
            self.library_path = Path.home() / "research_library.json"
        
        self.papers = []
        self.history = deque(maxlen=20)
        self.redo_stack = deque(maxlen=20)
        self.load_library()
    
    def load_library(self):
        if self.library_path.exists():
            try:
                with open(self.library_path, 'r') as f:
                    self.papers = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.papers = []
        else:
            self.papers = []
    
    def save_library(self):
        with open(self.library_path, 'w') as f:
            json.dump(self.papers, f, indent=2)
    
    def add_paper(self):
        print("\n--- Add New Paper ---")
        title = input("Title: ").strip()
        if not title:
            print("Error: Title cannot be empty.")
            return
        
        authors = input("Authors (comma-separated): ").strip()
        url = input("URL: ").strip()
        year_str = input("Publication Year: ").strip()
        
        try:
            year = int(year_str) if year_str else None
        except ValueError:
            print("Error: Year must be a number.")
            return
        
        tags = input("Tags (comma-separated): ").strip()
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        
        paper = {
            "id": len(self.papers),
            "title": title,
            "authors": authors,
            "url": url,
            "year": year,
            "tags": tag_list,
            "notes": "",
            "added_date": datetime.now().isoformat()
        }
        
        self.papers.append(paper)
        self.history.append(("add", len(self.papers) - 1))
        self.redo_stack.clear()
        self.save_library()
        print(f"Paper added successfully (ID: {paper['id']})")
    
    def search_papers(self):
        query = input("\nSearch (title, authors, or tags): ").strip().lower()
        if not query:
            print("Error: Search query cannot be empty.")
            return
        
        results = []
        for paper in self.papers:
            if (query in paper['title'].lower() or
                query in paper['authors'].lower() or
                any(query in tag.lower() for tag in paper['tags'])):
                results.append(paper)
        
        if not results:
            print("No papers found.")
            return
        
        print(f"\nFound {len(results)} paper(s):")
        for i, paper in enumerate(results):
            print(f"\n[{i}] {paper['title']}")
            print(f"    Authors: {paper['authors']}")
            print(f"    Year: {paper['year']}")
            print(f"    Tags: {', '.join(paper['tags']) if paper['tags'] else 'None'}")
            print(f"    URL: {paper['url']}")
    
    def list_papers(self):
        if not self.papers:
            print("\nNo papers in library.")
            return
        
        sort_choice = input("\nSort by (y=year descending, a=alphabetical): ").strip().lower()
        
        if sort_choice == 'y':
            sorted_papers = sorted(self.papers, key=lambda p: (p['year'] or 0), reverse=True)
        else:
            sorted_papers = sorted(self.papers, key=lambda p: p['title'].lower())
        
        print(f"\n--- Library ({len(sorted_papers)} papers) ---")
        for paper in sorted_papers:
            year_str = f"({paper['year']})" if paper['year'] else "(No year)"
            tags_str = f" [{', '.join(paper['tags'])}]" if paper['tags'] else ""
            print(f"[{paper['id']}] {paper['title']} {year_str}{tags_str}")
    
    def manage_notes(self):
        paper_id = input("\nEnter paper ID to edit notes: ").strip()
        try:
            paper_id = int(paper_id)
        except ValueError:
            print("Error: Invalid ID.")
            return
        
        paper = next((p for p in self.papers if p['id'] == paper_id), None)
        if not paper:
            print("Error: Paper not found.")
            return
        
        print(f"\nCurrent notes for '{paper['title']}':")
        print(paper['notes'] if paper['notes'] else "(No notes)")
        print("\nEnter new notes (press Enter twice to finish):")
        
        lines = []
        while True:
            line = input()
            if line == "":
                if lines and lines[-1] == "":
                    lines.pop()
                    break
                lines.append(line)
            else:
                lines.append(line)
        
        old_notes = paper['notes']
        paper['notes'] = '\n'.join(lines)
        self.history.append(("edit_notes", paper_id, old_notes))
        self.redo_stack.clear()
        self.save_library()
        print("Notes updated.")
    
    def export_library(self):
        filename = input("\nExport filename (default: research_export.json): ").strip()
        if not filename:
            filename = "research_export.json"
        
        export_path = Path.home() / filename
        with open(export_path, 'w') as f:
            json.dump(self.papers, f, indent=2)
        
        self.history.clear()
        self.redo_stack.clear()
        print(f"Library exported to {export_path}")
    
    def import_library(self):
        filename = input("\nImport filename: ").strip()
        if not filename:
            print("Error: Filename cannot be empty.")
            return
        
        import_path = Path.home() / filename
        if not import_path.exists():
            print(f"Error: File not found at {import_path}")
            return
        
        try:
            with open(import_path, 'r') as f:
                imported = json.load(f)
            
            if not isinstance(imported, list):
                print("Error: Invalid format. Expected list of papers.")
                return
            
            self.papers.extend(imported)
            self.history.clear()
            self.redo_stack.clear()
            self.save_library()
            print(f"Imported {len(imported)} paper(s).")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error: {e}")
    
    def delete_paper(self):
        paper_id = input("\nEnter paper ID to delete: ").strip()
        try:
            paper_id = int(paper_id)
        except ValueError:
            print("Error: Invalid ID.")
            return
        
        paper = next((p for p in self.papers if p['id'] == paper_id), None)
        if not paper:
            print("Error: Paper not found.")
            return
        
        confirm = input(f"Delete '{paper['title']}'? (y/n): ").strip().lower()
        if confirm == 'y':
            self.papers = [p for p in self.papers if p['id'] != paper_id]
            self.history.append(("delete", paper_id, paper))
            self.redo_stack.clear()
            self.save_library()
            print("Paper deleted.")
        else:
            print("Cancelled.")
    
    def list_tags(self):
        tag_counts = {}
        for paper in self.papers:
            for tag in paper['tags']:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        if not tag_counts:
            print("\nNo tags in library.")
            return
        
        print("\n--- All Tags ---")
        for tag in sorted(tag_counts.keys()):
            print(f"{tag}: {tag_counts[tag]} paper(s)")
    
    def undo(self):
        if not self.history:
            print("Nothing to undo.")
            return
        
        action = self.history.pop()
        
        if action[0] == "add":
            self.redo_stack.append(("add", self.papers[action[1]]))
            self.papers.pop(action[1])
        elif action[0] == "delete":
            self.redo_stack.append(("delete", action[2]))
            self.papers.append(action[2])
        elif action[0] == "edit_notes":
            paper = next((p for p in self.papers if p['id'] == action[1]), None)
            if paper:
                self.redo_stack.append(("edit_notes", action[1], paper['notes']))
                paper['notes'] = action[2]
        
        self.save_library()
        print("Undo completed.")
    
    def redo(self):
        if not self.redo_stack:
            print("Nothing to redo.")
            return
        
        action = self.redo_stack.pop()
        
        if action[0] == "add":
            self.papers.append(action[1])
            self.history.append(("add", len(self.papers) - 1))
        elif action[0] == "delete":
            self.history.append(("delete", action[1]['id'], action[1]))
            self.papers = [p for p in self.papers if p['id'] != action[1]['id']]
        elif action[0] == "edit_notes":
            paper = next((p for p in self.papers if p['id'] == action[1]), None)
            if paper:
                self.history.append(("edit_notes", action[1], paper['notes']))
                paper['notes'] = action[2]
        
        self.save_library()
        print("Redo completed.")
    
    def show_help(self):
        print("\n--- Keyboard Shortcuts ---")
        print("a - Add paper")
        print("s - Search papers")
        print("l - List papers")
        print("n - Manage notes")
        print("t - List tags")
        print("e - Export library")
        print("i - Import library")
        print("d - Delete paper")
        print("u - Undo")
        print("r - Redo")
        print("h - Help")
        print("q - Quit")
    
    def run(self):
        print("Research Citation Manager")
        print(f"Library: {self.library_path}")
        
        while True:
            print("\n[a]dd [s]earch [l]ist [n]otes [t]ags [e]xport [i]mport [d]elete [u]ndo [r]edo [h]elp [q]uit")
            cmd = input("Command: ").strip().lower()
            
            if cmd == 'a':
                self.add_paper()
            elif cmd == 's':
                self.search_papers()
            elif cmd == 'l':
                self.list_papers()
            elif cmd == 'n':
                self.manage_notes()
            elif cmd == 't':
                self.list_tags()
            elif cmd == 'e':
                self.export_library()
            elif cmd == 'i':
                self.import_library()
            elif cmd == 'd':
                self.delete_paper()
            elif cmd == 'u':
                self.undo()
            elif cmd == 'r':
                self.redo()
            elif cmd == 'h':
                self.show_help()
            elif cmd == 'q':
                print("Goodbye.")
                sys.exit(0)
            else:
                print("Invalid command. Type 'h' for help.")

if __name__ == "__main__":
    config_path = None
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv[1:]):
            if arg == "--config-path" and i + 2 < len(sys.argv):
                config_path = sys.argv[i + 2]
    
    manager = ResearchCitationManager(config_path)
    try:
        manager.run()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)