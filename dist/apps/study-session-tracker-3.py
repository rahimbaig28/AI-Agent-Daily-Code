# Auto-generated via Perplexity on 2026-01-26T08:50:29.792255Z
#!/usr/bin/env python3
import json
import csv
import datetime
import os
from collections import defaultdict, Counter
from typing import List, Dict, Any

DATA_FILE = "study_sessions.json"
CSV_FILE = "study_sessions.csv"

def load_sessions() -> List[Dict[str, Any]]:
    """Load sessions from JSON file or return empty list."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading data: {e}. Starting with empty data.")
    return []

def save_sessions(sessions: List[Dict[str, Any]]):
    """Save sessions to JSON file."""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(sessions, f, indent=2)
    except IOError as e:
        print(f"Error saving data: {e}")

def log_new_session(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prompt user for new session data and add to sessions."""
    subject = input("Subject: ").strip()
    if not subject:
        print("Subject cannot be empty.")
        return sessions
    
    try:
        duration = int(input("Duration (minutes): "))
        if duration <= 0:
            print("Duration must be positive.")
            return sessions
    except ValueError:
        print("Invalid duration.")
        return sessions
    
    notes = input("Notes (optional): ").strip()
    
    session = {
        "subject": subject,
        "duration": duration,
        "date": datetime.datetime.now().isoformat(),
        "notes": notes
    }
    sessions.append(session)
    save_sessions(sessions)
    print("Session logged successfully!")
    return sessions

def view_all_sessions(sessions: List[Dict[str, Any]]):
    """Display all sessions in a formatted table."""
    if not sessions:
        print("No sessions found.")
        return
    
    print("\n{:<20} {:<20} {:<10} {}".format("Subject", "Date", "Duration", "Notes"))
    print("-" * 70)
    for session in sessions:
        date_str = datetime.datetime.fromisoformat(session["date"]).strftime("%Y-%m-%d %H:%M")
        notes = session["notes"][:30] + "..." if len(session["notes"]) > 30 else session["notes"]
        print("{:<20} {:<20} {:<10} {}".format(
            session["subject"], date_str, f"{session['duration']}m", notes
        ))

def filter_by_subject(sessions: List[Dict[str, Any]]):
    """Filter and display sessions by subject with total hours."""
    subject = input("Enter subject to filter: ").strip()
    if not subject:
        print("Subject cannot be empty.")
        return
    
    subject_sessions = [s for s in sessions if s["subject"].lower() == subject.lower()]
    if not subject_sessions:
        print(f"No sessions found for '{subject}'.")
        return
    
    total_minutes = sum(s["duration"] for s in subject_sessions)
    total_hours = total_minutes / 60
    
    print(f"\nSessions for '{subject}' (Total: {total_hours:.2f} hours):")
    print("{:<20} {:<20} {:<10} {}".format("Subject", "Date", "Duration", "Notes"))
    print("-" * 70)
    for session in subject_sessions:
        date_str = datetime.datetime.fromisoformat(session["date"]).strftime("%Y-%m-%d %H:%M")
        notes = session["notes"][:30] + "..." if len(session["notes"]) > 30 else session["notes"]
        print("{:<20} {:<20} {:<10} {}".format(
            session["subject"], date_str, f"{session['duration']}m", notes
        ))
    print(f"\nTotal for '{subject}': {total_minutes}m ({total_hours:.2f} hours)")

def generate_summary(sessions: List[Dict[str, Any]]):
    """Generate comprehensive study statistics."""
    if not sessions:
        print("No sessions to summarize.")
        return
    
    total_sessions = len(sessions)
    total_minutes = sum(s["duration"] for s in sessions)
    total_hours = total_minutes / 60
    avg_minutes = total_minutes / total_sessions
    
    # Most studied subject
    subject_totals = defaultdict(int)
    for s in sessions:
        subject_totals[s["subject"]] += s["duration"]
    most_studied = max(subject_totals.items(), key=lambda x: x[1])
    
    # Study streak (consecutive days with sessions)
    dates = sorted(set(datetime.datetime.fromisoformat(s["date"]).date() for s in sessions))
    streak = 1
    max_streak = 1
    for i in range(1, len(dates)):
        if dates[i] == dates[i-1] + datetime.timedelta(days=1):
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 1
    
    print("\n" + "="*50)
    print("STUDY SESSION SUMMARY")
    print("="*50)
    print(f"Total sessions: {total_sessions}")
    print(f"Total study time: {total_hours:.2f} hours ({total_minutes}m)")
    print(f"Average session: {avg_minutes:.1f} minutes")
    print(f"Most studied: {most_studied[0]} ({most_studied[1]}m)")
    print(f"Longest streak: {max_streak} consecutive days")
    print("="*50)

def export_to_csv(sessions: List[Dict[str, Any]]):
    """Export sessions to CSV file."""
    if not sessions:
        print("No sessions to export.")
        return
    
    try:
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["Subject", "Date", "Duration_Minutes", "Notes"])
            writer.writeheader()
            for session in sessions:
                writer.writerow({
                    "Subject": session["subject"],
                    "Date": session["date"],
                    "Duration_Minutes": session["duration"],
                    "Notes": session["notes"]
                })
        print(f"Exported {len(sessions)} sessions to {CSV_FILE}")
    except IOError as e:
        print(f"Error exporting CSV: {e}")

def import_from_json(sessions: List[Dict[str, Any]]):
    """Import sessions from external JSON file and merge."""
    filename = input("Enter JSON file to import: ").strip()
    if not os.path.exists(filename):
        print(f"File '{filename}' not found.")
        return sessions
    
    try:
        with open(filename, 'r') as f:
            new_sessions = json.load(f)
        
        # Create unique key for duplicate detection: date+subject+duration
        existing_keys = {(s["date"], s["subject"], s["duration"]) for s in sessions}
        imported_count = 0
        
        for new_session in new_sessions:
            key = (new_session["date"], new_session["subject"], new_session["duration"])
            if key not in existing_keys:
                sessions.append(new_session)
                imported_count += 1
        
        save_sessions(sessions)
        print(f"Imported {imported_count} new sessions.")
        return sessions
        
    except (json.JSONDecodeError, KeyError, IOError) as e:
        print(f"Error importing data: {e}")
        return sessions

def main():
    """Main program loop."""
    sessions = load_sessions()
    
    while True:
        print("\n" + "="*40)
        print("STUDY SESSION TRACKER")
        print("="*40)
        print("1. Log new session")
        print("2. View all sessions")
        print("3. Filter by subject")
        print("4. Generate study summary")
        print("5. Export to CSV")
        print("6. Import from JSON")
        print("7. Exit")
        print("-"*40)
        
        choice = input("Enter choice (1-7): ").strip()
        
        if choice == "1":
            sessions = log_new_session(sessions)
        elif choice == "2":
            view_all_sessions(sessions)
        elif choice == "3":
            filter_by_subject(sessions)
        elif choice == "4":
            generate_summary(sessions)
        elif choice == "5":
            export_to_csv(sessions)
        elif choice == "6":
            sessions = import_from_json(sessions)
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-7.")

if __name__ == "__main__":
    main()