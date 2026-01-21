# Auto-generated via Perplexity on 2026-01-21T10:48:44.252292Z
#!/usr/bin/env python3
import json
import datetime
import os
import sys
import readline
from pathlib import Path

DATA_FILE = 'habits.json'
BACKUP_FILE = 'habits_backup.json'
REPORT_FILE = 'habit_report.txt'
ACTIONS_FILE = 'actions.json'

class Habit:
    def __init__(self, name, streak=0, last_completed=None):
        self.name = name
        self.streak = streak
        self.last_completed = last_completed or None

class HabitTracker:
    def __init__(self):
        self.habits = []
        self.undo_stack = []
        self.redo_stack = []
        self.today = datetime.date.today()
        self.load_data()
    
    def load_data(self):
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.habits = [Habit(h['name'], h['streak'], 
                                       datetime.date.fromisoformat(h['last_completed']) 
                                       if h['last_completed'] else None) 
                                 for h in data['habits']]
            if os.path.exists(ACTIONS_FILE):
                with open(ACTIONS_FILE, 'r') as f:
                    actions_data = json.load(f)
                    self.undo_stack = actions_data.get('undo', [])
                    self.redo_stack = actions_data.get('redo', [])
        except:
            self.habits = []
            self.undo_stack = []
            self.redo_stack = []
    
    def save_data(self):
        data = {
            'habits': [{'name': h.name, 'streak': h.streak, 
                       'last_completed': h.last_completed.isoformat() 
                       if h.last_completed else None} for h in self.habits]
        }
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        actions_data = {'undo': self.undo_stack[-5:], 'redo': self.redo_stack[-5:]}
        with open(ACTIONS_FILE, 'w') as f:
            json.dump(actions_data, f, indent=2)
    
    def backup_data(self):
        if os.path.exists(DATA_FILE):
            Path(DATA_FILE).replace(BACKUP_FILE)
    
    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def record_action(self, action, habit_name=None):
        self.undo_stack.append({'action': action, 'habit': habit_name, 
                               'state': self.get_habits_state()})
        self.undo_stack = self.undo_stack[-5:]
        self.redo_stack.clear()
    
    def get_habits_state(self):
        return [{'name': h.name, 'streak': h.streak, 
                'last_completed': h.last_completed.isoformat() 
                if h.last_completed else None} for h in self.habits]
    
    def undo(self):
        if not self.undo_stack:
            print("No actions to undo.")
            input("Press Enter...")
            return False
        
        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        
        target_state = action['state']
        self.habits = [Habit(h['name'], h['streak'], 
                           datetime.date.fromisoformat(h['last_completed']) 
                           if h['last_completed'] else None) 
                      for h in target_state]
        print(f"Undone: {action['action']} for {action['habit'] or 'add'}")
        input("Press Enter...")
        return True
    
    def redo(self):
        if not self.redo_stack:
            print("No actions to redo.")
            input("Press Enter...")
            return False
        
        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        
        target_state = action['state']
        self.habits = [Habit(h['name'], h['streak'], 
                           datetime.date.fromisoformat(h['last_completed']) 
                           if h['last_completed'] else None) 
                      for h in target_state]
        print(f"Redone: {action['action']} for {action['habit'] or 'add'}")
        input("Press Enter...")
        return True
    
    def find_habit_by_number(self, num):
        try:
            idx = int(num) - 1
            if 0 <= idx < len(self.habits):
                return self.habits[idx]
        except:
            pass
        return None
    
    def get_completions(self, text, state):
        names = [h.name for h in self.habits]
        return [n for n in names if n.lower().startswith(text.lower())][state:state+10]
    
    def list_habits(self):
        if not self.habits:
            print("No habits yet. Add some with option 2!")
            input("Press Enter...")
            return
        
        sorted_habits = sorted(self.habits, key=lambda h: h.streak, reverse=True)
        for i, habit in enumerate(sorted_habits, 1):
            date_str = habit.last_completed.strftime('%Y-%m-%d') if habit.last_completed else 'Never'
            print(f"[{i}] {habit.name} (streak: {habit.streak} days, last: {date_str})")
        input("\nPress Enter...")
    
    def add_habit(self):
        name = input("Habit name (max 50 chars): ").strip()[:50]
        if not name:
            print("Invalid name.")
            input("Press Enter...")
            return
        
        if any(h.name.lower() == name.lower() for h in self.habits):
            print("Habit already exists (case-insensitive).")
            input("Press Enter...")
            return
        
        self.habits.append(Habit(name))
        self.record_action('add', name)
        print(f"Added '{name}'!")
        self.save_data()
        input("Press Enter...")
    
    def complete_habit(self):
        self.list_habits()
        if not self.habits:
            return
        
        num = input("Select habit number: ").strip()
        habit = self.find_habit_by_number(num)
        
        if not habit:
            print("Invalid selection.")
            input("Press Enter...")
            return
        
        old_streak = habit.streak
        if habit.last_completed == self.today:
            print("Already completed today!")
        else:
            if habit.last_completed == self.today - datetime.timedelta(days=1):
                habit.streak += 1
            else:
                habit.streak = 1
            habit.last_completed = self.today
        
        self.record_action('complete', habit.name)
        print(f"Streak now {habit.streak}!")
        self.save_data()
        input("Press Enter...")
    
    def reset_streak(self):
        self.list_habits()
        if not self.habits:
            return
        
        num = input("Select habit number to reset: ").strip()
        habit = self.find_habit_by_number(num)
        
        if not habit:
            print("Invalid selection.")
            input("Press Enter...")
            return
        
        self.record_action('reset', habit.name)
        habit.streak = 0
        print(f"Reset '{habit.name}' streak to 0.")
        self.save_data()
        input("Press Enter...")
    
    def streaks_report(self):
        if not self.habits:
            print("No habits.")
            input("Press Enter...")
            return
        
        streaks = [(h.name, h.streak) for h in self.habits]
        streaks.sort(key=lambda x: x[1], reverse=True)
        
        print("=== TOP 3 LONGEST STREAKS ===")
        for i, (name, streak) in enumerate(streaks[:3], 1):
            print(f"{i}. {name}: {streak} days")
        
        total_habits = len(self.habits)
        avg_streak = sum(h.streak for h in self.habits) / total_habits if total_habits else 0
        print(f"\nTotal habits: {total_habits}")
        print(f"Average streak: {avg_streak:.1f} days")
        input("Press Enter...")
    
    def search_habits(self):
        readline.set_completer(self.get_completions)
        readline.parse_and_bind('tab: complete')
        
        query = input("Search habits (tab for completion): ").strip().lower()
        readline.set_completer(None)
        
        matches = [h for h in self.habits if query in h.name.lower()]
        if not matches:
            print("No matches found.")
        else:
            print("\nMatches:")
            for habit in matches:
                date_str = habit.last_completed.strftime('%Y-%m-%d') if habit.last_completed else 'Never'
                print(f"  {habit.name} (streak: {habit.streak}, last: {date_str})")
        
        input("Press Enter...")
    
    def export_report(self):
        if not self.habits:
            print("No habits to export.")
            input("Press Enter...")
            return
        
        sorted_habits = sorted(self.habits, key=lambda h: h.streak, reverse=True)
        with open(REPORT_FILE, 'w') as f:
            f.write("Habit Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {self.today}\n\n")
            f.write("Name\t\t\tStreak\tLast Completed\n")
            f.write("-" * 50 + "\n")
            for habit in sorted_habits:
                date_str = habit.last_completed.strftime('%Y-%m-%d') if habit.last_completed else 'Never'
                f.write(f"{habit.name:<20}\t{habit.streak}\t{date_str}\n")
        
        print(f"Report exported to {REPORT_FILE}")
        input("Press Enter...")
    
    def show_menu(self):
        self.clear_screen()
        print("=== DAILY HABIT FORGE ===")
        print(f"Today: {self.today.strftime('%Y-%m-%d')}")
        print("\n1. List habits")
        print("2. Add habit")
        print("3. Complete habit (today)")
        print("4. Reset streak")
        print("5. View streaks report")
        print("6. Search by name")
        print("7. Undo")
        print("8. Redo")
        print("9. Export report")
        print("0. Quit")
        print("-" * 20)

def main():
    tracker = HabitTracker()
    
    try:
        while True:
            tracker.show_menu()
            choice = input("Choose: ").strip()
            
            if choice == '1':
                tracker.list_habits()
            elif choice == '2':
                tracker.add_habit()
            elif choice == '3':
                tracker.complete_habit()
            elif choice == '4':
                tracker.reset_streak()
            elif choice == '5':
                tracker.streaks_report()
            elif choice == '6':
                tracker.search_habits()
            elif choice == '7':
                tracker.undo()
            elif choice == '8':
                tracker.redo()
            elif choice == '9':
                tracker.export_report()
            elif choice == '0':
                tracker.backup_data()
                tracker.save_data()
                print("Goodbye! Data saved.")
                break
            else:
                print("Invalid choice.")
                input("Press Enter...")
    
    except KeyboardInterrupt:
        tracker.backup_data()
        tracker.save_data()
        print("\n\nGoodbye! Data saved.")

if __name__ == "__main__":
    main()