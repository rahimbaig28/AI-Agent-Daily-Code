# Auto-generated via Perplexity on 2026-02-09T05:44:24.898213Z
#!/usr/bin/env python3
import os
import sys
import json
import csv
import datetime
from pathlib import Path
import argparse

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'
BOLD = '\033[1m'

DATA_FILE = Path(__file__).parent / "invoices.json"
BACKUP_FILE = Path(__file__).parent / "invoices.json.bak"

def load_data():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            print(f"{RED}Error loading data, starting fresh{END}")
    return []

def save_data(data):
    if DATA_FILE.exists():
        DATA_FILE.replace(BACKUP_FILE)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_next_id(data):
    return max([inv.get('id', 0) for inv in data] or [0]) + 1

def validate_date(date_str):
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except:
        return False

def parse_date(date_str):
    if not date_str or date_str.lower() == 'today':
        return datetime.date.today().isoformat()
    if validate_date(date_str):
        return date_str
    print(f"{RED}Invalid date format. Use YYYY-MM-DD or 'today'{END}")
    return None

def get_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except:
            print(f"{RED}Enter valid number{END}")

def multi_line_input(prompt):
    print(prompt)
    lines = []
    print("(Enter blank line to finish)")
    while True:
        line = input()
        if not line.strip():
            break
        lines.append(line)
    return '\n'.join(lines)

def print_table(invoices, title="Invoices"):
    if not invoices:
        print(f"{YELLOW}No invoices found{END}")
        return
    
    print(f"\n{BOLD}{title}{END}")
    print("-" * 80)
    print(f"{BOLD}{'ID':>4} {'Client':<20} {'Amount':>10} {'Date':<12} {'Description':<25}{END}")
    print("-" * 80)
    
    total = 0
    for inv in invoices:
        desc = (inv['description'][:22] + "...") if len(inv['description']) > 22 else inv['description']
        print(f"{inv['id']:>4} {inv['client']:<20.19} {inv['amount']:>9.2f} {inv['date']:<12} {desc:<25}")
        total += inv['amount']
    
    print("-" * 80)
    print(f"{BOLD}{'TOTAL':>36} {total:>9.2f}{END}")
    print()

def print_menu(options):
    for i, opt in enumerate(options, 1):
        print(f"{i}. {opt}")
    print("Q. Quit")

def add_invoice(data):
    client = input("Client name: ").strip()
    if not client:
        print(f"{RED}Client name required{END}")
        return
    
    amount = get_float("Amount: ")
    if amount <= 0:
        print(f"{RED}Amount must be > 0{END}")
        return
    
    date_input = input("Date (YYYY-MM-DD or 'today'): ").strip()
    date = parse_date(date_input)
    if not date:
        return
    
    desc = multi_line_input("Description:")
    
    inv = {
        'id': get_next_id(data),
        'client': client,
        'amount': amount,
        'date': date,
        'description': desc
    }
    data.append(inv)
    save_data(data)
    print(f"{GREEN}Invoice {inv['id']} added{END}")

def list_invoices(data):
    if not data:
        print(f"{YELLOW}No invoices{END}")
        return
    
    # Sort by date descending
    sorted_data = sorted(data, key=lambda x: x['date'], reverse=True)
    print_table(sorted_data)

def search_invoices(data):
    if not data:
        print(f"{YELLOW}No invoices{END}")
        return
    
    print("1. Search by client")
    print("2. Search by date range")
    choice = input("Choose (1-2): ").strip().lower()
    
    if choice == '1':
        client = input("Client name (partial): ").strip().lower()
        matches = [inv for inv in data if client in inv['client'].lower()]
    elif choice == '2':
        start = input("Start date (YYYY-MM-DD): ").strip()
        end = input("End date (YYYY-MM-DD): ").strip()
        if validate_date(start) and validate_date(end):
            matches = [inv for inv in data 
                      if start <= inv['date'] <= end]
        else:
            print(f"{RED}Invalid dates{END}")
            return
    else:
        return
    
    print_table(matches, f"Search Results ({len(matches)} found)")

def export_csv(data, filename=None):
    if not data:
        print(f"{YELLOW}No invoices to export{END}")
        return
    
    if not filename:
        today = datetime.date.today().strftime("%Y%m%d")
        filename = f"invoices_export_{today}.csv"
    
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'client', 'amount', 'date', 'description'])
        writer.writeheader()
        writer.writerows(data)
    
    print(f"{GREEN}Exported to {filename}{END}")

def delete_invoice(data):
    if not data:
        print(f"{YELLOW}No invoices{END}")
        return
    
    print_table(data, "Select invoice to delete:")
    try:
        inv_id = int(input("Invoice ID to delete: "))
        inv = next((i for i, inv in enumerate(data) if inv['id'] == inv_id), None)
        if inv:
            confirm = input(f"Delete invoice {inv_id} ({inv['client']})? (y/N): ").strip().lower()
            if confirm == 'y':
                data.pop(inv[0])
                save_data(data)
                print(f"{GREEN}Invoice {inv_id} deleted{END}")
            else:
                print("Cancelled")
        else:
            print(f"{RED}Invoice not found{END}")
    except ValueError:
        print(f"{RED}Invalid ID{END}")

def main_menu():
    data = load_data()
    
    # Add sample data on first run
    if not data:
        samples = [
            {'id': 1, 'client': 'Acme Corp', 'amount': 1500.00, 'date': '2026-02-01', 'description': 'Consulting services'},
            {'id': 2, 'client': 'Beta LLC', 'amount': 850.50, 'date': '2026-02-05', 'description': 'Software license'},
            {'id': 3, 'client': 'Gamma Inc', 'amount': 2200.75, 'date': '2026-02-08', 'description': 'Web development'}
        ]
        data.extend(samples)
        save_data(data)
        print(f"{GREEN}Sample invoices added{END}")
    
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print(f"{BOLD}=== Invoice Batch Organizer ==={END}")
        print(f"Total invoices: {len(data)}")
        print()
        
        print_menu([
            "1. Add Invoice",
            "2. List Invoices", 
            "3. Search Invoices",
            "4. Export CSV",
            "5. Delete Invoice",
            "6. Quit"
        ])
        
        choice = input("\nChoose: ").strip().lower()
        
        if choice == '1':
            add_invoice(data)
            input("\nPress Enter...")
        elif choice == '2':
            list_invoices(data)
            input("\nPress Enter...")
        elif choice == '3':
            search_invoices(data)
            input("\nPress Enter...")
        elif choice == '4':
            export_csv(sorted(data, key=lambda x: x['date'], reverse=True))
            input("\nPress Enter...")
        elif choice == '5':
            delete_invoice(data)
            input("\nPress Enter...")
        elif choice in ('6', 'q'):
            print(f"{GREEN}Goodbye!{END}")
            break
        else:
            print(f"{RED}Invalid choice{END}")
            input("\nPress Enter...")

def batch_add(client, amount, date, desc):
    data = load_data()
    date = parse_date(date)
    if not date:
        return 1
    
    try:
        amount = float(amount)
        if amount <= 0:
            return 1
    except:
        return 1
    
    inv = {
        'id': get_next_id(data),
        'client': client,
        'amount': amount,
        'date': date,
        'description': desc
    }
    data.append(inv)
    save_data(data)
    print(f"{GREEN}Added invoice {inv['id']}{END}")
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Invoice Batch Organizer")
    parser.add_argument('--export', action='store_true', help="Export all invoices and quit")
    parser.add_argument('--add', nargs=4, metavar=('client', 'amount', 'date', 'desc'),
                       help="Batch add: client amount date description")
    
    args = parser.parse_args()
    
    if args.add:
        sys.exit(batch_add(*args.add))
    elif args.export:
        data = load_data()
        export_csv(data)
        sys.exit(0)
    else:
        main_menu()