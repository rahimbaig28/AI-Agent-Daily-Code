# Auto-generated via Perplexity on 2025-12-28T04:43:22.540277Z
#!/usr/bin/env python3
import json
import os
import sys
import datetime
import re
import shutil
import tempfile
import statistics
import base64
import subprocess
import pathlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class Entry:
    date: str
    mood: int
    mood_label: str
    sleep_hours: float
    water_cups: int
    energy: int
    note: str
    tags: List[str]
    wellness_score: float
    created_at: str
    updated_at: str

MOOD_LABELS = {1: "Terrible", 2: "Bad", 3: "Okay", 4: "Good", 5: "Great"}
DATA_FILE = "wellness_snapshot.json"
BACKUP_DIR = "backups"
MAX_BACKUPS = 5

class WellnessTracker:
    def __init__(self):
        self.data_file = pathlib.Path(DATA_FILE)
        self.backup_dir = pathlib.Path(BACKUP_DIR)
        self.backup_dir.mkdir(exist_ok=True)
        self.data = self.load_data()
        self.entries = [Entry(**e) for e in self.data.get("entries", [])]
    
    def load_data(self) -> Dict[str, Any]:
        if not self.data_file.exists():
            return self.init_data()
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except:
            print("Error loading data. Try 'backup restore'")
            return self.init_data()
    
    def init_data(self) -> Dict[str, Any]:
        now = datetime.datetime.now().isoformat()
        data = {
            "metadata": {"version": "1.0", "created_at": now, "last_modified": now},
            "config": {"page_size": 10, "autosave": True, "weekday_start": "monday"},
            "entries": [],
            "backups": []
        }
        self.save_data(data)
        return data
    
    def save_data(self, data: Optional[Dict[str, Any]] = None):
        if data is None:
            data = self.data
        data["metadata"]["last_modified"] = datetime.datetime.now().isoformat()
        self.data = data
        self.entries = [Entry(**e) for e in data.get("entries", [])]
        
        # Atomic write
        with tempfile.NamedTemporaryFile(mode='w', delete=False, dir='.', suffix='.json') as tmp:
            json.dump(data, tmp, indent=2)
            tmp_path = pathlib.Path(tmp.name)
        
        tmp_path.replace(self.data_file)
        self.rotate_backup()
    
    def rotate_backup(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"wellness_{timestamp}.json"
        shutil.copy2(self.data_file, backup_file)
        
        backups = sorted(self.backup_dir.glob("wellness_*.json"), reverse=True)
        while len(backups) > MAX_BACKUPS:
            backups[-1].unlink()
            backups.pop()
    
    def parse_date(self, date_str: str) -> str:
        if date_str == "today":
            return datetime.date.today().isoformat()
        if date_str == "yesterday":
            return (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        try:
            return datetime.date.fromisoformat(date_str).isoformat()
        except:
            raise ValueError("Invalid date format. Use YYYY-MM-DD, 'today', or 'yesterday'")
    
    def calculate_wellness_score(self, entry: Entry) -> float:
        sleep_norm = min(entry.sleep_hours / 8.0, 1.0)
        return (entry.mood * 0.5 + entry.energy * 0.3 + sleep_norm * 0.2) / 5.0 * 100
    
    def add_entry_interactive(self):
        print("\n--- Add New Entry ---")
        date = self.parse_date(input("Date (today): ") or "today")
        mood = self.prompt_mood()
        sleep = self.prompt_float("Sleep hours (0-24): ", 0, 24)
        water = self.prompt_int("Water cups (0-50): ", 0, 50)
        energy = self.prompt_int("Energy level (1-5): ", 1, 5)
        note = input("Note (max 200 chars): ")[:200]
        tags = [t.strip() for t in input("Tags (comma sep, optional): ").split(",") if t.strip()]
        
        entry = Entry(
            date=date,
            mood=mood,
            mood_label=MOOD_LABELS[mood],
            sleep_hours=sleep,
            water_cups=water,
            energy=energy,
            note=note,
            tags=tags,
            wellness_score=self.calculate_wellness_score(Entry(date=date,mood=mood,mood_label="",sleep_hours=sleep,water_cups=water,energy=energy,note="",tags=[],created_at="",updated_at="")),
            created_at=datetime.datetime.now().isoformat(),
            updated_at=datetime.datetime.now().isoformat()
        )
        
        self.data["entries"].append(asdict(entry))
        self.save_data()
        print("✓ Entry added!")
    
    def prompt_mood(self) -> int:
        while True:
            print("Mood: 1=Terrible, 2=Bad, 3=Okay, 4=Good, 5=Great")
            try:
                inp = input("Mood (1-5): ").strip()
                mood = int(inp) if inp.isdigit() else next(k for k,v in MOOD_LABELS.items() if v.lower().startswith(inp.lower()))
                if 1 <= mood <= 5:
                    return mood
            except:
                pass
            print("Invalid mood")
    
    def prompt_int(self, msg: str, min_val: int, max_val: int) -> int:
        while True:
            try:
                val = int(input(msg))
                if min_val <= val <= max_val:
                    return val
            except:
                pass
            print(f"Enter integer between {min_val}-{max_val}")
    
    def prompt_float(self, msg: str, min_val: float, max_val: float) -> float:
        while True:
            try:
                val = float(input(msg))
                if min_val <= val <= max_val:
                    return val
            except:
                pass
            print(f"Enter number between {min_val}-{max_val}")
    
    def quick_add(self, quick_str: str):
        parts = quick_str.split()
        if len(parts) < 4:
            print("Format: today 4 7.5 6 'note' tags:run,cardio")
            return
        
        date = self.parse_date(parts[0])
        mood = int(parts[1])
        sleep = float(parts[2])
        water = int(parts[3])
        energy = 3  # default
        note = " ".join(parts[4:]) if len(parts) > 4 else ""
        tags = []
        
        # Parse tags
        if "tags:" in quick_str.lower():
            tags_part = quick_str.lower().split("tags:")[-1]
            tags = [t.strip() for t in tags_part.split(",") if t.strip()]
        
        entry = Entry(
            date=date, mood=mood, mood_label=MOOD_LABELS[mood],
            sleep_hours=sleep, water_cups=water, energy=energy,
            note=note[:200], tags=tags,
            wellness_score=self.calculate_wellness_score(Entry(date=date,mood=mood,mood_label="",sleep_hours=sleep,water_cups=water,energy=energy,note="",tags=[],created_at="",updated_at="")),
            created_at=datetime.datetime.now().isoformat(),
            updated_at=datetime.datetime.now().isoformat()
        )
        
        self.data["entries"].append(asdict(entry))
        self.save_data()
        print("✓ Quick entry added!")
    
    def list_entries(self, page: int = 1, page_size: Optional[int] = None):
        if not page_size:
            page_size = self.data["config"]["page_size"]
        
        start = (page - 1) * page_size
        end = start + page_size
        page_entries = self.entries[start:end]
        
        print(f"\n--- Entries (Page {page}, {len(page_entries)}/{len(self.entries)}) ---")
        for i, entry in enumerate(page_entries, start=start+1):
            note_preview = entry.note[:30] + "..." if len(entry.note) > 30 else entry.note
            print(f"{i:2d}. {entry.date} | {entry.mood_label} | Sleep:{entry.sleep_hours:.1f}h | Water:{entry.water_cups} | {note_preview}")
        
        print("n=next p=prev o<idx>=open d<idx>=delete | h=help")
    
    def show_entry(self, index: int):
        if 0 <= index < len(self.entries):
            entry = self.entries[index]
            print(f"\n--- Entry {index+1} ---")
            print(f"Date: {entry.date}")
            print(f"Mood: {entry.mood_label} ({entry.mood}/5)")
            print(f"Sleep: {entry.sleep_hours:.1f}h")
            print(f"Water: {entry.water_cups} cups")
            print(f"Energy: {entry.energy}/5")
            print(f"Wellness Score: {entry.wellness_score:.1f}")
            print(f"Note: {entry.note}")
            print(f"Tags: {', '.join(entry.tags)}")
        else:
            print("Invalid index")
    
    def delete_entry(self, index: int):
        if 0 <= index < len(self.entries):
            self.show_entry(index)
            if input("Delete? (y/n): ").lower() == 'y':
                del self.data["entries"][index]
                self.save_data()
                print("✓ Deleted")
        else:
            print("Invalid index")
    
    def filter_entries(self, query: str) -> List[Entry]:
        results = self.entries[:]
        
        # Parse query components
        parts = query.lower().split()
        for part in parts:
            if "mood>=" in part:
                min_mood = int(part.split("mood>=")[1])
                results = [e for e in results if e.mood >= min_mood]
            elif "tag:" in part:
                tag = part.split("tag:")[1]
                results = [e for e in results if tag in [t.lower() for t in e.tags]]
            elif ".." in part:  # date range
                dates = part.split("..")
                if len(dates) == 2:
                    try:
                        start_date = datetime.date.fromisoformat(dates[0])
                        end_date = datetime.date.fromisoformat(dates[1])
                        results = [e for e in results if start_date <= datetime.date.fromisoformat(e.date) <= end_date]
                    except:
                        pass
            elif any(word in part for word in results[0].note.lower().split() if results):
                results = [e for e in results if part in e.note.lower()]
        
        return results
    
    def summary(self, days: int = 7):
        now = datetime.date.today()
        cutoff = now - datetime.timedelta(days=days)
        
        period_entries = [e for e in self.entries 
                         if datetime.date.fromisoformat(e.date) >= cutoff]
        
        if not period_entries:
            print(f"No entries in last {days} days")
            return
        
        sleep_vals = [e.sleep_hours for e in period_entries]
        water_vals = [e.water_cups for e in period_entries]
        energy_vals = [e.energy for e in period_entries]
        wellness_vals = [e.wellness_score for e in period_entries]
        
        print(f"\n--- {days}-Day Summary ---")
        print(f"Avg Sleep: {statistics.mean(sleep_vals):.1f}h")
        print(f"Avg Water: {statistics.mean(water_vals):.0f} cups")
        print(f"Avg Energy: {statistics.mean(energy_vals):.1f}/5")
        print(f"Avg Wellness: {statistics.mean(wellness_vals):.1f}")
        
        mood_dist = {}
        for e in period_entries:
            mood_dist[e.mood] = mood_dist.get(e.mood, 0) + 1
        print("Mood: " + " ".join([f"{k}:{v}" for k,v in sorted(mood_dist.items())]))
        
        # Sparkline for mood (last 14 days max)
        if days >= 14:
            spark_entries = [e for e in self.entries 
                           if datetime.date.fromisoformat(e.date) >= (now - datetime.timedelta(days=14))]
            sparkline = "".join(["•" if e.mood >= 3 else "·" for e in spark_entries[::-1]])
            print(f"Mood trend: {sparkline}")
    
    def export(self, filename: str, date_range: Optional[str] = None):
        if date_range:
            dates = date_range.split("..")
            if len(dates) == 2:
                start_date = datetime.date.fromisoformat(dates[0])
                end_date = datetime.date.fromisoformat(dates[1])
                entries = [asdict(e) for e in self.entries 
                          if start_date <= datetime.date.fromisoformat(e.date) <= end_date]
            else:
                entries = self.data["entries"]
        else:
            entries = self.data["entries"]
        
        with open(filename, 'w') as f:
            json.dump(entries, f, indent=2)
        print(f"✓ Exported {len(entries)} entries to {filename}")
    
    def import_data(self, filename: str):
        try:
            with open(filename, 'r') as f:
                imported = json.load(f)
            
            added = 0
            for entry_dict in imported:
                # Check for duplicate by date + identical content
                date_key = entry_dict["date"]
                if not any(e["date"] == date_key and e["note"] == entry_dict["note"] 
                          for e in self.data["entries"]):
                    self.data["entries"].append(entry_dict)
                    added += 1
            
            if added > 0:
                self.save_data()
            print(f"✓ Imported {added} new entries")
        except Exception as e:
            print(f"Import failed: {e}")
    
    def share_entry(self, index: int):
        if 0 <= index < len(self.entries):
            payload = json.dumps(asdict(self.entries[index]))
            token = base64.urlsafe_b64encode(payload.encode()).decode()
            print(f"\nShare token: {token}")
            
            # Try clipboard (platform specific, no external deps)
            try:
                if sys.platform == "darwin":
                    subprocess.run(["pbcopy", "w"], input=token.encode(), check=True)
                elif sys.platform.startswith("linux"):
                    subprocess.run(["xclip", "-selection", "clipboard"], input=token.encode(), check=True)
                print("(Copied to clipboard)")
            except:
                pass
        else:
            print("Invalid index")
    
    def show_help(self):
        print("""
Commands:
  add                - Interactive entry
  quick <str>        - Quick add: "today 4 7.5 6 'note' tags:run"
  list [page]        - List entries (n/p = next/prev)
  open <idx>         - Show full entry
  delete <idx>       - Delete entry
  search <query>     - Filter: "mood>=4 tag:run 2024-01-01..2024-01-07"
  summary [7|30]     - Show summary
  export <file> [range] - Export JSON
  import <file>      - Import JSON
  share <idx>        - Share entry token
  config             - Settings
  backup restore     - Backup management
  help / quit        - This help / exit
        """)

def main():
    tracker = WellnessTracker()
    
    # First run tour
    if not tracker.entries:
        print("Welcome to Wellness Snapshot! Let's add your first entry.")
        tracker.show_help()
        tracker.add_entry_interactive()
    
    while True:
        try:
            cmd = input("\n> ").strip().lower().split()
            if not cmd:
                continue
            
            if cmd[0] in ['quit', 'exit', 'q']:
                break
            elif cmd[0] == 'help' or cmd[0] in ['h', '?']:
                tracker.show_help()
            elif cmd[0] == 'add':
                tracker.add_entry_interactive()
            elif cmd[0] == 'quick' and len(cmd) > 1:
                tracker.quick_add(" ".join(cmd[1:]))
            elif cmd[0] == 'list':
                page = int(cmd[1]) if len(cmd) > 1 else 1
                tracker.list_entries(page)
            elif cmd[0] in ['open', 'o'] and len(cmd) > 1:
                tracker.show_entry(int(cmd[1]) - 1)
            elif cmd[0] in ['delete', 'd'] and len(cmd) > 1:
                tracker.delete_entry(int(cmd[1]) - 1)
            elif cmd[0] == 'search' and len(cmd) > 1:
                results = tracker.filter_entries(" ".join(cmd[1:]))
                tracker.entries = results  # Temp for display
                tracker.list_entries()
                tracker.entries = sorted(tracker.entries, key=lambda e: e.date, reverse=True)
            elif cmd[0] == 'summary':
                days = int(cmd[1]) if len(cmd) > 1 else 7
                tracker.summary(days)
            elif cmd[0] == 'export' and len(cmd) > 1:
                date_range = " ".join(cmd[2:]) if len(cmd) > 2 else None
                tracker.export(cmd[1], date_range)
            elif cmd[0] == 'import' and len(cmd) > 1:
                tracker.import_data(cmd[1])
            elif cmd[0] == 'share' and len(cmd) > 1:
                tracker.share_entry(int(cmd[1]) - 1)
            elif cmd[0] == 'config':
                print("Config:", tracker.data["config"])
            else:
                print("Unknown command. Type 'help'")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()