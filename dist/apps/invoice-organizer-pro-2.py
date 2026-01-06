# Auto-generated via Perplexity on 2026-01-06T01:39:20.904374Z
#!/usr/bin/env python3
import os
import sys
import json
import curses
import datetime
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any

class InvoiceOrganizer:
    COLORS = {
        'normal': 0,
        'selected': 1,
        'header': 2,
        'paid': 3,
        'overdue': 4,
        'unpaid': 5,
        'error': 6
    }

    KEYMAP = {
        'q': 'Quit', 'n': 'New invoice', 'd': 'Delete', 'e': 'Edit', 
        's': 'Sort', '?': 'Help', '↑↓': 'Navigate', '↵': 'Details',
        'c': 'Copy client', 'p': 'Paste client', 'Tab': 'Next field'
    }

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.screen = 'main'
        self.cursor = 0
        self.selected_invoice = None
        self.edit_field = 0
        self.sort_mode = 0
        self.sort_orders = ['date_desc', 'date_asc', 'client', 'amount_desc', 'status']
        self.clipboard = ''
        self.invoices = []
        self.dir = Path(__file__).parent
        self.data_file = self.dir / 'invoices.json'
        self.config_file = self.dir / 'config.json'
        self.archive_dir = self.dir / 'invoices_archive'
        self.load_data()
        self.setup_colors()
        self.update_totals()

    def setup_colors(self):
        curses.start_color()
        curses.use_default_colors()
        for i, _ in enumerate(self.COLORS.values()):
            curses.init_pair(i+1, curses.COLOR_BLACK, i+1 if i else -1)
        self.color = lambda c: curses.color_pair(list(self.COLORS.values()).index(c) + 1)

    def load_data(self):
        try:
            self.archive_dir.mkdir(exist_ok=True)
            config = {}
            if self.config_file.exists():
                config = json.loads(self.config_file.read_text())
            self.sort_mode = config.get('sort_mode', 0)
            
            self.invoices = []
            if self.data_file.exists():
                data = json.loads(self.data_file.read_text())
                for inv in data:
                    inv['date_obj'] = datetime.datetime.strptime(inv['date'], '%Y-%m-%d').date()
                    self.invoices.append(inv)
            self.sort_invoices()
        except Exception:
            self.invoices = []

    def save_data(self):
        try:
            data = []
            for inv in self.invoices:
                inv_copy = inv.copy()
                inv_copy['date_obj'] = inv['date']
                data.append(inv_copy)
            self.data_file.write_text(json.dumps(data, indent=2))
            
            config = {'sort_mode': self.sort_mode}
            self.config_file.write_text(json.dumps(config, indent=2))
        except Exception:
            pass

    def sort_invoices(self):
        modes = self.sort_orders[self.sort_mode]
        if modes == 'date_desc':
            self.invoices.sort(key=lambda x: x['date_obj'], reverse=True)
        elif modes == 'date_asc':
            self.invoices.sort(key=lambda x: x['date_obj'])
        elif modes == 'client':
            self.invoices.sort(key=lambda x: x['client'].lower())
        elif modes == 'amount_desc':
            self.invoices.sort(key=lambda x: x['amount'], reverse=True)
        elif modes == 'status':
            order = {'Paid': 0, 'Unpaid': 1, 'Overdue': 2}
            self.invoices.sort(key=lambda x: order.get(x['status'], 3))

    def update_totals(self):
        now = datetime.date.today()
        self.unpaid_total = 0.0
        self.overdue_count = 0
        for inv in self.invoices:
            if inv['status'] == 'Unpaid':
                self.unpaid_total += inv['amount']
                days_old = (now - inv['date_obj']).days
                if days_old > 30:
                    self.overdue_count += 1
                    inv['status'] = 'Overdue'

    def is_overdue(self, inv):
        return inv['status'] == 'Overdue'

    def new_invoice(self):
        max_id = max([inv.get('id', 0) for inv in self.invoices], default=0)
        today = datetime.date.today().strftime('%Y-%m-%d')
        new_inv = {
            'id': max_id + 1, 'date': today, 'date_obj': datetime.date.today(),
            'client': '', 'amount': 0.0, 'status': 'Unpaid', 'notes': ''
        }
        self.invoices.insert(0, new_inv)
        self.selected_invoice = new_inv
        self.screen = 'edit'
        self.edit_field = 1
        self.save_data()

    def delete_invoice(self):
        if self.selected_invoice:
            self.archive_dir.mkdir(exist_ok=True)
            archive_file = self.archive_dir / f"invoice_{self.selected_invoice['id']}.json"
            archive_file.write_text(json.dumps(self.selected_invoice))
            self.invoices.remove(self.selected_invoice)
            self.selected_invoice = None if self.cursor >= len(self.invoices) else self.invoices[self.cursor]
            self.save_data()
            self.update_totals()

    def copy_client(self):
        if self.selected_invoice:
            self.clipboard = self.selected_invoice['client']

    def paste_client(self):
        if self.clipboard and self.selected_invoice:
            self.selected_invoice['client'] = self.clipboard
            self.save_data()

    def validate_date(self, date_str):
        try:
            datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            return True
        except:
            return False

    def validate_amount(self, amount_str):
        try:
            float(amount_str)
            return True
        except:
            return False

    def show_message(self, msg, title='Message'):
        h, w = self.stdscr.getmaxyx()
        msg_h = 5 + msg.count('\n')
        msg_w = max(len(line) for line in msg.split('\n')) + 4
        win = curses.newwin(msg_h, msg_w, (h-msg_h)//2, (w-msg_w)//2)
        win.box()
        win.addstr(1, 2, title, self.color('header'))
        for i, line in enumerate(msg.split('\n')):
            win.addstr(2+i, 2, line[:msg_w-4])
        win.refresh()
        self.stdscr.getch()
        win.clear()
        win.refresh()

    def show_help(self):
        help_text = '\n'.join([
            "INVOICE ORGANIZER PRO - KEY BINDINGS",
            "===================================",
            "",
            f"Navigation: ↑↓ Arrow keys, Enter ↵ (Details)",
            f"Actions: n (New), d (Delete), e (Edit)",
            f"        s (Sort), c (Copy client), p (Paste client)",
            f"        ? (Help), q (Quit)",
            "",
            "Edit mode: Tab (Next field), Esc (Save & Return)",
            "",
            "Status colors: Green=Paid, Red=Overdue, Yellow=Unpaid",
            "Footer shows: Unpaid total & Overdue count"
        ])
        self.show_message(help_text, "Help")

    def draw_main(self):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.clear()
        
        # Header
        self.stdscr.addstr(0, 0, "Invoice Organizer Pro", self.color('header'))
        self.stdscr.addstr(0, w-15, f"Sort: {self.sort_orders[self.sort_mode]}", self.color('header'))
        
        # Table headers
        headers = ["ID", "Date", "Client", "Amount", "Status"]
        col_widths = [4, 12, 25, 12, 12]
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            x = sum(col_widths[:i])
            self.stdscr.addstr(2, x+1, header, self.color('header'))
        
        # Invoices
        for i, inv in enumerate(self.invoices[max(0, self.cursor-18):self.cursor+6]):
            row = 3 + i
            if row >= h-4: break
            
            col = 0
            self.stdscr.addstr(row, col, str(inv['id']).rjust(4))
            col += 4
            self.stdscr.addstr(row, col, inv['date'][:10].ljust(12))
            col += 12
            self.stdscr.addstr(row, col, inv['client'][:24].ljust(25))
            col += 25
            self.stdscr.addstr(row, col, f"${inv['amount']:,.2f}".rjust(12))
            col += 12
            
            status_color = 'paid' if inv['status'] == 'Paid' else 'overdue' if self.is_overdue(inv) else 'unpaid'
            self.stdscr.addstr(row, col, inv['status'][:11].ljust(12), self.color(status_color))
            
            if i + self.cursor == self.cursor:
                self.stdscr.addstr(row, 0, ' '*72, self.color('selected'))
        
        # Cursor indicator
        if 0 <= self.cursor < len(self.invoices):
            self.stdscr.addstr(3 + min(self.cursor, 20), 0, '▶', self.color('selected'))
        
        # Footer totals
        footer = f"Unpaid: ${self.unpaid_total:,.2f} | Overdue: {self.overdue_count}"
        self.stdscr.addstr(h-1, 0, footer + ' '*(w-len(footer)-1), self.color('header'))
        self.stdscr.addstr(h-1, w-20, "n=dnew d=del e=edit q=quit", curses.A_REVERSE)
        
        self.stdscr.refresh()

    def draw_edit(self):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.clear()
        
        if not self.selected_invoice:
            self.screen = 'main'
            return
        
        inv = self.selected_invoice
        fields = [
            (f"ID: {inv['id']}", 0),
            (f"Date: {inv['date']}", 1),
            (f"Client: {inv['client']}", 2),
            (f"Amount: {inv['amount']}", 3),
            (f"Status: {inv['status']}", 4),
            ("Notes:", 5)
        ]
        
        y = 2
        for i, (text, field_id) in enumerate(fields):
            attr = self.color('selected') if i == self.edit_field else 0
            if field_id < 5:
                self.stdscr.addstr(y, 2, text, attr)
            else:
                self.stdscr.addstr(y, 2, text, attr)
                note_lines = inv['notes'].split('\n')
                for j, line in enumerate(note_lines[:h-y-4]):
                    self.stdscr.addstr(y+1+j, 10, line[:w-12])
            y += max(1, len(note_lines[:h-y-4]) if field_id == 5 else 1)
        
        keys = "Tab=Next Esc=Save ↑↓=Edit q=Quit"
        self.stdscr.addstr(h-1, 0, keys + ' '*(w-len(keys)-1), curses.A_REVERSE)
        self.stdscr.refresh()

    def handle_edit_input(self, ch):
        inv = self.selected_invoice
        if self.edit_field == 1:  # Date
            if ch == 27:  # Esc
                if self.validate_date(inv['date']):
                    try:
                        inv['date_obj'] = datetime.datetime.strptime(inv['date'], '%Y-%m-%d').date()
                        self.update_totals()
                        self.save_data()
                        self.screen = 'main'
                    except:
                        self.show_message("Invalid date format (YYYY-MM-DD)")
                else:
                    self.show_message("Invalid date format (YYYY-MM-DD)")
            elif ch == 9:  # Tab
                self.edit_field = (self.edit_field + 1) % 6
            else:
                pos = len(inv['date'])
                inv['date'] = (inv['date'][:pos] + chr(ch) + inv['date'][pos+1:]) if ch >= 32 else inv['date']
        
        elif self.edit_field == 2:  # Client
            if ch == 9: self.edit_field = (self.edit_field + 1) % 6
            elif ch == 27: 
                self.save_data()
                self.screen = 'main'
            elif ch >= 32 and len(inv['client']) < 30:
                inv['client'] += chr(ch)
            elif ch == 127 and inv['client']:  # Backspace
                inv['client'] = inv['client'][:-1]
        
        elif self.edit_field == 3:  # Amount
            if ch == 9: self.edit_field = (self.edit_field + 1) % 6
            elif ch == 27:
                try:
                    inv['amount'] = float(inv['amount']) if inv['amount'] else 0.0
                    self.update_totals()
                    self.save_data()
                    self.screen = 'main'
                except:
                    self.show_message("Invalid amount")
            elif ch >= ord('0') and ch <= ord('9') or ch in (ord('.'), ord('-')):
                inv['amount'] += chr(ch)
            elif ch == 127 and inv['amount']:  # Backspace
                inv['amount'] = inv['amount'][:-1]
        
        elif self.edit_field == 4:  # Status
            if ch == 9: self.edit_field = (self.edit_field + 1) % 6
            elif ch == 27:
                self.update_totals()
                self.save_data()
                self.screen = 'main'
            elif ch == ord('p'): inv['status'] = 'Paid'
            elif ch == ord('u'): inv['status'] = 'Unpaid'
        
        elif self.edit_field == 5:  # Notes
            if ch == 9: self.edit_field = 0
            elif ch == 27:
                self.save_data()
                self.screen = 'main'
            elif ch >= 32 and len(inv['notes']) < 200:
                inv['notes'] += chr(ch)
            elif ch == 127 and inv['notes']:  # Backspace
                inv['notes'] = inv['notes'][:-1]
            elif ch == 10:  # Enter
                inv['notes'] += '\n'

    def run(self):
        while True:
            if self.screen == 'main':
                self.draw_main()
                ch = self.stdscr.getch()
                
                if ch == ord('q'): break
                elif ch == ord('n'): self.new_invoice()
                elif ch == ord('d') and self.invoices:
                    self.show_message("Press 'y' to delete (moves to archive)")
                    if self.stdscr.getch() == ord('y'):
                        self.delete_invoice()
                elif ch == ord('e') and self.invoices:
                    self.screen = 'edit'
                    self.edit_field = 0
                elif ch == ord('s'):
                    self.sort_mode = (self.sort_mode + 1) % len(self.sort_orders)
                    self.sort_invoices()
                    self.save_data()
                elif ch == ord('c') and self.invoices:
                    self.copy_client()
                elif ch == ord('p') and self.invoices:
                    self.paste_client()
                elif ch == ord('?'): self.show_help()
                elif ch == curses.KEY_UP and self.cursor > 0:
                    self.cursor -= 1
                elif ch == curses.KEY_DOWN and self.cursor < len(self.invoices) - 1:
                    self.cursor += 1
                elif ch == 10 and self.invoices:  # Enter
                    self.selected_invoice = self.invoices[self.cursor]
                    self.screen = 'edit'
                    self.edit_field = 0
            
            elif self.screen == 'edit':
                self.draw_edit()
                ch = self.stdscr.getch()
                self.handle_edit_input(ch)
                if ch == curses.KEY_UP and self.edit_field > 0:
                    self.edit_field -= 1
                elif ch == curses.KEY_DOWN:
                    self.edit_field = (self.edit_field + 1) % 6
        
        self.save_data()

def main(stdscr):
    curses.curs_set(0)
    curses.cbreak()
    stdscr.keypad(True)
    try:
        app = InvoiceOrganizer(stdscr)
        app.run()
    except KeyboardInterrupt:
        pass
    finally:
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.curs_set(1)

if __name__ == '__main__':
    curses.wrapper(main)