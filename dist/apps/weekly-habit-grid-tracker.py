# Auto-generated via Perplexity on 2025-12-29T13:35:03.733647Z
import curses
import json
import os
import datetime
from collections import deque

DATA_FILE = 'habits.json'

class HabitTracker:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.screen_height, self.screen_width = stdscr.getmaxyx()
        self.habits = []
        self.completions = {}
        self.selected_row = 0
        self.selected_col = 0
        self.week_start = self.get_monday(datetime.date.today())
        self.undo_stack = deque(maxlen=50)
        self.redo_stack = deque(maxlen=50)
        self.load_data()
        
    def get_monday(self, date):
        days_ahead = 0 - date.weekday()
        return date + datetime.timedelta(days=days_ahead)
    
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.habits = data.get('habits', self.get_default_habits())
                    self.completions = data.get('completions', {})
                    saved_week = datetime.date.fromisoformat(data.get('week_start', self.week_start.isoformat()))
                    if saved_week < self.week_start:
                        self.advance_week()
            except:
                self.habits = self.get_default_habits()
        else:
            self.habits = self.get_default_habits()
    
    def get_default_habits(self):
        return ["Exercise", "Read 30min", "Meditate", "Water 2L", "Walk 10k", "Sleep 8h", "Journal"]
    
    def save_data(self):
        data = {
            'habits': self.habits,
            'completions': self.completions,
            'week_start': self.week_start.isoformat()
        }
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f)
    
    def advance_week(self):
        self.week_start += datetime.timedelta(days=7)
        self.completions = {}
        self.selected_row = 0
        self.selected_col = 0
    
    def get_days(self):
        days = []
        current = self.week_start
        for i in range(7):
            days.append(current.strftime("%a %d"))
            current += datetime.timedelta(days=1)
        return days
    
    def count_completed(self, row):
        return sum(1 for day in range(7) if self.is_completed(row, day))
    
    def is_completed(self, row, col):
        week_key = self.week_start.isoformat()
        return self.completions.get(f"{row}_{col}", {}).get(week_key, False)
    
    def toggle_cell(self, row, col):
        week_key = self.week_start.isoformat()
        cell_key = f"{row}_{col}"
        old_state = self.completions.get(cell_key, {}).get(week_key, False)
        new_state = not old_state
        
        self.undo_stack.append(('toggle', row, col, old_state))
        self.redo_stack.clear()
        
        if cell_key not in self.completions:
            self.completions[cell_key] = {}
        self.completions[cell_key][week_key] = new_state
    
    def clear_row(self, row):
        week_key = self.week_start.isoformat()
        old_states = [self.is_completed(row, col) for col in range(7)]
        
        self.undo_stack.append(('clear', row, old_states))
        self.redo_stack.clear()
        
        for col in range(7):
            cell_key = f"{row}_{col}"
            if cell_key not in self.completions:
                continue
            if week_key in self.completions[cell_key]:
                del self.completions[cell_key][week_key]
    
    def undo(self):
        if not self.undo_stack:
            return False
        
        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        
        if action[0] == 'toggle':
            _, row, col, old_state = action
            week_key = self.week_start.isoformat()
            cell_key = f"{row}_{col}"
            if cell_key not in self.completions:
                self.completions[cell_key] = {}
            self.completions[cell_key][week_key] = old_state
        elif action[0] == 'clear':
            _, row, old_states = action
            week_key = self.week_start.isoformat()
            for col, state in enumerate(old_states):
                cell_key = f"{row}_{col}"
                if cell_key not in self.completions:
                    self.completions[cell_key] = {}
                self.completions[cell_key][week_key] = state
        
        return True
    
    def redo(self):
        if not self.redo_stack:
            return False
        
        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        
        if action[0] == 'toggle':
            _, row, col, old_state = action
            week_key = self.week_start.isoformat()
            cell_key = f"{row}_{col}"
            if cell_key not in self.completions:
                self.completions[cell_key] = {}
            self.completions[cell_key][week_key] = not old_state
        elif action[0] == 'clear':
            _, row, _ = action
            self.clear_row(row)
        
        return True
    
    def get_status(self):
        days = self.get_days()
        completed = self.count_completed(self.selected_row)
        total = 7
        pct = (completed * 100) // total if total else 0
        undo_size = len(self.undo_stack)
        week_range = f"{days[0]} - {days[6]}"
        return f"Week: {week_range} | Habit: {self.habits[self.selected_row][:10]} | Day: {days[self.selected_col]} | {completed}/{total} ({pct}%) | Undo: {undo_size}"
    
    def draw_grid(self):
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Status bar
        self.stdscr.addstr(0, 0, self.get_status(), curses.A_REVERSE)
        
        # Grid area
        grid_y = 2
        grid_x = 2
        cell_w = max(8, (width - 4) // 7)
        cell_h = max(3, (height - 8) // 7)
        
        days = self.get_days()
        
        # Headers
        for col in range(7):
            x = grid_x + col * cell_w
            day_text = days[col][:min(8, cell_w-1)]
            self.stdscr.addstr(grid_y-1, x, day_text.center(cell_w-1), curses.A_BOLD)
        
        # Habits and grid
        for row in range(7):
            y = grid_y + row * cell_h
            habit_text = self.habits[row][:min(12, width-15)]
            self.stdscr.addstr(y, 1, f"{row+1:2d}. {habit_text}", curses.A_BOLD)
            
            for col in range(7):
                x = grid_x + col * cell_w
                is_sel = (row == self.selected_row and col == self.selected_col)
                completed = self.is_completed(row, col)
                
                if is_sel:
                    attr = curses.A_REVERSE
                elif completed:
                    attr = curses.color_pair(1) | curses.A_BOLD
                else:
                    attr = 0
                
                if completed:
                    self.stdscr.addstr(y+1, x+2, " ✓ ", attr | curses.A_BOLD)
                else:
                    self.stdscr.addstr(y+1, x+2, "   ", attr)
        
        # Key hints
        hints = [
            "W↑/S↓: Habit  A←/D→: Day  SPACE: Toggle  N: New habit  C: Clear row",
            "U: Undo  R: Redo  P: Print view  S: Save  Q: Quit"
        ]
        for i, hint in enumerate(hints):
            self.stdscr.addstr(height-2+i, 1, hint)
        
        self.stdscr.refresh()
    
    def print_view(self):
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        days = self.get_days()
        cell_w = max(10, (width - 20) // 7)
        
        # Title
        title = f"Weekly Habits - {days[0]} to {days[6]}"
        self.stdscr.addstr(1, (width-len(title))//2, title, curses.A_BOLD | curses.A_UNDERLINE)
        
        # Grid
        y = 4
        for row in range(7):
            self.stdscr.addstr(y, 2, f"{self.habits[row]:12} |")
            for col in range(7):
                x = 16 + col * cell_w
                completed = self.is_completed(row, col)
                mark = "✓" if completed else " "
                self.stdscr.addstr(y, x, f"[{mark}]".center(cell_w-1))
                if col < 6:
                    self.stdscr.addstr(y, x + cell_w - 1, "|")
            y += 1
        
        # Summary
        y += 2
        total_habits = sum(self.count_completed(row) for row in range(7))
        self.stdscr.addstr(y, 2, f"TOTAL: {total_habits}/49 completed", curses.A_BOLD)
        
        self.stdscr.addstr(y+2, 2, "Press any key to return...")
        self.stdscr.refresh()
        self.stdscr.getch()
    
    def edit_habit(self):
        self.stdscr.clear()
        self.stdscr.addstr(2, 2, "New habit name (max 12 chars):")
        edit_y, edit_x = 4, 2
        curses.echo()
        curses.curs_set(1)
        name = self.stdscr.getstr(edit_y, edit_x, 12).decode('utf-8')[:12]
        curses.noecho()
        curses.curs_set(0)
        
        if name.strip():
            old_name = self.habits[self.selected_row]
            self.undo_stack.append(('rename', self.selected_row, old_name))
            self.redo_stack.clear()
            self.habits[self.selected_row] = name.strip()
    
    def run(self):
        curses.curs_set(0)
        curses.cbreak()
        self.stdscr.keypad(True)
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        
        while True:
            self.draw_grid()
            c = self.stdscr.getch()
            
            if c == ord('q') or c == 27:  # Q or ESC
                break
            elif c == ord('w') or c == curses.KEY_UP:
                self.selected_row = (self.selected_row - 1) % 7
            elif c == ord('s') or c == curses.KEY_DOWN:
                self.selected_row = (self.selected_row + 1) % 7
            elif c == ord('a') or c == curses.KEY_LEFT:
                self.selected_col = (self.selected_col - 1) % 7
            elif c == ord('d') or c == curses.KEY_RIGHT:
                self.selected_col = (self.selected_col + 1) % 7
            elif c == ord(' '):
                self.toggle_cell(self.selected_row, self.selected_col)
            elif c == ord('n'):
                self.edit_habit()
            elif c == ord('c'):
                self.clear_row(self.selected_row)
            elif c == ord('u'):
                self.undo()
            elif c == ord('r'):
                self.redo()
            elif c == ord('p'):
                self.print_view()
            elif c == ord('s'):
                self.save_data()
        
        self.save_data()
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.curs_set(1)

def main(stdscr):
    try:
        tracker = HabitTracker(stdscr)
        tracker.run()
    except KeyboardInterrupt:
        pass
    finally:
        curses.endwin()

if __name__ == "__main__":
    curses.wrapper(main)