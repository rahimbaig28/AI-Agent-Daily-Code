# Auto-generated via Perplexity on 2026-01-21T14:50:46.116054Z
#!/usr/bin/env python3
import json
import csv
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import sys

class StudySessionTracker:
    def __init__(self, data_file="study_sessions.json"):
        self.data_file = Path(data_file)
        self.sessions = []
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = 50
        self.load_sessions()

    def load_sessions(self):
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.sessions = data.get('sessions', [])
            except (json.JSONDecodeError, IOError):
                self.sessions = []
        else:
            self.sessions = []

    def save_sessions(self):
        with open(self.data_file, 'w') as f:
            json.dump({'sessions': self.sessions}, f, indent=2)

    def validate_session(self, subject, duration, date_str, notes=""):
        if not subject or not subject.strip():
            raise ValueError("Subject cannot be empty")
        if duration <= 0:
            raise ValueError("Duration must be positive")
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
        return True

    def add_session(self, subject, duration, date_str, notes=""):
        self.validate_session(subject, duration, date_str, notes)
        session = {
            'id': len(self.sessions) + 1,
            'subject': subject.strip(),
            'duration': duration,
            'date': date_str,
            'notes': notes.strip(),
            'created_at': datetime.now().isoformat()
        }
        self.undo_stack.append(('add', len(self.sessions), None))
        self.redo_stack.clear()
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        self.sessions.append(session)
        self.save_sessions()
        return session

    def delete_session(self, session_id):
        for i, session in enumerate(self.sessions):
            if session['id'] == session_id:
                self.undo_stack.append(('delete', i, session.copy()))
                self.redo_stack.clear()
                if len(self.undo_stack) > self.max_history:
                    self.undo_stack.pop(0)
                self.sessions.pop(i)
                self.save_sessions()
                return True
        return False

    def edit_session(self, session_id, subject=None, duration=None, date_str=None, notes=None):
        for i, session in enumerate(self.sessions):
            if session['id'] == session_id:
                old_session = session.copy()
                if subject:
                    session['subject'] = subject.strip()
                if duration is not None:
                    if duration <= 0:
                        raise ValueError("Duration must be positive")
                    session['duration'] = duration
                if date_str:
                    try:
                        datetime.strptime(date_str, "%Y-%m-%d")
                        session['date'] = date_str
                    except ValueError:
                        raise ValueError("Invalid date format. Use YYYY-MM-DD")
                if notes is not None:
                    session['notes'] = notes.strip()
                self.undo_stack.append(('edit', i, old_session))
                self.redo_stack.clear()
                if len(self.undo_stack) > self.max_history:
                    self.undo_stack.pop(0)
                self.save_sessions()
                return session
        return None

    def undo(self):
        if not self.undo_stack:
            return False
        action, index, data = self.undo_stack.pop()
        if action == 'add':
            self.redo_stack.append(('add', index, self.sessions[index].copy()))
            self.sessions.pop(index)
        elif action == 'delete':
            self.redo_stack.append(('delete', index, data))
            self.sessions.insert(index, data)
        elif action == 'edit':
            self.redo_stack.append(('edit', index, self.sessions[index].copy()))
            self.sessions[index] = data
        self.save_sessions()
        return True

    def redo(self):
        if not self.redo_stack:
            return False
        action, index, data = self.redo_stack.pop()
        if action == 'add':
            self.undo_stack.append(('add', index, data))
            self.sessions.insert(index, data)
        elif action == 'delete':
            self.undo_stack.append(('delete', index, self.sessions[index].copy()))
            self.sessions.pop(index)
        elif action == 'edit':
            self.undo_stack.append(('edit', index, self.sessions[index].copy()))
            self.sessions[index] = data
        self.save_sessions()
        return True

    def list_sessions(self, subject=None, start_date=None, end_date=None):
        filtered = self.sessions
        if subject:
            filtered = [s for s in filtered if subject.lower() in s['subject'].lower()]
        if start_date:
            filtered = [s for s in filtered if s['date'] >= start_date]
        if end_date:
            filtered = [s for s in filtered if s['date'] <= end_date]
        return sorted(filtered, key=lambda x: x['date'], reverse=True)

    def search_sessions(self, query, min_duration=0):
        results = []
        query_lower = query.lower()
        for session in self.sessions:
            if (query_lower in session['subject'].lower() or 
                query_lower in session['notes'].lower()) and session['duration'] >= min_duration:
                results.append(session)
        return sorted(results, key=lambda x: x['date'], reverse=True)

    def get_stats(self):
        if not self.sessions:
            return {}
        stats = {
            'total_hours': sum(s['duration'] for s in self.sessions) / 60,
            'total_sessions': len(self.sessions),
            'by_subject': defaultdict(lambda: {'hours': 0, 'sessions': 0}),
            'longest_streak': 0,
            'daily_totals': defaultdict(int),
            'weekly_totals': defaultdict(int),
            'monthly_totals': defaultdict(int),
            'avg_session_length': 0,
            'most_studied': ''
        }
        
        for session in self.sessions:
            subject = session['subject']
            duration = session['duration']
            date = session['date']
            stats['by_subject'][subject]['hours'] += duration / 60
            stats['by_subject'][subject]['sessions'] += 1
            stats['daily_totals'][date] += duration
            
            year_week = datetime.strptime(date, "%Y-%m-%d").isocalendar()
            week_key = f"{year_week[0]}-W{year_week[1]}"
            stats['weekly_totals'][week_key] += duration
            
            month_key = date[:7]
            stats['monthly_totals'][month_key] += duration
        
        if stats['total_sessions'] > 0:
            stats['avg_session_length'] = stats['total_hours'] * 60 / stats['total_sessions']
            stats['most_studied'] = max(stats['by_subject'].items(), 
                                       key=lambda x: x[1]['hours'])[0]
            
            sorted_dates = sorted(stats['daily_totals'].keys())
            current_streak = 1
            max_streak = 1
            for i in range(1, len(sorted_dates)):
                if (datetime.strptime(sorted_dates[i], "%Y-%m-%d") - 
                    datetime.strptime(sorted_dates[i-1], "%Y-%m-%d")).days == 1:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 1
            stats['longest_streak'] = max_streak
        
        return stats

    def generate_report(self, sort_by='date'):
        if not self.sessions:
            return "No sessions recorded yet."
        
        sorted_sessions = sorted(self.sessions, 
                                key=lambda x: (x['subject'], x['date']) if sort_by == 'subject' else x['date'],
                                reverse=True)
        
        report = "=" * 70 + "\n"
        report += "STUDY SESSION REPORT\n"
        report += "=" * 70 + "\n\n"
        
        stats = self.get_stats()
        report += f"Total Study Time: {stats['total_hours']:.2f} hours\n"
        report += f"Total Sessions: {stats['total_sessions']}\n"
        report += f"Average Session Length: {stats['avg_session_length']:.2f} minutes\n"
        report += f"Longest Streak: {stats['longest_streak']} days\n"
        report += f"Most Studied Subject: {stats['most_studied']}\n\n"
        
        report += "BY SUBJECT:\n"
        report += "-" * 70 + "\n"
        for subject in sorted(stats['by_subject'].keys()):
            data = stats['by_subject'][subject]
            report += f"  {subject}: {data['hours']:.2f} hours ({data['sessions']} sessions)\n"
        
        report += "\n" + "=" * 70 + "\n"
        report += "SESSION DETAILS (sorted by {})\n".format(sort_by)
        report += "=" * 70 + "\n\n"
        
        for session in sorted_sessions:
            report += f"ID: {session['id']} | Subject: {session['subject']}\n"
            report += f"Date: {session['date']} | Duration: {session['duration']} minutes\n"
            if session['notes']:
                report += f"Notes: {session['notes']}\n"
            report += "-" * 70 + "\n"
        
        return report

    def export_to_csv(self, filename="study_sessions.csv"):
        if not self.sessions:
            return False
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Subject', 'Date', 'Duration (minutes)', 'Notes'])
                for session in sorted(self.sessions, key=lambda x: x['date']):
                    writer.writerow([session['id'], session['subject'], session['date'], 
                                   session['duration'], session['notes']])
            return True
        except IOError:
            return False


def interactive_menu(tracker):
    while True:
        print("\n" + "=" * 50)
        print("STUDY SESSION TRACKER")
        print("=" * 50)
        print("1. Add session")
        print("2. List sessions")
        print("3. Search sessions")
        print("4. Edit session")
        print("5. Delete session")
        print("6. View statistics")
        print("7. Generate report")
        print("8. Export to CSV")
        print("9. Undo (Ctrl+Z)")
        print("10. Redo (Ctrl+Y)")
        print("11. Exit")
        print("=" * 50)
        
        choice = input("Enter your choice (1-11): ").strip()
        
        if choice == '1':
            subject = input("Subject: ").strip()
            try:
                duration = int(input("Duration (minutes): "))
                date_str = input("Date (YYYY-MM-DD) [today]: ").strip() or datetime.now().strftime("%Y-%m-%d")
                notes = input("Notes (optional): ").strip()
                session = tracker.add_session(subject, duration, date_str, notes)
                print(f"\nSession added: {session['subject']} - {session['duration']} min on {session['date']}")
            except ValueError as e:
                print(f"Error: {e}")
        
        elif choice == '2':
            subject_filter = input("Filter by subject (leave blank for all): ").strip()
            start_date = input("Start date (YYYY-MM-DD, leave blank): ").strip() or None
            end_date = input("End date (YYYY-MM-DD, leave blank): ").strip() or None
            sessions = tracker.list_sessions(subject_filter or None, start_date, end_date)
            if sessions:
                print("\n" + "-" * 70)
                for s in sessions:
                    print(f"ID: {s['id']} | {s['subject']} | {s['date']} | {s['duration']} min")
                    if s['notes']:
                        print(f"  Notes: {s['notes']}")
                print("-" * 70)
            else:
                print("No sessions found.")
        
        elif choice == '3':
            query = input("Search query: ").strip()
            try:
                min_duration = int(input("Minimum duration (minutes, 0 for any): ") or "0")
                results = tracker.search_sessions(query, min_duration)
                if results:
                    print("\n" + "-" * 70)
                    for s in results:
                        print(f"ID: {s['id']} | {s['subject']} | {s['date']} | {s['duration']} min")
                        if s['notes']:
                            print(f"  Notes: {s['notes']}")
                    print("-" * 70)
                else:
                    print("No sessions found.")
            except ValueError:
                print("Invalid duration.")
        
        elif choice == '4':
            try:
                session_id = int(input("Session ID to edit: "))
                subject = input("New subject (leave blank to keep): ").strip() or None
                duration_str = input("New duration in minutes (leave blank to keep): ").strip()
                duration = int(duration_str) if duration_str else None
                date_str = input("New date YYYY-MM-DD (leave blank to keep): ").strip() or None
                notes = input("New notes (leave blank to keep): ").strip() or None
                result = tracker.edit_session(session_id, subject, duration, date_str, notes)
                if result:
                    print(f"Session updated.")
                else:
                    print("Session not found.")
            except ValueError as e:
                print(f"Error: {e}")
        
        elif choice == '5':
            try:
                session_id = int(input("Session ID to delete: "))
                if tracker.delete_session(session_id):
                    print("Session deleted.")
                else:
                    print("Session not found.")
            except ValueError:
                print("Invalid ID.")
        
        elif choice == '6':
            stats = tracker.get_stats()
            if stats:
                print("\n" + "=" * 50)
                print("STATISTICS")
                print("=" * 50)
                print(f"Total Study Time: {stats['total_hours']:.2f} hours")
                print(f"Total Sessions: {stats['total_sessions']}")
                print(f"Average Session Length: {stats['avg_session_length']:.2f} minutes")
                print(f"Longest Streak: {stats['longest_streak']} days")
                print(f"Most Studied Subject: {stats['most_studied']}")
                print("\nDaily Totals (last 7 days):")
                for date in sorted(stats['daily_totals'].keys(), reverse=True)[:7]:
                    print(f"  {date}: {stats['daily_totals'][date]} minutes")
                print("\nBy Subject:")
                for subject in sorted(stats['by_subject'].keys()):
                    data = stats['by_subject'][subject]
                    print(f"  {subject}: {data['hours']:.2f} hours ({data['sessions']} sessions)")
                print("=" * 50)
            else:
                print("No data available.")
        
        elif choice == '7':
            sort_by = input("Sort by (date/subject) [date]: ").strip().lower() or "date"
            report = tracker.generate_report(sort_by)
            print("\n" + report)
            save = input("Save report to file? (y/n): ").strip().lower()
            if save == 'y':
                filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, 'w') as f:
                    f.write(report)
                print(f"Report saved to {filename}")
        
        elif choice == '8':
            filename = input("CSV filename [study_sessions.csv]: ").strip() or "study_sessions.csv"
            if tracker.export_to_csv(filename):
                print(f"Exported to {filename}")
            else:
                print("Export failed.")
        
        elif choice == '9':
            if tracker.undo():
                print("Undo successful.")
            else:
                print("Nothing to undo.")
        
        elif choice == '10':
            if tracker.redo():
                print("Redo successful.")
            else:
                print("Nothing to redo.")
        
        elif choice == '11':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")


def main():
    parser = argparse.ArgumentParser(description='Study Session Tracker')
    parser.add_argument('--add', nargs='+', help='Add session: --add SUBJECT DURATION [DATE] [NOTES]')
    parser.add_argument('--list', action='store_true', help='List all sessions')
    parser.add_argument('--subject', help='Filter by subject')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--search', help='Search sessions')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--report', action='store_true', help='Generate report')
    parser.add_argument('--export', help='Export to CSV')
    parser.add_argument('--delete', type=int, help='Delete session by ID')
    parser.add_argument('--data-file', default='study_sessions.json', help='Data file path')
    
    args = parser.parse_args()
    tracker = StudySessionTracker(args.data_file)
    
    if args.add:
        try:
            subject = args.add[0]
            duration = int(args.add[1])
            date_str = args.add[2] if len(args.add) > 2 else datetime.now().strftime("%Y-%m-%d")
            notes = ' '.join(args.add[3:]) if len(args.add) > 3 else ""
            session = tracker.add_session(subject, duration, date_str, notes)
            print(f"Session added: {session['subject']} - {session['duration']} min on {session['date']}")
        except (ValueError, IndexError) as e:
            print(f"Error: {e}")
    
    elif args.list:
        sessions = tracker.list_sessions(args.subject, args.start_date, args.end_date)
        if sessions:
            for s in sessions:
                print(f"ID: {s['id']} | {s['subject']} | {s['date']} | {s['duration']} min")
        else:
            print("No sessions found.")
    
    elif args.search:
        results = tracker.search_sessions(args.search)
        if results:
            for s in results:
                print(f"ID: {s['id']} | {s['subject']} | {s['date']} | {s['duration']} min")
        else:
            print("No sessions found.")
    
    elif args.stats:
        stats = tracker.get_stats()
        if stats:
            print(f"Total Study Time: {stats['total_hours']:.2f} hours")
            print(f"Total Sessions: {stats['total_sessions']}")
            print(f"Average Session Length: {stats['avg_session_length']:.2f} minutes")
            print(f"Longest Streak: {stats['longest_streak']} days")
            print(f"Most Studied Subject: {stats['most_studied']}")
        else:
            print("No data available.")
    
    elif args.report:
        print(tracker.generate_report())
    
    elif args.export:
        if tracker.export_to_csv(args.export):
            print(f"Exported to {args.export}")
        else:
            print("Export failed.")
    
    elif args.delete:
        if tracker.delete_session(args.delete):
            print("Session deleted.")
        else:
            print("Session not found.")
    
    else:
        interactive_menu(tracker)


if __name__ == '__main__':
    main()