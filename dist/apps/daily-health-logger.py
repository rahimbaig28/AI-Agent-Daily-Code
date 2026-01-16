# Auto-generated via Perplexity on 2026-01-16T15:37:34.822232Z
#!/usr/bin/env python3

import json
import os
from datetime import datetime, timedelta

def get_log_path():
    return os.path.join(os.path.expanduser("~"), "health_log.json")

def load_data():
    path = get_log_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        print("Warning: Could not read health_log.json. Starting fresh.")
        return []

def save_data(data):
    path = get_log_path()
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Error saving data: {e}")

def get_today():
    return datetime.now().strftime("%Y-%m-%d")

def get_week_dates():
    today = datetime.now()
    start = today - timedelta(days=6)
    return [start + timedelta(days=i) for i in range(7)]

def find_entry(data, date):
    for entry in data:
        if entry["date"] == date:
            return entry
    return None

def log_entry(data):
    today = get_today()
    existing = find_entry(data, today)
    
    if existing:
        print(f"\nEntry for {today} already exists.")
        choice = input("Update it? (y/n): ").strip().lower()
        if choice != 'y':
            return data
        data.remove(existing)
    
    print(f"\n--- Log Entry for {today} ---")
    
    while True:
        try:
            water = float(input("Water intake (cups): "))
            if water < 0:
                raise ValueError
            break
        except ValueError:
            print("Please enter a positive number.")
    
    while True:
        try:
            sleep = float(input("Sleep hours: "))
            if sleep < 0:
                raise ValueError
            break
        except ValueError:
            print("Please enter a positive number.")
    
    while True:
        try:
            exercise = float(input("Exercise minutes: "))
            if exercise < 0:
                raise ValueError
            break
        except ValueError:
            print("Please enter a positive number.")
    
    while True:
        try:
            mood = int(input("Mood (1-5): "))
            if mood < 1 or mood > 5:
                raise ValueError
            break
        except ValueError:
            print("Please enter a number between 1 and 5.")
    
    notes = input("Notes (optional): ").strip()
    
    entry = {
        "date": today,
        "water": water,
        "sleep": sleep,
        "exercise": exercise,
        "mood": mood,
        "notes": notes
    }
    
    data.append(entry)
    save_data(data)
    print("Entry saved.\n")
    return data

def view_week(data):
    week_dates = get_week_dates()
    today = get_today()
    
    print("\n--- Weekly Summary ---")
    print(f"{'Date':<12} {'Water':<8} {'Sleep':<8} {'Exercise':<10} {'Mood':<6} {'Notes':<20}")
    print("-" * 70)
    
    totals = {"water": 0, "sleep": 0, "exercise": 0, "mood": 0, "count": 0}
    
    for date_obj in week_dates:
        date_str = date_obj.strftime("%Y-%m-%d")
        entry = find_entry(data, date_str)
        
        if entry:
            water = entry["water"]
            sleep = entry["sleep"]
            exercise = entry["exercise"]
            mood = entry["mood"]
            notes = entry["notes"][:17] if entry["notes"] else ""
            
            totals["water"] += water
            totals["sleep"] += sleep
            totals["exercise"] += exercise
            totals["mood"] += mood
            totals["count"] += 1
            
            marker = " (today)" if date_str == today else ""
            print(f"{date_str:<12} {water:<8.1f} {sleep:<8.1f} {exercise:<10.1f} {mood:<6} {notes:<20}{marker}")
        else:
            print(f"{date_str:<12} {'--':<8} {'--':<8} {'--':<10} {'--':<6}")
    
    print("-" * 70)
    if totals["count"] > 0:
        avg_mood = totals["mood"] / totals["count"]
        print(f"{'Weekly Avg':<12} {totals['water']:<8.1f} {totals['sleep']/totals['count']:<8.1f} {totals['exercise']:<10.1f} {avg_mood:<6.1f}")
    print()

def today_status(data):
    today = get_today()
    entry = find_entry(data, today)
    
    print(f"\n--- Today's Status ({today}) ---")
    if entry:
        print(f"Water: {entry['water']} cups")
        print(f"Sleep: {entry['sleep']} hours")
        print(f"Exercise: {entry['exercise']} minutes")
        print(f"Mood: {entry['mood']}/5")
        if entry['notes']:
            print(f"Notes: {entry['notes']}")
    else:
        print("No entry logged yet.")
    
    week_dates = get_week_dates()
    week_water = sum(find_entry(data, d.strftime("%Y-%m-%d"))["water"] for d in week_dates if find_entry(data, d.strftime("%Y-%m-%d")))
    week_entries = [find_entry(data, d.strftime("%Y-%m-%d")) for d in week_dates if find_entry(data, d.strftime("%Y-%m-%d"))]
    
    if week_entries:
        avg_sleep = sum(e["sleep"] for e in week_entries) / len(week_entries)
        total_exercise = sum(e["exercise"] for e in week_entries)
        print(f"\nWeek Quick Stats:")
        print(f"Total water: {week_water} cups")
        print(f"Avg sleep: {avg_sleep:.1f} hours")
        print(f"Total exercise: {total_exercise} minutes")
    print()

def edit_last(data):
    if not data:
        print("\nNo entries to edit.\n")
        return data
    
    last = data[-1]
    print(f"\n--- Edit Last Entry ({last['date']}) ---")
    print("1. Water intake")
    print("2. Sleep hours")
    print("3. Exercise minutes")
    print("4. Mood")
    print("5. Notes")
    print("6. Cancel")
    
    choice = input("Select field to edit: ").strip()
    
    if choice == "1":
        while True:
            try:
                last["water"] = float(input("New water intake (cups): "))
                if last["water"] < 0:
                    raise ValueError
                break
            except ValueError:
                print("Please enter a positive number.")
    elif choice == "2":
        while True:
            try:
                last["sleep"] = float(input("New sleep hours: "))
                if last["sleep"] < 0:
                    raise ValueError
                break
            except ValueError:
                print("Please enter a positive number.")
    elif choice == "3":
        while True:
            try:
                last["exercise"] = float(input("New exercise minutes: "))
                if last["exercise"] < 0:
                    raise ValueError
                break
            except ValueError:
                print("Please enter a positive number.")
    elif choice == "4":
        while True:
            try:
                last["mood"] = int(input("New mood (1-5): "))
                if last["mood"] < 1 or last["mood"] > 5:
                    raise ValueError
                break
            except ValueError:
                print("Please enter a number between 1 and 5.")
    elif choice == "5":
        last["notes"] = input("New notes: ").strip()
    elif choice == "6":
        print("Cancelled.\n")
        return data
    else:
        print("Invalid choice.\n")
        return data
    
    save_data(data)
    print("Entry updated.\n")
    return data

def delete_last(data):
    if not data:
        print("\nNo entries to delete.\n")
        return data
    
    last = data[-1]
    print(f"\nDelete entry for {last['date']}? (y/n): ", end="")
    if input().strip().lower() == 'y':
        data.pop()
        save_data(data)
        print("Entry deleted.\n")
    else:
        print("Cancelled.\n")
    
    return data

def main():
    data = load_data()
    
    while True:
        print("\n=== Daily Health Logger ===")
        print("1. Log today")
        print("2. View week")
        print("3. Today's status")
        print("4. Edit last entry")
        print("5. Delete last entry")
        print("6. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == "1":
            data = log_entry(data)
        elif choice == "2":
            view_week(data)
        elif choice == "3":
            today_status(data)
        elif choice == "4":
            data = edit_last(data)
        elif choice == "5":
            data = delete_last(data)
        elif choice == "6":
            print("Goodbye.\n")
            break
        else:
            print("Invalid option. Please try again.\n")

if __name__ == "__main__":
    main()