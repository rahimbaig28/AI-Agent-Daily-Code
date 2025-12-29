# Auto-generated via Perplexity on 2025-12-29T08:29:52.559424Z
import json
import datetime
import os
import sys
import collections
import urllib.parse
import webbrowser
import hashlib
import base64

DATA_FILE = 'cashflow.json'
PRINT_FILE = 'cashflow_print.txt'
SAMPLE_DATA = [
    {'date': '2025-12-01', 'amount': 1000.0, 'category': 'income', 'description': 'Salary'},
    {'date': '2025-12-02', 'amount': -300.0, 'category': 'food', 'description': 'Groceries'},
    {'date': '2025-12-03', 'amount': -800.0, 'category': 'rent', 'description': 'Monthly rent'},
    {'date': '2025-12-05', 'amount': -150.0, 'category': 'utils', 'description': 'Electricity'}
]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        return []
    except:
        print("Error loading data, starting fresh.")
        return []

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except:
        print("Error saving data!")
        return False

def get_today():
    return datetime.date.today().isoformat()

def validate_date(date_str):
    try:
        datetime.date.fromisoformat(date_str)
        return True
    except:
        return False

def print_header():
    clear_screen()
    print("""
$$$$$$$\\  $$$$$$$$\\ $$\\      $$\\ $$$$$$$$\\  $$$$$$\\ 
$$  __$$\\ $$  _____|$$ |     $$ |$$  _____|$$  __$$\\ 
$$ |  $$ |$$ |      $$ |     $$ |$$ |      $$ /  $$ |
$$$$$$$  |$$$$$\\    $$$$$\\   $$$$$\\$$$$$\\  $$$$$$$$ |
$$  __$$< $$  __|   $$  __| $$  __|$$  __| $$  __$$ |
$$ |  $$ |$$ |      $$ |    $$ |   $$ |    $$ |  $$ |
$$ |  $$ |$$$$$$$\\  $$ |    $$ |   $$$$$$$\\$$ |  $$ |
\\__|  \\__|\\_______|\\__|    \\__|   \\_______|\\__|  \\__|
                                                    
Plan Your Future
    """)

def add_transaction(data):
    date = input(f"Date (YYYY-MM-DD, default {get_today()}): ").strip()
    if not date:
        date = get_today()
    while not validate_date(date):
        print("Invalid date format. Use YYYY-MM-DD.")
        date = input("Date: ").strip()
    
    while True:
        try:
            amount = float(input("Amount (+ income/- expense): "))
            break
        except ValueError:
            print("Invalid amount. Enter a number.")
    
    category = input("Category (food/rent/utils/income/other): ").strip().lower()
    if category not in ['food', 'rent', 'utils', 'income', 'other']:
        category = 'other'
    
    desc = input("Description: ").strip()
    
    data.append({'date': date, 'amount': amount, 'category': category, 'description': desc})
    save_data(data)
    print("Transaction added!")

def get_balance(data):
    return sum(t['amount'] for t in data)

def get_summary(data):
    if not data:
        return "No transactions yet."
    
    balance = get_balance(data)
    cat_counter = collections.Counter()
    income_total = 0
    expense_total = 0
    
    for t in data:
        cat = t['category']
        amt = t['amount']
        cat_counter[cat] += abs(amt)
        if amt > 0:
            income_total += amt
        else:
            expense_total += abs(amt)
    
    print(f"{'='*50}")
    print(f"{'Current Balance:':<20} ${balance:>10.2f}")
    print(f"{'Total Income:':<20} ${income_total:>10.2f}")
    print(f"{'Total Expense:':<20} ${-expense_total:>10.2f}")
    print(f"{'='*50}")
    print(f"{'Category':<12} {'Amount':>10}")
    print(f"{'-'*25}")
    for cat, amt in cat_counter.most_common():
        print(f"{cat.capitalize():<12} ${amt:>10.2f}")
    print(f"{'='*50}")

def forecast(balance):
    try:
        monthly_target = float(input("Monthly income target: $"))
        days_30 = 30
        days_90 = 90
        daily_net = balance / max(len([t for t in data if t['date']]), 1) if data else 0
        
        proj_30 = balance + (daily_net * days_30)
        proj_90 = balance + (daily_net * days_90)
        
        print(f"\n30-day projection: ${proj_30:.2f}")
        print(f"90-day projection: ${proj_90:.2f}")
        
        if balance < 0:
            days_to_breakeven = abs(balance / max(daily_net, 0.01))
            print(f"Days to break even: {days_to_breakeven:.1f}")
    except ValueError:
        print("Invalid input.")

def ascii_pie_chart(data):
    if not data:
        print("No data for pie chart.")
        return
    
    cat_counter = collections.Counter()
    for t in data:
        cat_counter[t['category']] += abs(t['amount'])
    
    total = sum(cat_counter.values())
    if total == 0:
        return
    
    print("\nCategory Pie Chart (ASCII):")
    print("".join(["#####"] * 20))
    for cat, amt in cat_counter.most_common():
        pct = (amt / total) * 100
        bars = int((amt / total) * 20)
        print(f"{cat.capitalize():<10}: {'█' * bars} {pct:>5.1f}%")
    print("".join(["#####"] * 20))

def print_friendly(data):
    balance = get_balance(data)
    cat_counter = collections.Counter(abs(t['amount']) for t in data for cat in [t['category']])
    
    content = f"CashFlow Forecast Pro - Summary\n"
    content += f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    content += f"Current Balance: ${balance:.2f}\n\n"
    content += f"Category Breakdown:\n"
    for cat, amt in cat_counter.most_common():
        content += f"{cat.capitalize()}: ${amt:.2f}\n"
    
    daily_net = balance / max(len(data), 1) if data else 0
    proj_30 = balance + (daily_net * 30)
    proj_90 = balance + (daily_net * 90)
    content += f"\nForecast:\n"
    content += f"30-day projection: ${proj_30:.2f}\n"
    content += f"90-day projection: ${proj_90:.2f}\n"
    
    try:
        with open(PRINT_FILE, 'w') as f:
            f.write(content)
        print(f"Report saved to {PRINT_FILE}")
        
        choice = input("Open in default app? (y/n): ").strip().lower()
        if choice == 'y':
            webbrowser.open('file://' + os.path.abspath(PRINT_FILE))
    except:
        print("Error generating print file.")

def share_state(data):
    data_sorted = sorted(data, key=lambda x: (x['date'], x['amount'], x['category'], x['description']))
    json_str = json.dumps(data_sorted, sort_keys=True)
    hash_obj = hashlib.sha256(json_str.encode()).digest()
    b64_hash = base64.urlsafe_b64encode(hash_obj).decode().rstrip('=')
    share_url = f"cashflow://{urllib.parse.quote(b64_hash)}"
    print(f"Share URL: {share_url}")
    print("Copy this URL to share your cashflow state!")
    return share_url

# Main program
data = load_data()
if not data:
    data = SAMPLE_DATA[:]
    save_data(data)
    print("Sample data loaded!")

while True:
    print_header()
    print("\n1. Add transaction")
    print("2. View summary")
    print("3. Forecast")
    print("4. Category pie chart")
    print("5. Print-friendly report")
    print("6. Share state")
    print("q. Quit")
    
    choice = input("\nChoose (1-6,q): ").strip().lower()
    
    if choice == '1':
        add_transaction(data)
        input("\nPress Enter...")
    elif choice == '2':
        get_summary(data)
        input("\nPress Enter...")
    elif choice == '3':
        print(f"Current balance: ${get_balance(data):.2f}")
        forecast(data)
        input("\nPress Enter...")
    elif choice == '4':
        ascii_pie_chart(data)
        input("\nPress Enter...")
    elif choice == '5':
        print_friendly(data)
        input("\nPress Enter...")
    elif choice == '6':
        share_state(data)
        input("\nPress Enter...")
    elif choice == 'q':
        save_data(data)
        print("Data saved. Goodbye!")
        sys.exit(0)
    else:
        input("Invalid choice. Press Enter...")