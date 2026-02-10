# Auto-generated via Perplexity on 2026-02-10T12:00:50.781127Z
#!/usr/bin/env python3
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path
import curses
from typing import List, Dict, Any, Optional

DATA_FILE = Path.home() / "habit_tracker.json"
TODAY = date.today()

class Habit:
    def __init__(self, name: str, weekly_target: int = 7, streak: int = 0, history: List[str] = None):
        self.name = name[:20]
        self.weekly_target = weekly_target
        self.streak = streak
        self.history = history or []

    def is_completed_today(self) -> bool:
        return TODAY.isoformat() in self.history

    def toggle_today(self) -> int:
        today_str = TODAY.isoformat()
        if today_str in self.history:
            self.history.remove(today_str)
            self._update_streak()
            return 0  # unmarked
        else:
            self.history.append(today_str)
            self.streak += 1
            return 1  # marked

    def _update_streak(self):
        if not self.history:
            self.streak = 0
            return
        
        history_dates = [date.fromisoformat(d) for d in self.history]
        history_dates.sort()
        
        self.streak = 0
        for i in range(1, len(history_dates)):
            if history_dates[i] == history_dates[i-1] + timedelta(days=1):
                self.streak += 1
            else:
                break

    def weekly_completion(self) -> float:
        week_ago = TODAY - timedelta(days=7)
        week_history = [d for d in self.history if date.fromisoformat(d) >= week_ago]
        return len(week_history) / 7 * 100

class HabitTracker:
    def __init__(self):
        self.habits: List[Habit] = []
        self.load()

    def load(self):
        try:
            if DATA_FILE.exists():
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.habits = [Habit(**h) for h in data]
        except (json.JSONDecodeError, KeyError, TypeError):
            self.habits = []
            self.save()

    def save(self):
        try:
            data = [{
                'name': h.name,
                'streak': h.streak,
                'weekly_target': h.weekly_target,
                'history': h.history
            } for h in self.habits]
            DATA_FILE.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def add_habit(self, name: str, weekly_target: int = 7):
        if len([h for h in self.habits if h.name == name]) == 0:
            self.habits.append(Habit(name, weekly_target))
            self.save()

    def delete_habit(self, index: int):
        if 0 <= index < len(self.habits):
            del self.habits[index]
            self.save()

    def toggle_habit(self, index: int) -> bool:
        if 0 <= index < len(self.habits):
            return self.habits[index].toggle_today() == 1
        return False

def detect_theme(stdscr) -> str:
    term = os.environ.get('TERM', '')
    if 'dark' in term.lower() or '256color' in term:
        return 'dark'
    return 'light'

def get_colors(theme: str):
    if theme == 'dark':
        return {
            'bg': curses.COLOR_BLACK,
            'fg': curses.COLOR_WHITE,
            'highlight': curses.COLOR_CYAN,
            'success': curses.COLOR_GREEN,
            'error': curses.COLOR_RED,
            'warning': curses.COLOR_YELLOW
        }
    return {
        'bg': curses.COLOR_WHITE,
        'fg': curses.COLOR_BLACK,
        'highlight': curses.COLOR_BLUE,
        'success': curses.COLOR_GREEN,
        'error': curses.COLOR_RED,
        'warning': curses.COLOR_MAGENTA
    }

def draw_table(stdscr, tracker: HabitTracker, selected: int, mode: str, colors: Dict[str, int], maxy: int, maxx: int):
    stdscr.clear()
    
    # Header
    header = "Habit Tracker Pro - Use ↑↓ to navigate, ENTER to toggle, A=add, D=delete, S=stats, R=reset, Q=quit"
    stdscr.addstr(0, (maxx - len(header)) // 2, header, curses.color_pair(1) | curses.A_BOLD)
    
    if mode == 'stats':
        draw_stats(stdscr, tracker, colors, maxy, maxx)
        return
    
    # Table headers
    headers = ["Name", "Streak", "Today", "Week %"]
    col_widths = [20, 8, 6, 8]
    x_pos = 2
    for i, (header, width) in enumerate(zip(headers, col_widths)):
        stdscr.addstr(2, x_pos, header.ljust(width), curses.color_pair(1) | curses.A_BOLD)
        x_pos += width + 2
    
    # Table rows
    for i, habit in enumerate(tracker.habits):
        row = i + 3
        if row >= maxy - 2:
            break
            
        is_selected = (i == selected)
        attrs = curses.color_pair(1) | curses.A_BOLD if is_selected else curses.color_pair(0)
        
        # Name
        name = habit.name.ljust(col_widths[0])[:col_widths[0]]
        stdscr.addstr(row, 2, name, attrs)
        
        # Streak
        streak_str = str(habit.streak).rjust(col_widths[1])
        stdscr.addstr(row, 2 + col_widths[0] + 2, streak_str, attrs)
        
        # Today
        today_str = "✓" if habit.is_completed_today() else "✗"
        color = 3 if habit.is_completed_today() else 5  # green or yellow
        stdscr.addstr(row, 2 + sum(col_widths[:2]) + 4, today_str.rjust(col_widths[2]), 
                     curses.color_pair(color) | attrs)
        
        # Week %
        week_pct = f"{habit.weekly_completion():.0f}%".rjust(col_widths[3])
        stdscr.addstr(row, 2 + sum(col_widths[:3]) + 6, week_pct, attrs)
    
    # Status line
    if tracker.habits:
        status = f"Selected: {tracker.habits[selected].name} | {len([h for h in tracker.habits if h.is_completed_today()])}/{len(tracker.habits)} complete today"
    else:
        status = "No habits - press 'A' to add one"
    stdscr.addstr(maxy - 1, 1, status[:maxx-2])
    
    stdscr.refresh()

def draw_stats(stdscr, tracker: HabitTracker, colors: Dict[str, int], maxy: int, maxx: int):
    stdscr.clear()
    stdscr.addstr(0, 2, "📊 STATISTICS", curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(2, 2, "Press ENTER to return", curses.color_pair(0))
    
    if not tracker.habits:
        stdscr.addstr(4, 2, "No habits to analyze", curses.color_pair(5))
        stdscr.refresh()
        return
    
    # Top streaks
    stdscr.addstr(5, 2, "🏆 TOP STREAKS:", curses.color_pair(1) | curses.A_BOLD)
    sorted_habits = sorted(tracker.habits, key=lambda h: h.streak, reverse=True)
    for i, habit in enumerate(sorted_habits[:5]):
        stdscr.addstr(6 + i, 4, f"{habit.name}: {habit.streak}", curses.color_pair(3))
    
    # Overall stats
    total_streak = sum(h.streak for h in tracker.habits)
    avg_completion = sum(h.weekly_completion() for h in tracker.habits) / len(tracker.habits)
    stdscr.addstr(12, 2, f"📈 Total streak points: {total_streak}", curses.color_pair(1))
    stdscr.addstr(13, 2, f"📊 Avg weekly completion: {avg_completion:.1f}%", curses.color_pair(1))
    
    stdscr.refresh()

def prompt_input(stdscr, prompt: str, colors: Dict[str, int], maxx: int) -> str:
    curses.echo()
    stdscr.clear()
    stdscr.addstr(0, 2, prompt, curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(2, 2, "Enter text (max 20 chars): ")
    stdscr.refresh()
    
    curses.curs_set(1)
    input_str = stdscr.getstr(2, 24, 20).decode('utf-8').strip()
    curses.curs_set(0)
    curses.noecho()
    return input_str

def main(stdscr):
    try:
        curses.curs_set(0)
        curses.use_default_colors()
        
        theme = detect_theme(stdscr)
        colors = get_colors(theme)
        
        # Initialize color pairs
        curses.start_color()
        curses.init_pair(1, colors['highlight'], colors['bg'])  # header/selected
        curses.init_pair(2, colors['fg'], colors['bg'])         # normal
        curses.init_pair(3, colors['success'], colors['bg'])    # success
        curses.init_pair(4, colors['warning'], colors['bg'])    # warning  
        curses.init_pair(5, colors['error'], colors['bg'])      # error
        
        tracker = HabitTracker()
        selected = 0
        mode = 'main'  # main, stats
        
        while True:
            maxy, maxx = stdscr.getmaxyx()
            
            if mode == 'main':
                if tracker.habits:
                    selected = selected % len(tracker.habits)
                
                draw_table(stdscr, tracker, selected, mode, colors, maxy, maxx)
                
                key = stdscr.getch()
                
                if key == ord('q') or key == 27:  # q or ESC
                    break
                elif key == ord('a'):  # add
                    name = prompt_input(stdscr, "ADD HABIT", colors, maxx)
                    if name:
                        tracker.add_habit(name)
                elif key == ord('d') and tracker.habits:  # delete
                    tracker.delete_habit(selected)
                    if selected >= len(tracker.habits):
                        selected = max(0, len(tracker.habits) - 1)
                elif key == ord('s'):  # stats
                    mode = 'stats'
                elif key == ord('r'):  # reset yesterday
                    yesterday = (TODAY - timedelta(days=1)).isoformat()
                    for habit in tracker.habits:
                        if yesterday in habit.history:
                            habit.history.remove(yesterday)
                            habit._update_streak()
                    tracker.save()
                elif key == 10 or key == curses.KEY_ENTER:  # enter - toggle
                    if tracker.habits:
                        was_completed = tracker.toggle_habit(selected)
                        tracker.save()
                elif key == curses.KEY_UP and tracker.habits:
                    selected = (selected - 1) % len(tracker.habits)
                elif key == curses.KEY_DOWN and tracker.habits:
                    selected = (selected + 1) % len(tracker.habits)
            
            elif mode == 'stats':
                key = stdscr.getch()
                if key == 10 or key == curses.KEY_ENTER or key == ord('q'):
                    mode = 'main'
        
        tracker.save()
        sys.exit(0)
        
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        sys.exit(1)

if __name__ == "__main__":
    curses.wrapper(main)