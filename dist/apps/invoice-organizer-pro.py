# Auto-generated via Perplexity on 2025-12-29T12:41:57.300124Z
#!/usr/bin/env python3
import argparse
import json
import csv
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime, date
import argparse

DATA_FILE = Path("invoices.json")
BACKUP_FILE = Path("invoices.json.bak")

def load_invoices():
    """Load invoices from JSON file."""
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, PermissionError) as e:
        print(f"Error reading {DATA_FILE}: {e}", file=sys.stderr)
        sys.exit(1)

def save_invoices(invoices):
    """Save invoices to JSON file with backup."""
    try:
        if DATA_FILE.exists():
            shutil.copy2(DATA_FILE, BACKUP_FILE)
        with open(DATA_FILE, 'w') as f:
            json.dump(invoices, f, indent=2)
    except PermissionError as e:
        print(f"Permission denied writing {DATA_FILE}: {e}", file=sys.stderr)
        sys.exit(1)

def generate_id(invoices):
    """Generate unique ID: YYYYMMDD-NNN."""
    today = datetime.now().strftime("%Y%m%d")
    counter = 1
    while True:
        candidate = f"{today}-{counter:03d}"
        if not any(inv['id'] == candidate for inv in invoices):
            return candidate
        counter += 1

def parse_date(date_str):
    """Parse YYYY-MM-DD date."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError("Date must be YYYY-MM-DD")

def is_overdue(due_date):
    """Check if invoice is overdue."""
    return due_date < date.today() and not is_paid(due_date)

def is_paid(invoice):
    """Check if invoice is paid."""
    return invoice.get('paid_date') is not None

def format_amount(amount):
    """Format amount as currency."""
    return f"${amount:,.2f}"

def get_terminal_width():
    """Get terminal width or default."""
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80

def print_table(invoices, filters=None):
    """Print invoices in table format."""
    if filters:
        filtered = [inv for inv in invoices if filters(inv)]
    else:
        filtered = invoices
    
    filtered.sort(key=lambda x: x['due_date'])
    
    # Headers
    headers = ["ID", "Customer", "Amount", "Due", "Status", "Description"]
    widths = [12, 20, 12, 12, 12, 30]
    
    print("\n" + "="*len(headers))
    print(" ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("="*len(headers))
    
    total_due = total_overdue = total_paid = 0.0
    
    for inv in filtered:
        status = "PAID" if is_paid(inv) else ("OVERDUE" if is_overdue(inv['due_date']) else "UNPAID")
        color = "\033[91m" if status == "OVERDUE" else ""
        reset = "\033[0m" if status == "OVERDUE" else ""
        
        desc = inv['description'][:27] + "..." if len(inv['description']) > 30 else inv['description']
        
        row = f"{inv['id']:<12} {inv['customer']:<20} {format_amount(inv['amount']):>12} {inv['due_date']:<12} {status:<12} {desc:<30}"
        
        if status == "OVERDUE":
            total_overdue += inv['amount']
            print(f"{color}{row}{reset}")
        else:
            print(row)
            if status == "PAID":
                total_paid += inv['amount']
            else:
                total_due += inv['amount']
    
    print("="*len(headers))
    
    # Stats
    print(f"Total Due: {format_amount(total_due)} | Overdue: {format_amount(total_overdue)} | Paid: {format_amount(total_paid)}")

def print_invoice(id, invoices):
    """Print detailed invoice summary."""
    inv = next((i for i in invoices if i['id'] == id), None)
    if not inv:
        print(f"Invoice {id} not found", file=sys.stderr)
        sys.exit(1)
    
    border = "┌" + "─" * 78 + "┐"
    print(border)
    print(f"│ {'INVOICE':^78} │")
    print(border)
    print(f"│ ID: {inv['id']:<70} │")
    print(f"│ Customer: {inv['customer']:<70} │")
    print(f"│ Amount: {format_amount(inv['amount']):>70} │")
    print(f"│ Due Date: {inv['due_date']:<70} │")
    status = "PAID" if is_paid(inv) else "UNPAID"
    paid_date = inv.get('paid_date', 'N/A')
    print(f"│ Status: {status:<64} │")
    print(f"│ Paid Date: {paid_date:<70} │")
    print(border)
    print(f"│ Description: {inv['description']:<70} │")
    print(border)

def export_csv(path, invoices, filters=None):
    """Export filtered invoices to CSV."""
    if filters:
        filtered = [inv for inv in invoices if filters(inv)]
    else:
        filtered = invoices
    
    fieldnames = ['id', 'customer', 'amount', 'due_date', 'paid_date', 'description']
    
    try:
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered)
        print(f"Exported {len(filtered)} invoices to {path}")
    except PermissionError as e:
        print(f"Cannot write to {path}: {e}", file=sys.stderr)
        sys.exit(1)

def add_invoice(args):
    """Add new invoice."""
    invoices = load_invoices()
    
    if float(args.amount) <= 0:
        print("Amount must be greater than 0", file=sys.stderr)
        sys.exit(1)
    
    new_inv = {
        'id': generate_id(invoices),
        'customer': args.customer,
        'amount': float(args.amount),
        'due_date': args.due.isoformat(),
        'paid_date': None,
        'description': args.description
    }
    
    invoices.append(new_inv)
    save_invoices(invoices)
    print(f"Added invoice {new_inv['id']}")

def list_invoices(args):
    """List invoices with optional filters."""
    invoices = load_invoices()
    
    filters = []
    if args.overdue:
        filters.append(lambda x: is_overdue(x['due_date']))
    if args.paid:
        filters.append(lambda x: is_paid(x))
    if args.unpaid:
        filters.append(lambda x: not is_paid(x))
    
    if args.month:
        try:
            year, month = map(int, args.month.split('-'))
            month_filter = lambda x: x['due_date'][:7] == f"{year:04d}-{month:02d}"
            filters.append(month_filter)
        except:
            print("Invalid month format. Use YYYY-MM", file=sys.stderr)
            sys.exit(1)
    
    combined_filter = None if not filters else (lambda x: any(f(x) for f in filters))
    print_table(invoices, combined_filter)

def pay_invoice(args):
    """Mark invoice as paid."""
    invoices = load_invoices()
    inv = next((i for i in invoices if i['id'] == args.id), None)
    
    if not inv:
        print(f"Invoice {args.id} not found", file=sys.stderr)
        sys.exit(1)
    
    if is_paid(inv):
        print(f"Invoice {args.id} already paid", file=sys.stderr)
        sys.exit(1)
    
    inv['paid_date'] = datetime.now().isoformat()
    save_invoices(invoices)
    print(f"Marked invoice {args.id} as paid")

def main():
    parser = argparse.ArgumentParser(
        description="Invoice Organizer Pro - Manage your invoices from the command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s add --customer "ABC Corp" --amount 1500.50 --due 2025-12-15 --description "Consulting"
  %(prog)s list --overdue
  %(prog)s pay 20251229-001
  %(prog)s export overdue.csv
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add new invoice')
    add_parser.add_argument('--customer', required=True, help='Customer name')
    add_parser.add_argument('--amount', required=True, type=float, help='Invoice amount')
    add_parser.add_argument('--due', required=True, type=parse_date, help='Due date (YYYY-MM-DD)')
    add_parser.add_argument('--description', required=True, help='Invoice description')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List invoices')
    list_parser.add_argument('--overdue', action='store_true', help='Show only overdue invoices')
    list_parser.add_argument('--paid', action='store_true', help='Show only paid invoices')
    list_parser.add_argument('--unpaid', action='store_true', help='Show only unpaid invoices')
    list_parser.add_argument('--month', help='Filter by month (YYYY-MM)')
    
    # Pay command
    pay_parser = subparsers.add_parser('pay', help='Mark invoice as paid')
    pay_parser.add_argument('id', help='Invoice ID')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export invoices to CSV')
    export_parser.add_argument('path', help='Output CSV file path')
    export_parser.add_argument('--overdue', action='store_true', help='Export only overdue')
    export_parser.add_argument('--unpaid', action='store_true', help='Export only unpaid')
    
    # Print command
    print_parser = subparsers.add_parser('print', help='Print invoice details')
    print_parser.add_argument('id', help='Invoice ID')
    
    args = parser.parse_args()
    
    if args.command == 'add':
        add_invoice(args)
    elif args.command == 'list':
        list_invoices(args)
    elif args.command == 'pay':
        pay_invoice(args)
    elif args.command == 'export':
        invoices = load_invoices()
        filters = []
        if args.overdue:
            filters.append(lambda x: is_overdue(x['due_date']))
        if args.unpaid:
            filters.append(lambda x: not is_paid(x))
        combined_filter = None if not filters else (lambda x: any(f(x) for f in filters))
        export_csv(args.path, invoices, combined_filter)
    elif args.command == 'print':
        print_invoice(args.id, load_invoices())
    else:
        parser.print_help()

if __name__ == '__main__':
    main()