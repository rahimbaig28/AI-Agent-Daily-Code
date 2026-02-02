# Auto-generated via Perplexity on 2026-02-02T17:58:33.062697Z
#!/usr/bin/env python3
import curses
import json
import csv
import argparse
from pathlib import Path
from datetime import datetime, date
from collections import deque
import os

class InvoiceTracker:
    def __init__(self, stdscr, data_file=None, export_file=None):
        self.stdscr = stdscr
        self.data_file = Path(data_file or 'invoices.json')
        self.export_file = export_file
        self.invoices = []
        self.selected = 0
        self.top_row = 0
        self.scroll_offset = 0
        self.edit_mode = False
        self.edit_col = 0
        self.edit_row = 0
        self.edit_value = ''
        self.change_count = 0
        self.max_changes = 10
        self.actions = deque(maxlen=20)
        self.undone_actions = deque(maxlen=20)
        self.load_data()
        curses.curs_set(0)
        self.stdscr.keypad(True)
        self.stdscr.timeout(100)

    def load_data(self):
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    self.invoices = json.load(f)
                # Ensure ID field exists and auto-increment
                for i, inv in enumerate(self.invoices):
                    if 'id' not in inv:
                        inv['id'] = i + 1
                self.normalize_ids()
            except:
                self.invoices = []

    def save_data(self):
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.invoices, f, indent=2, default=str)
        except Exception as e:
            self.message(f"Save failed: {e}", curses.A_REVERSE)

    def export_csv(self):
        if self.export_file and self.export_file.exists():
            self.stdscr.addstr(1, 0, "Overwrite existing CSV? (y/n): ")
            self.stdscr.refresh()
            if self.stdscr.getch() != ord('y'):
                return
        try:
            with open(self.export_file or 'invoices.csv', 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'date', 'customer', 'amount', 'status'])
                writer.writeheader()
                writer.writerows(self.invoices)
            self.message("Exported to CSV", curses.color_pair(2))
        except Exception as e:
            self.message(f"Export failed: {e}", curses.A_REVERSE)

    def normalize_ids(self):
        for i, inv in enumerate(self.invoices):
            inv['id'] = i + 1

    def push_action(self):
        self.actions.append(json.dumps(self.invoices, default=str))
        self.undone_actions.clear()
        self.change_count += 1
        if self.change_count >= self.max_changes:
            self.save_data()
            self.change_count = 0

    def undo(self):
        if self.actions:
            self.undone_actions.append(self.actions.pop())
            self.invoices = json.loads(self.actions[-1] if self.actions else '[]')
            self.normalize_ids()

    def redo(self):
        if self.undone_actions:
            self.actions.append(self.undone_actions.pop())
            self.invoices = json.loads(self.actions[-1])

    def add_invoice(self):
        new_id = max((inv.get('id', 0) for inv in self.invoices), default=0) + 1
        self.invoices.insert(self.selected, {
            'id': new_id,
            'date': date.today().isoformat(),
            'customer': 'New Customer',
            'amount': 0.0,
            'status': 'pending'
        })
        self.normalize_ids()
        self.push_action()

    def delete_invoice(self):
        if self.invoices:
            del self.invoices[self.selected]
            self.normalize_ids()
            if self.selected >= len(self.invoices):
                self.selected = len(self.invoices) - 1
            self.push_action()

    def get_status_color(self, inv):
        today = date.today()
        inv_date = datetime.fromisoformat(inv['date']).date()
        if inv['status'] == 'paid':
            return curses.color_pair(2)  # green
        elif inv['status'] == 'pending':
            return curses.color_pair(3)  # yellow
        elif inv_date < today:
            return curses.color_pair(1)  # red
        return 0

    def truncate_text(self, text, max_len):
        return (text[:max_len-3] + '...') if len(text) > max_len else text

    def draw_table(self):
        maxy, maxx = self.stdscr.getmaxyx()
        table_height = min(20, maxy - 5)
        
        # Headers
        headers = ['ID', 'Date', 'Customer', 'Amount', 'Status']
        col_widths = [6, 12, 20, 12, 12]
        
        self.stdscr.clear()
        
        # Draw headers
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            x = sum(col_widths[:i])
            self.stdscr.addstr(0, x, header.center(width-1), curses.A_BOLD)
        
        # Draw rows
        for i in range(table_height):
            row_idx = self.top_row + i
            if row_idx >= len(self.invoices):
                break
                
            inv = self.invoices[row_idx]
            row_attrs = curses.A_REVERSE if row_idx == self.selected else 0
            x = 0
            
            # ID
            self.stdscr.addstr(i+1, x, str(inv['id']).center(col_widths[0]-1), row_attrs)
            x += col_widths[0]
            
            # Date
            self.stdscr.addstr(i+1, x, self.truncate_text(inv['date'], col_widths[1]-1), row_attrs)
            x += col_widths[1]
            
            # Customer
            self.stdscr.addstr(i+1, x, self.truncate_text(inv['customer'], col_widths[2]-1), row_attrs)
            x += col_widths[2]
            
            # Amount
            self.stdscr.addstr(i+1, x, f"${inv['amount']:.2f}".rjust(col_widths[3]-1), row_attrs)
            x += col_widths[3]
            
            # Status with color
            status_attrs = row_attrs | self.get_status_color(inv)
            self.stdscr.addstr(i+1, x, inv['status'].center(col_widths[4]-1), status_attrs)
        
        # Scrollbar
        if len(self.invoices) > table_height:
            bar_height = int(table_height * table_height / len(self.invoices))
            bar_pos = int(self.top_row * (table_height - bar_height) / max(1, len(self.invoices) - table_height))
            for i in range(table_height):
                bar_char = curses.ACS_BLOCK if bar_pos <= i < bar_pos + bar_height else curses.ACS_VLINE
                self.stdscr.addch(i+1, sum(col_widths), bar_char)
        
        # Stats
        total = len(self.invoices)
        total_amount = sum(inv['amount'] for inv in self.invoices)
        pending = sum(1 for inv in self.invoices if inv['status'] == 'pending')
        stats = f"Total: {total} | Amount: ${total_amount:.2f} | Pending: {pending}"
        self.stdscr.addstr(maxy-3, 0, stats, curses.A_BOLD)
        
        # Shortcuts
        shortcuts = "[↑↓] Navigate [Enter] Edit [Tab] Next [i] Insert [d] Delete [u] Undo [r] Redo [s] Save/Export [q] Quit"
        self.stdscr.addstr(maxy-2, 0, shortcuts)
        
        self.stdscr.refresh()

    def edit_field(self, row, col):
        inv = self.invoices[row]
        fields = ['date', 'customer', 'amount', 'status']
        if col >= len(fields):
            return
            
        field = fields[col]
        self.edit_value = str(inv[field])
        
        while True:
            self.draw_edit_field(row, col)
            ch = self.stdscr.getch()
            
            if ch == 27:  # ESC
                break
            elif ch == curses.KEY_ENTER or ch == 10:
                if self.validate_edit(field):
                    old_value = inv[field]
                    inv[field] = self.edit_value
                    self.normalize_ids()
                    self.push_action()
                    break
            elif ch == curses.KEY_BACKSPACE or ch == 127:
                self.edit_value = self.edit_value[:-1]
            elif 32 <= ch <= 127:
                self.edit_value += chr(ch)
            elif ch == curses.KEY_DOWN:
                return True
            elif ch == curses.KEY_UP:
                return False
            elif ch == 9:  # Tab
                return True
        
        return False

    def draw_edit_field(self, row, col):
        maxy, maxx = self.stdscr.getmaxyx()
        table_height = min(20, maxy - 5)
        screen_row = 1 + (row - self.top_row)
        if screen_row < 1 or screen_row > table_height:
            return
            
        fields = ['date', 'customer', 'amount', 'status']
        col_widths = [6, 12, 20, 12, 12]
        x = sum(col_widths[:col+1])
        
        self.stdscr.addstr(screen_row, x - col_widths[col+1] + 1, 
                          self.edit_value.ljust(col_widths[col+1]-2), 
                          curses.A_REVERSE | curses.A_BOLD)
        self.stdscr.refresh()

    def validate_edit(self, field):
        try:
            if field == 'date':
                datetime.strptime(self.edit_value, '%Y-%m-%d')
            elif field == 'amount':
                amount = float(self.edit_value)
                if amount <= 0:
                    raise ValueError("Amount must be > 0")
                self.edit_value = str(amount)
            elif field == 'status':
                if self.edit_value not in ['pending', 'paid', 'overdue']:
                    raise ValueError("Invalid status")
            return True
        except:
            self.message(f"Invalid {field}", curses.A_REVERSE)
            return False

    def message(self, text, attrs=0):
        maxy, maxx = self.stdscr.getmaxyx()
        self.stdscr.addstr(maxy-1, 0, " " * maxx, curses.A_REVERSE)
        self.stdscr.addstr(maxy-1, 0, text[:maxx-1], curses.A_REVERSE | attrs)
        self.stdscr.refresh()
        self.stdscr.getch()

    def run(self):
        curses.curs_set(1) if self.edit_mode else curses.curs_set(0)
        self.draw_table()
        
        while True:
            try:
                ch = self.stdscr.getch()
            except:
                continue
                
            maxy, maxx = self.stdscr.getmaxyx()
            table_height = min(20, maxy - 5)
            
            if self.edit_mode:
                continue  # Edit mode handled separately
            
            if ch == ord('q'):
                if self.change_count > 0:
                    self.save_data()
                break
            elif ch == ord('i'):
                self.add_invoice()
            elif ch == ord('d') and self.invoices:
                self.delete_invoice()
            elif ch == ord('u'):
                self.undo()
            elif ch == ord('r'):
                self.redo()
            elif ch == ord('s'):
                self.save_data()
                self.export_csv()
            elif ch == curses.KEY_UP:
                self.selected = max(0, self.selected - 1)
                if self.selected < self.top_row:
                    self.top_row = self.selected
            elif ch == curses.KEY_DOWN:
                self.selected = min(len(self.invoices) - 1, self.selected + 1)
                if self.selected >= self.top_row + table_height:
                    self.top_row = self.selected - table_height + 1
            elif ch == curses.KEY_PPAGE:
                self.top_row = max(0, self.top_row - table_height)
                self.selected = max(0, self.selected - table_height)
            elif ch == curses.KEY_NPAGE:
                self.top_row = min(len(self.invoices) - table_height, 
                                 self.top_row + table_height)
                self.selected = min(len(self.invoices) - 1, 
                                 self.selected + table_height)
            elif ch == curses.KEY_ENTER and self.invoices:
                next_field = self.edit_field(self.selected, 1)
                if next_field:
                    self.selected = min(len(self.invoices) - 1, self.selected + 1)
            
            self.draw_table()

def main(stdscr):
    # Setup colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)     # overdue
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)   # paid
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # pending
    
    parser = argparse.ArgumentParser(description='Invoice Tracker Pro')
    parser.add_argument('--file', help='JSON data file')
    parser.add_argument('--export', help='CSV export file')
    args = parser.parse_args()
    
    app = InvoiceTracker(stdscr, args.file, args.export)
    app.run()

if __name__ == '__main__':
    curses.wrapper(main)