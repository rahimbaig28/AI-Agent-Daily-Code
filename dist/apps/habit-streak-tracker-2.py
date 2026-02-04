# Auto-generated via Perplexity on 2026-02-04T10:59:49.426660Z
import json
import os
import datetime
from typing import List, Dict, Any, Optional

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

DATA_FILE = "habits.json"

class Habit:
    def __init__(self, name: str, streak: int = 0, last_completed: Optional[str] = None):
        self.name = name
        self.streak = streak
        self.last_completed = last_completed

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'streak': self.streak,
            'last_completed': self.last_completed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Habit':
        return cls(data['name'], data['streak'], data.get('last_completed'))

class HabitTracker:
    def __init__(self):
        self.habits: List[Habit] = []
        self.undo_stack: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []
        self.load_data()

    def load_data(self):
        """Load habits from JSON file."""
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.habits = [Habit.from_dict(h) for h in data]
        except (json.JSONDecodeError, KeyError):
            self.habits = []
            print(f"{YELLOW}Invalid JSON, starting fresh.{RESET}")

    def save_data(self):
        """Save habits to JSON file."""
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump([h.to_dict() for h in self.habits], f, indent=2)
        except Exception as e:
            print(f"{RED}Save failed: {e}{RESET}")

    def add_action_to_stack(self, action: Dict[str, Any]):
        """Add action to undo stack and clear redo stack."""
        self.undo_stack.append(action)
        if len(self.undo_stack) > 10:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def days_since_last(self, habit: Habit) -> str:
        """Calculate days since last completion."""
        if not habit.last_completed:
            return "Never"
        try:
            last_date = datetime.datetime.strptime(habit.last_completed, '%Y-%m-%d').date()
            today = datetime.date.today()
            days = (today - last_date).days
            if days == 0:
                return "Today"
            return str(days)
        except ValueError:
            return "Invalid date"

    def list_habits(self):
        """Display habits sorted by streak."""
        if not self.habits:
            print("No habits yet.")
            return

        sorted_habits = sorted(self.habits, key=lambda h: h.streak, reverse=True)
        print(f"\n{BOLD}Habits (sorted by streak):{RESET}")
        for i, habit in enumerate(sorted_habits, 1):
            status_color = GREEN if habit.streak > 0 else RED
            days_str = self.days_since_last(habit)
            print(f"{BLUE}{i:2d}.{RESET} {status_color}{habit.name:<20} Streak: {habit.streak:2d}  "
                  f"({days_str}){RESET}")

    def add_habit(self, name: str):
        """Add new habit."""
        if any(h.name.lower() == name.lower() for h in self.habits):
            print(f"{RED}Habit '{name}' already exists.{RESET}")
            return False

        old_habits = [h.to_dict() for h in self.habits]
        self.habits.append(Habit(name))
        self.add_action_to_stack({'type': 'add', 'old_habits': old_habits, 'new_habit': self.habits[-1].to_dict()})
        self.save_data()
        print(f"{GREEN}Added habit '{name}'.{RESET}")
        return True

    def mark_complete(self, index: int):
        """Mark habit complete for today."""
        if not (0 < index <= len(self.habits)):
            print(f"{RED}Invalid habit number.{RESET}")
            return False

        habit = self.habits[index - 1]
        old_streak = habit.streak
        old_date = habit.last_completed
        today_str = datetime.date.today().isoformat()

        # Check if yesterday or earlier
        increment_streak = True
        if habit.last_completed:
            try:
                last_date = datetime.datetime.strptime(habit.last_completed, '%Y-%m-%d').date()
                yesterday = datetime.date.today() - datetime.timedelta(days=1)
                if last_date != yesterday:
                    increment_streak = True
                else:
                    increment_streak = False
            except ValueError:
                increment_streak = True

        if increment_streak:
            habit.streak += 1
        habit.last_completed = today_str

        self.add_action_to_stack({
            'type': 'mark',
            'index': index - 1,
            'old_streak': old_streak,
            'old_date': old_date
        })
        self.save_data()
        print(f"{GREEN}Marked '{habit.name}' complete! Streak: {habit.streak}{RESET}")
        return True

    def edit_habit(self, index: int, new_name: str):
        """Edit habit name."""
        if not (0 < index <= len(self.habits)):
            print(f"{RED}Invalid habit number.{RESET}")
            return False

        habit = self.habits[index - 1]
        old_name = habit.name
        if any(h.name.lower() == new_name.lower() and h != habit for h in self.habits):
            print(f"{RED}Name '{new_name}' already exists.{RESET}")
            return False

        self.add_action_to_stack({'type': 'edit', 'index': index - 1, 'old_name': old_name})
        habit.name = new_name
        self.save_data()
        print(f"{GREEN}Renamed '{old_name}' to '{new_name}'.{RESET}")
        return True

    def delete_habit(self, index: int):
        """Delete habit."""
        if not (0 < index <= len(self.habits)):
            print(f"{RED}Invalid habit number.{RESET}")
            return False

        habit = self.habits[index - 1]
        old_habits = [h.to_dict() for h in self.habits]
        self.habits.pop(index - 1)
        self.add_action_to_stack({'type': 'delete', 'old_habits': old_habits})
        self.save_data()
        print(f"{GREEN}Deleted '{habit.name}'.{RESET}")
        return True

    def undo(self):
        """Undo last action."""
        if not self.undo_stack:
            print(f"{YELLOW}Nothing to undo.{RESET}")
            return False

        action = self.undo_stack.pop()
        self.redo_stack.append(action)

        if action['type'] == 'add':
            self.habits = [Habit.from_dict(h) for h in action['old_habits']]
        elif action['type'] == 'delete':
            self.habits = [Habit.from_dict(h) for h in action['old_habits']]
        elif action['type'] == 'mark':
            habit = self.habits[action['index']]
            habit.streak = action['old_streak']
            habit.last_completed = action['old_date']
        elif action['type'] == 'edit':
            self.habits[action['index']].name = action['old_name']

        self.save_data()
        print(f"{YELLOW}Undone.{RESET}")
        return True

    def redo(self):
        """Redo last undone action."""
        if not self.redo_stack:
            print(f"{YELLOW}Nothing to redo.{RESET}")
            return False

        action = self.redo_stack.pop()
        self.undo_stack.append(action)

        if action['type'] == 'add':
            self.habits.append(Habit.from_dict(action['new_habit']))
        elif action['type'] == 'delete':
            self.habits.pop(action['index'] + 1)  # Deleted one, index shifted
        elif action['type'] == 'mark':
            self.mark_complete(action['index'] + 1)
        elif action['type'] == 'edit':
            self.edit_habit(action['index'] + 1, action.get('new_name', ''))

        self.save_data()
        print(f"{YELLOW}Redone.{RESET}")
        return True

    def export_json(self, filename: str):
        """Export habits to JSON file."""
        try:
            shutil.copy2(DATA_FILE, filename)
            print(f"{GREEN}Exported to '{filename}'.{RESET}")
            return True
        except Exception as e:
            print(f"{RED}Export failed: {e}{RESET}")
            return False

    def import_json(self, filename: str, overwrite: bool):
        """Import habits from JSON file."""
        try:
            with open(filename, 'r') as f:
                new_data = json.load(f)
            
            old_habits = [h.to_dict() for h in self.habits]
            if overwrite:
                self.habits = [Habit.from_dict(h) for h in new_data]
            else:
                # Merge: add new habits only
                existing_names = {h.name.lower() for h in self.habits}
                for h_data in new_data:
                    if h_data['name'].lower() not in existing_names:
                        self.habits.append(Habit.from_dict(h_data))
                        existing_names.add(h_data['name'].lower())

            self.add_action_to_stack({'type': 'import', 'old_habits': old_habits})
            self.save_data()
            print(f"{GREEN}Imported from '{filename}' ({'overwritten' if overwrite else 'merged'}).{RESET}")
            return True
        except Exception as e:
            print(f"{RED}Import failed: {e}{RESET}")
            return False

def get_int_input(prompt: str, min_val: int = 1, max_val: int = float('inf')) -> Optional[int]:
    """Get validated integer input."""
    while True:
        try:
            inp = input(prompt).strip()
            if not inp:
                return None
            val = int(inp)
            if min_val <= val <= max_val:
                return val
            print(f"{RED}Enter number between {min_val}-{max_val}.{RESET}")
        except ValueError:
            print(f"{RED}Invalid number.{RESET}")

def main_menu(tracker: HabitTracker):
    """Main menu loop."""
    while True:
        print(f"\n{BOLD}{BLUE}=== Habit Streak Tracker ==={RESET}")
        tracker.list_habits()
        print(f"\n{BOLD}1.{RESET} List habits")
        print(f"{BOLD}2.{RESET} Add habit")
        print(f"{BOLD}3.{RESET} Mark complete")
        print(f"{BOLD}4.{RESET} Edit habit")
        print(f"{BOLD}5.{RESET} Delete habit")
        print(f"{BOLD}6.{RESET} Undo/Redo")
        print(f"{BOLD}7.{RESET} Export JSON")
        print(f"{BOLD}8.{RESET} Import JSON")
        print(f"{BOLD}9.{RESET} Quit")
        print(f"{YELLOW}Shortcuts: 'u'=undo, 'r'=redo{RESET}")

        choice = input("\nChoose (1-9, u, r): ").strip().lower()

        if choice == '1':
            tracker.list_habits()
            input("\nPress Enter...")
        elif choice == '2':
            name = input("Habit name: ").strip()
            if name:
                tracker.add_habit(name)
        elif choice == '3':
            num = get_int_input("Habit number: ", 1, len(tracker.habits))
            if num:
                tracker.mark_complete(num)
        elif choice == '4':
            num = get_int_input("Habit number: ", 1, len(tracker.habits))
            if num:
                new_name = input("New name: ").strip()
                if new_name:
                    tracker.edit_habit(num, new_name)
        elif choice == '5':
            num = get_int_input("Habit number: ", 1, len(tracker.habits))
            if num and input(f"Delete habit {num}? (y/N): ").lower() == 'y':
                tracker.delete_habit(num)
        elif choice in ('6', 'u'):
            tracker.undo()
        elif choice == 'r':
            tracker.redo()
        elif choice == '7':
            filename = input("Export filename (default: habits_backup.json): ").strip()
            if not filename:
                filename = "habits_backup.json"
            tracker.export_json(filename)
        elif choice == '8':
            filename = input("Import filename: ").strip()
            if filename:
                overwrite = input("Overwrite existing? (y/N): ").lower() == 'y'
                tracker.import_json(filename, overwrite)
        elif choice == '9':
            print("Goodbye!")
            break
        else:
            print(f"{RED}Invalid choice.{RESET}")

if __name__ == "__main__":
    import shutil
    tracker = HabitTracker()
    try:
        main_menu(tracker)
    finally:
        tracker.save_data()