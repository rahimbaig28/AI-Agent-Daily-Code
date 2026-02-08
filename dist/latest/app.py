# Auto-generated via Perplexity on 2026-02-08T16:49:20.248055Z
import json
import os
from datetime import datetime, date, timedelta
from pathlib import Path

class HabitTrackerPro:
    def __init__(self):
        self.data_file = Path(__file__).parent / "habits.json"
        self.habits = self.load_habits()
    
    def load_habits(self):
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_habits(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.habits, f, indent=2)
        print("Saved to habits.json")
    
    def get_next_id(self):
        return max([h['id'] for h in self.habits], default=0) + 1
    
    def clear_screen(self):
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def calculate_streak(self, habit):
        if not habit['logs']:
            return 0
        logs = sorted([datetime.strptime(log, '%Y-%m-%d').date() for log in habit['logs']])
        today = date.today()
        streak = 0
        current_date = today
        for log_date in reversed(logs):
            if log_date == current_date or log_date == current_date - timedelta(days=1):
                streak += 1
                current_date = log_date
            else:
                break
        return streak
    
    def get_completion_rate(self, habit):
        if not habit['logs']:
            return 0.0
        start = datetime.strptime(habit['start_date'], '%Y-%m-%d').date()
        today = date.today()
        days_elapsed = (today - start).days + 1
        return (len(habit['logs']) / days_elapsed * 100) if days_elapsed > 0 else 0.0
    
    def get_avg_daily_time(self, habit):
        if not habit['total_logs']:
            return 0
        return habit['total_time'] // habit['total_logs']
    
    def get_productivity_score(self):
        if not self.habits:
            return 0.0
        total_rate = sum(self.get_completion_rate(h) for h in self.habits)
        return total_rate / len(self.habits)
    
    def get_weekly_heatmap(self):
        today = date.today()
        heatmap = {}
        for i in range(7):
            day = today - timedelta(days=6-i)
            heatmap[day.strftime('%a %m/%d')] = '✗'
        
        for habit in self.habits:
            for log in habit['logs']:
                log_date = datetime.strptime(log, '%Y-%m-%d').date()
                if (today - log_date).days < 7:
                    key = log_date.strftime('%a %m/%d')
                    if key in heatmap:
                        heatmap[key] = '✓'
        
        return heatmap
    
    def add_habit(self):
        self.clear_screen()
        print("=== ADD HABIT ===\n")
        
        name = input("Habit name (max 30 chars): ").strip()[:30]
        if not name:
            print("Error: Name cannot be empty")
            input("Press Enter to continue...")
            return
        
        if any(h['name'].lower() == name.lower() for h in self.habits):
            print("Error: Habit already exists")
            input("Press Enter to continue...")
            return
        
        print("Categories: 1=Work, 2=Personal, 3=Health")
        cat_choice = input("Select category (1-3): ").strip()
        categories = {'1': 'Work', '2': 'Personal', '3': 'Health'}
        category = categories.get(cat_choice, 'Personal')
        
        try:
            target = int(input("Target daily time (1-240 mins): ").strip())
            if not 1 <= target <= 240:
                raise ValueError
        except ValueError:
            print("Error: Invalid target time")
            input("Press Enter to continue...")
            return
        
        start_input = input("Start date (YYYY-MM-DD or press Enter for today): ").strip()
        if start_input:
            try:
                datetime.strptime(start_input, '%Y-%m-%d')
                start_date = start_input
            except ValueError:
                print("Error: Invalid date format")
                input("Press Enter to continue...")
                return
        else:
            start_date = date.today().strftime('%Y-%m-%d')
        
        habit = {
            'id': self.get_next_id(),
            'name': name,
            'category': category,
            'target_mins': target,
            'start_date': start_date,
            'logs': [],
            'streak': 0,
            'total_logs': 0,
            'total_time': 0
        }
        self.habits.append(habit)
        self.save_habits()
        print(f"\nAdded habit: {name}")
        input("Press Enter to continue...")
    
    def list_habits(self):
        self.clear_screen()
        print("=== HABITS ===\n")
        
        if not self.habits:
            print("No habits yet. Add one to get started!")
            input("Press Enter to continue...")
            return
        
        print(f"{'ID':<4} {'Name':<20} {'Category':<10} {'Streak':<8} {'Logs':<6} {'Avg Time':<10}")
        print("-" * 60)
        
        for h in self.habits:
            streak = self.calculate_streak(h)
            avg_time = self.get_avg_daily_time(h)
            print(f"{h['id']:<4} {h['name']:<20} {h['category']:<10} {streak:<8} {h['total_logs']:<6} {avg_time:<10}")
        
        input("\nPress Enter to continue...")
    
    def log_streak(self):
        self.clear_screen()
        print("=== LOG STREAK ===\n")
        
        if not self.habits:
            print("No habits to log.")
            input("Press Enter to continue...")
            return
        
        self.list_habits()
        
        try:
            habit_id = int(input("Enter habit ID to log: ").strip())
            habit = next((h for h in self.habits if h['id'] == habit_id), None)
            if not habit:
                print("Error: Habit not found")
                input("Press Enter to continue...")
                return
        except ValueError:
            print("Error: Invalid ID")
            input("Press Enter to continue...")
            return
        
        today_str = date.today().strftime('%Y-%m-%d')
        if today_str in habit['logs']:
            print(f"Already logged for today!")
            input("Press Enter to continue...")
            return
        
        try:
            time_spent = int(input(f"Time spent today (mins, optional, press Enter for 0): ").strip() or "0")
            if time_spent < 0:
                raise ValueError
        except ValueError:
            print("Error: Invalid time")
            input("Press Enter to continue...")
            return
        
        habit['logs'].append(today_str)
        habit['total_logs'] += 1
        habit['total_time'] += time_spent
        habit['streak'] = self.calculate_streak(habit)
        
        self.save_habits()
        print(f"Logged for {habit['name']}! Current streak: {habit['streak']} days")
        input("Press Enter to continue...")
    
    def view_stats(self):
        self.clear_screen()
        print("=== STATISTICS ===\n")
        
        if not self.habits:
            print("No habits to analyze.")
            input("Press Enter to continue...")
            return
        
        print("PER-HABIT STATS:")
        print(f"{'Name':<20} {'Streak':<8} {'Completion %':<15} {'Avg vs Target':<15}")
        print("-" * 60)
        
        for h in self.habits:
            streak = self.calculate_streak(h)
            completion = self.get_completion_rate(h)
            avg_time = self.get_avg_daily_time(h)
            vs_target = f"{avg_time}/{h['target_mins']} min"
            print(f"{h['name']:<20} {streak:<8} {completion:<14.1f}% {vs_target:<15}")
        
        print("\nOVERALL STATS:")
        print(f"Total habits: {len(self.habits)}")
        print(f"Average streak: {sum(self.calculate_streak(h) for h in self.habits) / len(self.habits):.1f} days")
        print(f"Productivity score: {self.get_productivity_score():.1f}%")
        
        print("\nLAST 7 DAYS HEATMAP:")
        heatmap = self.get_weekly_heatmap()
        for day, status in heatmap.items():
            print(f"{day}: {status}")
        
        input("\nPress Enter to continue...")
    
    def edit_habit(self):
        self.clear_screen()
        print("=== EDIT HABIT ===\n")
        
        if not self.habits:
            print("No habits to edit.")
            input("Press Enter to continue...")
            return
        
        self.list_habits()
        
        try:
            habit_id = int(input("Enter habit ID to edit: ").strip())
            habit = next((h for h in self.habits if h['id'] == habit_id), None)
            if not habit:
                print("Error: Habit not found")
                input("Press Enter to continue...")
                return
        except ValueError:
            print("Error: Invalid ID")
            input("Press Enter to continue...")
            return
        
        print(f"\nEditing: {habit['name']}")
        print("Leave blank to keep current value\n")
        
        new_name = input(f"Name ({habit['name']}): ").strip()
        if new_name:
            habit['name'] = new_name[:30]
        
        print("Categories: 1=Work, 2=Personal, 3=Health")
        cat_choice = input(f"Category ({habit['category']}): ").strip()
        if cat_choice:
            categories = {'1': 'Work', '2': 'Personal', '3': 'Health'}
            habit['category'] = categories.get(cat_choice, habit['category'])
        
        new_target = input(f"Target daily time ({habit['target_mins']} mins): ").strip()
        if new_target:
            try:
                target = int(new_target)
                if 1 <= target <= 240:
                    habit['target_mins'] = target
            except ValueError:
                pass
        
        new_start = input(f"Start date ({habit['start_date']}): ").strip()
        if new_start:
            try:
                datetime.strptime(new_start, '%Y-%m-%d')
                habit['start_date'] = new_start
            except ValueError:
                pass
        
        self.save_habits()
        print(f"\nUpdated {habit['name']}")
        input("Press Enter to continue...")
    
    def delete_habit(self):
        self.clear_screen()
        print("=== DELETE HABIT ===\n")
        
        if not self.habits:
            print("No habits to delete.")
            input("Press Enter to continue...")
            return
        
        self.list_habits()
        
        try:
            habit_id = int(input("Enter habit ID to delete: ").strip())
            habit = next((h for h in self.habits if h['id'] == habit_id), None)
            if not habit:
                print("Error: Habit not found")
                input("Press Enter to continue...")
                return
        except ValueError:
            print("Error: Invalid ID")
            input("Press Enter to continue...")
            return
        
        confirm = input(f"Delete '{habit['name']}'? (y/n): ").strip().lower()
        if confirm == 'y':
            self.habits.remove(habit)
            self.save_habits()
            print("Deleted!")
        else:
            print("Cancelled")
        
        input("Press Enter to continue...")
    
    def main_menu(self):
        while True:
            self.clear_screen()
            score = self.get_productivity_score()
            print(f"=== HABIT TRACKER PRO ===")
            print(f"Productivity Score: {score:.1f}%\n")
            print("1. Add habit")
            print("2. List habits")
            print("3. Log streak")
            print("4. View stats")
            print("5. Edit habit")
            print("6. Delete habit")
            print("7. Quit")
            
            choice = input("\nSelect option (1-7): ").strip()
            
            if choice == '1':
                self.add_habit()
            elif choice == '2':
                self.list_habits()
            elif choice == '3':
                self.log_streak()
            elif choice == '4':
                self.view_stats()
            elif choice == '5':
                self.edit_habit()
            elif choice == '6':
                self.delete_habit()
            elif choice == '7':
                print("Goodbye!")
                break
            else:
                print("Invalid option")
                input("Press Enter to continue...")

if __name__ == "__main__":
    tracker = HabitTrackerPro()
    tracker.main_menu()