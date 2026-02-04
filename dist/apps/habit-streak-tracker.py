# Auto-generated via Perplexity on 2026-02-04T10:01:04.895702Z
#!/usr/bin/env python3
import json
import datetime
import os
import sys
from typing import List, Dict, Optional

DATA_FILE = 'habits.json'
BACKUP_FILE = 'habits_backup.json'

class HabitTracker:
    def __init__(self):
        self.habits: List[Dict] = []
        self.load_data()
    
    def load_data(self):
        """Load habits from JSON file, handle corrupt data gracefully."""
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    self.habits = json.load(f)
                self.prune_zero_streak()
        except (json.JSONDecodeError, KeyError, TypeError):
            print("⚠️  Corrupt data detected. Starting fresh.")
            self.habits = []
    
    def save_data(self):
        """Save habits to JSON file."""
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self.habits, f, indent=2)
        except Exception as e:
            print(f"❌ Save failed: {e}")
    
    def prune_zero_streak(self):
        """Remove habits with streak 0 that haven't been done recently."""
        today = datetime.date.today()
        self.habits = [
            h for h in self.habits 
            if h.get('streak', 0) > 0 or self.is_recent(h, today)
        ]
    
    def is_recent(self, habit: Dict, today: datetime.date) -> bool:
        """Check if habit was done within last 7 days."""
        try:
            last_date = datetime.date.fromisoformat(habit['last_date'])
            return (today - last_date).days <= 7
        except:
            return False
    
    def add_habit(self, name: str):
        """Add new habit with validation."""
        name = name.strip()
        if not name:
            print("❌ Habit name cannot be empty.")
            return
        if any(h['name'].lower() == name.lower() for h in self.habits):
            print("❌ Habit name already exists.")
            return
        self.habits.append({
            "name": name,
            "streak": 0,
            "last_date": ""
        })
        self.save_data()
        print(f"✅ Added habit: {name}")
    
    def mark_done(self, name: str):
        """Mark habit as done today with streak logic."""
        today_str = datetime.date.today().isoformat()
        habit = self.find_habit(name)
        if not habit:
            print("❌ Habit not found.")
            return
        
        if habit['last_date'] == today_str:
            print("⚠️  Already marked today.")
            return
        
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        if habit['last_date'] == yesterday.isoformat():
            habit['streak'] += 1
        else:
            habit['streak'] = 1
        
        habit['last_date'] = today_str
        self.save_data()
        print(f"✅ {habit['name']} marked! Streak: {habit['streak']}")
    
    def edit_habit(self, old_name: str, new_name: str):
        """Edit habit name."""
        habit = self.find_habit(old_name)
        if not habit:
            print("❌ Habit not found.")
            return
        new_name = new_name.strip()
        if not new_name or any(h['name'].lower() == new_name.lower() for h in self.habits if h != habit):
            print("❌ Invalid or duplicate name.")
            return
        habit['name'] = new_name
        self.save_data()
        print(f"✅ Renamed to: {new_name}")
    
    def delete_habit(self, name: str):
        """Delete habit."""
        habit = self.find_habit(name)
        if not habit:
            print("❌ Habit not found.")
            return
        self.habits.remove(habit)
        self.save_data()
        print(f"🗑️  Deleted: {name}")
    
    def find_habit(self, name: str) -> Optional[Dict]:
        """Find habit by name (case-insensitive)."""
        for habit in self.habits:
            if habit['name'].lower() == name.lower():
                return habit
        return None
    
    def display_habits(self):
        """Display habits sorted by streak, with color coding."""
        if not self.habits:
            print("No habits yet. Add some with option 2!")
            return
        
        # Sort by streak descending
        sorted_habits = sorted(self.habits, key=lambda h: h.get('streak', 0), reverse=True)
        
        print("\n📊 Current Habits (sorted by streak):")
        print("-" * 60)
        for h in sorted_habits:
            streak = h.get('streak', 0)
            last_date = h.get('last_date', 'Never')
            color = "\033[92m" if streak > 0 else "\033[91m"  # Green for active, red for broken
            reset = "\033[0m"
            print(f"{color}{h['name']:20} Streak: {streak:2d}  Last: {last_date:10}{reset}")
        print("-" * 60)
    
    def export_backup(self):
        """Export to timestamped backup."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"habits_backup_{timestamp}.json"
        try:
            with open(backup_file, 'w') as f:
                json.dump(self.habits, f, indent=2)
            print(f"💾 Backup saved: {backup_file}")
        except Exception as e:
            print(f"❌ Backup failed: {e}")
    
    def import_data(self, filepath: str):
        """Import from JSON file."""
        if not os.path.exists(filepath):
            print("❌ File not found.")
            return
        try:
            with open(filepath, 'r') as f:
                imported = json.load(f)
            if not isinstance(imported, list):
                print("❌ Invalid format. Must be list of habits.")
                return
            
            # Validate and merge
            for habit in imported:
                if not all(k in habit for k in ['name', 'streak', 'last_date']):
                    print("⚠️  Skipping invalid habit.")
                    continue
                existing = self.find_habit(habit['name'])
                if existing:
                    existing.update(habit)
                else:
                    self.habits.append(habit)
            
            self.save_data()
            print(f"✅ Imported {len(imported)} habits.")
        except Exception as e:
            print(f"❌ Import failed: {e}")
    
    def print_table(self):
        """Generate print-friendly table."""
        if not self.habits:
            print("No habits to print.")
            return
        
        sorted_habits = sorted(self.habits, key=lambda h: h.get('streak', 0), reverse=True)
        
        # Console table
        print("\n📋 Habits Table:")
        print(f"{'Name':<25} {'Streak':<8} {'Last Date':<12}")
        print("-" * 50)
        for h in sorted_habits:
            print(f"{h['name']:<25} {h.get('streak', 0):<8} {h.get('last_date', 'Never'):<12}")
        
        # Save to file
        try:
            with open('habits_print.txt', 'w') as f:
                f.write("Habit Streak Tracker\n")
                f.write("=" * 50 + "\n")
                f.write(f"{'Name':<25} {'Streak':<8} {'Last Date':<12}\n")
                f.write("-" * 50 + "\n")
                for h in sorted_habits:
                    f.write(f"{h['name']:<25} {h.get('streak', 0):<8} {h.get('last_date', 'Never'):<12}\n")
            print("💾 Saved to habits_print.txt")
        except Exception as e:
            print(f"❌ Print save failed: {e}")

def main():
    tracker = HabitTracker()
    unsaved_changes = False
    
    try:
        while True:
            print("\n" + "="*50)
            print("🏃‍♂️  HABIT STREAK TRACKER")
            print("="*50)
            tracker.display_habits()
            print("\n[1] Add Habit  [2] Mark Done  [3] Edit Name  [4] Delete")
            print("[5] Export    [6] Import     [7] Print     [0] Quit")
            choice = input("\nChoose (0-7): ").strip()
            
            if choice == '1':
                name = input("Habit name: ").strip()
                tracker.add_habit(name)
                unsaved_changes = True
            elif choice == '2':
                name = input("Habit name: ").strip()
                tracker.mark_done(name)
                unsaved_changes = True
            elif choice == '3':
                old = input("Current name: ").strip()
                new = input("New name: ").strip()
                tracker.edit_habit(old, new)
                unsaved_changes = True
            elif choice == '4':
                name = input("Habit name: ").strip()
                tracker.delete_habit(name)
                unsaved_changes = True
            elif choice == '5':
                tracker.export_backup()
            elif choice == '6':
                path = input("JSON file path: ").strip()
                tracker.import_data(path)
                unsaved_changes = True
            elif choice == '7':
                tracker.print_table()
            elif choice == '0':
                break
            else:
                print("❌ Invalid choice.")
    
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Saving...")
    
    finally:
        if unsaved_changes:
            confirm = input("\n💾 Save changes? (y/n): ").lower()
            if confirm in ['y', 'yes']:
                tracker.save_data()
        print("Goodbye! 💪")
        tracker.save_data()

if __name__ == "__main__":
    main()