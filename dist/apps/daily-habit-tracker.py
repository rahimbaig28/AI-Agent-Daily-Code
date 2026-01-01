# Auto-generated via Perplexity on 2026-01-01T12:39:41.885697Z
import curses
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

class HabitTracker:
    def __init__(self):
        self.habits_file = "habits.json"
        self.habits = []
        self.history = []
        self.history_index = -1
        self.load_habits()
        self.selected_idx = 0
        self.mode = "main"
        self.input_buffer = ""
        self.edit_idx = -1

    def load_habits(self):
        if os.path.exists(self.habits_file):
            try:
                with open(self.habits_file, 'r') as f:
                    self.habits = json.load(f)
            except:
                self.habits = []
        else:
            self.habits = []

    def save_habits(self):
        with open(self.habits_file, 'w') as f:
            json.dump(self.habits, f, indent=2)

    def push_state(self):
        self.history = self.history[:self.history_index + 1]
        self.history.append(json.loads(json.dumps(self.habits)))
        self.history_index += 1
        if len(self.history) > 10:
            self.history.pop(0)
            self.history_index -= 1

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.habits = json.loads(json.dumps(self.history[self.history_index]))

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.habits = json.loads(json.dumps(self.history[self.history_index]))

    def add_habit(self, name):
        if name.strip():
            self.push_state()
            self.habits.append({
                "name": name.strip(),
                "streak": 0,
                "completions": {}
            })
            self.save_habits()

    def delete_habit(self, idx):
        if 0 <= idx < len(self.habits):
            self.push_state()
            self.habits.pop(idx)
            self.save_habits()
            if self.selected_idx >= len(self.habits) and self.selected_idx > 0:
                self.selected_idx -= 1

    def edit_habit(self, idx, name):
        if 0 <= idx < len(self.habits) and name.strip():
            self.push_state()
            self.habits[idx]["name"] = name.strip()
            self.save_habits()

    def toggle_completion(self, idx):
        if 0 <= idx < len(self.habits):
            self.push_state()
            today = datetime.utcnow().strftime("%Y-%m-%d")
            habit = self.habits[idx]
            if today not in habit["completions"]:
                habit["completions"][today] = True
            else:
                habit["completions"][today] = not habit["completions"][today]
            self.update_streak(idx)
            self.save_habits()

    def update_streak(self, idx):
        habit = self.habits[idx]
        completions = habit["completions"]
        today = datetime.utcnow().date()
        streak = 0
        current = today
        while current.strftime("%Y-%m-%d") in completions and completions[current.strftime("%Y-%m-%d")]:
            streak += 1
            current -= timedelta(days=1)
        habit["streak"] = streak

    def get_today_status(self, idx):
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if 0 <= idx < len(self.habits):
            completions = self.habits[idx]["completions"]
            return completions.get(today, False)
        return False

    def get_last_completed(self, idx):
        if 0 <= idx < len(self.habits):
            completions = self.habits[idx]["completions"]
            dates = sorted([d for d, v in completions.items() if v], reverse=True)
            return dates[0] if dates else "Never"
        return "Never"

    def get_week_completion(self, idx):
        if 0 <= idx < len(self.habits):
            completions = self.habits[idx]["completions"]
            today = datetime.utcnow().date()
            count = 0
            for i in range(7):
                date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
                if completions.get(date_str, False):
                    count += 1
            return f"{count}/7"
        return "0/7"

    def draw(self, stdscr):
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        if self.mode == "main":
            self.draw_main(stdscr, h, w)
        elif self.mode == "add":
            self.draw_add(stdscr, h, w)
        elif self.mode == "edit":
            self.draw_edit(stdscr, h, w)
        elif self.mode == "help":
            self.draw_help(stdscr, h, w)

        stdscr.refresh()

    def draw_main(self, stdscr, h, w):
        try:
            curses.curs_set(0)
            if curses.has_colors():
                curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
                curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
                curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
                curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)

            stdscr.addstr(0, 0, "DAILY HABIT TRACKER", curses.A_BOLD)
            stdscr.addstr(1, 0, "=" * min(w, 80))

            header = "Habit | Streak | Today | Last Completed | Week"
            stdscr.addstr(3, 0, header[:w-1])
            stdscr.addstr(4, 0, "-" * min(w, 80))

            for i, habit in enumerate(self.habits):
                if i + 5 >= h - 3:
                    break
                today_status = "✓" if self.get_today_status(i) else "○"
                last = self.get_last_completed(i)
                week = self.get_week_completion(i)
                line = f"{habit['name'][:15]:15} | {habit['streak']:6} | {today_status:5} | {last:14} | {week}"
                line = line[:w-1]

                if i == self.selected_idx:
                    stdscr.addstr(i + 5, 0, line, curses.color_pair(1) | curses.A_BOLD)
                else:
                    stdscr.addstr(i + 5, 0, line)

            status_y = h - 3
            status = "a:add e:edit d:delete r:reset u:undo y:redo ?:help q:quit"
            stdscr.addstr(status_y, 0, status[:w-1], curses.A_DIM)

            if self.selected_idx < len(self.habits):
                habit = self.habits[self.selected_idx]
                msg = f"Selected: {habit['name']} (Streak: {habit['streak']})"
                stdscr.addstr(h - 2, 0, msg[:w-1], curses.color_pair(2))
            else:
                stdscr.addstr(h - 2, 0, "No habits. Press 'a' to add one.", curses.color_pair(4))

        except curses.error:
            pass

    def draw_add(self, stdscr, h, w):
        stdscr.addstr(h // 2 - 2, 0, "Add New Habit")
        stdscr.addstr(h // 2, 0, "Name: " + self.input_buffer)
        stdscr.addstr(h // 2 + 2, 0, "(Enter to save, Esc to cancel)")
        curses.curs_set(1)

    def draw_edit(self, stdscr, h, w):
        if 0 <= self.edit_idx < len(self.habits):
            stdscr.addstr(h // 2 - 2, 0, f"Edit Habit #{self.edit_idx + 1}")
            stdscr.addstr(h // 2, 0, "Name: " + self.input_buffer)
            stdscr.addstr(h // 2 + 2, 0, "(Enter to save, Esc to cancel)")
            curses.curs_set(1)

    def draw_help(self, stdscr, h, w):
        help_text = [
            "DAILY HABIT TRACKER - HELP",
            "",
            "NAVIGATION:",
            "  ↑/↓ - Select habit",
            "",
            "ACTIONS:",
            "  SPACE - Toggle completion for today",
            "  a - Add new habit",
            "  e - Edit selected habit",
            "  d - Delete selected habit",
            "  r - Reset streak to 0",
            "  u - Undo last action",
            "  y - Redo last action",
            "  ? - Show this help",
            "  q - Quit and save",
            "",
            "FEATURES:",
            "  • Streaks: consecutive days completed",
            "  • Week: completion count for last 7 days",
            "  • Auto-save to habits.json",
            "  • 10-step undo/redo history",
            "",
            "Press any key to return..."
        ]
        for i, line in enumerate(help_text):
            if i < h - 1:
                stdscr.addstr(i, 0, line[:w-1])

    def run(self, stdscr):
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)

        while True:
            self.draw(stdscr)
            try:
                ch = stdscr.getch()
            except:
                continue

            if self.mode == "main":
                if ch == ord('q'):
                    break
                elif ch == curses.KEY_UP:
                    if self.selected_idx > 0:
                        self.selected_idx -= 1
                elif ch == curses.KEY_DOWN:
                    if self.selected_idx < len(self.habits) - 1:
                        self.selected_idx += 1
                elif ch == ord(' '):
                    self.toggle_completion(self.selected_idx)
                elif ch == ord('a'):
                    self.mode = "add"
                    self.input_buffer = ""
                elif ch == ord('e'):
                    if 0 <= self.selected_idx < len(self.habits):
                        self.mode = "edit"
                        self.edit_idx = self.selected_idx
                        self.input_buffer = self.habits[self.selected_idx]["name"]
                elif ch == ord('d'):
                    self.delete_habit(self.selected_idx)
                elif ch == ord('r'):
                    if 0 <= self.selected_idx < len(self.habits):
                        self.push_state()
                        self.habits[self.selected_idx]["streak"] = 0
                        self.save_habits()
                elif ch == ord('u'):
                    self.undo()
                elif ch == ord('y'):
                    self.redo()
                elif ch == ord('?'):
                    self.mode = "help"

            elif self.mode == "add":
                if ch == 27:
                    self.mode = "main"
                elif ch == 10:
                    self.add_habit(self.input_buffer)
                    self.mode = "main"
                elif ch == curses.KEY_BACKSPACE or ch == 127:
                    self.input_buffer = self.input_buffer[:-1]
                elif 32 <= ch <= 126:
                    self.input_buffer += chr(ch)

            elif self.mode == "edit":
                if ch == 27:
                    self.mode = "main"
                elif ch == 10:
                    self.edit_habit(self.edit_idx, self.input_buffer)
                    self.mode = "main"
                elif ch == curses.KEY_BACKSPACE or ch == 127:
                    self.input_buffer = self.input_buffer[:-1]
                elif 32 <= ch <= 126:
                    self.input_buffer += chr(ch)

            elif self.mode == "help":
                self.mode = "main"

        curses.nocbreak()
        curses.echo()
        stdscr.keypad(False)
        curses.endwin()

if __name__ == "__main__":
    tracker = HabitTracker()
    curses.wrapper(tracker.run)