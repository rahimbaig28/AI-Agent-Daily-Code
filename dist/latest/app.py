# Auto-generated via Perplexity on 2026-02-02T13:35:16.474865Z
#!/usr/bin/env python3
import json
import csv
import datetime
import collections
import statistics
import curses
import os
import random
import shutil

DATA_FILE = "habits.json"
BACKUP_FILE = "habits_backup.json"

def get_today():
    return datetime.date.today().isoformat()

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                habits = data.get('habits', [])
                logs = data.get('logs', {})
                return habits, logs
        except:
            if os.path.exists(BACKUP_FILE):
                shutil.copy(BACKUP_FILE, DATA_FILE)
            return [], {}
    return [], {}

def save_data(habits, logs):
    data = {'habits': habits, 'logs': logs}
    shutil.copy(DATA_FILE, BACKUP_FILE)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def get_7day_averages(habits, logs):
    today = datetime.date.today()
    averages = {}
    for habit in habits:
        values = []
        for i in range(7):
            date = (today - datetime.timedelta(days=i)).isoformat()
            value = logs.get(date, {}).get(habit, 0)
            values.append(value)
        avg = statistics.mean(values) if values else 0
        averages[habit] = avg
    return averages

def get_stats(habits, logs):
    today = datetime.date.today()
    stats = {}
    for habit in habits:
        values = [logs.get(d, {}).get(habit, 0) for d in logs]
        values = [v for v in values if v > 0]
        if values:
            stats[habit] = {
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'streak': calculate_streak(habits, logs, habit),
                'best': max(values),
                'worst': min(values)
            }
        else:
            stats[habit] = {'mean': 0, 'median': 0, 'streak': 0, 'best': 0, 'worst': 0}
    return stats

def calculate_streak(habits, logs, habit):
    streak = 0
    today = datetime.date.today()
    for i in range(365):
        date = (today - datetime.timedelta(days=i)).isoformat()
        if logs.get(date, {}).get(habit, 0) > 0:
            streak += 1
        else:
            break
    return streak

def get_color(value):
    if value >= 7: return curses.COLOR_GREEN
    elif value >= 4: return curses.COLOR_YELLOW
    else: return curses.COLOR_RED

def draw_bar(stdscr, x, y, value, max_width=50):
    bar_width = int((value / 10.0) * max_width)
    color = get_color(value)
    stdscr.attron(curses.color_pair(color))
    stdscr.addstr(y, x, '#' * bar_width + ' ' * (max_width - bar_width))
    stdscr.attroff(curses.color_pair(color))

def input_dialog(stdscr, prompt):
    curses.echo()
    stdscr.addstr(10, 0, prompt)
    stdscr.refresh()
    return stdscr.getstr(10, len(prompt), 20).decode().strip()

def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    
    habits, logs = load_data()
    
    # Sample data
    sample_habits = ['Exercise', 'Read', 'Hydrate']
    if not habits:
        habits = sample_habits[:]
        today = datetime.date.today()
        for i in range(7):
            date = (today - datetime.timedelta(days=i)).isoformat()
            logs[date] = {}
            for habit in habits:
                logs[date][habit] = random.randint(0, 10)
        save_data(habits, logs)
    
    selected_habit = 0
    selected_day = 0
    show_stats = False
    max_habit = len(habits) - 1
    
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # Header
        stdscr.addstr(0, 0, "Habit Tracker Visualizer", curses.A_BOLD)
        stdscr.addstr(1, 0, f"Controls: ↑↓ habit, ←→ day, ENTER log, s stats, i import, e export, q quit")
        
        # Main chart
        averages = get_7day_averages(habits, logs)
        today = datetime.date.today()
        
        stdscr.addstr(3, 0, "7-Day Rolling Averages (0-10 scale):")
        stdscr.hline(4, 0, '-', w-1)
        
        for i, habit in enumerate(habits):
            y = 5 + i * 2
            if y >= h - 10: break
            
            color = curses.A_REVERSE if i == selected_habit else 0
            stdscr.addstr(y, 0, f"{habit:12}", color)
            
            avg = averages[habit]
            draw_bar(stdscr, 15, y, avg, 50)
            stdscr.addstr(y, 68, f"{avg:.1f}")
        
        # Day selector
        stdscr.addstr(15, 0, "Days:")
        for i in range(7):
            date = (today - datetime.timedelta(days=6-i)).isoformat()
            color = curses.A_REVERSE if i == selected_day else 0
            stdscr.addstr(15, 6 + i*11, date[:10][:10], color)
        
        current_date = (today - datetime.timedelta(days=selected_day)).isoformat()
        stdscr.addstr(17, 0, f"Current: {current_date}")
        if current_date in logs:
            current_values = logs[current_date]
            for i, habit in enumerate(habits):
                if i == selected_habit:
                    stdscr.addstr(18 + i, 0, f"{habit}: {current_values.get(habit, 0)}", curses.A_BOLD)
        
        # Stats panel
        if show_stats:
            stdscr.addstr(25, 0, "Statistics:", curses.A_BOLD)
            stats = get_stats(habits, logs)
            for i, habit in enumerate(habits[:5]):  # Limit display
                s = stats[habit]
                y = 26 + i
                if y >= h - 2: break
                stdscr.addstr(y, 0, f"{habit:10}: mean={s['mean']:.1f} med={s['median']:.1f} streak={s['streak']} best={s['best']} worst={s['worst']}")
        
        stdscr.refresh()
        
        key = stdscr.getch()
        
        if key == ord('q'):
            break
        elif key == curses.KEY_UP and selected_habit > 0:
            selected_habit -= 1
        elif key == curses.KEY_DOWN and selected_habit < max_habit:
            selected_habit += 1
        elif key == curses.KEY_LEFT and selected_day < 6:
            selected_day += 1
        elif key == curses.KEY_RIGHT and selected_day > 0:
            selected_day -= 1
        elif key == 10 or key == curses.KEY_ENTER:  # Enter
            habit = habits[selected_habit]
            current_date = (today - datetime.timedelta(days=selected_day)).isoformat()
            if current_date not in logs:
                logs[current_date] = {}
            
            curses.curs_set(1)
            value = input_dialog(stdscr, f"Enter {habit} value (0-10) [{logs[current_date].get(habit, 0)}]: ")
            curses.curs_set(0)
            
            try:
                new_value = int(value) if value else logs[current_date].get(habit, 0)
                if 0 <= new_value <= 10:
                    logs[current_date][habit] = new_value
                    save_data(habits, logs)
            except ValueError:
                pass
        elif key == ord('s'):
            show_stats = not show_stats
        elif key == ord('i'):
            curses.curs_set(1)
            filename = input_dialog(stdscr, "CSV import file: ")
            curses.curs_set(0)
            try:
                with open(filename, 'r') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 3:
                            date, hname, value = row[0], row[1], int(row[2])
                            if hname not in habits:
                                habits.append(hname)
                            if date not in logs:
                                logs[date] = {}
                            logs[date][hname] = value
                save_data(habits, logs)
            except Exception:
                pass
        elif key == ord('e'):
            curses.curs_set(1)
            choice = input_dialog(stdscr, "Export (j=JSON, c=CSV): ")
            curses.curs_set(0)
            if choice == 'j':
                filename = input_dialog(stdscr, "JSON filename: ")
                save_data(habits, logs)  # Save to habits.json
                shutil.copy(DATA_FILE, filename)
            elif choice == 'c':
                filename = input_dialog(stdscr, "CSV filename: ")
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['date', 'habit', 'value'])
                    for date in logs:
                        for habit in habits:
                            if habit in logs[date]:
                                writer.writerow([date, habit, logs[date][habit]])

if __name__ == "__main__":
    curses.wrapper(main)