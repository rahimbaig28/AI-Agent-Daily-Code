# Auto-generated via Perplexity on 2026-02-02T23:43:37.730599Z
#!/usr/bin/env python3
import curses
import json
import os
import datetime
import shutil
from curses import wrapper
from curses.textpad import rectangle, Textbox

DATA_FILE = 'cashflow.json'
CATEGORIES = ['Income', 'Food/Groceries', 'Rent/Utilities', 'Savings', 'Entertainment', 'Transport']
DEFAULT_BUDGETS = {cat: 0.0 for cat in CATEGORIES}

class CashFlowGrid:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.screen = curses.newwin(0, 0, 0, 0)
        self.screen.keypad(True)
        curses.curs_set(1)
        self.init_colors()
        self.transactions = []
        self.budgets = {}
        self.current_month = datetime.date.today().replace(day=1)
        self.focus_row = 0
        self.focus_col = 0
        self.editing = False
        self.popup_win = None
        self.textbox = None
        self.load_data()
        self.ensure_budgets()

    def init_colors(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)  # Focus
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Positive
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)    # Negative
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Normal
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Header

    def ensure_budgets(self):
        if not self.budgets:
            self.budgets = DEFAULT_BUDGETS.copy()
            self.save_data()

    def load_data(self):
        try:
            shutil.copy(DATA_FILE, DATA_FILE + '.bak')
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                self.transactions = data.get('transactions', [])
                self.budgets = data.get('budgets', {})
        except:
            self.transactions = []
            self.budgets = {}

    def save_data(self):
        data = {
            'transactions': self.transactions,
            'budgets': self.budgets
        }
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def parse_date(self, date_str):
        try:
            return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None

    def get_month_transactions(self, month):
        ym = month.strftime('%Y-%m')
        return [t for t in self.transactions 
                if self.parse_date(t['date']) and 
                self.parse_date(t['date']).strftime('%Y-%m') == ym]

    def aggregate_by_category(self, month):
        trans = self.get_month_transactions(month)
        actuals = {cat: 0.0 for cat in CATEGORIES}
        for t in trans:
            if t['category'] in actuals:
                sign = 1 if t['type'] == 'income' else -1
                actuals[t['category']] += sign * t['amount']
        return actuals

    def get_grid_data(self):
        actuals = self.aggregate_by_category(self.current_month)
        grid = []
        total_budget = total_actual = 0
        for cat in CATEGORIES:
            budget = self.budgets.get(cat, 0.0)
            actual = actuals.get(cat, 0.0)
            diff = actual - budget
            grid.append((cat, budget, actual, diff))
            total_budget += budget
            total_actual += actual
        grid.append(('NET CASHFLOW', total_budget, total_actual, total_actual - total_budget))
        return grid

    def format_amount(self, amt):
        color = curses.color_pair(2) if amt >= 0 else curses.color_pair(3)
        return f"{amt:8.2f}", color

    def draw_grid(self):
        self.screen.clear()
        h, w = self.screen.getmaxyx()
        grid = self.get_grid_data()
        
        # Headers
        headers = ["Category", "Budgeted", "Actual", "Diff"]
        for col, header in enumerate(headers):
            self.screen.addstr(0, col*12+1, header, curses.color_pair(5) | curses.A_BOLD)
        
        # Month display
        month_str = self.current_month.strftime("%B %Y")
        self.screen.addstr(0, w-len(month_str)-2, month_str, curses.color_pair(5) | curses.A_BOLD)
        
        # Grid rows
        for row, (cat, budget, actual, diff) in enumerate(grid):
            y = row + 1
            if y >= h-2: break
            
            # Category column
            self.screen.addstr(y, 0, cat[:10].ljust(11))
            
            # Data columns
            for col, value in enumerate([budget, actual, diff]):
                x = col*12 + 12
                fmt_val, color = self.format_amount(value)
                attr = color
                if row == self.focus_row:
                    attr |= curses.color_pair(1) | curses.A_BOLD
                self.screen.addstr(y, x, fmt_val, attr)
        
        # Help
        help_text = "?=help a=add d=del TAB=month 1-9=months ↑↓←→=nav ENT=edit"
        self.screen.addstr(h-1, 0, help_text[:w-1])
        
        self.screen.refresh()

    def show_help(self):
        h, w = self.screen.getmaxyx()
        help_win = curses.newwin(min(15, h-2), min(50, w-2), (h-15)//2, (w-50)//2)
        help_win.box()
        help_text = [
            "CONTROLS:",
            "↑↓←→  Navigate cells",
            "Enter  Edit focused cell",
            "Tab    Next month",
            "1-9    Jump to month N",
            "'a'    Add transaction",
            "'d'    Delete row",
            "Shift+↑↓ Reorder row",
            "'s'    Save & quit",
            "'?'    Show help",
            "",
            "MONTHS: 1=Current, 2=1mo ago, etc"
        ]
        for i, line in enumerate(help_text):
            if i < help_win.getmaxyx()[0]-2:
                help_win.addstr(i+1, 1, line[:help_win.getmaxyx()[1]-3])
        help_win.refresh()
        self.screen.getch()
        help_win.clear()
        del help_win

    def create_popup(self, height, width, title):
        h, w = self.screen.getmaxyx()
        py, px = (h-height)//2, (w-width)//2
        win = curses.newwin(height, width, py, px)
        rectangle(self.screen, py-1, px-1, py+height, px+width)
        self.screen.addstr(py-1, px+(width-len(title))//2, title)
        self.screen.refresh()
        return win

    def input_field(self, label, default=""):
        h, w = self.screen.getmaxyx()
        win = curses.newwin(4, 30, (h-4)//2, (w-30)//2)
        win.addstr(1, 1, f"{label}: {default}")
        textbox = Textbox(win)
        rectangle(self.screen, (h-4)//2-1, (w-30)//2-1, (h-4)//2+4, (w-30)//2+30)
        self.screen.refresh()
        textbox.edit()
        val = textbox.gather().strip()
        win.clear()
        del win, textbox
        self.screen.refresh()
        return val

    def add_transaction(self):
        today = datetime.date.today().strftime('%Y-%m-%d')
        date = self.input_field("Date (YYYY-MM-DD)", today)
        if not self.parse_date(date): return
        
        amount_str = self.input_field("Amount")
        try:
            amount = float(amount_str)
        except:
            return
        
        cat = self.input_field("Category", CATEGORIES[0])
        typ = self.input_field("Type (income/expense)", "expense")
        desc = self.input_field("Description", "")
        
        self.transactions.append({
            'date': date, 'amount': amount, 'type': typ,
            'category': cat, 'desc': desc
        })
        self.draw_grid()

    def delete_row(self):
        if self.focus_row < len(CATEGORIES):
            cat = CATEGORIES[self.focus_row]
            confirm = self.input_field("Delete all transactions for {}? (y/n)".format(cat[:10]), "n")
            if confirm.lower() == 'y':
                self.transactions = [t for t in self.transactions if t['category'] != cat]
                self.draw_grid()

    def edit_cell(self):
        row_data = self.get_grid_data()[self.focus_row]
        if self.focus_col == 0: return  # Can't edit category
        if self.focus_row == len(CATEGORIES): return  # Can't edit net row
        
        cat = row_data[0]
        field = ['budget', 'actual', 'diff'][self.focus_col-1]
        if field == 'actual': return  # Actuals computed
        if field == 'diff': return   # Diffs computed
        
        current = self.budgets.get(cat, 0.0)
        new_val_str = self.input_field(f"{cat} Budget", f"{current:.2f}")
        try:
            new_val = float(new_val_str)
            self.budgets[cat] = new_val
            self.draw_grid()
        except:
            pass

    def change_month(self, delta):
        year, month = self.current_month.year, self.current_month.month
        month += delta
        year += (month-1) // 12
        month = (month-1) % 12 + 1
        self.current_month = self.current_month.replace(year=year, month=month)

    def reorder_row(self, direction):
        if 0 <= self.focus_row < len(CATEGORIES)-1:
            cats = list(CATEGORIES)
            idx = self.focus_row
            cats[idx], cats[idx+direction] = cats[idx+direction], cats[idx]
            global CATEGORIES
            CATEGORIES = cats
            self.focus_row += direction
            if self.focus_row < 0: self.focus_row = 0
            self.draw_grid()

    def run(self):
        self.draw_grid()
        while True:
            try:
                key = self.screen.getch()
                
                if key == ord('?'):
                    self.show_help()
                elif key == ord('a'):
                    self.add_transaction()
                elif key == ord('d'):
                    self.delete_row()
                elif key == ord('s'):
                    self.save_data()
                    break
                elif key == 27:  # ESC
                    continue
                elif key in [ord('1'), ord('2'), ord('3'), ord('4'), ord('5'), ord('6'), ord('7'), ord('8'), ord('9')]:
                    months_back = key - ord('1') + 1
                    new_month = (self.current_month.replace(day=1) - datetime.timedelta(days=30*months_back)).replace(day=1)
                    self.current_month = new_month
                    self.draw_grid()
                elif key == curses.KEY_TAB or key == 9:
                    self.change_month(-1)
                    self.draw_grid()
                elif key == curses.KEY_UP:
                    if curses.has_key(curses.KEY_SHIFT):  # Simulate shift
                        self.reorder_row(-1)
                    else:
                        self.focus_row = max(0, self.focus_row-1)
                        self.draw_grid()
                elif key == curses.KEY_DOWN:
                    if curses.has_key(curses.KEY_SHIFT):
                        self.reorder_row(1)
                    else:
                        grid_rows = min(len(self.get_grid_data()), self.screen.getmaxyx()[0]-2)
                        self.focus_row = min(grid_rows-1, self.focus_row+1)
                        self.draw_grid()
                elif key == curses.KEY_LEFT:
                    self.focus_col = max(0, self.focus_col-1)
                    self.draw_grid()
                elif key == curses.KEY_RIGHT:
                    self.focus_col = min(3, self.focus_col+1)
                    self.draw_grid()
                elif key == curses.KEY_ENTER or key == 10 or key == 13:
                    self.edit_cell()
                else:
                    self.draw_grid()
                    
            except KeyboardInterrupt:
                self.save_data()
                break

def main(stdscr):
    app = CashFlowGrid(stdscr)
    app.run()
    curses.endwin()

if __name__ == "__main__":
    wrapper(main)