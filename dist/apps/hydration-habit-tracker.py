# Auto-generated via Perplexity on 2026-01-24T04:05:39.173250Z
#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

DATA_FILE = "hydration.json"
BACKUP_FILE = "hydration.json.bak"

def detect_theme():
    term = os.environ.get('TERM', '').lower()
    if 'dark' in term or term in ['xterm-256color', 'screen']:
        return 'dark'
    return 'light'

def get_color(theme, color_type):
    if theme == 'dark':
        colors = {
            'dim': '\033[90m',
            'reset': '\033[0m',
            'bold': '\033[1m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'red': '\033[91m',
        }
    else:
        colors = {
            'dim': '\033[37m',
            'reset': '\033[0m',
            'bold': '\033[1m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'red': '\033[31m',
        }
    return colors.get(color_type, '')

def load_data():
    if Path(DATA_FILE).exists():
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                return data
        except (json.JSONDecodeError, IOError):
            Path(DATA_FILE).rename(BACKUP_FILE)
            return {'entries': [], 'goal': 8}
    return {'entries': [], 'goal': 8}

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Error saving data: {e}")

def log_water(data, theme):
    print("\n--- Log Water Intake ---")
    while True:
        try:
            cups_input = input("Enter cups (1-20) or 'q' to quit: ").strip()
            if cups_input.lower() == 'q':
                return
            cups = int(cups_input)
            if 1 <= cups <= 20:
                break
            print("Please enter a number between 1 and 20.")
        except ValueError:
            print("Invalid input. Enter a number.")
    
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now().strftime('%H:%M')
    
    entry = {'date': today, 'cups': cups, 'time': now}
    data['entries'].append(entry)
    save_data(data)
    
    color_green = get_color(theme, 'green')
    color_reset = get_color(theme, 'reset')
    print(f"{color_green}✓ Logged {cups} cups at {now}{color_reset}")

def get_daily_summary(data, date_str):
    total = sum(e['cups'] for e in data['entries'] if e['date'] == date_str)
    return total

def get_streak(data):
    if not data['entries']:
        return 0
    
    sorted_entries = sorted(set(e['date'] for e in data['entries']), reverse=True)
    today = datetime.now().strftime('%Y-%m-%d')
    streak = 0
    current_date = datetime.strptime(today, '%Y-%m-%d')
    
    for date_str in sorted_entries:
        entry_date = datetime.strptime(date_str, '%Y-%m-%d')
        if (current_date - entry_date).days == streak:
            streak += 1
            current_date = entry_date
        else:
            break
    
    return streak

def view_daily_summary(data, theme):
    today = datetime.now().strftime('%Y-%m-%d')
    cups_today = get_daily_summary(data, today)
    goal = data['goal']
    percentage = int((cups_today / goal * 100)) if goal > 0 else 0
    streak = get_streak(data)
    
    color_bold = get_color(theme, 'bold')
    color_green = get_color(theme, 'green')
    color_reset = get_color(theme, 'reset')
    
    print(f"\n--- Daily Summary ({today}) ---")
    print(f"{color_bold}{cups_today}/{goal} cups - {percentage}%{color_reset}")
    print(f"Streak: {color_green}{streak} day(s){color_reset}")
    input("\nPress Enter to continue...")

def view_weekly_summary(data, theme):
    print("\n--- Weekly Summary ---")
    today = datetime.now()
    week_data = {}
    
    for i in range(7):
        date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        cups = get_daily_summary(data, date)
        week_data[date] = cups
    
    goal = data['goal']
    color_bold = get_color(theme, 'bold')
    color_reset = get_color(theme, 'reset')
    
    print(f"\n{'Date':<12} {'Cups':<8} {'% Goal':<10}")
    print("-" * 30)
    
    total_cups = 0
    for date in sorted(week_data.keys()):
        cups = week_data[date]
        total_cups += cups
        percentage = int((cups / goal * 100)) if goal > 0 else 0
        print(f"{date:<12} {cups:<8} {percentage}%")
    
    avg = total_cups / 7
    print("-" * 30)
    print(f"Average: {avg:.1f} cups/day")
    input("\nPress Enter to continue...")

def set_daily_goal(data, theme):
    print("\n--- Set Daily Goal ---")
    while True:
        try:
            goal_input = input(f"Enter daily goal (current: {data['goal']} cups) or 'q' to quit: ").strip()
            if goal_input.lower() == 'q':
                return
            goal = int(goal_input)
            if goal > 0:
                data['goal'] = goal
                save_data(data)
                color_green = get_color(theme, 'green')
                color_reset = get_color(theme, 'reset')
                print(f"{color_green}✓ Goal set to {goal} cups{color_reset}")
                return
            print("Goal must be positive.")
        except ValueError:
            print("Invalid input. Enter a number.")

def export_json(data, theme):
    export_file = "hydration_export.json"
    try:
        with open(export_file, 'w') as f:
            json.dump(data, f, indent=2)
        color_green = get_color(theme, 'green')
        color_reset = get_color(theme, 'reset')
        print(f"{color_green}✓ Exported to {export_file}{color_reset}")
    except IOError as e:
        print(f"Export error: {e}")
    input("\nPress Enter to continue...")

def import_json(data, theme):
    print("\n--- Import JSON ---")
    import_file = input("Enter filename to import (or 'q' to quit): ").strip()
    if import_file.lower() == 'q':
        return
    
    if not Path(import_file).exists():
        print("File not found.")
        return
    
    try:
        with open(import_file, 'r') as f:
            import_data = json.load(f)
        
        if 'entries' in import_data:
            response = input("Overwrite existing entries? (y/n): ").strip().lower()
            if response == 'y':
                data['entries'] = import_data['entries']
            else:
                data['entries'].extend(import_data['entries'])
        
        if 'goal' in import_data:
            data['goal'] = import_data['goal']
        
        save_data(data)
        color_green = get_color(theme, 'green')
        color_reset = get_color(theme, 'reset')
        print(f"{color_green}✓ Imported successfully{color_reset}")
    except (json.JSONDecodeError, IOError) as e:
        print(f"Import error: {e}")
    
    input("\nPress Enter to continue...")

def print_report(data, theme):
    print("\n--- 30-Day Report ---")
    today = datetime.now()
    goal = data['goal']
    
    print(f"\n{'Date':<12} {'Cups':<8} {'% Goal':<10} {'Status':<15}")
    print("-" * 50)
    
    total_cups = 0
    days_met_goal = 0
    
    for i in range(29, -1, -1):
        date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        cups = get_daily_summary(data, date)
        total_cups += cups
        percentage = int((cups / goal * 100)) if goal > 0 else 0
        
        if cups >= goal:
            status = "✓ Goal Met"
            days_met_goal += 1
        elif cups > 0:
            status = "~ Partial"
        else:
            status = "✗ No intake"
        
        print(f"{date:<12} {cups:<8} {percentage}%{' ' * 6}{status:<15}")
    
    print("-" * 50)
    avg = total_cups / 30
    success_rate = int((days_met_goal / 30 * 100))
    print(f"30-Day Average: {avg:.1f} cups/day")
    print(f"Days Goal Met: {days_met_goal}/30 ({success_rate}%)")
    print("\n💧 Stay hydrated! 💧")
    input("\nPress Enter to continue...")

def main():
    theme = detect_theme()
    data = load_data()
    
    while True:
        color_bold = get_color(theme, 'bold')
        color_reset = get_color(theme, 'reset')
        
        print(f"\n{color_bold}=== Hydration Habit Tracker ==={color_reset}")
        print("1) Log water intake")
        print("2) View daily summary")
        print("3) View weekly summary")
        print("4) Set daily goal")
        print("5) Export JSON")
        print("6) Import JSON")
        print("7) Print 30-day report")
        print("8) Quit")
        
        choice = input("\nSelect option (1-8): ").strip()
        
        if choice == '1':
            log_water(data, theme)
        elif choice == '2':
            view_daily_summary(data, theme)
        elif choice == '3':
            view_weekly_summary(data, theme)
        elif choice == '4':
            set_daily_goal(data, theme)
        elif choice == '5':
            export_json(data, theme)
        elif choice == '6':
            import_json(data, theme)
        elif choice == '7':
            print_report(data, theme)
        elif choice == '8' or choice.lower() == 'q':
            print("Goodbye!")
            break
        else:
            print("Invalid option. Try again.")

if __name__ == '__main__':
    main()