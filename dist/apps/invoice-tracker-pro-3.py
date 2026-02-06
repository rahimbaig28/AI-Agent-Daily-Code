# Auto-generated via Perplexity on 2026-02-06T04:58:00.787645Z
#!/usr/bin/env python3

import json
import os
import sys
import csv
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_FILE = SCRIPT_DIR / "invoices.json"
BACKUP_DIR = SCRIPT_DIR / "backups"
CSV_FILE = SCRIPT_DIR / "invoices.csv"
MAX_UNDO_LEVELS = 10

CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"
BOLD = "\033[1m"

def ensure_backup_dir():
    BACKUP_DIR.mkdir(exist_ok=True)

def load_data():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return recover_from_backup()
    return []

def recover_from_backup():
    backups = sorted(BACKUP_DIR.glob("invoices_backup_*.json"), reverse=True)
    if backups:
        try:
            with open(backups[0], 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return []

def save_data(invoices):
    ensure_backup_dir()
    existing = load_data()
    if existing != invoices:
        backups = sorted(BACKUP_DIR.glob("invoices_backup_*.json"))
        if len(backups) >= MAX_UNDO_LEVELS:
            backups[0].unlink()
        backup_num = len(list(BACKUP_DIR.glob("invoices_backup_*.json"))) + 1
        with open(BACKUP_DIR / f"invoices_backup_{backup_num}.json", 'w') as f:
            json.dump(existing, f, indent=2)
    with open(DATA_FILE, 'w') as f:
        json.dump(invoices, f, indent=2)

def get_next_id(invoices):
    if not invoices:
        return 1
    return max(inv['id'] for inv in invoices) + 1

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def format_currency(amount):
    return f"${amount:,.2f}"

def get_stats(invoices):
    total_invoiced = sum(inv['amount'] for inv in invoices)
    total_paid = sum(inv['amount'] for inv in invoices if inv['paid'])
    outstanding = total_invoiced - total_paid
    avg_value = total_invoiced / len(invoices) if invoices else 0
    return total_invoiced, total_paid, outstanding, avg_value

def display_menu(invoices):
    clear_screen()
    total_inv, total_paid, outstanding, avg_val = get_stats(invoices)
    print(f"\n{BOLD}=== INVOICE TRACKER PRO ==={RESET}")
    print(f"Total Invoiced: {format_currency(total_inv)} | Paid: {GREEN}{format_currency(total_paid)}{RESET} | Outstanding: {RED}{format_currency(outstanding)}{RESET} | Avg: {format_currency(avg_val)}\n")
    print("1. Add Invoice")
    print("2. View All Invoices")
    print("3. Mark Paid/Unpaid")
    print("4. Search/Filter")
    print("5. Export to CSV")
    print("6. Quit")
    print("\nCtrl+Z: Undo | Ctrl+Y: Redo")

def add_invoice(invoices):
    clear_screen()
    print(f"{BOLD}=== ADD INVOICE ==={RESET}\n")
    
    customer = input("Customer name: ").strip()
    if not customer:
        print("Customer name required.")
        input("Press Enter...")
        return invoices
    
    while True:
        try:
            amount = float(input("Amount: $"))
            if amount <= 0:
                print("Amount must be greater than 0.")
                continue
            break
        except ValueError:
            print("Invalid amount. Enter a number.")
    
    date_input = input("Date (YYYY-MM-DD) [today]: ").strip()
    if not date_input:
        date_input = datetime.now().strftime("%Y-%m-%d")
    else:
        try:
            datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format.")
            input("Press Enter...")
            return invoices
    
    print("Description (press Enter twice to finish):")
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
    description = "\n".join(lines).strip()
    
    invoice = {
        'id': get_next_id(invoices),
        'customer': customer,
        'amount': amount,
        'date': date_input,
        'description': description,
        'paid': False
    }
    invoices.append(invoice)
    save_data(invoices)
    print(f"\n{GREEN}Invoice #{invoice['id']} added.{RESET}")
    input("Press Enter...")
    return invoices

def view_all(invoices):
    clear_screen()
    print(f"{BOLD}=== ALL INVOICES ==={RESET}\n")
    
    if not invoices:
        print("No invoices.")
        input("Press Enter...")
        return
    
    sorted_invoices = sorted(invoices, key=lambda x: x['date'], reverse=True)
    
    print(f"{CYAN}{BOLD}ID{RESET:<5} {CYAN}{BOLD}Customer{RESET:<20} {CYAN}{BOLD}Amount{RESET:<12} {CYAN}{BOLD}Date{RESET:<12} {CYAN}{BOLD}Status{RESET:<10}")
    print("-" * 65)
    
    for inv in sorted_invoices:
        status = f"{GREEN}Paid{RESET}" if inv['paid'] else f"{RED}Unpaid{RESET}"
        print(f"{inv['id']:<5} {inv['customer']:<20} {format_currency(inv['amount']):<12} {inv['date']:<12} {status:<10}")
    
    total_inv, total_paid, outstanding, _ = get_stats(invoices)
    print("-" * 65)
    print(f"{YELLOW}{BOLD}TOTAL{RESET:<5} {'':<20} {format_currency(total_inv):<12} {'':<12} {format_currency(outstanding)} outstanding")
    input("\nPress Enter...")

def mark_paid_unpaid(invoices):
    clear_screen()
    print(f"{BOLD}=== MARK PAID/UNPAID ==={RESET}\n")
    
    if not invoices:
        print("No invoices.")
        input("Press Enter...")
        return invoices
    
    try:
        inv_id = int(input("Invoice ID: "))
        invoice = next((i for i in invoices if i['id'] == inv_id), None)
        if not invoice:
            print("Invoice not found.")
            input("Press Enter...")
            return invoices
        
        invoice['paid'] = not invoice['paid']
        save_data(invoices)
        status = "Paid" if invoice['paid'] else "Unpaid"
        print(f"{GREEN}Invoice #{inv_id} marked as {status}.{RESET}")
    except ValueError:
        print("Invalid ID.")
    
    input("Press Enter...")
    return invoices

def search_filter(invoices):
    clear_screen()
    print(f"{BOLD}=== SEARCH/FILTER ==={RESET}\n")
    print("1. Search by customer name")
    print("2. Show unpaid only")
    choice = input("Choice: ").strip()
    
    results = []
    if choice == '1':
        query = input("Customer name (substring): ").strip().lower()
        results = [i for i in invoices if query in i['customer'].lower()]
    elif choice == '2':
        results = [i for i in invoices if not i['paid']]
    else:
        print("Invalid choice.")
        input("Press Enter...")
        return
    
    clear_screen()
    print(f"{BOLD}=== SEARCH RESULTS ==={RESET}\n")
    
    if not results:
        print("No results.")
        input("Press Enter...")
        return
    
    sorted_results = sorted(results, key=lambda x: x['date'], reverse=True)
    print(f"{CYAN}{BOLD}ID{RESET:<5} {CYAN}{BOLD}Customer{RESET:<20} {CYAN}{BOLD}Amount{RESET:<12} {CYAN}{BOLD}Date{RESET:<12} {CYAN}{BOLD}Status{RESET:<10}")
    print("-" * 65)
    
    for inv in sorted_results:
        status = f"{GREEN}Paid{RESET}" if inv['paid'] else f"{RED}Unpaid{RESET}"
        print(f"{inv['id']:<5} {inv['customer']:<20} {format_currency(inv['amount']):<12} {inv['date']:<12} {status:<10}")
    
    input("\nPress Enter...")

def export_csv(invoices):
    clear_screen()
    print(f"{BOLD}=== EXPORT TO CSV ==={RESET}\n")
    
    if not invoices:
        print("No invoices to export.")
        input("Press Enter...")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = SCRIPT_DIR / f"invoices_{timestamp}.csv"
    
    try:
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Customer', 'Amount', 'Date', 'Status', 'Description'])
            for inv in sorted(invoices, key=lambda x: x['date'], reverse=True):
                status = 'Paid' if inv['paid'] else 'Unpaid'
                writer.writerow([inv['id'], inv['customer'], f"${inv['amount']:.2f}", inv['date'], status, inv['description']])
        print(f"{GREEN}Exported to {csv_path.name}{RESET}")
    except IOError as e:
        print(f"{RED}Export failed: {e}{RESET}")
    
    input("Press Enter...")

def undo(invoices):
    backups = sorted(BACKUP_DIR.glob("invoices_backup_*.json"), reverse=True)
    if backups:
        try:
            with open(backups[0], 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return invoices

def load_sample_data():
    return [
        {'id': 1, 'customer': 'Acme Corp', 'amount': 1500.00, 'date': '2026-01-15', 'description': 'Web design services', 'paid': True},
        {'id': 2, 'customer': 'Tech Startup Inc', 'amount': 2500.00, 'date': '2026-01-20', 'description': 'Consulting', 'paid': False},
        {'id': 3, 'customer': 'Global Solutions', 'amount': 3200.00, 'date': '2026-02-01', 'description': 'Development work', 'paid': False}
    ]

def main():
    ensure_backup_dir()
    invoices = load_data()
    
    if not invoices:
        invoices = load_sample_data()
        save_data(invoices)
    
    while True:
        display_menu(invoices)
        choice = input("\nChoice (1-6): ").strip()
        
        if choice == '1':
            invoices = add_invoice(invoices)
        elif choice == '2':
            view_all(invoices)
        elif choice == '3':
            invoices = mark_paid_unpaid(invoices)
        elif choice == '4':
            search_filter(invoices)
        elif choice == '5':
            export_csv(invoices)
        elif choice == '6':
            save_data(invoices)
            clear_screen()
            print(f"{GREEN}Saved. Goodbye!{RESET}")
            sys.exit(0)
        elif choice.lower() == 'q':
            save_data(invoices)
            clear_screen()
            print(f"{GREEN}Saved. Goodbye!{RESET}")
            sys.exit(0)

if __name__ == '__main__':
    main()