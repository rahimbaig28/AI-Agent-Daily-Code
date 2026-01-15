# Auto-generated via Perplexity on 2026-01-15T14:41:23.030082Z
#!/usr/bin/env python3
"""
Study Session Tracker - Single-file CLI application
Tracks study sessions with full statistics, keyboard navigation, and data persistence.
"""

import json
import os
import sys
from datetime import datetime, timedelta, date
from pathlib import Path
import random
from typing import List, Dict, Any, Optional
import shutil

# Constants
DATA_FILE = Path.home() / ".study_tracker.json"
MOTIVATIONAL_MESSAGES = [
    "Great job! Consistency beats intensity every time.",
    "You're building habits that will last a lifetime!",
    "Every minute counts. Keep stacking those wins!",
    "Progress, not perfection. You're doing amazing!",
    "The compound effect of daily study is unstoppable.",
    "Knowledge compounds like interest. Keep investing!",
    "Small daily improvements create massive results.",
    "You're stronger than your excuses. Keep going!",
    "Discipline today, freedom tomorrow.",
    "One more session closer to mastery."
]

class StudyTracker:
    def __init__(self):
        self.data_file = DATA_FILE
        self.sessions: List[Dict[str, Any]] = []
        self.load_data()
    
    def load_data(self):
        """Load sessions from JSON file."""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.sessions = data.get('sessions', [])
        except (json.JSONDecodeError, IOError):
            self.sessions = []
    
    def save_data(self):
        """Save sessions to JSON file."""
        try:
            data = {'sessions': self.sessions}
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving data: {e}")
    
    def add_session(self, subject: str, duration: int, timestamp: Optional[str] = None):
        """Add a new study session."""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        session = {
            'subject': subject.strip(),
            'duration_minutes': duration,
            'timestamp': timestamp,
            'date': datetime.fromisoformat(timestamp).date().isoformat()
        }
        self.sessions.append(session)
        self.sessions.sort(key=lambda x: x['timestamp'], reverse=True)
        self.save_data()
    
    def get_total_hours(self) -> float:
        """Calculate total study hours."""
        total_minutes = sum(s['duration_minutes'] for s in self.sessions)
        return round(total_minutes / 60, 2)
    
    def get_sessions_per_subject(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics per subject."""
        stats = {}
        for session in self.sessions:
            subject = session['subject']
            if subject not in stats:
                stats[subject] = {'count': 0, 'total_minutes': 0}
            stats[subject]['count'] += 1
            stats[subject]['total_minutes'] += session['duration_minutes']
        return stats
    
    def get_longest_streak(self) -> int:
        """Calculate longest consecutive study days."""
        if not self.sessions:
            return 0
        
        dates = sorted(set(s['date'] for s in self.sessions))
        if not dates:
            return 0
        
        max_streak = current_streak = 1
        for i in range(1, len(dates)):
            date1 = date.fromisoformat(dates[i-1])
            date2 = date.fromisoformat(dates[i])
            if (date2 - date1).days == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1
        
        return max_streak
    
    def get_daily_goal(self) -> float:
        """Calculate suggested daily goal based on historical average."""
        if not self.sessions:
            return 25.0  # Pomodoro default
        
        days = (datetime.now().date() - date.fromisoformat(self.sessions[0]['date'])).days + 1
        if days == 0:
            return 25.0
        
        avg_minutes = sum(s['duration_minutes'] for s in self.sessions) / days
        return round(max(15, min(180, avg_minutes)), 1)  # Clamp between 15-180 min
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent sessions."""
        return self.sessions[:limit]

def detect_dark_mode() -> bool:
    """Auto-detect dark terminal theme."""
    env_dark = os.environ.get('COLORF1_BACKGROUND', '')
    return 'dark' in env_dark.lower() or 'black' in env_dark.lower()

def print_banner(dark_mode: bool = True):
    """Print styled banner."""
    colors = {
        'dark': {'header': '\033[96m', 'success': '\033[92m', 'info': '\033[94m', 'reset': '\033[0m'},
        'light': {'header': '\033[95m', 'success': '\033[92m', 'info': '\033[34m', 'reset': '\033[0m'}
    }
    style = colors['dark' if dark_mode else 'light']
    
    print(f"{style['header']}{'='*60}{style['reset']}")
    print(f"{style['header']}      📚 STUDY SESSION TRACKER      {style['reset']}")
    print(f"{style['header']}{'='*60}{style['reset']}")

def print_stats(tracker: StudyTracker, dark_mode: bool):
    """Display comprehensive statistics."""
    colors = {
        'dark': {'header': '\033[96m', 'success': '\033[92m', 'info': '\033[94m', 'reset': '\033[0m'},
        'light': {'header': '\033[95m', 'success': '\033[92m', 'info': '\033[34m', 'reset': '\033[0m'}
    }
    style = colors['dark' if dark_mode else 'light']
    
    total_hours = tracker.get_total_hours()
    daily_goal = tracker.get_daily_goal()
    streak = tracker.get_longest_streak()
    subject_stats = tracker.get_sessions_per_subject()
    
    print(f"\n{style['header']}📊 STATISTICS{style['reset']}")
    print(f"{style['info']}Total Study Time: {total_hours} hours{style['reset']}")
    print(f"{style['info']}Longest Streak: {streak} days{style['reset']}")
    print(f"{style['info']}Suggested Daily Goal: {daily_goal} minutes{style['reset']}")
    print(f"{style['info']}Total Sessions: {len(tracker.sessions)}{style['reset']}")
    
    if subject_stats:
        print(f"\n{style['header']}📚 BY SUBJECT{style['reset']}")
        for subject, data in sorted(subject_stats.items(), key=lambda x: x[1]['total_minutes'], reverse=True):
            hours = data['total_minutes'] / 60
            print(f"  {subject}: {data['count']} sessions, {hours:.1f} hours")

def get_input(prompt: str, validate=None, error_msg: str = "Invalid input.") -> str:
    """Get validated input with reset capability."""
    while True:
        try:
            print(f"\r{prompt}", end="", flush=True)
            result = input().strip()
            if validate and not validate(result):
                print(f"{error_msg} Try again.")
                continue
            return result
        except KeyboardInterrupt:
            print("\nCancelled.")
            return ""

def validate_duration(duration_str: str) -> bool:
    """Validate duration input."""
    try:
        duration = int(duration_str)
        return 1 <= duration <= 1440  # 1 min to 24 hours
    except ValueError:
        return False

def validate_subject(subject: str) -> bool:
    """Validate subject name."""
    return 1 <= len(subject) <= 50 and subject.isprintable()

def input_session(tracker: StudyTracker) -> bool:
    """Interactive session input."""
    print("\n📝 NEW STUDY SESSION")
    print("Press R to reset, Q to cancel")
    
    subject = get_input("Subject: ", validate_subject, "Subject must be 1-50 chars.")
    if subject.upper() in ['Q', 'R']:
        return False
    
    duration = get_input("Duration (minutes) [1-1440]: ", validate_duration,
                        "Duration must be 1-1440 minutes.")
    if duration.upper() in ['Q', 'R']:
        return False
    
    tracker.add_session(subject, int(duration))
    print(f"\n✅ Session added: {subject} - {duration} minutes")
    print(random.choice(MOTIVATIONAL_MESSAGES))
    input("\nPress Enter to continue...")
    return True

def review_history(tracker: StudyTracker):
    """Display session history."""
    sessions = tracker.get_recent_sessions(20)
    if not sessions:
        print("\n📭 No sessions yet.")
        input("\nPress Enter to continue...")
        return
    
    print("\n📋 RECENT SESSIONS (newest first)")
    print("-" * 70)
    for i, session in enumerate(sessions, 1):
        dt = datetime.fromisoformat(session['timestamp'])
        date_str = dt.strftime("%Y-%m-%d %H:%M")
        print(f"{i:2d}. {session['subject']:<20} {session['duration_minutes']:>3}min  {date_str}")
    
    input("\nPress Enter to continue...")

def export_text(tracker: StudyTracker):
    """Export formatted text report."""
    filename = f"study_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    
    with open(filename, 'w') as f:
        f.write("STUDY SESSION REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        total_hours = tracker.get_total_hours()
        streak = tracker.get_longest_streak()
        daily_goal = tracker.get_daily_goal()
        
        f.write(f"TOTAL STUDY TIME: {total_hours} hours\n")
        f.write(f"LONGEST STREAK: {streak} days\n")
        f.write(f"SUGGESTED DAILY GOAL: {daily_goal} minutes\n")
        f.write(f"TOTAL SESSIONS: {len(tracker.sessions)}\n\n")
        
        subject_stats = tracker.get_sessions_per_subject()
        if subject_stats:
            f.write("BY SUBJECT:\n")
            f.write("-" * 30 + "\n")
            for subject, data in sorted(subject_stats.items(), key=lambda x: x[1]['total_minutes'], reverse=True):
                hours = data['total_minutes'] / 60
                f.write(f"{subject}: {data['count']} sessions, {hours:.1f} hours\n")
            f.write("\n")
        
        f.write("RECENT SESSIONS:\n")
        f.write("-" * 50 + "\n")
        for session in tracker.get_recent_sessions(50):
            dt = datetime.fromisoformat(session['timestamp'])
            f.write(f"{session['date']} {dt.strftime('%H:%M')} | {session['subject']:<20} | {session['duration_minutes']:>3}min\n")
    
    print(f"\n💾 Report exported to: {filename}")
    input("\nPress Enter to continue...")

def clear_data(tracker: StudyTracker) -> bool:
    """Clear all data with confirmation."""
    print("\n⚠️  CLEAR ALL DATA")
    print("This action cannot be undone!")
    confirm = get_input("Type 'DELETE' to confirm: ").upper()
    if confirm == 'DELETE':
        tracker.sessions.clear()
        tracker.save_data()
        print("\n✅ All data cleared.")
        return True
    else:
        print("\n❌ Cancelled.")
    input("\nPress Enter to continue...")
    return False

def keyboard_menu(options: List[str], title: str, dark_mode: bool = True) -> int:
    """Keyboard-navigable menu with arrow keys."""
    colors = {
        'dark': {'select': '\033[92m', 'normal': '\033[97m', 'reset': '\033[0m'},
        'light': {'select': '\033[92m', 'normal': '\033[37m', 'reset': '\033[0m'}
    }
    style = colors['dark' if dark_mode else 'light']
    
    selected = 0
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print_banner(dark_mode)
        print(f"\n{title}")
        print("-" * len(title))
        
        for i, option in enumerate(options):
            marker = "➤ " if i == selected else "  "
            color = style['select'] if i == selected else style['normal']
            print(f"{color}{marker}{option}{style['reset']}")
        
        print("\n↑↓ Arrow keys: Navigate | Enter: Select | Q: Quit")
        print("R: Return to main menu")
        
        try:
            import termios, tty
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            
            key = sys.stdin.read(1)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            
            if key == '\x1b':  # Escape sequence
                next_key = sys.stdin.read(2)
                if next_key == '[A':  # Up
                    selected = (selected - 1) % len(options)
                elif next_key == '[B':  # Down
                    selected = (selected + 1) % len(options)
            
            elif key.lower() == 'q':
                return -1
            elif key.lower() == 'r':
                return -2
            elif key == '\n' or key == '\r':  # Enter
                return selected
                
        except ImportError:
            # Fallback for Windows/non-termios systems
            choice = input("\nEnter number (1-6) or Q: ").strip().lower()
            if choice == 'q':
                return -1
            elif choice == 'r':
                return -2
            try:
                return int(choice) - 1
            except ValueError:
                continue

def main():
    """Main application loop."""
    dark_mode = detect_dark_mode()
    tracker = StudyTracker()
    
    MENU_OPTIONS = [
        "📝 Start New Session",
        "📊 View Statistics",
        "📋 Review History",
        "💾 Export to Text",
        "🗑️  Clear All Data",
        "❌ Quit"
    ]
    
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print_banner(dark_mode)
        
        total_hours = tracker.get_total_hours()
        daily_goal = tracker.get_daily_goal()
        streak = tracker.get_longest_streak()
        
        print(f"\n🎯 Daily Goal: {daily_goal}min | Total: {total_hours}h | Streak: {streak}d")
        print(random.choice(MOTIVATIONAL_MESSAGES))
        print()
        
        choice = keyboard_menu(MENU_OPTIONS, "MAIN MENU", dark_mode)
        
        if choice == 0:  # Start Session
            input_session(tracker)
        elif choice == 1:  # View Stats
            print_stats(tracker, dark_mode)
        elif choice == 2:  # Review History
            review_history(tracker)
        elif choice == 3:  # Export
            export_text(tracker)
        elif choice == 4:  # Clear Data
            clear_data(tracker)
        elif choice == 5 or choice == -1:  # Quit
            print("\n👋 Thanks for studying! Keep up the great work!")
            tracker.save_data()
            sys.exit(0)
        elif choice == -2:  # Return (handled by menu)
            continue

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)