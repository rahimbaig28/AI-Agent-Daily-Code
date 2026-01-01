# Auto-generated via Perplexity on 2026-01-01T08:27:24.377170Z
import json
import datetime
import hashlib
import os
import sys
import tempfile
import shutil
from collections import defaultdict, Counter

DATA_FILE = 'cashflow.json'
CATEGORIES = ['Food', 'Rent', 'Salary', 'Fun', 'Other']

def load_data():
    if not os.path.exists(DATA_FILE):
        return {'transactions': [], 'goals': {}}
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'transactions': [], 'goals': {}}

def save_data(data):
    tmp_fd, tmp_path = tempfile.mkstemp()
    try:
        with os.fdopen(tmp_fd, 'w') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, DATA_FILE)
    except:
        os.unlink(tmp_path)
        raise

def get_current_month():
    today = datetime.date.today()
    return today.strftime('%Y-%m')

def parse_date(date_str):
    if not date_str:
        return datetime.date.today().isoformat()
    try:
        return datetime.datetime.fromisoformat(date_str).date().isoformat()
    except:
        raise ValueError("Invalid date format. Use YYYY-MM-DD")

def get_goal_month():
    today = datetime.date.today()
    return today.strftime('%Y-%m')

def prompt_date():
    while True:
        date_str = input("Date (YYYY-MM-DD or Enter for today): ").strip()
        try:
            return parse_date(date_str)
        except ValueError as e:
            print(e)

def prompt_amount():
    while True:
        try:
            amt = float(input("Amount (>0): "))
            if amt > 0:
                return amt
            print("Amount must be positive")
        except ValueError:
            print("Invalid amount")

def prompt_category():
    print("Categories:", ', '.join(CATEGORIES))
    while True:
        cat = input("Category: ").strip().title()
        if cat in CATEGORIES:
            return cat
        matches = [c for c in CATEGORIES if c.lower().startswith(cat.lower())]
        if matches:
            return matches[0]
        print("Invalid category")

def add_transaction(data):
    txn = {
        'date': prompt_date(),
        'type': input("Type (income/expense): ").strip().lower(),
        'amount': prompt_amount(),
        'category': prompt_category(),
        'description': input("Description: ").strip(),
        'goal_month': get_goal_month()
    }
    if txn['type'] not in ['income', 'expense']:
        print("Type must be 'income' or 'expense'")
        return
    data['transactions'].append(txn)
    print("Transaction added")

def set_goal(data):
    month = input("Goal month (YYYY-MM): ").strip()
    if not month or len(month) != 7 or month[4] != '-':
        print("Invalid format")
        return
    try:
        target = float(input("Target savings: "))
        if target <= 0:
            print("Target must be positive")
            return
        data['goals'][month] = target
        print(f"Goal set for {month}: ${target:,.2f}")
    except ValueError:
        print("Invalid amount")

def get_month_key(txn):
    return txn['date'][:7]

def view_summary(data):
    transactions = data['transactions']
    if not transactions:
        print("No transactions")
        return
    
    current_month = get_current_month()
    month_data = defaultdict(lambda: {'income': 0, 'expense': 0})
    
    for txn in transactions:
        month = get_month_key(txn)
        month_data[month][txn['type']] += txn['amount']
    
    print(f"\n{'Month':<12} {'Income':>10} {'Expense':>10} {'Net':>10}")
    print("-" * 45)
    
    for month in sorted(month_data):
        inc = month_data[month]['income']
        exp = month_data[month]['expense']
        net = inc - exp
        goal = data['goals'].get(month, 0)
        pct = (net/goal*100) if goal else 0
        print(f"{month:<12} ${inc:>9,.2f} ${exp:>9,.2f} ${net:>9,.2f}", end="")
        if goal:
            print(f" ({pct:>5.1f}%)")
        else:
            print()
    
    # Category bars for current month
    current_txns = [t for t in transactions if get_month_key(t) == current_month]
    cat_totals = Counter(t['category'] for t in current_txns)
    if cat_totals:
        print("\nCategory breakdown (current month):")
        total = sum(cat_totals.values())
        max_name = max(len(c) for c in cat_totals)
        for cat, amt in cat_totals.most_common():
            pct = amt/total*100
            bar_len = int(pct * 50 / 100)
            bar = '#' * bar_len
            print(f"{cat:<{max_name}} |{bar:<50}| {amt:>6} ({pct:>5.1f}%)")

def print_report(data):
    transactions = data['transactions']
    if not transactions:
        print("No transactions")
        return
    
    print("\n" + "="*80)
    print("CASHFLOW REPORT")
    print("="*80)
    
    month_data = defaultdict(lambda: {'income': 0, 'expense': 0})
    cat_data = Counter()
    
    for txn in transactions:
        month = get_month_key(txn)
        month_data[month][txn['type']] += txn['amount']
        cat_data[txn['category']] += txn['amount']
    
    print(f"\n{'Month':<12} {'Income':>12} {'Expense':>12} {'Net':>12}")
    print("-"*50)
    total_inc, total_exp, total_net = 0, 0, 0
    for month in sorted(month_data):
        inc = month_data[month]['income']
        exp = month_data[month]['expense']
        net = inc - exp
        total_inc += inc
        total_exp += exp
        total_net += net
        print(f"{month:<12} ${inc:>11,.2f} ${exp:>11,.2f} ${net:>11,.2f}")
    
    print("-"*50)
    print(f"TOTALS{'':<12} ${total_inc:>11,.2f} ${total_exp:>11,.2f} ${total_net:>11,.2f}")
    
    print(f"\nTop categories:")
    print(f"{'Category':<15} {'Amount':>10}")
    print("-"*27)
    for cat, amt in cat_data.most_common(5):
        print(f"{cat:<15} ${amt:>9,.2f}")

def share_hash(data):
    data_str = json.dumps(data, sort_keys=True)
    hash_obj = hashlib.sha256(data_str.encode()).digest()
    hash_b64 = base64.urlsafe_b64encode(hash_obj).decode()[:8]
    print(f"Share: cashflow.app/#{hash_b64}")

def main():
    data = load_data()
    
    while True:
        print("\n1. Add transaction")
        print("2. View summary")
        print("3. Set goal")
        print("4. Print report")
        print("5. Share hash")
        print("6. Quit")
        
        choice = input("\nChoice: ").strip()
        
        try:
            if choice == '1':
                add_transaction(data)
            elif choice == '2':
                view_summary(data)
            elif choice == '3':
                set_goal(data)
            elif choice == '4':
                print_report(data)
            elif choice == '5':
                share_hash(data)
            elif choice == '6':
                save_data(data)
                print("Data saved. Goodbye!")
                break
            else:
                print("Invalid choice")
            
            save_data(data)
        except KeyboardInterrupt:
            print("\nSaving...")
            save_data(data)
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()