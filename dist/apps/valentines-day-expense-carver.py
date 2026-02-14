# Auto-generated via Perplexity on 2026-02-14T09:46:08.093377Z
import json
import datetime
import os
import sys
import statistics
from typing import List, Dict, Any

CATEGORIES = ["Romance", "Dinner", "Gifts", "Self-Care", "Other"]
DATA_FILE = 'expenses.json'
BACKUP_FILE = 'expenses_backup.json'
CSV_FILE = 'expenses.csv'

class Expense:
    def __init__(self, date: str, amount: float, category: str, description: str):
        self.date = date
        self.amount = amount
        self.category = category
        self.description = description

class ExpenseTracker:
    def __init__(self):
        self.expenses: List[Dict[str, Any]] = []
        self.monthly_budget = 0.0
        self.load_data()
    
    def load_data(self):
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.expenses = data.get('expenses', [])
                    self.monthly_budget = data.get('budget', 0.0)
            elif os.path.exists(BACKUP_FILE):
                with open(BACKUP_FILE, 'r') as f:
                    data = json.load(f)
                    self.expenses = data.get('expenses', [])
                    self.monthly_budget = data.get('budget', 0.0)
            else:
                self._add_sample_data()
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def _add_sample_data(self):
        sample = [
            {"date": "2026-02-14", "amount": 75.50, "category": "Dinner", "description": "Romantic dinner"},
            {"date": "2026-02-13", "amount": 120.00, "category": "Gifts", "description": "Roses and chocolates"}
        ]
        self.expenses = sample
        self.monthly_budget = 500.0
    
    def save_data(self):
        try:
            if os.path.exists(DATA_FILE):
                self.backup_data()
            data = {
                'expenses': self.expenses,
                'budget': self.monthly_budget
            }
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    def backup_data(self):
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                with open(BACKUP_FILE, 'w') as f:
                    json.dump(data, f, indent=2)
        except:
            pass
    
    def add_expense(self, date: str, amount: float, category: str, description: str):
        expense = {
            "date": date,
            "amount": amount,
            "category": category,
            "description": description
        }
        self.expenses.append(expense)
        return self.save_data()
    
    def get_total_spent(self) -> float:
        return sum(e['amount'] for e in self.expenses)
    
    def get_expenses_in_range(self, days: int = 30) -> List[Dict[str, Any]]:
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
        return [e for e in self.expenses if e['date'] >= cutoff]
    
    def get_avg_daily_spend(self, days: int = 30) -> float:
        recent = self.get_expenses_in_range(days)
        if not recent:
            return 0.0
        return statistics.mean([e['amount'] for e in recent])
    
    def get_category_breakdown(self) -> Dict[str, Dict[str, float]]:
        breakdown = {}
        total = self.get_total_spent()
        for cat in CATEGORIES:
            cat_total = sum(e['amount'] for e in self.expenses if e['category'] == cat)
            breakdown[cat] = {
                'total': cat_total,
                'percent': (cat_total / total * 100) if total > 0 else 0
            }
        return breakdown

def detect_theme() -> str:
    term = os.environ.get('TERM', '')
    return 'dark' if 'dark' in term.lower() or '256color' not in term else 'light'

def color_print(text: str, color: str = 'white', theme: str = None, bold: bool = False):
    if theme is None:
        theme = detect_theme()
    
    colors = {
        'dark': {
            'white': '\033[97m',
            'black': '\033[30m',
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'reset': '\033[0m'
        },
        'light': {
            'white': '\033[37m',
            'black': '\033[30m',
            'red': '\033[31m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'reset': '\033[0m'
        }
    }
    
    prefix = '\033[1m' if bold else ''
    suffix = colors[theme][color] + prefix + text + colors[theme]['reset']
    print(suffix)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_terminal_width():
    try:
        return os.get_terminal_size().columns
    except:
        return 80

def draw_table(data: List[List[str]], headers: List[str], width: int = None):
    if width is None:
        width = get_terminal_width()
    
    col_widths = [max(len(str(row[i])) for row in data + [headers]) for i in range(len(headers))]
    col_widths = [min(w, (width - len(headers) - 1) // len(headers)) for w in col_widths]
    
    header_row = '│ ' + ' │ '.join(h.ljust(w) for h, w in zip(headers, col_widths)) + ' │'
    separator = '├' + '─'*(len(header_row)-2) + '┤'
    
    print(header_row)
    print(separator)
    for row in data:
        print('│ ' + ' │ '.join(str(r).ljust(w) for r, w in zip(row, col_widths)) + ' │')

def print_menu(options: List[str], title: str = "Valentine's Day Expense Carver 💕"):
    clear_screen()
    theme = detect_theme()
    color_print(title, 'red' if theme == 'dark' else 'blue', theme, True)
    print('═' * get_terminal_width())
    for i, opt in enumerate(options, 1):
        print(f"{i:2d}. {opt}")
    print('═' * get_terminal_width())

def get_date_input() -> str:
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_str = input(f"Date (YYYY-MM-DD, Enter for today {today}): ").strip()
    if not date_str:
        return today
    
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except:
        print("Invalid date format. Using today.")
        return today

def get_float_input(prompt: str) -> float:
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Please enter a valid number.")

def get_category_input() -> str:
    while True:
        print("\nCategories:")
        for i, cat in enumerate(CATEGORIES, 1):
            print(f"  {i}. {cat}")
        choice = input("Select category (1-5): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(CATEGORIES):
                return CATEGORIES[idx]
        except:
            pass
        print("Invalid choice.")

def set_budget(tracker: ExpenseTracker):
    budget = get_float_input("Enter monthly budget: $")
    tracker.monthly_budget = budget
    tracker.save_data()
    color_print(f"Budget set to ${budget:.2f}", 'green')

def add_expense_menu(tracker: ExpenseTracker):
    clear_screen()
    color_print("💕 Add New Expense 💕", 'red')
    
    date = get_date_input()
    amount = get_float_input("Amount: $")
    category = get_category_input()
    desc = input("Description: ").strip()
    
    if tracker.add_expense(date, amount, category, desc):
        color_print("✅ Expense added successfully!", 'green')
    input("\nPress Enter to continue...")

def view_summary(tracker: ExpenseTracker):
    clear_screen()
    total = tracker.get_total_spent()
    avg7 = tracker.get_avg_daily_spend(7)
    avg30 = tracker.get_avg_daily_spend(30)
    
    color_print("💰 Expense Summary 💰", 'yellow')
    print(f"Total spent: ${total:.2f}")
    print(f"Avg daily (7d): ${avg7:.2f}")
    print(f"Avg daily (30d): ${avg30:.2f}")
    
    if tracker.monthly_budget > 0:
        remaining = tracker.monthly_budget - total
        percent_used = (total / tracker.monthly_budget) * 100
        print(f"Budget: ${tracker.monthly_budget:.2f} | Used: {percent_used:.1f}% | Remaining: ${remaining:.2f}")
        if remaining < tracker.monthly_budget * 0.2:
            color_print("⚠️  WARNING: Less than 20% budget remaining!", 'red')
    
    input("\nPress Enter to continue...")

def category_breakdown(tracker: ExpenseTracker):
    clear_screen()
    breakdown = tracker.get_category_breakdown()
    theme = detect_theme()
    
    color_print("📊 Category Breakdown 📊", 'yellow')
    table_data = []
    for cat, data in breakdown.items():
        pct = f"{data['percent']:.1f}%"
        if data['percent'] > 30:
            color_print(f"{cat}: ${data['total']:.2f} ({pct})", 'red', theme)
        else:
            print(f"{cat}: ${data['total']:.2f} ({pct})")
        table_data.append([cat, f"${data['total']:.2f}", pct])
    
    print()
    headers = ["Category", "Total", "%"]
    draw_table(table_data, headers)
    input("\nPress Enter to continue...")

def budget_check(tracker: ExpenseTracker):
    clear_screen()
    if tracker.monthly_budget == 0:
        color_print("No budget set. Use option 4 to set budget.", 'yellow')
    else:
        total = tracker.get_total_spent()
        remaining = tracker.monthly_budget - total
        percent_left = (remaining / tracker.monthly_budget) * 100
        
        color_print("💳 Budget Status 💳", 'blue')
        print(f"Monthly Budget: ${tracker.monthly_budget:.2f}")
        print(f"Spent: ${total:.2f}")
        print(f"Remaining: ${remaining:.2f} ({percent_left:.1f}%)")
        
        if percent_left < 20:
            color_print("🚨 CRITICAL: Less than 20% remaining!", 'red', bold=True)
        elif percent_left < 50:
            color_print("⚠️  Caution: Less than 50% remaining", 'yellow')
        else:
            color_print("✅ Budget looking good!", 'green')
    
    input("\nPress Enter to continue...")

def export_csv(tracker: ExpenseTracker):
    try:
        with open(CSV_FILE, 'w') as f:
            f.write("date,amount,category,description\n")
            for e in tracker.expenses:
                f.write(f"{e['date']},{e['amount']:.2f},{e['category']},{e['description']}\n")
        color_print(f"✅ Exported to {CSV_FILE}", 'green')
    except Exception as e:
        print(f"Export failed: {e}")
    input("\nPress Enter to continue...")

def reset_data(tracker: ExpenseTracker):
    confirm = input("Are you sure you want to reset ALL data? (yes/no): ").lower()
    if confirm == 'yes':
        tracker.expenses = []
        tracker.monthly_budget = 0.0
        tracker.save_data()
        color_print("✅ Data reset successfully!", 'green')
    input("\nPress Enter to continue...")

def main_menu_loop():
    tracker = ExpenseTracker()
    menu_options = [
        "1. 💕 Add Expense",
        "2. 📊 View Summary", 
        "3. 📈 Category Breakdown",
        "4. 💳 Budget Check/Set",
        "5. 💾 Export CSV",
        "6. 📥 Import JSON (auto)",
        "7. 🗑️ Reset Data",
        "8. ❌ Quit"
    ]
    
    while True:
        print_menu(menu_options)
        
        choice = input("Enter choice (1-8) or 'q' to quit: ").strip().lower()
        
        if choice in ['q', '8']:
            color_print("Happy Valentine's Day! 💖", 'red')
            break
        elif choice == '1':
            add_expense_menu(tracker)
        elif choice == '2':
            view_summary(tracker)
        elif choice == '3':
            category_breakdown(tracker)
        elif choice == '4':
            if tracker.monthly_budget == 0:
                set_budget(tracker)
            else:
                budget_check(tracker)
        elif choice == '5':
            export_csv(tracker)
        elif choice == '6':
            tracker.load_data()
            color_print("✅ Data reloaded from file", 'green')
            input("\nPress Enter to continue...")
        elif choice == '7':
            reset_data(tracker)
        else:
            color_print("Invalid choice. Try again.", 'yellow')
            input("Press Enter to continue...")

def run_tests():
    tracker = ExpenseTracker()
    print("🧪 Running tests...")
    
    # Test add expense
    tracker.expenses = []
    success = tracker.add_expense("2026-02-14", 25.50, "Romance", "Test")
    assert success and len(tracker.expenses) == 1
    print("✅ Add expense test passed")
    
    # Test summary
    total = tracker.get_total_spent()
    assert abs(total - 25.50) < 0.01
    print("✅ Summary test passed")
    
    # Test export
    export_csv(tracker)
    assert os.path.exists(CSV_FILE)
    print("✅ Export test passed")
    
    print("All tests passed! 🎉")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        run_tests()
    else:
        main_menu_loop()