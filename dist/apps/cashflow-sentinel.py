# Auto-generated via Perplexity on 2026-02-05T03:09:50.001460Z
#!/usr/bin/env python3
import curses
import json
import datetime
import os
import sys
from collections import defaultdict, Counter
from curses import wrapper

DATA_FILE = 'cashflow.json'
CATEGORIES = {'groceries', 'rent', 'salary', 'bills', 'other'}
COLOR_LIGHT = 1
COLOR_DARK = 2
add_count = 0

def load_data():
    if not os.path.exists(DATA_FILE):
        return [
            {'date': '2026-02-01', 'amount': 3000.0, 'type': 'income', 'category': 'salary', 'desc': 'Monthly salary'},
            {'date': '2026-02-02', 'amount': 250.0, 'type': 'expense', 'category': 'groceries', 'desc': 'Weekly groceries'},
            {'date': '2026-02-03', 'amount': 1200.0, 'type': 'expense', 'category': 'rent', 'desc': 'February rent'}
        ]
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return [dict(t) for t in data if all(k in t for k in ['date', 'amount', 'type', 'category', 'desc'])]
    except:
        return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def validate_date(date_str):
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except:
        return False

def get_input(stdscr, prompt, default='', validator=None):
    curses.echo()
    curses.curs_set(1)
    stdscr.addstr(0, 0, prompt + (default if default else ''))
    if default:
        stdscr.clrtoeol()
    stdscr.refresh()
    while True:
        ch = stdscr.getch()
        if ch == 27:  # ESC
            curses.noecho()
            curses.curs_set(0)
            return None
        elif ch == 10 or ch == 13:  # Enter
            val = stdscr.getstr(0, len(prompt), 100).decode().strip()
            curses.noecho()
            curses.curs_set(0)
            if not val and default:
                return default
            if val and (validator is None or validator(val)):
                return val
            stdscr.addstr(1, 0, "Invalid input. Press any key.")
            stdscr.getch()
            stdscr.clear()
            stdscr.addstr(0, 0, prompt + (default if default else ''))
            stdscr.refresh()
        elif ch == 127 or ch == curses.KEY_BACKSPACE:
            stdscr.delch(0, stdscr.getyx()[1] - 1)
            stdscr.refresh()

def detect_theme(stdscr):
    try:
        curses.use_default_colors()
        curses.start_color()
        if curses.can_change_color():
            return COLOR_LIGHT
        curses.init_pair(COLOR_DARK, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_LIGHT, curses.COLOR_BLACK, curses.COLOR_WHITE)
        return COLOR_DARK
    except:
        curses.init_pair(COLOR_DARK, curses.COLOR_GREEN, curses.COLOR_BLACK)
        return COLOR_DARK

def draw_menu(stdscr, selected, theme):
    stdscr.clear()
    stdscr.addstr(0, 0, "=== CashFlow Sentinel ===", curses.A_BOLD)
    menu_items = [
        "A - Add transaction",
        "V - View summary", 
        "F - Filter by period",
        "E - Edit last transaction",
        "R - Reset data (clear all)",
        "Q - Quit"
    ]
    for i, item in enumerate(menu_items):
        attr = curses.A_REVERSE if i == selected else 0
        color = curses.color_pair(theme)
        stdscr.addstr(2 + i, 2, item, attr | color)
    stdscr.refresh()

def add_transaction(stdscr, data, theme):
    global add_count
    stdscr.clear()
    today = datetime.date.today().isoformat()
    
    date = get_input(stdscr, "Date (YYYY-MM-DD) [{}] : ".format(today), today, validate_date)
    if date is None:
        return data
    
    while True:
        amount_str = get_input(stdscr, "Amount: ")
        if amount_str is None:
            return data
        try:
            amount = float(amount_str)
            if amount > 0:
                break
            stdscr.addstr(3, 0, "Amount must be positive.")
        except:
            stdscr.addstr(3, 0, "Invalid amount.")
        stdscr.getch()
    
    txn_type = get_input(stdscr, "Type (income/expense): ")
    if txn_type is None or txn_type not in ['income', 'expense']:
        return data
    
    category = get_input(stdscr, "Category ({}) : ".format('/'.join(CATEGORIES)))
    if category is None or category not in CATEGORIES:
        return data
    
    desc = get_input(stdscr, "Description: ") or 'No description'
    
    txn = {
        'date': date,
        'amount': amount,
        'type': txn_type,
        'category': category,
        'desc': desc[:30] + '...' if len(desc) > 30 else desc
    }
    data.append(txn)
    add_count += 1
    
    stdscr.clear()
    stdscr.addstr(0, 0, "Added: {} ${:.2f} {} - {}".format(
        txn['date'], txn['amount'], txn['type'], txn['desc']), curses.color_pair(theme))
    stdscr.addstr(2, 0, "Summary: Income=${:.2f}, Expense=${:.2f}, Net=${:.2f}".format(
        sum(t['amount'] for t in data if t['type'] == 'income'),
        sum(t['amount'] for t in data if t['type'] == 'expense'),
        sum(t['amount'] if t['type'] == 'income' else -t['amount'] for t in data)
    ))
    stdscr.getch()
    return data

def view_summary(stdscr, data, theme):
    stdscr.clear()
    income = sum(t['amount'] for t in data if t['type'] == 'income')
    expense = sum(t['amount'] for t in data if t['type'] == 'expense')
    net = income - expense
    
    stdscr.addstr(0, 0, "=== SUMMARY ===", curses.A_BOLD | curses.color_pair(theme))
    stdscr.addstr(2, 0, f"Total Income:  ${income:>8.2f}", curses.color_pair(theme) | curses.A_BOLD)
    stdscr.addstr(3, 0, f"Total Expense: ${expense:>8.2f}", curses.color_pair(theme+1) | curses.A_BOLD)
    stdscr.addstr(4, 0, f"Net Cashflow:  ${net:>8.2f}", 
                 curses.color_pair(theme if net >= 0 else theme+1) | curses.A_BOLD)
    
    cat_breakdown = Counter(t['category'] for t in data)
    stdscr.addstr(6, 0, "Category breakdown:", curses.A_BOLD | curses.color_pair(theme))
    for i, (cat, count) in enumerate(cat_breakdown.most_common()):
        if i * 20 < curses.LINES - 8:
            bar = '#' * min(count * 3, 30)
            stdscr.addstr(8 + i, 2, f"{cat:10}: {count:2d} [{bar}]")
    
    stdscr.addstr(curses.LINES-2, 0, "Press any key to return")
    stdscr.refresh()
    stdscr.getch()

def filter_period(stdscr, data, theme):
    stdscr.clear()
    start_date = get_input(stdscr, "Start date (YYYY-MM-DD): ")
    if start_date is None or not validate_date(start_date):
        return
    end_date = get_input(stdscr, "End date (YYYY-MM-DD): ")
    if end_date is None or not validate_date(end_date):
        return
    
    filtered = [t for t in data if start_date <= t['date'] <= end_date]
    if not filtered:
        stdscr.addstr(2, 0, "No transactions found.", curses.color_pair(theme))
        stdscr.getch()
        return
    
    stdscr.clear()
    stdscr.addstr(0, 0, f"Transactions {start_date} to {end_date}:", curses.A_BOLD | curses.color_pair(theme))
    for i, t in enumerate(filtered[:20]):
        color = curses.color_pair(theme) if t['type'] == 'income' else curses.color_pair(theme+1)
        stdscr.addstr(2+i, 0, f"{t['date']:10} {t['type']:7} ${t['amount']:8.2f} {t['category']:10} {t['desc']}")
    stdscr.addstr(curses.LINES-2, 0, "Press any key to return")
    stdscr.refresh()
    stdscr.getch()

def edit_last(stdscr, data, theme):
    if not data:
        stdscr.addstr(2, 0, "No transactions to edit.")
        stdscr.getch()
        return data
    last = data[-1]
    stdscr.clear()
    stdscr.addstr(0, 0, f"Editing: {last}", curses.A_BOLD | curses.color_pair(theme))
    data[-1] = add_transaction(stdscr, data, theme)[-1] if len(data) > 0 else data
    return data

def reset_data(stdscr, theme):
    stdscr.clear()
    stdscr.addstr(0, 0, "Really reset ALL data? (y/N): ", curses.A_BOLD | curses.color_pair(theme))
    stdscr.refresh()
    ch = stdscr.getch()
    if ch == ord('y') or ch == ord('Y'):
        save_data([])
        stdscr.addstr(2, 0, "Data reset!")
        stdscr.getch()
    else:
        stdscr.addstr(2, 0, "Cancelled.")
        stdscr.getch()

def display_transactions(stdscr, data, theme, page=0):
    per_page = 20
    start = page * per_page
    end = start + per_page
    page_data = data[start:end]
    
    stdscr.clear()
    stdscr.addstr(0, 0, "Transactions (PgUp/PgDn/Q)", curses.A_BOLD | curses.color_pair(theme))
    header = f"{'Date':^10} {'Type':^7} {'Amount':^9} {'Category':^10} {'Description'}"
    stdscr.addstr(2, 0, header, curses.A_REVERSE | curses.color_pair(theme))
    
    for i, t in enumerate(page_data):
        color = curses.color_pair(theme) if t['type'] == 'income' else curses.color_pair(theme+1)
        line = f"{t['date'][:10]:^10} {t['type'][:7]:^7} ${t['amount']:>7.2f} {t['category'][:10]:^10} {t['desc'][:25]:25}"
        stdscr.addstr(3+i, 0, line[:80], color)
    
    pages = (len(data) + per_page - 1) // per_page
    stdscr.addstr(curses.LINES-2, 0, f"Page {page+1}/{pages} - {len(data)} total")
    stdscr.refresh()

def main(stdscr):
    global add_count
    curses.curs_set(0)
    curses.noecho()
    theme = detect_theme(stdscr)
    
    data = load_data()
    if add_count >= 5:
        save_data(data)
        add_count = 0
    
    selected = 0
    menu_keys = {'a': 0, 'v': 1, 'f': 2, 'e': 3, 'r': 4}
    
    while True:
        draw_menu(stdscr, selected, theme)
        key = stdscr.getch()
        
        if key == ord('q') or key == 27:
            if add_count > 0:
                stdscr.addstr(10, 0, "Save before quit? (y/N): ")
                stdscr.refresh()
                ch = stdscr.getch()
                if ch in (ord('y'), ord('Y')):
                    save_data(data)
            save_data(data)
            break
        elif key == curses.KEY_UP:
            selected = (selected - 1) % 6
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % 6
        elif key == 10 or key == 13:  # Enter
            if selected == 0:
                data = add_transaction(stdscr, data, theme)
            elif selected == 1:
                view_summary(stdscr, data, theme)
            elif selected == 2:
                filter_period(stdscr, data, theme)
            elif selected == 3:
                data = edit_last(stdscr, data, theme)
            elif selected == 4:
                reset_data(stdscr, theme)
        elif chr(key).lower() in menu_keys:
            selected = menu_keys[chr(key).lower()]

if __name__ == "__main__":
    wrapper(main)