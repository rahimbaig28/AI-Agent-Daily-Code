# Auto-generated via Perplexity on 2025-12-22T04:38:50.791075Z
#!/usr/bin/env python3
import argparse
import json
import os
import sys
import csv
import shutil
from datetime import datetime
from pathlib import Path

DATA_FILE = "invoices.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_next_id(data):
    return max([inv['id'] for inv in data], default=0) + 1

def validate_date(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def get_terminal_width():
    return shutil.get_terminal_size((80, 20)).columns

def truncate(text, width):
    if len(text) > width:
        return text[:width-1] + "…"
    return text

def cmd_add(args):
    data = load_data()
    
    print("\n=== Add New Invoice ===")
    customer = input("Customer name: ").strip()
    if not customer:
        print("Error: Customer name required.")
        return
    
    date_input = input(f"Date (YYYY-MM-DD, default today): ").strip()
    if not date_input:
        date_input = datetime.now().strftime('%Y-%m-%d')
    if not validate_date(date_input):
        print("Error: Invalid date format.")
        return
    
    items = []
    print("Add items (leave name blank to finish):")
    while True:
        name = input("  Item name: ").strip()
        if not name:
            break
        try:
            qty = float(input("  Quantity: "))
            price = float(input("  Unit price: "))
            if qty <= 0 or price <= 0:
                print("  Error: Quantity and price must be positive.")
                continue
            items.append({"name": name, "qty": qty, "price": price})
        except ValueError:
            print("  Error: Invalid quantity or price.")
            continue
    
    if not items:
        print("Error: At least one item required.")
        return
    
    total = sum(item['qty'] * item['price'] for item in items)
    invoice = {
        "id": get_next_id(data),
        "date": date_input,
        "customer": customer,
        "items": items,
        "total": round(total, 2),
        "status": "pending"
    }
    data.append(invoice)
    save_data(data)
    print(f"Invoice #{invoice['id']} created successfully.")

def cmd_list(args):
    data = load_data()
    
    if args.status:
        data = [inv for inv in data if inv['status'] == args.status]
    
    data.sort(key=lambda x: x['date'], reverse=True)
    
    if not data:
        print("No invoices found.")
        return
    
    width = get_terminal_width()
    col_id = 5
    col_date = 12
    col_customer = max(20, width - col_id - col_date - 12 - 10)
    col_total = 10
    col_status = 10
    
    header = f"{'ID':<{col_id}} {'Date':<{col_date}} {'Customer':<{col_customer}} {'Total':>{col_total}} {'Status':<{col_status}}"
    print("\n" + header)
    print("-" * len(header))
    
    for inv in data:
        cust = truncate(inv['customer'], col_customer)
        status = inv['status']
        print(f"{inv['id']:<{col_id}} {inv['date']:<{col_date}} {cust:<{col_customer}} ${inv['total']:>{col_total-1}.2f} {status:<{col_status}}")

def cmd_view(args):
    data = load_data()
    inv = next((i for i in data if i['id'] == args.id), None)
    if not inv:
        print(f"Invoice #{args.id} not found.")
        return
    
    print(f"\n=== Invoice #{inv['id']} ===")
    print(f"Date: {inv['date']}")
    print(f"Customer: {inv['customer']}")
    print(f"Status: {inv['status']}")
    print("\nItems:")
    print(f"{'Name':<30} {'Qty':>10} {'Price':>10} {'Total':>10}")
    print("-" * 60)
    for item in inv['items']:
        name = truncate(item['name'], 30)
        print(f"{name:<30} {item['qty']:>10.2f} ${item['price']:>9.2f} ${item['qty']*item['price']:>9.2f}")
    print("-" * 60)
    print(f"{'TOTAL':<30} {'':<10} {'':<10} ${inv['total']:>9.2f}")

def cmd_edit(args):
    data = load_data()
    inv = next((i for i in data if i['id'] == args.id), None)
    if not inv:
        print(f"Invoice #{args.id} not found.")
        return
    
    print(f"\n=== Edit Invoice #{args.id} ===")
    customer = input(f"Customer name ({inv['customer']}): ").strip() or inv['customer']
    date_input = input(f"Date ({inv['date']}): ").strip() or inv['date']
    if not validate_date(date_input):
        print("Error: Invalid date format.")
        return
    
    items = []
    print("Re-enter items (leave name blank to finish):")
    while True:
        name = input("  Item name: ").strip()
        if not name:
            break
        try:
            qty = float(input("  Quantity: "))
            price = float(input("  Unit price: "))
            if qty <= 0 or price <= 0:
                print("  Error: Quantity and price must be positive.")
                continue
            items.append({"name": name, "qty": qty, "price": price})
        except ValueError:
            print("  Error: Invalid quantity or price.")
            continue
    
    if not items:
        print("Error: At least one item required.")
        return
    
    total = sum(item['qty'] * item['price'] for item in items)
    inv['customer'] = customer
    inv['date'] = date_input
    inv['items'] = items
    inv['total'] = round(total, 2)
    save_data(data)
    print(f"Invoice #{args.id} updated successfully.")

def cmd_delete(args):
    data = load_data()
    inv = next((i for i in data if i['id'] == args.id), None)
    if not inv:
        print(f"Invoice #{args.id} not found.")
        return
    
    confirm = input(f"Delete invoice #{args.id}? (y/n): ").strip().lower()
    if confirm == 'y':
        data = [i for i in data if i['id'] != args.id]
        save_data(data)
        print(f"Invoice #{args.id} deleted.")
    else:
        print("Cancelled.")

def cmd_print(args):
    data = load_data()
    inv = next((i for i in data if i['id'] == args.id), None)
    if not inv:
        print(f"Invoice #{args.id} not found.")
        return
    
    print("\n" + "="*60)
    print(f"INVOICE #{inv['id']}".center(60))
    print("="*60)
    print(f"\nCustomer: {inv['customer']}")
    print(f"Date: {inv['date']}")
    print(f"Status: {inv['status']}")
    print("\n" + "-"*60)
    print(f"{'Item':<35} {'Qty':>10} {'Price':>10}")
    print("-"*60)
    for item in inv['items']:
        name = truncate(item['name'], 35)
        print(f"{name:<35} {item['qty']:>10.2f} ${item['price']:>9.2f}")
    print("-"*60)
    print(f"{'TOTAL':>45} ${inv['total']:>9.2f}".replace('TOTAL', '**TOTAL**'))
    print("="*60)
    input("\nPress Enter when ready to print...")

def cmd_export(args):
    data = load_data()
    if not data:
        print("No invoices to export.")
        return
    
    with open('invoices.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Date', 'Customer', 'Item', 'Qty', 'Price', 'Total', 'Status'])
        for inv in data:
            for i, item in enumerate(inv['items']):
                writer.writerow([
                    inv['id'] if i == 0 else '',
                    inv['date'] if i == 0 else '',
                    inv['customer'] if i == 0 else '',
                    item['name'],
                    item['qty'],
                    item['price'],
                    inv['total'] if i == 0 else '',
                    inv['status'] if i == 0 else ''
                ])
    print("Exported to invoices.csv")

def main():
    parser = argparse.ArgumentParser(
        prog='Invoice Tracker Pro',
        description='Manage invoices with ease'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    subparsers.add_parser('add', help='Add new invoice')
    
    list_parser = subparsers.add_parser('list', help='List all invoices')
    list_parser.add_argument('--status', choices=['pending', 'paid'], help='Filter by status')
    
    view_parser = subparsers.add_parser('view', help='View invoice details')
    view_parser.add_argument('id', type=int, help='Invoice ID')
    
    edit_parser = subparsers.add_parser('edit', help='Edit invoice')
    edit_parser.add_argument('id', type=int, help='Invoice ID')
    
    delete_parser = subparsers.add_parser('delete', help='Delete invoice')
    delete_parser.add_argument('id', type=int, help='Invoice ID')
    
    print_parser = subparsers.add_parser('print', help='Print invoice')
    print_parser.add_argument('id', type=int, help='Invoice ID')
    
    subparsers.add_parser('export', help='Export to CSV')
    
    args = parser.parse_args()
    
    if args.command == 'add':
        cmd_add(args)
    elif args.command == 'list':
        cmd_list(args)
    elif args.command == 'view':
        cmd_view(args)
    elif args.command == 'edit':
        cmd_edit(args)
    elif args.command == 'delete':
        cmd_delete(args)
    elif args.command == 'print':
        cmd_print(args)
    elif args.command == 'export':
        cmd_export(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()