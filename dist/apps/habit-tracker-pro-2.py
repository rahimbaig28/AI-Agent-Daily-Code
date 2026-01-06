# Auto-generated via Perplexity on 2026-01-06T04:38:36.438605Z
import json
import os
import datetime
import curses
import re

DATA_FILE = 'habits.json'
ACTION_COUNT_FILE = 'action_count.txt'
TODAY = datetime.date.today().isoformat()

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_action_count():
    if os.path.exists(ACTION_COUNT_FILE):
        try:
            with open(ACTION_COUNT_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            return 0
    return 0

def save_action_count(count):
    with open(ACTION_COUNT_FILE, 'w') as f:
        f.write(str(count))

def calculate_streak(habit_data):
    if not habit_data.get('history'):
        return 0
    
    dates = sorted(habit_data['history'].keys(), reverse=True)
    streak = 0
    for date_str in dates:
        date = datetime.date.fromisoformat(date_str)
        days_ago = (datetime.date.today() - date).days
        if days_ago == streak and habit_data['history'][date_str]:
            streak += 1
        else:
            break
    return streak

def get_status_symbol(habit_data):
    if TODAY in habit_data.get('history', {}):
        return '✓' if habit_data['history'][TODAY] else '✗'
    return ' '

def format_history(history):
    if not history:
        return ["No history"]
    
    dates = sorted(history.keys(), reverse=True)[:7]
    week = []
    for i, date_str in enumerate(dates):
        days_ago = (datetime.date.today() - datetime.date.fromisoformat(date_str)).days
        status = '✓' if history[date_str] else '✗'
        week.append(f"{days_ago}d:{status}")
    
    while len(week) < 7:
        week.append("   -")
    
    return week

def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    try:
        curses.init_pair(1, curses.COLOR_GREEN, -1)   # Completed ✓
        curses.init_pair(2, curses.COLOR_RED, -1)     # Broken ✗  
        curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Selected
        curses.init_pair(4, curses.COLOR_CYAN, -1)    # Header
    except:
        pass

    data = load_data()
    habits = list(data.keys())
    selected = 0
    sort_mode = 'streak'  # 'streak' or 'alpha'
    action_count = load_action_count()
    
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # Header
        stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
        header = f"Habit Tracker Pro | {TODAY} | Habits: {len(habits)} | Sort: {sort_mode}"
        stdscr.addstr(0, 0, header[:w-1])
        stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
        
        # Help
        help_text = "↑↓:Nav SP:Toggle n:add d:del e:edit s:sort v:view r:reset q:quit"
        stdscr.addstr(1, 0, help_text[:w-1])
        
        if not habits:
            stdscr.addstr(3, 0, "No habits. Press 'n' to add one!")
            stdscr.refresh()
        else:
            # Sort habits
            if sort_mode == 'streak':
                sorted_habits = sorted(habits, key=lambda h: calculate_streak(data[h]), reverse=True)
            else:
                sorted_habits = sorted(habits)
            
            # Display habits
            for i, habit in enumerate(sorted_habits[:h-5]):
                streak = calculate_streak(data[habit])
                status = get_status_symbol(data[habit])
                
                line = f"{habit:<25} {status} Streak: {streak:2d}"
                
                if i == selected:
                    stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
                    stdscr.addstr(i+3, 0, line[:w-1])
                    stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
                else:
                    if status == '✓':
                        stdscr.attron(curses.color_pair(1))
                    elif status == '✗':
                        stdscr.attron(curses.color_pair(2))
                    stdscr.addstr(i+3, 0, line[:w-1])
                    stdscr.attroff(curses.color_pair(1) | curses.color_pair(2))
        
        stdscr.refresh()
        
        # Input handling
        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            break
            
        action_count += 1
        if action_count % 10 == 0:
            save_data(data)
            save_action_count(action_count)
        
        if key == ord('q'):
            break
        elif key == curses.KEY_UP and habits:
            selected = (selected - 1) % len(habits)
        elif key == curses.KEY_DOWN and habits:
            selected = (selected + 1) % len(habits)
        elif key == ord(' ') and habits:
            habit = habits[selected]
            if TODAY not in data[habit]['history']:
                data[habit]['history'][TODAY] = False
            data[habit]['history'][TODAY] = not data[habit]['history'][TODAY]
        elif key == ord('n'):
            stdscr.clear()
            stdscr.addstr(0, 0, "New habit name: ")
            stdscr.refresh()
            curses.echo()
            name = stdscr.getstr(1, 0, 30).decode().strip()
            curses.noecho()
            
            if name and name not in data:
                data[name] = {'streak': 0, 'history': {}, 'goal': ''}
                habits.append(name)
        elif key == ord('d') and habits:
            habit = habits[selected]
            del data[habit]
            habits.remove(habit)
            if selected >= len(habits):
                selected = len(habits) - 1
        elif key == ord('e') and habits:
            stdscr.clear()
            habit = habits[selected]
            stdscr.addstr(0, 0, f"Edit '{habit}': ")
            stdscr.refresh()
            curses.echo()
            new_name = stdscr.getstr(1, 0, 30).decode().strip()
            curses.noecho()
            
            if new_name and new_name != habit and new_name not in data:
                data[new_name] = data.pop(habit)
                habits[habits.index(habit)] = new_name
        elif key == ord('s'):
            sort_mode = 'alpha' if sort_mode == 'streak' else 'streak'
        elif key == ord('v') and habits:
            stdscr.clear()
            habit = habits[selected]
            stdscr.addstr(0, 0, f"7-day history for {habit}:")
            stdscr.addstr(2, 0, "-" * 40)
            
            history_lines = format_history(data[habit].get('history', {}))
            for i, line in enumerate(history_lines):
                stdscr.addstr(3+i, 0, line)
            
            stdscr.addstr(11, 0, "Press any key to continue...")
            stdscr.refresh()
            stdscr.getch()
        elif key == ord('r') and habits:
            habit = habits[selected]
            data[habit]['history'] = {}
            data[habit]['streak'] = 0
    
    save_data(data)
    save_action_count(action_count)

if __name__ == "__main__":
    curses.wrapper(main)
    
    # Test data generation
    print("Habit Tracker Pro loaded successfully!")
    print("Test: Run the app, add habits with 'n', toggle with spacebar.")
    print("Data stored in habits.json. View with: cat habits.json")