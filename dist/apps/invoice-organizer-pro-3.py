# Auto-generated via Perplexity on 2026-02-06T17:03:20.551438Z
#!/usr/bin/env python3
import json
import os
import sys
import datetime
import pathlib
import csv
import hashlib
import argparse
import base64
import shutil
from typing import List, Dict, Any

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

DATA_DIR = pathlib.Path.home() / ".invoice_data"
DATA_FILE = DATA_DIR / "invoice_data.json"
BACKUP_FILE = DATA_DIR / "invoice_data_backup.json"

def get_terminal_width():
    try:
        return os.get_terminal_size().columns
    except:
        return 80

def ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)

def load_invoices() -> List[Dict[str, Any]]:
    ensure_data_dir()
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return []

def save_invoices(invoices: List[Dict[str, Any]]):
    ensure_data_dir()
    shutil.copy2(DATA_FILE, BACKUP_FILE) if DATA_FILE.exists() else None
    with open(DATA_FILE, 'w') as f:
        json.dump(invoices, f, indent=2)

def generate_invoice_id(client: str, due_date: str) -> str:
    return hashlib.sha256(f"{client}{due_date}".encode()).hexdigest()[:8]

def parse_date(date_str: str) -> datetime.date:
    return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

def is_overdue(invoice: Dict[str, Any]) -> bool:
    if invoice.get('paid_date'):
        return False
    today = datetime.date.today()
    due = parse_date(invoice['due_date'])
    return due < today

def days_overdue(invoice: Dict[str, Any]) -> int:
    if invoice.get('paid_date') or not is_overdue(invoice):
        return 0
    return (datetime.date.today() - parse_date(invoice['due_date'])).days

def is_due_this_week(invoice: Dict[str, Any]) -> bool:
    if invoice.get('paid_date'):
        return False
    today = datetime.date.today()
    due = parse_date(invoice['due_date'])
    return today <= due <= today + datetime.timedelta(days=7-today.weekday())

def calculate_stats(invoices: List[Dict[str, Any]]):
    unpaid = [i for i in invoices if not i.get('paid_date')]
    overdue = [i for i in unpaid if is_overdue(i)]
    total_unpaid = sum(float(i['amount']) for i in unpaid)
    overdue_total = sum(float(i['amount']) for i in overdue)
    avg_days_overdue = sum(days_overdue(i) for i in overdue) / len(overdue) if overdue else 0
    return {
        'total_unpaid': total_unpaid,
        'overdue_total': overdue_total,
        'avg_days_overdue': avg_days_overdue,
        'unpaid_count': len(unpaid),
        'overdue_count': len(overdue)
    }

def print_header(stats: Dict[str, Any]):
    print(f"\n{BOLD}📊 Invoice Organizer Pro{CRESET}")
    print(f"💰 Total Unpaid: ${stats['total_unpaid']:.2f} | 🚨 Overdue: ${stats['overdue_total']:.2f} ({stats['overdue_count']})")
    print(f"📅 Avg Days Overdue: {stats['avg_days_overdue']:.1f} | 📋 Total Invoices: {len(load_invoices())}")
    print("-" * get_terminal_width())

def print_table(invoices: List[Dict[str, Any]], width: int):
    if not invoices:
        print("No invoices found.")
        return
    
    header = f"{'ID':<10} {'Client':<20} {'Amount':>10} {'Due':<12} {'Status':<15} {'Days Late'}"
    print(header)
    print("-" * len(header))
    
    for inv in invoices:
        id_ = inv['invoice_id'][:8]
        client = inv['client'][:19]
        amt = f"${float(inv['amount']):>9.2f}"
        due = inv['due_date']
        
        if inv.get('paid_date'):
            status = "✅ PAID"
            days_late = ""
            color = GREEN
        elif is_overdue(inv):
            status = "🚨 OVERDUE"
            days_late = str(days_overdue(inv))
            color = RED
        else:
            status = "⏳ PENDING"
            days_late = ""
            color = CYAN
            
        line = f"{id_:<10} {client:<20} {amt:>10} {due:<12} {status:<15} {days_late}"
        print(color + line + RESET)

def add_test_invoices(invoices: List[Dict[str, Any]]):
    if not invoices:
        today = datetime.date.today()
        test_invoices = [
            {
                'invoice_id': generate_invoice_id('Test Client A', '2026-02-05'),
                'client': 'Test Client A',
                'amount': '1500.00',
                'due_date': '2026-02-05',  # Yesterday
            },
            {
                'invoice_id': generate_invoice_id('Test Client B', '2026-02-10'),
                'client': 'Test Client B',
                'amount': '2500.50',
                'due_date': '2026-02-10',
            },
            {
                'invoice_id': generate_invoice_id('Test Client C', '2026-02-12'),
                'client': 'Test Client C',
                'amount': '800.75',
                'due_date': '2026-02-12',
            }
        ]
        save_invoices(test_invoices)
        print(f"{GREEN}✅ Added 3 test invoices (1 overdue)!{RESET}")

def main_menu():
    invoices = load_invoices()
    if not invoices:
        add_test_invoices(invoices)
        invoices = load_invoices()
    
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        stats = calculate_stats(invoices)
        print_header(stats)
        
        if datetime.date.today().weekday() == 4:  # Friday
            weekly = [i for i in invoices if is_due_this_week(i) and not i.get('paid_date')]
            if weekly:
                print(f"\n{ MAGENTA }🔔 FRIDAY FEATURE: {len(weekly)} invoices due this week:{RESET}")
                print_table(weekly[:5], get_terminal_width())
        
        print("\n📋 Main Menu:")
        print("1. 📋 List All     2. ➕ Add Invoice    3. ✅ Mark Paid")
        print("4. 💾 Export CSV   5. 🔗 Share Summary  6. 📥 Import")
        print("q. 🚪 Quit")
        print("\n" + "=" * get_terminal_width())
        
        try:
            choice = sys.stdin.read(1).strip().lower()
        except:
            choice = input("Enter choice (1-6, q): ").strip().lower()
        
        if choice == 'q':
            break
        elif choice == '1':
            list_invoices(invoices)
        elif choice == '2':
            add_invoice(invoices)
        elif choice == '3':
            mark_paid(invoices)
        elif choice == '4':
            export_csv(invoices)
        elif choice == '5':
            share_summary(invoices)
        elif choice == '6':
            import_summary(invoices)
        
        input("\nPress Enter to continue...")
        invoices = load_invoices()

def list_invoices(invoices: List[Dict[str, Any]]):
    if datetime.date.today().weekday() == 4:  # Friday
        print(f"\n{ MAGENTA }📅 WEEKLY VIEW (Mon-Sun):{RESET}")
    sorted_invoices = sorted(invoices, key=lambda x: parse_date(x['due_date']))
    print_table(sorted_invoices, get_terminal_width())

def add_invoice(invoices: List[Dict[str, Any]]):
    print("\n➕ Add New Invoice")
    client = input("Client name: ").strip()
    if not client:
        print(f"{RED}❌ Client name required!{RESET}")
        return
    
    while True:
        try:
            amount = input("Amount ($): ").strip()
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be > 0")
            break
        except:
            print(f"{RED}❌ Invalid amount!{RESET}")
    
    while True:
        due_date = input("Due date (YYYY-MM-DD): ").strip()
        try:
            parse_date(due_date)
            invoice_id = generate_invoice_id(client, due_date)
            if any(inv['invoice_id'] == invoice_id for inv in invoices):
                print(f"{RED}❌ Duplicate invoice ID! Try different date.{RESET}")
                continue
            break
        except:
            print(f"{RED}❌ Invalid date format!{RESET}")
    
    invoice = {
        'invoice_id': invoice_id,
        'client': client,
        'amount': f"{amount:.2f}",
        'due_date': due_date
    }
    invoices.append(invoice)
    save_invoices(invoices)
    print(f"{GREEN}✅ Invoice {invoice_id} added!{RESET}")

def mark_paid(invoices: List[Dict[str, Any]]):
    unpaid = [i for i in invoices if not i.get('paid_date')]
    if not unpaid:
        print(f"{YELLOW}ℹ️ No unpaid invoices.{RESET}")
        return
    
    print("\n✅ Unpaid Invoices:")
    print_table(unpaid, get_terminal_width())
    
    try:
        idx = int(input("\nEnter invoice number to mark paid (or 0 to cancel): ")) - 1
        if 0 <= idx < len(unpaid):
            unpaid[idx]['paid_date'] = datetime.date.today().isoformat()
            save_invoices(invoices)
            print(f"{GREEN}✅ Invoice {unpaid[idx]['invoice_id']} marked paid!{RESET}")
    except:
        print(f"{RED}❌ Invalid selection.{RESET}")

def export_csv(invoices: List[Dict[str, Any]]):
    unpaid = [i for i in invoices if not i.get('paid_date')]
    if not unpaid:
        print(f"{YELLOW}ℹ️ No unpaid invoices to export.{RESET}")
        return
    
    filename = f"invoices_unpaid_{datetime.date.today().strftime('%Y%m%d')}.csv"
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['invoice_id', 'client', 'amount', 'due_date'])
        writer.writeheader()
        writer.writerows(unpaid)
    print(f"{GREEN}✅ Exported {len(unpaid)} invoices to {filename}{RESET}")

def share_summary(invoices: List[Dict[str, Any]]):
    stats = calculate_stats(invoices)
    unpaid = [i for i in invoices if not i.get('paid_date')]
    summary = {
        'stats': stats,
        'unpaid': unpaid[:10]  # First 10 for brevity
    }
    data = json.dumps(summary).encode()
    hash_str = base64.urlsafe_b64encode(data).decode().rstrip('=')
    print(f"\n🔗 Shareable Summary: {hash_str}")
    print(f"ℹ️ Others can import with: python3 script.py --import {hash_str}")
    print("💡 Copy the hash above!")

def import_summary(invoices: List[Dict[str, Any]]):
    print("\n📥 Enter hash to import:")
    hash_str = input().strip()
    try:
        data = base64.urlsafe_b64decode(hash_str + '===')
        summary = json.loads(data)
        new_invoices = summary['unpaid']
        merged = 0
        for inv in new_invoices:
            if not any(i['invoice_id'] == inv['invoice_id'] for i in invoices):
                invoices.append(inv)
                merged += 1
        save_invoices(invoices)
        print(f"{GREEN}✅ Imported {merged} new invoices!{RESET}")
    except Exception as e:
        print(f"{RED}❌ Invalid hash or import failed.{RESET}")

def non_interactive(args):
    invoices = load_invoices()
    if args.import_hash:
        import_summary(invoices)
    elif args.export:
        export_csv(invoices)
    else:
        stats = calculate_stats(invoices)
        print(f"Total Unpaid: ${stats['total_unpaid']:.2f}")
        print(f"Overdue: ${stats['overdue_total']:.2f} ({stats['overdue_count']})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Invoice Organizer Pro")
    parser.add_argument('--import', dest='import_hash', help='Import invoices from hash')
    parser.add_argument('--export', action='store_true', help='Export unpaid invoices to CSV')
    args = parser.parse_args()
    
    if args.import_hash or args.export:
        non_interactive(args)
    else:
        main_menu()