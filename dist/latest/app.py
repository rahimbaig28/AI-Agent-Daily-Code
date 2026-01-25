# Auto-generated via Perplexity on 2026-01-25T16:40:27.041725Z
#!/usr/bin/env python3
import json
import datetime
import uuid
import argparse
import os
from typing import Dict, List, Any

DATA_FILE = 'invoices.json'
VALID_STATUSES = {'draft', 'sent', 'paid'}

def load_invoices() -> List[Dict[str, Any]]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        print("Error: Invalid or corrupted JSON file. Starting fresh.")
        return []

def save_invoices(invoices: List[Dict[str, Any]]):
    with open(DATA_FILE, 'w') as f:
        json.dump(invoices, f, indent=2)

def get_invoice_by_id(invoices: List[Dict[str, Any]], invoice_id: str) -> Dict[str, Any]:
    for inv in invoices:
        if inv['id'] == invoice_id:
            return inv
    return None

def format_currency(amount: float) -> str:
    return f"${amount:.2f}"

def format_date(dt: str) -> str:
    return datetime.datetime.fromisoformat(dt).strftime('%Y-%m-%d')

def add_invoice():
    invoices = load_invoices()
    invoice = {
        'id': str(uuid.uuid4()),
        'client': input("Client name: ").strip(),
        'amount': 0.0,
        'date': datetime.datetime.now().isoformat(),
        'status': 'draft'
    }
    
    while True:
        try:
            amount_str = input("Amount: ").strip()
            if not amount_str:
                print("Amount is required.")
                continue
            amount = float(amount_str)
            if amount <= 0:
                print("Amount must be positive.")
                continue
            invoice['amount'] = amount
            break
        except ValueError:
            print("Invalid amount. Please enter a number.")
    
    while invoice['client'] == '':
        invoice['client'] = input("Client name (required): ").strip()
    
    invoices.append(invoice)
    save_invoices(invoices)
    print(f"Invoice {invoice['id'][:8]}... created successfully.")

def list_invoices():
    invoices = load_invoices()
    if not invoices:
        print("No invoices found.")
        return
    
    invoices.sort(key=lambda x: x['date'], reverse=True)
    print("\nID".ljust(10) + "CLIENT".ljust(20) + "AMOUNT".ljust(12) + "DATE".ljust(12) + "STATUS")
    print("-" * 60)
    for inv in invoices:
        print(
            inv['id'][:8].ljust(10) +
            inv['client'][:19].ljust(20) +
            format_currency(inv['amount']).ljust(12) +
            format_date(inv['date']).ljust(12) +
            inv['status'].upper()
        )

def update_status(invoice_id: str, status: str):
    invoices = load_invoices()
    invoice = get_invoice_by_id(invoices, invoice_id)
    
    if not invoice:
        print(f"Invoice {invoice_id} not found.")
        return
    
    if status not in VALID_STATUSES:
        print(f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")
        return
    
    invoice['status'] = status
    save_invoices(invoices)
    print(f"Invoice {invoice_id[:8]}... updated to '{status}'.")

def delete_invoice(invoice_id: str):
    invoices = load_invoices()
    invoice = get_invoice_by_id(invoices, invoice_id)
    
    if not invoice:
        print(f"Invoice {invoice_id} not found.")
        return
    
    confirm = input(f"Delete invoice {invoice_id[:8]}... for {invoice['client']}? (y/N): ")
    if confirm.lower() == 'y':
        invoices = [inv for inv in invoices if inv['id'] != invoice_id]
        save_invoices(invoices)
        print("Invoice deleted.")

def export_invoices(filename: str):
    invoices = load_invoices()
    try:
        with open(filename, 'w') as f:
            json.dump(invoices, f, indent=2)
        print(f"Exported {len(invoices)} invoices to {filename}")
    except IOError as e:
        print(f"Error writing file: {e}")

def import_invoices(filename: str):
    if not os.path.exists(filename):
        print(f"File {filename} not found.")
        return
    
    try:
        with open(filename, 'r') as f:
            new_invoices = json.load(f)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error reading JSON file: {e}")
        return
    
    invoices = load_invoices()
    existing_ids = {inv['id'] for inv in invoices}
    
    imported_count = 0
    for inv in new_invoices:
        if inv.get('id') not in existing_ids:
            invoices.append(inv)
            imported_count += 1
        elif inv.get('status'):  # Update status if present
            for existing in invoices:
                if existing['id'] == inv['id']:
                    existing['status'] = inv['status']
    
    save_invoices(invoices)
    print(f"Imported {imported_count} new invoices, merged with existing.")

def show_stats():
    invoices = load_invoices()
    if not invoices:
        print("No invoices found.")
        return
    
    total_invoiced = sum(inv['amount'] for inv in invoices)
    total_paid = sum(inv['amount'] for inv in invoices if inv['status'] == 'paid')
    outstanding = total_invoiced - total_paid
    
    status_counts = {}
    for inv in invoices:
        status = inv['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\n=== Invoice Statistics ===")
    print(f"Total invoiced:    {format_currency(total_invoiced)}")
    print(f"Total paid:        {format_currency(total_paid)}")
    print(f"Outstanding:       {format_currency(outstanding)}")
    print("\nStatus breakdown:")
    for status in sorted(status_counts):
        count = status_counts[status]
        print(f"  {status.upper()}: {count}")

def main():
    parser = argparse.ArgumentParser(description="Invoice Logger - Track your small business invoices")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # add
    add_parser = subparsers.add_parser('add', help='Add new invoice')
    
    # list
    subparsers.add_parser('list', help='List all invoices')
    
    # update
    update_parser = subparsers.add_parser('update', help='Update invoice status')
    update_parser.add_argument('invoice_id', help='Invoice ID')
    update_parser.add_argument('--status', required=True, choices=VALID_STATUSES,
                             help='New status (draft/sent/paid)')
    
    # delete
    delete_parser = subparsers.add_parser('delete', help='Delete invoice')
    delete_parser.add_argument('invoice_id', help='Invoice ID')
    
    # export
    export_parser = subparsers.add_parser('export', help='Export invoices to JSON')
    export_parser.add_argument('filename', help='Output filename')
    
    # import
    import_parser = subparsers.add_parser('import', help='Import invoices from JSON')
    import_parser.add_argument('filename', help='Input filename')
    
    # stats
    subparsers.add_parser('stats', help='Show invoice statistics')
    
    args = parser.parse_args()
    
    if args.command == 'add':
        add_invoice()
    elif args.command == 'list':
        list_invoices()
    elif args.command == 'update':
        update_status(args.invoice_id, args.status)
    elif args.command == 'delete':
        delete_invoice(args.invoice_id)
    elif args.command == 'export':
        export_invoices(args.filename)
    elif args.command == 'import':
        import_invoices(args.filename)
    elif args.command == 'stats':
        show_stats()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()