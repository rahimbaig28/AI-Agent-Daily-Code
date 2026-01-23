# Auto-generated via Perplexity on 2026-01-23T21:33:34.282414Z
import json
import os
import datetime
import curses
from curses import wrapper

DATA_FILE = "habits.json"
DEFAULT_HABITS = ["Water", "Exercise", "Read", "Meditate", "Sleep 8h"]
MAX_HABITS = 10

class HabitTracker:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.habits = []
        self.week_start = self.get_week_start()
        self.current_day = 0
        self.selected_habit = 0
        self.habit_focus = True  # True: habit list, False: grid
        self.load_data()
        curses.curs_set(0)
        self.setup_colors()
        self.main_loop()

    def setup_colors(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)   # ✓
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)     # empty
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # today
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)    # headers
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)   # selected

    def get_week_start(self):
        today = datetime.date.today()
        return today - datetime.timedelta(days=today.weekday())

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.habits = data.get('habits', DEFAULT_HABITS)
                    saved_week = datetime.date.fromisoformat(data.get('week_start'))
                    if (self.week_start - saved_week).days < 14:
                        self.week_start = saved_week
                        completions = data.get('completions', {})
                        for habit in self.habits:
                            if habit not in completions:
                                completions[habit] = [False] * 7
                        self.completions = completions
                    else:
                        self.init_completions()
            except:
                self.init_completions()
        else:
            self.init_completions()

    def init_completions(self):
        self.completions = {habit: [False] * 7 for habit in DEFAULT_HABITS}
        self.habits = DEFAULT_HABITS[:]

    def save_data(self):
        data = {
            'habits': self.habits,
            'completions': self.completions,
            'week_start': self.week_start.isoformat()
        }
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f)
        except:
            pass

    def get_day_date(self, day_offset):
        return self.week_start + datetime.timedelta(days=day_offset)

    def draw(self):
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Determine grid size based on width
        if width < 100:
            cols = 3
            col_width = (width - 20) // 3
        else:
            cols = 5
            col_width = (width - 20) // 5
        
        rows = min(len(self.habits), (height - 10) // 2)
        
        # Headers
        self.stdscr.attron(curses.color_pair(4))
        for col in range(min(7, cols)):
            day = self.get_day_date(col)
            day_str = day.strftime("%a %d").center(col_width)
            self.stdscr.addstr(1, 20 + col * col_width, day_str[:col_width])
        self.stdscr.attroff(curses.color_pair(4))
        
        # Highlight today
        today_col = (datetime.date.today() - self.week_start).days
        if 0 <= today_col < 7:
            self.stdscr.attron(curses.color_pair(3))
            day_str = self.get_day_date(today_col).strftime("%a %d").center(col_width)
            self.stdscr.addstr(1, 20 + today_col * col_width, day_str[:col_width])
            self.stdscr.attroff(curses.color_pair(3))
        
        # Grid
        for row in range(rows):
            habit = self.habits[row]
            # Habit name
            name = habit[:15]
            if self.habit_focus and row == self.selected_habit:
                self.stdscr.attron(curses.color_pair(5))
            self.stdscr.addstr(3 + row * 2, 1, name)
            if self.habit_focus and row == self.selected_habit:
                self.stdscr.attroff(curses.color_pair(5))
            
            # Cells
            for col in range(min(7, cols)):
                completed = self.completions.get(habit, [False]*7)[col]
                if row == self.selected_habit and not self.habit_focus:
                    attr = curses.color_pair(5)
                elif completed:
                    attr = curses.color_pair(1)
                else:
                    attr = curses.color_pair(2)
                
                sym = "✓" if completed else " "
                self.stdscr.addstr(3 + row * 2, 20 + col * col_width, sym, attr)
        
        # Stats panel
        self.draw_stats(3 + rows * 2 + 2, width)
        
        # Controls
        controls = [
            "'←→/hjkl': Navigate", "'Space': Toggle", "'Tab': Focus",
            "'a': Add habit", "'d': Delete", "'n': Next week",
            "'s': Save&Exit", "'q': Quit"
        ]
        for i, ctrl in enumerate(controls):
            if 3 + rows * 2 + 5 + i < height - 1:
                self.stdscr.addstr(3 + rows * 2 + 5 + i, 1, ctrl)
        
        self.stdscr.refresh()

    def draw_stats(self, y, width):
        self.stdscr.addstr(y, 1, "Stats (this week):", curses.A_BOLD)
        y += 1
        for i, habit in enumerate(self.habits[:5]):  # Show top 5
            if y + i >= self.stdscr.getmaxyx()[0] - 2:
                break
            streak = self.calc_streak(habit)
            total_done = sum(self.completions[habit])
            pct = (total_done / 7 * 100) if total_done else 0
            stat = f"{habit}: {streak}d streak, {pct:.0f}%"
            self.stdscr.addstr(y + i, 1, stat[:width-10])

    def calc_streak(self, habit):
        comp = self.completions[habit][::-1]
        streak = 0
        for day in comp:
            if day:
                streak += 1
            else:
                break
        return streak

    def toggle_cell(self):
        if not self.habit_focus:
            habit = self.habits[self.selected_habit]
            self.completions[habit][self.current_day] = not self.completions[habit][self.current_day]

    def add_habit(self):
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, "Enter new habit name (max 15 chars, Enter to confirm, ESC to cancel):")
        curses.echo()
        curses.curs_set(1)
        self.stdscr.move(2, 0)
        name = self.stdscr.getstr(2, 0, 15).decode().strip()
        curses.curs_set(0)
        curses.noecho()
        if name and len(self.habits) < MAX_HABITS:
            self.habits.append(name)
            self.completions[name] = [False] * 7

    def delete_habit(self):
        if len(self.habits) > 0:
            del self.habits[self.selected_habit]
            del self.completions[list(self.completions.keys())[self.selected_habit]]
            if self.selected_habit >= len(self.habits):
                self.selected_habit = len(self.habits) - 1

    def next_week(self):
        self.week_start += datetime.timedelta(days=7)
        self.current_day = 0
        for habit in self.habits:
            self.completions[habit] = [False] * 7

    def handle_key(self, key):
        if key == ord('q'):
            return 'quit'
        elif key == ord('s'):
            self.save_data()
            return 'quit'
        elif key == ord('a'):
            self.add_habit()
        elif key == ord('d'):
            self.delete_habit()
        elif key == ord('n'):
            self.next_week()
        elif key == ord('\t'):
            self.habit_focus = not self.habit_focus
        elif key == ord(' '):
            self.toggle_cell()
        elif key == curses.KEY_LEFT or key == ord('h'):
            self.current_day = max(0, self.current_day - 1)
        elif key == curses.KEY_RIGHT or key == ord('l'):
            self.current_day = min(6, self.current_day + 1)
        elif key == curses.KEY_UP or key == ord('k'):
            if self.habit_focus:
                self.selected_habit = max(0, self.selected_habit - 1)
        elif key == curses.KEY_DOWN or key == ord('j'):
            if self.habit_focus:
                self.selected_habit = min(len(self.habits) - 1, self.selected_habit + 1)
        return 'continue'

    def main_loop(self):
        while True:
            self.draw()
            try:
                key = self.stdscr.getch()
                action = self.handle_key(key)
                if action == 'quit':
                    break
            except KeyboardInterrupt:
                break

def main(stdscr):
    try:
        tracker = HabitTracker(stdscr)
    except curses.error:
        pass

if __name__ == "__main__":
    wrapper(main)