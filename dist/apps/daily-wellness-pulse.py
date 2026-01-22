# Auto-generated via Perplexity on 2026-01-22T06:53:09.600499Z
import json
import os
from datetime import datetime, timedelta
from statistics import mean

DATA_FILE = "wellness_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_today_key():
    return datetime.now().strftime("%Y-%m-%d")

def validate_input(prompt, min_val, max_val):
    while True:
        try:
            value = int(input(prompt))
            if min_val <= value <= max_val:
                return value
            print(f"Please enter a value between {min_val} and {max_val}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def log_entry(data):
    today = get_today_key()
    print("\n--- Log Daily Wellness Entry ---")
    mood = validate_input("Mood (1-10): ", 1, 10)
    energy = validate_input("Energy Level (1-10): ", 1, 10)
    water = validate_input("Water Cups (0-20): ", 0, 20)
    sleep = validate_input("Sleep Hours (0-24): ", 0, 24)
    
    data[today] = {
        "mood": mood,
        "energy": energy,
        "water": water,
        "sleep": sleep
    }
    save_data(data)
    print("✓ Entry logged successfully!")

def get_week_data(data):
    today = datetime.now()
    week_data = []
    for i in range(7):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        if date in data:
            week_data.append(data[date])
    return week_data

def calculate_streak(data):
    today = datetime.now()
    streak = 0
    for i in range(365):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        if date in data:
            streak += 1
        else:
            break
    return streak

def calculate_wellness_score(mood_avg, energy_avg, water_total, sleep_avg):
    mood_score = (mood_avg / 10) * 25
    energy_score = (energy_avg / 10) * 25
    water_score = min((water_total / 56) * 25, 25)
    sleep_score = min((sleep_avg / 8) * 25, 25)
    return int(mood_score + energy_score + water_score + sleep_score)

def view_summary(data):
    week_data = get_week_data(data)
    if not week_data:
        print("\n--- Weekly Summary ---")
        print("No data available for this week.")
        return
    
    moods = [entry["mood"] for entry in week_data]
    energies = [entry["energy"] for entry in week_data]
    waters = [entry["water"] for entry in week_data]
    sleeps = [entry["sleep"] for entry in week_data]
    
    avg_mood = round(mean(moods), 1)
    avg_energy = round(mean(energies), 1)
    total_water = sum(waters)
    avg_sleep = round(mean(sleeps), 1)
    streak = calculate_streak(data)
    wellness_score = calculate_wellness_score(avg_mood, avg_energy, total_water, avg_sleep)
    
    print("\n--- Weekly Summary ---")
    print(f"Days Logged: {len(week_data)}/7")
    print(f"Average Mood: {avg_mood}/10")
    print(f"Average Energy: {avg_energy}/10")
    print(f"Total Water: {total_water} cups")
    print(f"Average Sleep: {avg_sleep} hours")
    print(f"Current Streak: {streak} days")
    print(f"Wellness Score: {wellness_score}/100")
    
    return {
        "avg_mood": avg_mood,
        "avg_energy": avg_energy,
        "total_water": total_water,
        "avg_sleep": avg_sleep,
        "streak": streak,
        "wellness_score": wellness_score,
        "days_logged": len(week_data)
    }

def generate_summary(data):
    summary_data = view_summary(data)
    if not summary_data:
        return
    
    text = "\n=== DAILY WELLNESS PULSE - WEEKLY SUMMARY ===\n"
    text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    text += f"📊 WEEKLY STATS\n"
    text += f"Days Logged: {summary_data['days_logged']}/7\n"
    text += f"Mood Average: {summary_data['avg_mood']}/10\n"
    text += f"Energy Average: {summary_data['avg_energy']}/10\n"
    text += f"Water Intake: {summary_data['total_water']} cups\n"
    text += f"Sleep Average: {summary_data['avg_sleep']} hours\n\n"
    text += f"🔥 STREAKS & SCORES\n"
    text += f"Logging Streak: {summary_data['streak']} days\n"
    text += f"Wellness Score: {summary_data['wellness_score']}/100\n"
    text += f"\n{'='*40}\n"
    
    print("\n--- Shareable Summary ---")
    print(text)
    print("(Copy the text above to share)")

def view_entries(data):
    today = datetime.now()
    print("\n--- Recent Entries ---")
    found = False
    for i in range(7):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        if date in data:
            entry = data[date]
            print(f"{date}: Mood {entry['mood']}/10 | Energy {entry['energy']}/10 | Water {entry['water']}c | Sleep {entry['sleep']}h")
            found = True
    if not found:
        print("No entries found.")

def main():
    print("=== DAILY WELLNESS PULSE ===\n")
    data = load_data()
    
    while True:
        print("\n--- Main Menu ---")
        print("1. Log Today's Entry")
        print("2. View Weekly Summary")
        print("3. Generate Shareable Summary")
        print("4. View Recent Entries")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            log_entry(data)
        elif choice == "2":
            view_summary(data)
        elif choice == "3":
            generate_summary(data)
        elif choice == "4":
            view_entries(data)
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please select 1-5.")

if __name__ == "__main__":
    main()