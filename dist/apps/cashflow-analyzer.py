# Auto-generated via Perplexity on 2026-01-28T07:38:22.461429Z
import curses
import json
import os
import sys
from datetime import datetime
from curses import wrapper
from curses.textpad import Textbox, rectangle
from collections import defaultdict

DATA_FILE = 'cashflow.json'
CATEGORIES = ['Food/Groceries', 'Rent/Utilities', 'Transport', 'Entertainment', 'Income', 'Other']

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_current_date():
    return datetime.now().strftime('%Y-%m-%d')

def add_sample_data(data):
    samples = [
        {'date': '2026-01-01', 'amount': 1000.0, 'category': 'Income', 'description': 'Salary'},
        {'date': '2026-01-02', 'amount': -50.0, 'category': 'Food/Groceries', 'description': 'Dinner'},
        {'date': '2026-01-03', 'amount': -100.0, 'category': 'Rent/Utilities', 'description': 'Rent'},
        {'date': '2026-01-04', 'amount': -25.0, 'category': 'Transport', 'description': 'Bus fare'},
        {'date': '2026-01-05', 'amount': -75.0, 'category': 'Food/Groceries', 'description': 'Groceries'}
    ]
    data.extend(samples)
    save_data(data)

def calculate_summary(data):
    total_income = sum(t['amount'] for t in data if t['amount'] > 0)
    total_expenses = sum(t['amount'] for t in data if t['amount'] < 0)
    net = total_income + total_expenses
    
    cat_totals = defaultdict(float)
    for t in data:
        cat_totals[t['category']] += t['amount']
    
    sorted_cats = sorted(cat_totals.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
    return total_income, total_expenses, net, dict(sorted_cats)

def filter_by_month(data, year, month):
    y, m = int(year), int(month)
    return [t for t in data if t['date'].startswith(f'{y}-{m:02d}')]

def export_csv(data, filename='cashflow_export.csv'):
    with open(filename, 'w') as f:
        f.write('Date,Amount,Category,Description\n')
        for t in data:
            f.write(f"{t['date']},{t['amount']:.2f},{t['category']},{t['description']}\n")

def draw_menu(stdscr, header_win, menu_win, status_win, selected, status_msg, data):
    header_win.clear()
    total_income, total_expenses, net, _ = calculate_summary(data)
    header_win.addstr(0, 0, f"Balance: ${net:.2f} | Income: ${total_income:.2f} | Expenses: ${total_expenses:.2f}", curses.A_REVERSE)
    header_win.refresh()
    
    menu_win.clear()
    menu_items = ['Add Transaction', 'View Summary', 'Monthly Report', 'Reset Data', 'Export CSV']
    for i, item in enumerate(menu_items):
        attr = curses.A_REVERSE if i == selected else 0
        menu_win.addstr(i+1, 1, item[:menu_win.getmaxyx()[1]-3], attr)
    menu_win.refresh()
    
    status_win.clear()
    status_win.addstr(0, 0, status_msg[:status_win.getmaxyx()[1]-3])
    status_win.refresh()

def input_textbox(win, prompt):
    win.clear()
    win.addstr(0, 0, prompt)
    textbox_win = curses.newwin(3, 40, 2, 1)
    rectangle(win, 1, 0, 1+3, 1+40)
    win.refresh()
    box = Textbox(textbox_win, show_echo=True)
    curses.echo()
    box.edit()
    curses.noecho()
    return box.gather().strip()

def select_category(stdscr, current=0):
    stdscr.clear()
    stdscr.addstr(0, 0, "Select category (arrows/enter):")
    while True:
        for i, cat in enumerate(CATEGORIES):
            attr = curses.A_REVERSE if i == current else 0
            stdscr.addstr(i+2, 0, f"  {cat}", attr)
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP and current > 0:
            current -= 1
        elif key == curses.KEY_DOWN and current < len(CATEGORIES)-1:
            current += 1
        elif key == 10 or key == curses.KEY_ENTER:  # Enter
            return CATEGORIES[current]
        elif key == 27 or key == ord('q'):  # ESC/q
            return None

def confirm_dialog(stdscr, msg):
    stdscr.clear()
    stdscr.addstr(0, 0, msg)
    stdscr.addstr(2, 0, "[y/N]")
    stdscr.refresh()
    return stdscr.getch() == ord('y')

def main(stdscr):
    curses.curs_set(0)
    curses.cbreak()
    stdscr.keypad(True)
    curses.noecho()
    
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    
    data = load_data()
    if not data:
        add_sample_data(data)
    
    sh, sw = stdscr.getmaxyx()
    header_win = curses.newwin(1, sw, 0, 0)
    menu_win = curses.newwin(sh-3, sw, 1, 0)
    status_win = curses.newwin(2, sw, sh-2, 0)
    
    selected = 0
    status_msg = "Use arrows to navigate, Enter to select, q/ESC to quit"
    
    while True:
        draw_menu(stdscr, header_win, menu_win, status_win, selected, status_msg, data)
        
        key = menu_win.getch()
        if key == 27 or key == ord('q'):  # ESC/q
            break
        elif key == curses.KEY_UP and selected > 0:
            selected -= 1
        elif key == curses.KEY_DOWN and selected < 4:
            selected += 1
        elif key == 10 or key == curses.KEY_ENTER:  # Enter
            if selected == 0:  # Add Transaction
                cat = select_category(stdscr)
                if not cat:
                    status_msg = "Add cancelled"
                    continue
                
                amount_str = input_textbox(stdscr, f"Amount (+ for income, - for expense) [{cat}]: ")
                try:
                    amount = float(amount_str)
                except ValueError:
                    status_msg = "Invalid amount"
                    continue
                
                desc = input_textbox(stdscr, "Description: ")
                
                data.append({
                    'date': get_current_date(),
                    'amount': amount,
                    'category': cat,
                    'description': desc
                })
                save_data(data)
                status_msg = f"Added: ${amount:.2f} {cat}"
            
            elif selected == 1:  # View Summary
                stdscr.clear()
                income, expenses, net, cats = calculate_summary(data)
                stdscr.addstr(0, 0, f"Totals: Income=${income:.2f}, Expenses=${expenses:.2f}, Net=${net:.2f}")
                for i, (cat, amt) in enumerate(cats.items()):
                    stdscr.addstr(i+2, 0, f"{cat}: ${amt:.2f}")
                stdscr.addstr(10, 0, "Press any key...")
                stdscr.refresh()
                stdscr.getch()
                status_msg = "Summary viewed"
            
            elif selected == 2:  # Monthly Report
                year = input_textbox(stdscr, "Year (YYYY): ")
                month = input_textbox(stdscr, "Month (1-12): ")
                try:
                    month_data = filter_by_month(data, year, month)
                    stdscr.clear()
                    inc, exp, net, cats = calculate_summary(month_data)
                    stdscr.addstr(0, 0, f"{year}-{month}: Income=${inc:.2f}, Expenses=${exp:.2f}, Net=${net:.2f}")
                    for i, (cat, amt) in enumerate(cats.items()):
                        stdscr.addstr(i+2, 0, f"{cat}: ${amt:.2f}")
                    stdscr.addstr(10, 0, "Press any key...")
                    stdscr.refresh()
                    stdscr.getch()
                    status_msg = f"Monthly report {year}-{month}"
                except:
                    status_msg = "Invalid date"
            
            elif selected == 3:  # Reset Data
                if confirm_dialog(stdscr, "Really reset all data? (y/N)"):
                    data.clear()
                    save_data(data)
                    status_msg = "Data reset"
                else:
                    status_msg = "Reset cancelled"
            
            elif selected == 4:  # Export CSV
                export_csv(data)
                status_msg = "Exported to cashflow_export.csv"
    
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.curs_set(1)

if __name__ == "__main__":
    wrapper(main)