# Auto-generated via Perplexity on 2025-12-12T01:27:46.709894Z
#!/usr/bin/env python3
import argparse
import json
import os
import sys
import tempfile
import shutil
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import re

DATA_FILE = 'solo_invoice_data.json'
BACKUP_DIR = 'backups'

def parse_date(s):
    if s.lower() == 'today':
        return date.today().isoformat()
    try:
        return datetime.fromisoformat(s).date().isoformat()
    except ValueError:
        return None

def decimal_input(prompt, default=None):
    while True:
        s = input(f"{prompt} [{default}]: ").strip()
        if not s and default is not None:
            return Decimal(str(default))
        try:
            return Decimal(s)
        except InvalidOperation:
            print("Invalid decimal. Try again.")

def date_input(prompt, default=None):
    while True:
        s = input(f"{prompt} [{default}]: ").strip()
        if not s and default is not None:
            return default
        d = parse_date(s)
        if d:
            return d
        print("Invalid date. Use YYYY-MM-DD or 'today'.")

def yesno_input(prompt, default='n'):
    while True:
        s = input(f"{prompt} [{default}]: ").strip().lower()
        if not s:
            return default == 'y'
        return s in ('y', 'yes', '1')

def load_data(data_path):
    if not os.path.exists(data_path):
        data = {"invoices": [], "ledger": [], "meta": {"next_invoice_id": 1, "history": []}}
        save_data(data, data_path)
    with open(data_path, 'r') as f:
        return json.load(f)

def save_data(data, data_path, backup=False):
    if backup:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        shutil.copy2(data_path, f'{BACKUP_DIR}/{ts}_{os.path.basename(data_path)}')
    
    tmp = tempfile.NamedTemporaryFile(mode='w', delete=False, dir=os.path.dirname(data_path))
    try:
        json.dump(data, tmp, indent=2, default=str)
        tmp.close()
        shutil.move(tmp.name, data_path)
    except:
        os.unlink(tmp.name)
        raise

def push_history(data):
    history = data['meta'].setdefault('history', [])
    history.append(json.dumps(data, default=str))
    if len(history) > 10:
        history.pop(0)

def undo(data):
    history = data['meta'].setdefault('history', [])
    if len(history) < 2:
        print("No undo available")
        return False
    data.update(json.loads(history[-2]))
    print("Undone last change")
    return True

def redo(data):
    history = data['meta'].setdefault('history', [])
    if len(history) < 1:
        print("No redo available")
        return False
    data.update(json.loads(history[-1]))
    print("Redone last change")
    return True

def compute_invoice_total(invoice):
    subtotal = sum(Decimal(str(item['qty'])) * Decimal(str(item['unit_price'])) 
                   for item in invoice['items'])
    tax = subtotal * (Decimal(str(invoice['tax_rate'])) / Decimal('100'))
    return subtotal + tax

def find_invoice(data, inv_id):
    for inv in data['invoices']:
        if inv['id'] == inv_id:
            return inv
    return None

def find_ledger_entry(data, inv_id):
    for entry in data['ledger']:
        if entry['reference'] == inv_id and entry['type'] == 'invoice':
            return entry
    return None

def create_invoice_interactive(data, quiet=False):
    inv = {
        'id': data['meta']['next_invoice_id'],
        'date': date.today().isoformat(),
        'customer_name': '',
        'items': [],
        'tax_rate': 0.0,
        'status': 'draft',
        'total': 0.0,
        'notes': ''
    }
    
    if not quiet:
        inv['customer_name'] = input("Customer name: ").strip()
        inv['date'] = date_input("Date", inv['date'])
    
    while True:
        if not quiet:
            desc = input("Item description (or Enter to finish): ").strip()
            if not desc:
                break
            qty = decimal_input("Quantity", 1)
            price = decimal_input("Unit price")
            inv['items'].append({'description': desc, 'qty': float(qty), 'unit_price': float(price)})
        
        if quiet:
            break
    
    if not quiet:
        inv['tax_rate'] = float(decimal_input("Tax rate %", 0))
        inv['notes'] = input("Notes: ").strip()
    
    inv['total'] = float(compute_invoice_total(inv))
    data['invoices'].append(inv)
    data['meta']['next_invoice_id'] += 1
    
    print(f"Created invoice {inv['id']} for {inv['customer_name']}, total: ${inv['total']:.2f}")
    return True

def list_invoices(data, args):
    invoices = data['invoices'][:]
    
    if args.status:
        invoices = [i for i in invoices if i['status'] == args.status]
    if args.customer:
        invoices = [i for i in invoices if args.customer.lower() in i['customer_name'].lower()]
    if args.from_date:
        invoices = [i for i in invoices if i['date'] >= args.from_date]
    if args.to_date:
        invoices = [i for i in invoices if i['date'] <= args.to_date]
    if args.min_amount:
        min_amt = Decimal(str(args.min_amount))
        invoices = [i for i in invoices if Decimal(str(i['total'])) >= min_amt]
    
    if args.sort == 'date':
        invoices.sort(key=lambda x: x['date'])
    elif args.sort == 'total':
        invoices.sort(key=lambda x: x['total'])
    elif args.sort == 'id':
        invoices.sort(key=lambda x: x['id'])
    
    if not invoices:
        print("No invoices found")
        return
    
    print(f"{'ID':<4} {'Date':<11} {'Customer':<20} {'Status':<8} {'Total':<10}")
    print("-" * 55)
    for inv in invoices:
        print(f"{inv['id']:<4} {inv['date'][:10]:<11} {inv['customer_name'][:19]:<20} "
              f"{inv['status']:<8} ${inv['total']:<9.2f}")

def view_invoice(data, inv_id):
    inv = find_invoice(data, inv_id)
    if not inv:
        print(f"Invoice {inv_id} not found")
        return
    
    print(f"\nInvoice #{inv['id']} - {inv['customer_name']}")
    print(f"Date: {inv['date']}")
    print(f"Status: {inv['status']}")
    print(f"Notes: {inv['notes']}")
    print("\nItems:")
    print(f"{'Desc':<25} {'Qty':<6} {'Price':<8} {'Total':<10}")
    print("-" * 50)
    subtotal = Decimal('0')
    for item in inv['items']:
        qty, price = Decimal(str(item['qty'])), Decimal(str(item['unit_price']))
        line_total = qty * price
        subtotal += line_total
        print(f"{item['description'][:24]:<25} {qty:<6} ${price:<7.2f} ${line_total:<9.2f}")
    
    tax = subtotal * (Decimal(str(inv['tax_rate'])) / Decimal('100'))
    total = subtotal + tax
    print("-" * 50)
    print(f"{'Subtotal':<39} ${subtotal:<9.2f}")
    print(f"{'Tax ('+str(inv['tax_rate'])+'%)':<39} ${tax:<9.2f}")
    print(f"{'TOTAL':<39} ${total:<9.2f}")

def edit_invoice(data, inv_id, quiet=False):
    inv = find_invoice(data, inv_id)
    if not inv:
        print(f"Invoice {inv_id} not found")
        return False
    
    old_status = inv['status']
    old_total = inv['total']
    
    if not quiet:
        print(f"\nEditing invoice {inv_id}")
        inv['customer_name'] = input(f"Customer [{inv['customer_name']}]: ") or inv['customer_name']
        print("Items (leave empty to keep current):")
        new_items = []
        for i, item in enumerate(inv['items']):
            print(f"  {i}: {item['description']} ({item['qty']} x ${item['unit_price']:.2f})")
        
        while True:
            desc = input("Add/modify item desc (or Enter to finish): ").strip()
            if not desc:
                break
            qty = decimal_input("Qty", 1)
            price = decimal_input("Unit price")
            new_items.append({'description': desc, 'qty': float(qty), 'unit_price': float(price)})
        if new_items:
            inv['items'] = new_items
        
        inv['tax_rate'] = float(decimal_input("Tax rate %", inv['tax_rate']))
        inv['notes'] = input(f"Notes [{inv['notes']}]: ") or inv['notes']
        status = input(f"Status [{inv['status']}]: ").strip() or inv['status']
        if status in ('draft', 'sent', 'paid', 'partial'):
            inv['status'] = status
    
    inv['total'] = float(compute_invoice_total(inv))
    
    # Handle ledger for status changes
    ledger_entry = find_ledger_entry(data, inv_id)
    if old_status != 'paid' and inv['status'] == 'paid' and not quiet:
        if yesno_input("Mark as paid? Create ledger entry"):
            data['ledger'].append({
                'id': len(data['ledger']) + 1,
                'date': date.today().isoformat(),
                'type': 'invoice',
                'amount': inv['total'],
                'reference': inv_id,
                'balance_after': 0  # computed later
            })
    elif old_status == 'paid' and inv['status'] != 'paid' and ledger_entry and not quiet:
        if yesno_input("Remove paid status? Delete ledger entry"):
            data['ledger'] = [e for e in data['ledger'] if e['reference'] != inv_id or e['type'] != 'invoice']
    
    print(f"Updated invoice {inv_id}")
    return True

def mark_paid(data, inv_id, date_str=None, amount=None, quiet=False):
    inv = find_invoice(data, inv_id)
    if not inv:
        print(f"Invoice {inv_id} not found")
        return False
    
    pay_date = date_str or date.today().isoformat()
    pay_amount = amount or inv['total']
    
    data['ledger'].append({
        'id': len(data['ledger']) + 1,
        'date': pay_date,
        'type': 'payment',
        'amount': float(pay_amount),
        'reference': inv_id,
        'balance_after': 0
    })
    
    if float(pay_amount) >= inv['total']:
        inv['status'] = 'paid'
    else:
        inv['status'] = 'partial'
    
    print(f"Marked invoice {inv_id} {'fully' if float(pay_amount) >= inv['total'] else 'partially'} paid")
    return True

def add_ledger(data, quiet=False):
    entry = {
        'id': len(data['ledger']) + 1,
        'date': date.today().isoformat(),
        'type': '',
        'amount': 0.0,
        'reference': '',
        'balance_after': 0
    }
    
    if not quiet:
        entry['type'] = input("Type (expense/adjustment): ").strip()
        entry['date'] = date_input("Date", entry['date'])
        entry['amount'] = float(decimal_input("Amount (neg for expense)"))
        entry['reference'] = input("Reference/note: ").strip()
    
    data['ledger'].append(entry)
    print("Ledger entry added")
    return True

def show_ledger(data, from_date=None, to_date=None, type_filter=None):
    ledger = data['ledger'][:]
    if from_date:
        ledger = [e for e in ledger if e['date'] >= from_date]
    if to_date:
        ledger = [e for e in ledger if e['date'] <= to_date]
    if type_filter:
        ledger = [e for e in ledger if e['type'] == type_filter]
    
    ledger.sort(key=lambda x: x['date'])
    
    balance = Decimal('0')
    print(f"{'ID':<4} {'Date':<11} {'Type':<10} {'Amount':<12} {'Ref':<15} {'Balance':<12}")
    print("-" * 65)
    
    for entry in ledger:
        balance += Decimal(str(entry['amount']))
        entry['balance_after'] = float(balance)
        print(f"{entry['id']:<4} {entry['date'][:10]:<11} {entry['type']:<10} "
              f"${entry['amount']:+11.2f} {str(entry['reference'])[:14]:<15} ${balance:<11.2f}")

def export_invoice(data, inv_id, fmt):
    inv = find_invoice(data, inv_id)
    if not inv or not fmt:
        print("Invalid invoice or format")
        return
    
    filename = f"invoice_{inv_id}.{fmt}"
    with open(filename, 'w') as f:
        if fmt == 'csv':
            f.write("Description,Qty,Unit Price,Total\n")
            for item in inv['items']:
                qty, price = item['qty'], item['unit_price']
                total = qty * price
                f.write(f"{item['description']},{qty},{price},{total}\n")
            f.write(f"TOTAL,,,{inv['total']}\n")
        else:
            f.write(f"Invoice #{inv['id']}\n")
            f.write(f"Customer: {inv['customer_name']}\n")
            f.write(f"Date: {inv['date']}\n")
            for item in inv['items']:
                f.write(f"{item['description']}: {item['qty']} x ${item['unit_price']:.2f}\n")
            f.write(f"TOTAL: ${inv['total']:.2f}\n")
    print(f"Exported to {filename}")

def export_ledger(data, fmt='csv', from_date=None, to_date=None):
    if fmt != 'csv':
        print("Only CSV export supported for ledger")
        return
    
    filename = "ledger.csv"
    with open(filename, 'w') as f:
        f.write("Date,Type,Amount,Reference,Balance\n")
        ledger = data['ledger'][:]
        if from_date:
            ledger = [e for e in ledger if e['date'] >= from_date]
        if to_date:
            ledger = [e for e in ledger if e['date'] <= to_date]
        ledger.sort(key=lambda x: x['date'])
        
        balance = Decimal('0')
        for entry in ledger:
            balance += Decimal(str(entry['amount']))
            f.write(f"{entry['date']},{entry['type']},{entry['amount']},{entry['reference']},{float(balance)}\n")
    print(f"Exported to {filename}")

def seed_data(data):
    data['invoices'] = [
        {'id': 1, 'date': '2025-12-01', 'customer_name': 'Acme Corp', 'items': 
         [{'description': 'Consulting', 'qty': 10, 'unit_price': 100}], 'tax_rate': 8.5, 
         'status': 'paid', 'total': 1085.0, 'notes': ''},
        {'id': 2, 'date': '2025-12-05', 'customer_name': 'Beta LLC', 'items': 
         [{'description': 'Software', 'qty': 1, 'unit_price': 5000}], 'tax_rate': 8.5, 
         'status': 'sent', 'total': 5425.0, 'notes': ''},
        {'id': 3, 'date': '2025-12-10', 'customer_name': 'Gamma Inc', 'items': 
         [{'description': 'Support', 'qty': 5, 'unit_price': 200}], 'tax_rate': 0, 
         'status': 'draft', 'total': 1000.0, 'notes': ''}
    ]
    data['ledger'] = [
        {'id': 1, 'date': '2025-12-01', 'type': 'invoice', 'amount': 1085.0, 'reference': 1, 'balance_after': 1085.0},
        {'id': 2, 'date': '2025-12-08', 'type': 'expense', 'amount': -250.0, 'reference': 'Office', 'balance_after': 835.0}
    ]
    data['meta']['next_invoice_id'] = 4
    print("Sample data created")

def interactive_menu(data, quiet=False):
    while True:
        print("\n=== Solo Invoice & Quick Ledger ===")
        print("1. Create Invoice (c)")
        print("2. List Invoices (l)")
        print("3. View Ledger (v)")
        print("4. Undo (u)")
        print("5. Redo (r)")
        print("6. Exit (q)")
        
        choice = input("\nChoice: ").strip().lower()
        if choice in ('1', 'c'):
            create_invoice_interactive(data)
        elif choice in ('2', 'l'):
            list_invoices(data, argparse.Namespace())
        elif choice in ('3', 'v'):
            show_ledger(data)
        elif choice in ('4', 'u'):
            undo(data)
        elif choice in ('5', 'r'):
            redo(data)
        elif choice in ('6', 'q', 'exit'):
            break

def main():
    parser = argparse.ArgumentParser(description='Solo Invoice & Quick Ledger')
    parser.add_argument('--data', default=DATA_FILE, help='Data file path')
    parser.add_argument('--seed', help='Create sample data')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without saving')
    parser.add_argument('--quiet', '-q', action='store_true')
    parser.add_argument('--yes', '-y', action='store_true')
    
    subparsers = parser.add_subparsers(dest='command')
    
    # Invoice commands
    p = subparsers.add_parser('create-invoice')
    p = subparsers.add_parser('list-invoices')
    p.add_argument('--status', choices=['draft','sent','paid','partial'])
    p.add_argument('--customer')
    p.add_argument('--from-date')
    p.add_argument('--to-date')
    p.add_argument('--min-amount')
    p.add_argument('--sort', choices=['date','total','id'])
    
    p = subparsers.add_parser('view-invoice')
    p.add_argument('inv_id', type=int)
    
    p = subparsers.add_parser('edit-invoice')
    p.add_argument('inv_id', type=int)
    
    p = subparsers.add_parser('mark-paid')
    p.add_argument('inv_id', type=int)
    p.add_argument('--date')
    p.add_argument('--amount', type=float)
    
    p = subparsers.add_parser('export-invoice')
    p.add_argument('inv_id', type=int)
    p.add_argument('--csv', dest='fmt', action='store_const', const='csv')
    p.add_argument('--txt', dest='fmt', action='store_const', const='txt')
    
    # Ledger commands
    p = subparsers.add_parser('add-ledger')
    p = subparsers.add_parser('ledger')
    p.add_argument('--from-date')
    p.add_argument('--to-date')
    p.add_argument('--type')
    
    p = subparsers.add_parser('export-ledger')
    p.add_argument('--from-date')
    p.add_argument('--to-date')
    
    # History
    subparsers.add_parser('undo')
    subparsers.add_parser('redo')
    subparsers.add_parser('backup')
    
    args = parser.parse_args()
    
    data = load_data(args.data)
    
    if args.seed:
        seed_data(data)
        save_data(data, args.data)
        return
    
    modified = False
    
    if args.command == 'create-invoice':
        push_history(data)
        modified = create_invoice_interactive(data, args.quiet)
    elif args.command == 'list-invoices':
        list_invoices(data, args)
    elif args.command == 'view-invoice':
        view_invoice(data, args.inv_id)
    elif args.command == 'edit-invoice':
        push_history(data)
        modified = edit_invoice(data, args.inv_id, args.quiet)
    elif args.command == 'mark-paid':
        push_history(data)
        modified = mark_paid(data, args.inv_id, args.date, args.amount, args.quiet)
    elif args.command == 'add-ledger':
        push_history(data)
        modified = add_ledger(data, args.quiet)
    elif args.command == 'ledger':
        show_ledger(data, args.from_date, args.to_date, getattr(args, 'type', None))
    elif args.command == 'export-invoice':
        export_invoice(data, args.inv_id, getattr(args, 'fmt', None))
    elif args.command == 'export-ledger':
        export_ledger(data, 'csv', args.from_date, args.to_date)
    elif args.command == 'undo':
        push_history(data)
        modified = undo(data)
    elif args.command == 'redo':
        push_history(data)
        modified = redo(data)
    elif args.command == 'backup':
        save_data(data, args.data, backup=True)
        print("Backup created")
        return
    elif not args.command:
        interactive_menu(data)
        return
    else:
        parser.print_help()
        return
    
    if modified and not args.dry_run:
        save_data(data, args.data)

if __name__ == '__main__':
    main()