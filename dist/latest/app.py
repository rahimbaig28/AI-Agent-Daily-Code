# Auto-generated via Perplexity on 2025-12-15T04:39:06.985781Z
import curses
import json
import os
import datetime
from curses import wrapper, newwin, newpad
from curses.textpad import Textbox, rectangle
from datetime import datetime, date
import re

DATA_FILE = 'cashflow.json'
CATEGORIES = ['Food', 'Groceries', 'Rent', 'Utilities', 'Entertainment', 'Salary', 'Other']
GRID_ROWS, GRID_COLS = 20, 4
COL_WIDTHS = [12, 12, 15, 12]
SAVE_ACTIONS = 5

class CashFlowAnalyzer:
    def __init__(self):
        self.transactions = []
        self.selected_row = 0
        self.scroll_offset = 0
        self.monthly_filter = False
        self.action_count = 0
        self.editing = False
        self.edit_col = 0
        self.edit_row = 0
        self.load_data()
    
    def load_data(self):
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.transactions = [self.validate_txn(t) for t in data]
        except:
            self.transactions = []
    
    def validate_txn(self, txn):
        try:
            txn['date'] = datetime.strptime(txn['date'], '%Y-%m-%d').strftime('%Y-%m-%d')
            txn['amount'] = float(txn['amount'])
            txn['category'] = str(txn.get('category', 'Other'))
            txn['desc'] = str(txn.get('desc', ''))
            return txn
        except:
            return None
    
    def save_data(self):
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self.transactions, f, indent=2)
        except Exception as e:
            pass
    
    def get_filtered_transactions(self):
        txns = sorted(self.transactions, key=lambda x: x['date'], reverse=True)
        if self.monthly_filter:
            today = date.today()
            month_start = today.replace(day=1)
            txns = [t for t in txns if datetime.strptime(t['date'], '%Y-%m-%d').date() >= month_start]
        return txns
    
    def calculate_balance(self, txns):
        balance = 0.0
        balances = []
        for txn in reversed(txns):
            balance += txn['amount']
            balances.append(balance)
        return list(reversed(balances))
    
    def get_stats(self):
        txns = self.get_filtered_transactions()
        total_income = sum(t['amount'] for t in txns if t['amount'] > 0)
        total_expense = sum(-t['amount'] for t in txns if t['amount'] < 0)
        balance = total_income + total_expense
        
        cat_totals = {}
        for txn in txns:
            if txn['amount'] < 0:
                cat = txn['category']
                cat_totals[cat] = cat_totals.get(cat, 0) + abs(txn['amount'])
        
        total_spent = sum(cat_totals.values())
        if total_spent > 0:
            cat_pcts = {cat: (amt/total_spent)*100 for cat, amt in cat_totals.items()}
        else:
            cat_pcts = {}
        
        return {
            'income': total_income,
            'expense': total_expense,
            'balance': balance,
            'categories': cat_pcts
        }
    
    def format_amount(self, amount):
        return f"{amount:>10.2f}"
    
    def format_date(self, date_str):
        return date_str[:10]
    
    def render_grid(self, stdscr, txns, balances):
        stdscr.clear()
        
        # Headers
        headers = ['Date', 'Amount', 'Category', 'Balance']
        for col, (header, width) in enumerate(zip(headers, COL_WIDTHS)):
            stdscr.addstr(0, sum(COL_WIDTHS[:col]), header[:width-2].center(width-2),
                         curses.A_REVERSE if col == self.edit_col and self.editing else curses.A_REVERSE)
        
        # Data rows
        start_row = self.scroll_offset
        end_row = min(start_row + GRID_ROWS, len(txns))
        for i in range(start_row, end_row):
            row_idx = i - start_row + 1
            txn = txns[i]
            balance = balances[i] if i < len(balances) else 0
            
            attrs = curses.A_BOLD if i == self.selected_row else 0
            if self.editing and i == self.edit_row:
                attrs |= curses.A_REVERSE
            
            stdscr.addstr(row_idx, 0, self.format_date(txn['date'])[:COL_WIDTHS[0]-1], attrs)
            stdscr.addstr(row_idx, COL_WIDTHS[0], self.format_amount(txn['amount'])[:COL_WIDTHS[1]-1], attrs)
            stdscr.addstr(row_idx, sum(COL_WIDTHS[:2]), txn['category'][:COL_WIDTHS[2]-3], attrs)
            stdscr.addstr(row_idx, sum(COL_WIDTHS[:3]), self.format_amount(balance)[:COL_WIDTHS[3]-1], attrs)
        
        # Status bar
        status = f"Rows: {len(txns)} | Monthly: {'ON' if self.monthly_filter else 'OFF'} | Sel: {self.selected_row}"
        stdscr.addstr(curses.LINES-1, 0, status[:curses.COLS-1], curses.A_REVERSE)
        
        stdscr.refresh()
    
    def render_stats(self, stdscr):
        stdscr.clear()
        stats = self.get_stats()
        
        stdscr.addstr(1, 1, f"Total Income:  ${stats['income']:>8.2f}", curses.A_BOLD)
        stdscr.addstr(2, 1, f"Total Expense: ${stats['expense']:>8.2f}", curses.A_BOLD)
        stdscr.addstr(3, 1, f"Net Balance:  ${stats['balance']:>8.2f}", curses.A_BOLD)
        
        stdscr.addstr(5, 1, "Category Spending (this month):")
        y = 7
        total = sum(stats['categories'].values())
        for cat, pct in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
            bar = '#' * int(pct / 2)
            stdscr.addstr(y, 1, f"{cat:15} {bar:20} {pct:5.1f}%")
            y += 1
        
        stdscr.addstr(curses.LINES-2, 0, "Press any key to return to grid...", curses.A_REVERSE)
        stdscr.refresh()
        stdscr.getkey()
    
    def prompt_input(self, stdscr, prompt, default='', validate=None):
        stdscr.clear()
        stdscr.addstr(0, 0, prompt)
        stdscr.addstr(1, 0, default)
        
        editwin = newwin(3, 50, 3, 1)
        rectangle(stdscr, 2, 0, 2+3, 0+50)
        stdscr.refresh()
        
        box = Textbox(editwin, insert_mode=True)
        box.stripspaces = False
        curses.echo()
        box.edit()
        curses.noecho()
        value = box.gather().strip()
        
        if validate and not validate(value):
            return default
        return value if value else default
    
    def add_transaction(self, stdscr):
        today = datetime.now().strftime('%Y-%m-%d')
        date_str = self.prompt_input(stdscr, "Date (YYYY-MM-DD) [default today]: ", today,
                                   lambda x: re.match(r'\d{4}-\d{2}-\d{2}', x) is not None)
        
        amount_str = self.prompt_input(stdscr, "Amount (+income/-expense): ", "0",
                                     lambda x: re.match(r'-?\d+(\.\d+)?$', x) is not None)
        amount = float(amount_str)
        
        categories_str = '/'.join(CATEGORIES)
        category = self.prompt_input(stdscr, f"Category [{categories_str}]: ", "Other",
                                   lambda x: x in CATEGORIES)
        
        desc = self.prompt_input(stdscr, "Description: ", "")
        
        txn = {'date': date_str, 'amount': amount, 'category': category, 'desc': desc}
        self.transactions.insert(0, txn)
        self.action_count += 1
    
    def edit_transaction(self, stdscr, txns):
        if not txns:
            return
        
        txn = txns[self.selected_row]
        date_str = self.prompt_input(stdscr, "Date (YYYY-MM-DD): ", txn['date'],
                                   lambda x: re.match(r'\d{4}-\d{2}-\d{2}', x) is not None)
        
        amount_str = self.prompt_input(stdscr, "Amount (+income/-expense): ", str(txn['amount']),
                                     lambda x: re.match(r'-?\d+(\.\d+)?$', x) is not None)
        amount = float(amount_str)
        
        categories_str = '/'.join(CATEGORIES)
        category = self.prompt_input(stdscr, f"Category [{categories_str}]: ", txn['category'],
                                   lambda x: x in CATEGORIES)
        
        desc = self.prompt_input(stdscr, "Description: ", txn['desc'])
        
        txn['date'] = date_str
        txn['amount'] = amount
        txn['category'] = category
        txn['desc'] = desc
        self.action_count += 1
    
    def delete_transaction(self, stdscr, txns):
        if txns and self.selected_row < len(txns):
            del self.transactions[self.selected_row]
            self.selected_row = min(self.selected_row, len(self.transactions)-1)
            self.action_count += 1
    
    def sort_transactions(self, stdscr):
        stdscr.clear()
        stdscr.addstr(0, 0, "Sort by: [d]ate [a]mount [c]ategory (d=default)")
        stdscr.refresh()
        key = stdscr.getkey().lower()
        
        reverse = True
        key_func = lambda x: x['date']
        if key == 'a':
            key_func = lambda x: x['amount']
        elif key == 'c':
            key_func = lambda x: x['category']
        
        self.transactions.sort(key=key_func, reverse=reverse)
        self.action_count += 1
    
    def handle_drag(self, direction):
        if len(self.transactions) < 2:
            return
        
        idx = self.selected_row
        if direction == 'up' and idx > 0:
            self.transactions[idx-1], self.transactions[idx] = self.transactions[idx], self.transactions[idx-1]
            self.selected_row -= 1
        elif direction == 'down' and idx < len(self.transactions) - 1:
            self.transactions[idx+1], self.transactions[idx] = self.transactions[idx], self.transactions[idx+1]
            self.selected_row += 1
        self.action_count += 1
    
    def autosave(self):
        if self.action_count >= SAVE_ACTIONS:
            self.save_data()
            self.action_count = 0
    
    def main(self, stdscr):
        curses.curs_set(1)
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        
        while True:
            txns = self.get_filtered_transactions()
            balances = self.calculate_balance(txns)
            
            self.render_grid(stdscr, txns, balances)
            
            if self.editing:
                # Simple inline edit simulation - full edit on enter
                pass
            
            try:
                key = stdscr.getkey().lower()
            except:
                continue
            
            if key == 'q':
                self.save_data()
                break
            elif key == 'a':
                self.add_transaction(stdscr)
                self.selected_row = 0
            elif key == 'e' or key == '\n':
                self.edit_transaction(stdscr, txns)
            elif key == 'd':
                self.delete_transaction(stdscr, txns)
            elif key == 's':
                self.sort_transactions(stdscr)
            elif key == 'r':
                self.render_stats(stdscr)
            elif key == 'm':
                self.monthly_filter = not self.monthly_filter
            elif key == 'k' or (key == 'k' and curses.has_key('KEY_SHIFT')):
                self.handle_drag('up')
            elif key == 'j' or (key == 'j' and curses.has_key('KEY_SHIFT')):
                self.handle_drag('down')
            elif key in ('h', curses.KEY_LEFT):
                self.edit_col = max(0, self.edit_col - 1)
            elif key in ('l', curses.KEY_RIGHT):
                self.edit_col = min(3, self.edit_col + 1)
            elif key == 'i' or key == curses.KEY_UP:
                self.selected_row = max(0, self.selected_row - 1)
            elif key == 'i' or key == curses.KEY_DOWN:
                self.selected_row = min(len(txns) - 1, self.selected_row + 1)
            
            # Scrolling
            if self.selected_row < self.scroll_offset:
                self.scroll_offset = self.selected_row
            elif self.selected_row >= self.scroll_offset + GRID_ROWS:
                self.scroll_offset = self.selected_row - GRID_ROWS + 1
            
            self.autosave()

if __name__ == "__main__":
    wrapper(CashFlowAnalyzer().main)