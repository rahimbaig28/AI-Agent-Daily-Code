# Auto-generated via Perplexity on 2025-12-26T04:34:33.817266Z
import curses
import json
import datetime
import os
import csv
import statistics
import base64
import hashlib
from curses import wrapper
from curses.textpad import Textbox, rectangle
from datetime import timedelta

DATA_FILE = 'cashflow.json'
BACKUP_FILE = 'cashflow_backup.json'

def init_data():
    if not os.path.exists(DATA_FILE):
        sample_data = [
            {'date': '2025-12-20', 'amount': 3000.0, 'category': 'salary', 'description': 'Monthly salary'},
            {'date': '2025-12-22', 'amount': 1500.0, 'category': 'salary', 'description': 'Freelance work'},
            {'date': '2025-12-24', 'amount': 500.0, 'category': 'bonus', 'description': 'Holiday bonus'},
            {'date': '2025-12-21', 'amount': -250.0, 'category': 'groceries', 'description': 'Weekly shopping'},
            {'date': '2025-12-23', 'amount': -120.0, 'category': 'rent', 'description': 'Rent payment'},
            {'date': '2025-12-24', 'amount': -45.0, 'category': 'utilities', 'description': 'Electricity bill'},
            {'date': '2025-12-25', 'amount': -80.0, 'category': 'groceries', 'description': 'Christmas dinner'},
            {'date': '2025-12-25', 'amount': -200.0, 'category': 'gifts', 'description': 'Holiday gifts'}
        ]
        save_data(sample_data)

def save_data(transactions):
    try:
        if os.path.exists(DATA_FILE):
            os.rename(DATA_FILE, BACKUP_FILE)
        with open(DATA_FILE, 'w') as f:
            json.dump(transactions, f, indent=2)
    except Exception as e:
        status_msg = f"Save failed: {e}"
        return False, status_msg
    return True, "Saved successfully"

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        return []
    except:
        if os.path.exists(BACKUP_FILE):
            try:
                with open(BACKUP_FILE, 'r') as f:
                    data = json.load(f)
                with open(DATA_FILE, 'w') as f:
                    json.dump(data, f)
                return data
            except:
                pass
        return []

def parse_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return None

def get_today():
    return datetime.date.today()

def get_balance(transactions):
    return sum(t['amount'] for t in transactions)

def get_daily_nets(transactions, days=30):
    today = get_today()
    cutoff = today - timedelta(days=days)
    daily = {}
    
    for t in transactions:
        date = parse_date(t['date'])
        if date and cutoff <= date <= today:
            d_str = date.strftime('%Y-%m-%d')
            daily[d_str] = daily.get(d_str, 0) + t['amount']
    
    return list(daily.values())

def get_forecast(daily_nets):
    if not daily_nets:
        return 0.0, "No data"
    
    avg_daily = statistics.mean(daily_nets)
    forecast_7d = avg_daily * 7
    
    if len(daily_nets) > 1:
        std_dev = statistics.stdev(daily_nets)
        reliability = "High" if std_dev < 50 else "Medium" if std_dev < 200 else "Low"
    else:
        std_dev = 0
        reliability = "No data"
    
    return forecast_7d, f"Avg: ${avg_daily:.0f}/day, Std: {std_dev:.0f}, {reliability}"

def get_category_summary(transactions):
    cat_totals = {}
    for t in transactions:
        cat = t['category']
        cat_totals[cat] = cat_totals.get(cat, 0) + t['amount']
    
    # Sort by total spent (negative amounts first)
    sorted_cats = sorted(cat_totals.items(), key=lambda x: x[1])
    return sorted_cats[:5]

def get_recent_transactions(transactions, n=10):
    def date_key(t):
        return parse_date(t['date']) or datetime.date.min
    return sorted(transactions, key=date_key, reverse=True)[:n]

def input_dialog(stdscr, title, fields, default_values=None):
    h, w = stdscr.getmaxyx()
    dialog_h = len(fields) * 2 + 4
    dialog_w = 50
    y, x = (h - dialog_h) // 2, (w - dialog_w) // 2
    
    win = curses.newwin(dialog_h, dialog_w, y, x)
    rectangle(stdscr, y, x, y + dialog_h, x + dialog_w)
    stdscr.addstr(y, x + (dialog_w - len(title)) // 2, title)
    stdscr.refresh()
    
    values = default_values or [''] * len(fields)
    for i, (field, val) in enumerate(zip(fields, values)):
        stdscr.addstr(y + 2 + i*2, x + 2, f"{field}: {val}")
    
    stdscr.refresh()
    win.refresh()
    
    def validate_input():
        try:
            if fields[0] == "date":
                parse_date(values[0])
            if fields[1] == "amount":
                float(values[1])
            return True
        except:
            return False
    
    while True:
        stdscr.addstr(h-1, 0, " " * w)
        if not validate_input():
            stdscr.addstr(h-1, 0, "Invalid date or amount! Press Enter to retry.")
        stdscr.refresh()
        
        win.clear()
        rectangle(stdscr, y, x, y + dialog_h, x + dialog_w)
        stdscr.addstr(y, x + (dialog_w - len(title)) // 2, title)
        
        for i, (field, val) in enumerate(zip(fields, values)):
            stdscr.addstr(y + 2 + i*2, x + 2, f"{field}: {val}")
        
        stdscr.refresh()
        
        textbox_win = curses.newwin(1, dialog_w-4, y + 2 + len(fields)*2, x + 2)
        textbox = Textbox(textbox_win, insert_mode=True)
        curses.echo()
        textbox.edit()
        curses.noecho()
        new_line = textbox.gather().strip()
        
        if new_line == '' or new_line.lower() == 'q':
            return None
        
        field_idx = len(fields) - 1  # Edit last field (amount/description)
        values[field_idx] = new_line
        
        if textbox_win.getch() == 10:  # Enter
            if validate_input():
                break
    
    win.clear()
    stdscr.refresh()
    return values

def share_summary(transactions):
    balance = get_balance(transactions)
    daily_nets = get_daily_nets(transactions)
    forecast, _ = get_forecast(daily_nets)
    
    summary = {
        'balance': round(balance, 2),
        'forecast_7d': round(forecast, 2),
        'date': get_today().isoformat()
    }
    
    data = json.dumps(summary).encode()
    hash_obj = hashlib.sha256(data)
    hash_b64 = base64.urlsafe_b64encode(hash_obj.digest()).decode()[:8]
    print(f"Share: cashflow://{hash_b64}")
    return hash_b64

def draw_dashboard(stdscr, transactions, selected_idx=0):
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    
    if not transactions:
        stdscr.addstr(h//2, w//2 - 10, "No transactions yet!")
        stdscr.refresh()
        return
    
    balance = get_balance(transactions)
    daily_nets = get_daily_nets(transactions)
    forecast, forecast_info = get_forecast(daily_nets)
    
    # Header
    stdscr.addstr(0, 0, "Cash Flow Forecaster", curses.A_BOLD)
    stdscr.addstr(1, 0, f"Balance: ${balance:,.2f}", curses.A_BOLD | 
                  (curses.color_pair(1) if balance >= 0 else curses.color_pair(2)))
    stdscr.addstr(1, 20, f"7-Day Forecast: ${forecast:,.0f} ({forecast_info})", curses.A_BOLD)
    
    # Category table
    stdscr.addstr(3, 0, "Top 5 Categories:", curses.A_BOLD)
    cat_summary = get_category_summary(transactions)
    for i, (cat, total) in enumerate(cat_summary):
        color = curses.color_pair(1) if total >= 0 else curses.color_pair(2)
        stdscr.addstr(4 + i, 0, f"{cat:<12}: ${total:>8,.0f}", color)
    
    # Recent transactions
    stdscr.addstr(3, 25, "Recent Transactions:", curses.A_BOLD)
    recent = get_recent_transactions(transactions)
    for i, t in enumerate(recent[:6]):  # Show 6 to fit screen
        color = curses.color_pair(1) if t['amount'] >= 0 else curses.color_pair(2)
        date_str = t['date'][-5:]  # MM-DD
        stdscr.addstr(4 + i, 25, f"{date_str} {t['category']:<10} ${t['amount']:>8.0f}", color)
        if i < len(recent) and len(t['description']) > 0:
            stdscr.addstr(4 + i, 60, t['description'][:15])
    
    # Instructions
    stdscr.addstr(h-3, 0, "↑↓ Scroll | Enter Edit | + Add | s Save | r Refresh | q Quit | x Share", curses.A_BOLD)
    
    # Status
    stdscr.addstr(h-1, 0, f"Transactions: {len(transactions)} | Selected: {selected_idx + 1}/{len(transactions)}")
    
    stdscr.refresh()

def main(stdscr):
    curses.curs_set(0)
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Income
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)    # Expense
    
    transactions = load_data()
    init_data()
    if not transactions:
        transactions = load_data()
    
    selected_idx = 0
    mode = 'dashboard'  # 'dashboard', 'edit'
    
    while True:
        if mode == 'dashboard':
            draw_dashboard(stdscr, transactions, selected_idx)
            
            key = stdscr.getch()
            if key == ord('q'):
                break
            elif key == ord('s'):
                success, msg = save_data(transactions)
                stdscr.addstr(stdscr.getmaxyx()[0]-1, 0, f" {msg} " * 20)
                stdscr.refresh()
                stdscr.getch()
            elif key == ord('r'):
                pass  # Refresh already happens
            elif key == ord('+'):
                today_str = get_today().isoformat()
                values = input_dialog(stdscr, "Add Transaction", 
                                    ["date", "amount", "category", "description"],
                                    [today_str, "0.0", "other", ""])
                if values:
                    try:
                        transactions.append({
                            'date': values[0],
                            'amount': float(values[1]),
                            'category': values[2],
                            'description': values[3]
                        })
                        selected_idx = len(transactions) - 1
                    except:
                        pass
            elif key == ord('x'):
                share_summary(transactions)
            elif key in [curses.KEY_UP, ord('k')]:
                selected_idx = max(0, selected_idx - 1)
            elif key in [curses.KEY_DOWN, ord('j')]:
                selected_idx = min(len(transactions) - 1, selected_idx + 1)
            elif key == curses.KEY_ENTER or key == 10:
                if transactions:
                    t = transactions[selected_idx]
                    values = input_dialog(stdscr, "Edit Transaction", 
                                        ["date", "amount", "category", "description"],
                                        [t['date'], str(t['amount']), t['category'], t['description']])
                    if values:
                        transactions[selected_idx] = {
                            'date': values[0],
                            'amount': float(values[1]),
                            'category': values[2],
                            'description': values[3]
                        }
        
        stdscr.refresh()
    
    save_data(transactions)
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.curs_set(1)

if __name__ == "__main__":
    wrapper(main)