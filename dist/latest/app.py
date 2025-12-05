# Auto-generated via Perplexity on 2025-12-05T13:29:21.594042Z
#!/usr/bin/env python3

import json
import csv
import os
from datetime import datetime
from pathlib import Path

DATA_FILE = "invoices.json"
CSV_FILE = "invoices_export.csv"

def load_invoices():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_invoices(invoices):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(invoices, f, indent=2)
    except IOError as e:
        print(f"Error saving invoices: {e}")

def generate_invoice_id(invoices):
    if not invoices:
        return 1
    return max(int(inv['id']) for inv in invoices) + 1

def validate_amount(amount_str):
    try:
        amount = float(amount_str)
        if amount <= 0:
            print("Amount must be greater than 0.")
            return None
        return amount
    except ValueError:
        print("Invalid amount. Please enter a valid number.")
        return None

def validate_client_name(name):
    name = name.strip()
    if not name:
        print("Client name cannot be empty.")
        return None
    return name

def validate_date(date_str):
    if not date_str.strip():
        return datetime.now().strftime("%Y-%m-%d")
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        print("Invalid date format. Use YYYY-MM-DD.")
        return None

def validate_status(status):
    valid_statuses = ["draft", "sent", "paid"]
    if status.lower() in valid_statuses:
        return status.lower()
    print(f"Invalid status. Choose from: {', '.join(valid_statuses)}")
    return None

def add_invoice(invoices):
    print("\n--- Add New Invoice ---")
    
    client_name = None
    while client_name is None:
        client_name = validate_client_name(input("Client name: "))
    
    amount = None
    while amount is None:
        amount = validate_amount(input("Amount: "))
    
    date_input = input("Date (YYYY-MM-DD) [leave blank for today]: ").strip()
    date = None
    while date is None:
        date = validate_date(date_input if date_input else "")
        if date is None and date_input:
            date_input = input("Date (YYYY-MM-DD) [leave blank for today]: ").strip()
    
    status = None
    while status is None:
        status = validate_status(input("Status (draft/sent/paid) [default: draft]: ").strip() or "draft")
    
    invoice_id = generate_invoice_id(invoices)
    invoice = {
        "id": str(invoice_id),
        "client_name": client_name,
        "date": date,
        "amount": amount,
        "status": status
    }
    
    invoices.append(invoice)
    save_invoices(invoices)
    print(f"Invoice #{invoice_id} created successfully.")

def list_invoices(invoices):
    if not invoices:
        print("\nNo invoices found.")
        return
    
    print("\n--- Filter Invoices ---")
    print("1. All invoices")
    print("2. Draft")
    print("3. Sent")
    print("4. Paid")
    
    choice = input("Select filter (1-4): ").strip()
    
    status_map = {"2": "draft", "3": "sent", "4": "paid"}
    filter_status = status_map.get(choice)
    
    filtered = invoices if choice == "1" else [inv for inv in invoices if inv["status"] == filter_status]
    
    if not filtered:
        print(f"\nNo invoices found with status '{filter_status}'.")
        return
    
    print("\n--- Invoices ---")
    print(f"{'ID':<5} {'Client':<20} {'Date':<12} {'Amount':<10} {'Status':<10}")
    print("-" * 60)
    for inv in filtered:
        print(f"{inv['id']:<5} {inv['client_name']:<20} {inv['date']:<12} ${inv['amount']:<9.2f} {inv['status']:<10}")

def edit_invoice_status(invoices):
    if not invoices:
        print("\nNo invoices found.")
        return
    
    print("\n--- Edit Invoice Status ---")
    invoice_id = input("Enter invoice ID: ").strip()
    
    invoice = next((inv for inv in invoices if inv["id"] == invoice_id), None)
    if not invoice:
        print(f"Invoice #{invoice_id} not found.")
        return
    
    print(f"Current status: {invoice['status']}")
    new_status = None
    while new_status is None:
        new_status = validate_status(input("New status (draft/sent/paid): "))
    
    invoice["status"] = new_status
    save_invoices(invoices)
    print(f"Invoice #{invoice_id} updated successfully.")

def delete_invoice(invoices):
    if not invoices:
        print("\nNo invoices found.")
        return
    
    print("\n--- Delete Invoice ---")
    invoice_id = input("Enter invoice ID: ").strip()
    
    invoice = next((inv for inv in invoices if inv["id"] == invoice_id), None)
    if not invoice:
        print(f"Invoice #{invoice_id} not found.")
        return
    
    confirm = input(f"Delete invoice #{invoice_id} for {invoice['client_name']}? (yes/no): ").strip().lower()
    if confirm == "yes":
        invoices.remove(invoice)
        save_invoices(invoices)
        print(f"Invoice #{invoice_id} deleted successfully.")
    else:
        print("Deletion cancelled.")

def export_to_csv(invoices):
    if not invoices:
        print("\nNo invoices to export.")
        return
    
    try:
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["id", "client_name", "date", "amount", "status"])
            writer.writeheader()
            writer.writerows(invoices)
        print(f"\nInvoices exported to {CSV_FILE} successfully.")
    except IOError as e:
        print(f"Error exporting to CSV: {e}")

def show_help():
    print("\n--- Invoice Tracker Help ---")
    print("1. Add Invoice       - Create a new invoice")
    print("2. List Invoices     - View invoices with filtering")
    print("3. Edit Status       - Update invoice status")
    print("4. Delete Invoice    - Remove an invoice")
    print("5. Export to CSV     - Export all invoices to CSV")
    print("6. Help              - Show this help message")
    print("7. Exit              - Quit the application")

def main():
    print("=== Invoice Tracker ===")
    
    while True:
        print("\n--- Main Menu ---")
        print("1. Add Invoice")
        print("2. List Invoices")
        print("3. Edit Status")
        print("4. Delete Invoice")
        print("5. Export to CSV")
        print("6. Help")
        print("7. Exit")
        
        choice = input("\nSelect an option (1-7): ").strip()
        
        invoices = load_invoices()
        
        if choice == "1":
            add_invoice(invoices)
        elif choice == "2":
            list_invoices(invoices)
        elif choice == "3":
            edit_invoice_status(invoices)
        elif choice == "4":
            delete_invoice(invoices)
        elif choice == "5":
            export_to_csv(invoices)
        elif choice == "6":
            show_help()
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please select 1-7.")

if __name__ == "__main__":
    main()