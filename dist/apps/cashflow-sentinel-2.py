# Auto-generated via Perplexity on 2026-02-10T15:25:03.632362Z
#!/usr/bin/env python3
import curses
import json
import datetime
import hashlib
import os
import sys
import re
from curses import wrapper, KEY_UP, KEY_DOWN, KEY_ENTER, KEY_LEFT, KEY_RIGHT

DATA_FILE = 'cashflow.json'
BACKUP_FILE = 'cashflow.json.bak'
EXPORT_FILE = 'export.json'
CATEGORIES = ['food', 'salary', 'rent', 'other']
TYPES = ['income', 'expense']

def get_theme():
    dark = os.environ.get('DARK_MODE') == '1' or os.environ.get('COLORF1') == '0'
    return 'dark' if dark else 'light'

def init_colors(stdscr, theme):
    curses.start_color()
    if theme == 'dark':
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # fg white, bg black
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)  # fg black, bg white (highlight)
    else:
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # fg black, bg white
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)  # fg white, bg black (highlight)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            # Validate data
            valid_data = []
            for t in data:
                if validate_transaction(t):
                    valid_data.append(t)
            if len(valid_data) != len(data):
                save_data(valid_data)
            return valid_data
        except:
            if os.path.exists(BACKUP_FILE):
                with open(BACKUP_FILE, 'r') as f:
                    return json.load(f)
            return []
    else:
        # Sample data on first run
        today = datetime.date.today().isoformat()
        samples = [
            {"date": today, "amount": 1000.0, "type": "income", "category": "salary", "desc": "Monthly salary", "hash": ""},
            {"date": today, "amount": 200.0, "type": "expense", "category": "rent", "desc": "Rent", "hash": ""},
            {"date": today, "amount": 50.0, "type": "expense", "category": "food", "desc": "Groceries", "hash": ""},
            {"date": today, "amount": 30.0, "type": "expense", "category": "food", "desc": "Lunch", "hash": ""},
            {"date": today, "amount": 20.0, "type": "expense", "category": "other", "desc": "Coffee", "hash": ""}
        ]
        for t in samples:
            t['hash'] = transaction_hash(t)
        save_data(samples)
        return samples
    return []

def save_data(data):
    try:
        if os.path.exists(DATA_FILE):
            os.rename(DATA_FILE, BACKUP_FILE)
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Save error: {e}", file=sys.stderr)

def transaction_hash(t):
    content = f"{t['date']}{t['amount']}{t['type']}{t['category']}{t['desc']}".encode()
    return hashlib.sha256(content).hexdigest()[:32]

def validate_transaction(t):
    try:
        datetime.date.fromisoformat(t['date'])
        float(t['amount'])
        t['type'] in TYPES
        t['category'] in CATEGORIES
        isinstance(t['desc'], str)
        return True
    except:
        return False

def parse_date(s):
    try:
        return datetime.date.fromisoformat(s).isoformat()
    except:
        return datetime.date.today().isoformat()

def get_balance(data):
    return sum(t['amount'] if t['type'] == 'income' else -t['amount'] for t in data)

def get_summary(data):
    income = sum(t['amount'] for t in data if t['type'] == 'income')
    expense = sum(t['amount'] for t in data if t['type'] == 'expense')
    return income, expense, income - expense

def monthly_totals(data):
    months = {}
    for t in data:
        month = t['date'][:7]
        months[month] = months.get(month, 0) + (t['amount'] if t['type'] == 'income' else -t['amount'])
    return sorted(months.items(), key=lambda x: x[0], reverse=True)

def category_totals(data):
    cats = {}
    for t in data:
        cats[t['category']] = cats.get(t['category'], 0) + (t['amount'] if t['type'] == 'income' else -t['amount'])
    total = sum(cats.values())
    return {k: v/total*100 for k,v in cats.items() if total > 0}

def ascii_pie(cats):
    total = sum(cats.values())
    if total == 0: return "No data"
    lines = []
    for cat, pct in sorted(cats.items(), key=lambda x: x[1], reverse=True)[:3]:
        bar = '█' * int(pct / 5)
        lines.append(f"{cat:8}: {bar} {pct:5.1f}%")
    return '\n'.join(lines)

def filter_data(data, date_from=None, date_to=None, type_filter=None, cat_filter=None):
    filtered = data[:]
    if date_from:
        filtered = [t for t in filtered if t['date'] >= date_from]
    if date_to:
        filtered = [t for t in filtered if t['date'] <= date_to]
    if type_filter:
        filtered = [t for t in filtered if t['type'] == type_filter]
    if cat_filter:
        filtered = [t for t in filtered if t['category'] == cat_filter]
    return filtered

def dataset_hash(data):
    content = json.dumps(sorted(data, key=lambda t: t['hash']))
    return hashlib.sha256(content.encode()).hexdigest()[:32]

def input_str(stdscr, y, x, prompt, default='', validate=None):
    stdscr.addstr(y, x, prompt + default)
    stdscr.refresh()
    curses.echo()
    curses.curs_set(1)
    try:
        while True:
            ch = stdscr.getch(y + len(prompt), x + len(default))
            if ch == 27 or ch == ord('\n'):  # Esc or Enter
                val = stdscr.instr(y, x + len(prompt), 50).decode().strip()
                if not validate or validate(val):
                    return val or default
                stdscr.addstr(y, x + len(prompt), ' ' * 50)
                stdscr.addstr(y, x, prompt + default)
                stdscr.refresh()
    finally:
        curses.noecho()
        curses.curs_set(0)

def select_item(stdscr, items, title):
    sel = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, title)
        for i, item in enumerate(items):
            attr = curses.color_pair(2) if i == sel else curses.color_pair(1)
            stdscr.addstr(i+2, 0, item, attr)
        stdscr.refresh()
        ch = stdscr.getch()
        if ch == KEY_UP and sel > 0: sel -= 1
        elif ch == KEY_DOWN and sel < len(items)-1: sel += 1
        elif ch == KEY_ENTER or ch == 10: return items[sel]
        elif ch == 27 or ch == ord('q'): return None

def draw_header(stdscr, balance, mode, theme):
    stdscr.addstr(0, 0, f"Balance: ${balance:8.2f} | Mode: {mode} | a=add v=view f=filter e=exp i=imp s=share ?=help q=quit", curses.color_pair(1))

def draw_list(stdscr, data, page, theme):
    per_page = 10
    start = page * per_page
    for i, t in enumerate(data[start:start+per_page]):
        line = f"{t['date']} {t['type'][:4]:6} ${t['amount']:8.2f} {t['category']:8} {t['desc'][:30]}"
        attr = curses.color_pair(1)
        stdscr.addstr(i+3, 0, line[:80], attr)
    stdscr.addstr(len(data[start:start+per_page])+3, 0, f"Page {page+1}/{max(1, (len(data)+9)//10)} ↑↓=nav pgup/pgdn=page q=back")

def main(stdscr):
    theme = get_theme()
    init_colors(stdscr, theme)
    curses.cbreak()
    curses.noecho()
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.timeout(100)

    data = load_data()
    mode = 'main'
    filter_params = {}
    page = 0
    balance = get_balance(data)

    while True:
        h, w = stdscr.getmaxyx()
        stdscr.clear()
        draw_header(stdscr, balance, mode, theme)

        if mode == 'main':
            menu = ['Add Transaction', 'View Summary', 'Filter View', 'Export JSON', 'Import JSON', 'Share Hash']
            sel = 0
            while True:
                for i, item in enumerate(menu):
                    attr = curses.color_pair(2) if i == sel else curses.color_pair(1)
                    stdscr.addstr(i+2, 2, item, attr)
                stdscr.addstr(8, 2, "↑↓=select Enter=go q=quit", curses.color_pair(1))
                stdscr.refresh()
                ch = stdscr.getkey()
                if ch == 'q' or ch == 'Q': return
                elif ch == 'a' or ch == 'A': mode = 'add'; break
                elif ch == 'v' or ch == 'V': mode = 'summary'; break
                elif ch == 'f' or ch == 'F': mode = 'filter'; break
                elif ch == 'e' or ch == 'E': export_data(data); continue
                elif ch == 'i' or ch == 'I': data = import_data(data); balance = get_balance(data); continue
                elif ch == 's' or ch == 'S': stdscr.addstr(10, 0, f"Share: cashflow://{dataset_hash(data)}"); stdscr.getch(); continue
                elif ch == '?': stdscr.addstr(10, 0, "a=add v=view f=filter e=exp i=imp s=share q=quit"); stdscr.getch(); continue
                elif ch == KEY_UP and sel > 0: sel -= 1
                elif ch == KEY_DOWN and sel < len(menu)-1: sel += 1
                elif ch in (KEY_ENTER, '\n'): 
                    if sel == 0: mode = 'add'
                    elif sel == 1: mode = 'summary'
                    elif sel == 2: mode = 'filter'
                    elif sel == 3: export_data(data)
                    elif sel == 4: data = import_data(data); balance = get_balance(data)
                    elif sel == 5: stdscr.addstr(10, 0, f"Share: cashflow://{dataset_hash(data)}"); stdscr.getch()
                    break

        elif mode == 'add':
            date = input_str(stdscr, 10, 2, "Date (YYYY-MM-DD) [today]: ", parse_date(''))
            try:
                amount = float(input_str(stdscr, 11, 2, "Amount: ", '0', lambda x: x.replace('.','').isdigit()))
            except: continue
            type_idx = 0
            type_sel = select_item(stdscr, TYPES, "Type: ↑↓ select Enter=ok")
            if type_sel: type_idx = TYPES.index(type_sel)
            cat_idx = 0
            cat_sel = select_item(stdscr, CATEGORIES, "Category: ↑↓ select Enter=ok")
            if cat_sel: cat_idx = CATEGORIES.index(cat_sel)
            desc = input_str(stdscr, 13, 2, "Description: ", '')
            t = {
                'date': date, 'amount': amount, 'type': TYPES[type_idx],
                'category': CATEGORIES[cat_idx], 'desc': desc,
                'hash': ''
            }
            t['hash'] = transaction_hash(t)
            data.append(t)
            save_data(data)
            balance = get_balance(data)
            mode = 'main'

        elif mode == 'summary':
            inc, exp, net = get_summary(data)
            months = monthly_totals(data)
            cats = category_totals(data)
            stdscr.addstr(2, 2, f"Income:  ${inc:8.2f}", curses.color_pair(1))
            stdscr.addstr(3, 2, f"Expense: ${exp:8.2f}", curses.color_pair(1))
            stdscr.addstr(4, 2, f"Net:     ${net:8.2f}", curses.color_pair(1))
            stdscr.addstr(6, 2, "Recent Months:")
            for i, (m, amt) in enumerate(months[:5]):
                stdscr.addstr(7+i, 2, f"{m}: ${amt:8.2f}")
            stdscr.addstr(13, 2, "Top Categories:")
            stdscr.addstr(14, 2, ascii_pie(cats))
            stdscr.addstr(20, 2, "Press any key to return")
            stdscr.refresh()
            stdscr.getch()
            mode = 'main'

        elif mode == 'filter':
            stdscr.addstr(2, 2, "f=from d=to t=type c=cat Enter=view q=back", curses.color_pair(1))
            stdscr.refresh()
            ch = stdscr.getkey()
            if ch == 'q': mode = 'main'
            elif ch == '\n':
                filtered = filter_data(data, **filter_params)
                balance = get_balance(filtered)
                mode = 'list'
                page = 0
            elif ch == 'f':
                filter_params['date_from'] = input_str(stdscr, 4, 2, "From (YYYY-MM-DD): ")
            elif ch == 'd':
                filter_params['date_to'] = input_str(stdscr, 5, 2, "To (YYYY-MM-DD): ")
            elif ch == 't':
                type_sel = select_item(stdscr, ['all'] + TYPES, "Type:")
                if type_sel != 'all': filter_params['type_filter'] = type_sel
                else: filter_params.pop('type_filter', None)
            elif ch == 'c':
                cat_sel = select_item(stdscr, ['all'] + CATEGORIES, "Category:")
                if cat_sel != 'all': filter_params['cat_filter'] = cat_sel
                else: filter_params.pop('cat_filter', None)

        elif mode == 'list':
            filtered = filter_data(data, **filter_params)
            draw_list(stdscr, filtered, page, theme)
            stdscr.refresh()
            ch = stdscr.getkey()
            if ch == 'q': mode = 'main'; page = 0; balance = get_balance(data)
            elif ch == KEY_UP and page > 0: page -= 1
            elif ch == KEY_DOWN: page += 1
            elif ch == 339: page = max(0, page-1)  # PgUp
            elif ch == 338: page += 1  # PgDn

def export_data(data):
    try:
        with open(EXPORT_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        pass

def import_data(data):
    try:
        with open(EXPORT_FILE, 'r') as f:
            new_data = json.load(f)
        hashes = {t['hash'] for t in data}
        for t in new_data:
            if validate_transaction(t) and t['hash'] not in hashes:
                data.append(t)
        save_data(data)
        return data
    except:
        return data

if __name__ == "__main__":
    try:
        wrapper(main)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fallback text mode due to error: {e}", file=sys.stderr)
        # Simple text fallback
        data = load_data()
        while True:
            print("\n1. Add 2. View 3. Quit")
            choice = input("> ")
            if choice == '3': break
            elif choice == '1':
                t = {}
                t['date'] = input("Date: ") or datetime.date.today().isoformat()
                t['amount'] = float(input("Amount: "))
                t['type'] = input("Type (income/expense): ")
                t['category'] = input("Category: ")
                t['desc'] = input("Desc: ")
                t['hash'] = transaction_hash(t)
                data.append(t)
                save_data(data)