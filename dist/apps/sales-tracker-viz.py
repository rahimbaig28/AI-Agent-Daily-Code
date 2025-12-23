# Auto-generated via Perplexity on 2025-12-23T04:36:54.965385Z
import json
import csv
import datetime
import os
import sys
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

DATA_FILE = 'sales_data.json'
EXPORT_FILE = 'sales_export.csv'
CATEGORIES = ['Electronics', 'Clothing', 'Food', 'Other']
CATEGORY_COLORS = {
    'Electronics': 'blue',
    'Clothing': 'green',
    'Food': 'orange',
    'Other': 'gray'
}

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        else:
            # Pre-populate sample data on first run
            sample_data = [
                {'date': '2025-12-20', 'product': 'iPhone 15', 'category': 'Electronics', 'units': 2, 'price': 999.99},
                {'date': '2025-12-21', 'product': 'T-Shirt', 'category': 'Clothing', 'units': 5, 'price': 29.99},
                {'date': '2025-12-22', 'product': 'Pizza', 'category': 'Food', 'units': 3, 'price': 15.99},
                {'date': '2025-12-22', 'product': 'Laptop', 'category': 'Electronics', 'units': 1, 'price': 1299.99}
            ]
            save_data(sample_data)
            return sample_data
    except:
        return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_unique_key(sale):
    return f"{sale['date']}_{sale['product']}"

def add_sale():
    print("\n--- Add Sale ---")
    product = input("Product: ").strip()
    if not product:
        print("Invalid product name.")
        return
    
    print("Category (enter number 1-4):")
    for i, cat in enumerate(CATEGORIES, 1):
        print(f"{i}. {cat}")
    while True:
        try:
            cat_choice = input("Choice: ").strip()
            category = CATEGORIES[int(cat_choice) - 1]
            break
        except:
            print("Invalid choice. Try again.")
    
    while True:
        try:
            units = int(input("Units: "))
            if units <= 0:
                raise ValueError
            break
        except:
            print("Invalid units. Enter positive integer.")
    
    while True:
        try:
            price = float(input("Price: "))
            if price <= 0:
                raise ValueError
            break
        except:
            print("Invalid price. Enter positive number.")
    
    sale = {
        'date': datetime.date.today().isoformat(),
        'product': product,
        'category': category,
        'units': units,
        'price': price
    }
    data = load_data()
    data.append(sale)
    save_data(data)
    print("Sale added successfully!")

def view_table(data):
    if not data:
        print("\nNo data available.")
        return
    
    print("\n{'Date':<12} {'Product':<15} {'Category':<10} {'Units':<6} {'Price':<8} {'Total'}")
    print("-" * 70)
    for sale in data:
        total = sale['units'] * sale['price']
        print(f"{sale['date']:<12} {sale['product']:<15} {sale['category']:<10} {sale['units']:<6} ${sale['price']:<7.2f} ${total:>8.2f}")

def prepare_viz_data(data, filter_category=None):
    if filter_category and filter_category != 'all':
        data = [s for s in data if s['category'] == filter_category]
    
    if not data:
        return None, None, None, None
    
    # Revenue by category
    rev_by_cat = defaultdict(float)
    for sale in data:
        rev_by_cat[sale['category']] += sale['units'] * sale['price']
    
    # Daily totals
    daily_totals = defaultdict(float)
    for sale in data:
        daily_totals[sale['date']] += sale['units'] * sale['price']
    dates = sorted(daily_totals.keys())
    daily_values = [daily_totals[d] for d in dates]
    
    # Units by category
    units_by_cat = defaultdict(int)
    for sale in data:
        units_by_cat[sale['category']] += sale['units']
    
    # Units vs price per product
    products = {}
    for sale in data:
        key = sale['product']
        if key not in products:
            products[key] = {'units': 0, 'price': sale['price']}
        products[key]['units'] += sale['units']
    
    return rev_by_cat, (dates, daily_values), units_by_cat, products

def show_dashboard(data, filter_category=None):
    os.system('clear' if os.name == 'posix' else 'cls')
    print("Sales Dashboard" + (f" (Filtered: {filter_category})" if filter_category != 'all' else ""))
    
    rev_by_cat, daily_data, units_by_cat, products = prepare_viz_data(data, filter_category)
    
    if not rev_by_cat:
        print("No data available for visualization.")
        input("Press Enter to continue...")
        return
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Sales Tracker Dashboard', fontsize=16, fontweight='bold')
    
    # Top-left: Revenue by category (bar)
    cats = list(rev_by_cat.keys())
    revs = list(rev_by_cat.values())
    colors = [CATEGORY_COLORS.get(cat, 'gray') for cat in cats]
    bars1 = ax1.bar(cats, revs, color=colors, alpha=0.7)
    ax1.set_title('Total Revenue by Category')
    ax1.set_ylabel('Revenue ($)')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)
    
    # Top-right: Daily sales (line)
    dates, values = daily_data
    ax2.plot(dates, values, marker='o', linewidth=2, markersize=6, color='purple')
    ax2.set_title('Daily Total Sales')
    ax2.set_ylabel('Total Sales ($)')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3)
    
    # Bottom-left: Units by category (pie)
    units_cats = list(units_by_cat.keys())
    units_vals = list(units_by_cat.values())
    colors_pie = [CATEGORY_COLORS.get(cat, 'gray') for cat in units_cats]
    ax3.pie(units_vals, labels=units_cats, autopct='%1.1f%%', colors=colors_pie, startangle=90)
    ax3.set_title('Units by Category')
    
    # Bottom-right: Units vs price (scatter)
    prod_names = list(products.keys())
    units_list = [products[p]['units'] for p in prod_names]
    prices_list = [products[p]['price'] for p in prod_names]
    scatter_colors = [CATEGORY_COLORS.get(next(s['category'] for s in data if s['product'] == p), 'gray') 
                     for p in prod_names]
    ax4.scatter(units_list, prices_list, c=scatter_colors, s=100, alpha=0.7)
    ax4.set_xlabel('Total Units')
    ax4.set_ylabel('Price per Unit ($)')
    ax4.set_title('Units vs Price per Product')
    ax4.grid(True, alpha=0.3)
    
    legend_elements = [mpatches.Patch(color=CATEGORY_COLORS[cat], label=cat) 
                      for cat in CATEGORIES if cat in rev_by_cat]
    if legend_elements:
        fig.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.02))
    
    plt.tight_layout()
    plt.show(block=False)
    input("\nPress Enter to continue...")

def export_csv(data, filename):
    if not data:
        print("No data to export.")
        return
    
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'product', 'category', 'units', 'price', 'total'])
        writer.writeheader()
        for sale in data:
            writer.writerow({**sale, 'total': sale['units'] * sale['price']})
    print(f"Data exported to {filename}")

def import_json(filename):
    try:
        with open(filename, 'r') as f:
            new_data = json.load(f)
        
        existing_data = load_data()
        existing_keys = {get_unique_key(s): s for s in existing_data}
        
        for sale in new_data:
            key = get_unique_key(sale)
            if key not in existing_keys:
                existing_data.append(sale)
        
        save_data(existing_data)
        print(f"Imported {len(new_data)} records ({len(new_data) - len([s for s in new_data if get_unique_key(s) in existing_keys])} new).")
    except Exception as e:
        print(f"Error importing {filename}: {e}")

def main():
    # Handle drag-drop
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if filename.endswith('.json'):
            import_json(filename)
        elif filename.endswith('.csv'):
            print("CSV import not implemented.")
        print("Press Enter to continue...")
        input()
    
    while True:
        data = load_data()
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=== Sales Tracker ===")
        print("1. Add sale")
        print("2. View data table")
        print(f"3. Dashboard ({len(data)} records)")
        print("4. Filter & viz")
        print("5. Export CSV")
        print("6. Import JSON")
        print("q. Quit")
        
        choice = input("\nChoice (1-6, q): ").strip().lower()
        
        if choice == 'q':
            break
        elif choice == '1':
            add_sale()
        elif choice == '2':
            view_table(data)
        elif choice == '3':
            show_dashboard(data)
        elif choice == '4':
            print("\nFilter by category:")
            print("0. All")
            for i, cat in enumerate(CATEGORIES, 1):
                print(f"{i}. {cat}")
            filt = input("Choice (0-4): ").strip()
            filter_cat = 'all'
            if filt in '1234':
                filter_cat = CATEGORIES[int(filt) - 1]
            filtered_data = [s for s in data if filter_cat == 'all' or s['category'] == filter_cat]
            show_dashboard(filtered_data, filter_cat)
        elif choice == '5':
            filename = input("Export filename (default: sales_export.csv): ").strip() or EXPORT_FILE
            export_csv(data, filename)
        elif choice == '6':
            filename = input("JSON filename: ").strip()
            if filename:
                import_json(filename)
        else:
            print("Invalid choice.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()