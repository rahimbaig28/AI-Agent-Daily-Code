# Auto-generated via Perplexity on 2026-01-24T07:31:10.391248Z
#!/usr/bin/env python3
"""
Simple console-based Habit Tracker.

Tracks daily completion of habits and calculates current streaks.
Uses only standard library.
"""
import datetime
import json
import os
import sys
from typing import Dict, List

DATA_FILE = 'habits.json'

def load_habits() -> Dict[str, List[bool]]:
    """Load habits from JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_habits(habits: Dict[str, List[bool]]):
    """Save habits to JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(habits, f, indent=2)

def get_today_index() -> int:
    """Get today's index (days since epoch)."""
    today = datetime.date.today()
    epoch = datetime.date(2023, 1, 1)  # Fixed start date
    return (today - epoch).days

def calculate_streak(habit_days: List[bool]) -> int:
    """Calculate current streak for a habit."""
    streak = 0
    today_idx = get_today_index()
    for i in range(today_idx, -1, -1):
        if i >= len(habit_days):
            continue
        if habit_days[i]:
            streak += 1
        else:
            break
    return streak

def print_status(habits: Dict[str, List[bool]]):
    """Print current status of all habits."""
    today_idx = get_today_index()
    print("\n=== Habit Tracker Status ===")
    print(f"Today: {datetime.date.today()}")
    print()
    
    for habit, days in habits.items():
        streak = calculate_streak(days)
        completed_today = today_idx < len(days) and days[today_idx]
        status = "✅" if completed_today else "❌"
        print(f"{habit}: {status} (Streak: {streak} days)")
    
    print()

def mark_habit(habits: Dict[str, List[bool]], habit_name: str):
    """Mark a habit as completed today."""
    today_idx = get_today_index()
    if habit_name not in habits:
        habits[habit_name] = [False] * (today_idx + 1)
    while len(habits[habit_name]) <= today_idx:
        habits[habit_name].append(False)
    habits[habit_name][today_idx] = True
    print(f"✅ Marked '{habit_name}' as completed for today.")

def add_habit(habits: Dict[str, List[bool]], habit_name: str):
    """Add a new habit."""
    if habit_name in habits:
        print(f"'{habit_name}' already exists.")
        return
    habits[habit_name] = []
    print(f"Added new habit: '{habit_name}'")

def main():
    habits = load_habits()
    
    while True:
        print_status(habits)
        print("Commands: mark <habit>, add <habit>, list, quit")
        cmd = input("> ").strip()
        
        if cmd == 'quit':
            save_habits(habits)
            print("Habits saved. Goodbye!")
            break
        elif cmd == 'list':
            continue
        elif cmd.startswith('mark '):
            habit = cmd[5:].strip()
            if habit:
                mark_habit(habits, habit)
        elif cmd.startswith('add '):
            habit = cmd[4:].strip()
            if habit:
                add_habit(habits, habit)
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()