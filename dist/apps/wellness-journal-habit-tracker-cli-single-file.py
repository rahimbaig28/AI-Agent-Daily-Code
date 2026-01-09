# Auto-generated via Perplexity on 2026-01-09T04:40:06.559782Z
#!/usr/bin/env python3
import argparse
import json
import os
import sys
import textwrap
from copy import deepcopy
from datetime import date, datetime, timedelta
from pathlib import Path

APP_VERSION = 1
UNDO_LIMIT = 20
DEFAULT_FILE = "wellness_journal.json"
BACKUP_PREFIX = "wellness_journal_backup_"
WEEKLY_EXPORT_PREFIX = "weekly_summary_"

# --------------- Utilities ---------------


def parse_args():
    parser = argparse.ArgumentParser(description="Wellness Journal & Habit Tracker")
    parser.add_argument("--file", type=str, default=DEFAULT_FILE, help="Path to data file")
    parser.add_argument("--today", type=str, help="Override today's date (YYYY-MM-DD)")
    return parser.parse_args()


def iso_today(override=None):
    if override:
        try:
            return datetime.strptime(override, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid --today date; using system date.")
    return date.today()


def atomic_write(path: Path, data: str):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(data)
    tmp.replace(path)


def input_line(prompt):
    try:
        return input(prompt)
    except EOFError:
        return "q"
    except KeyboardInterrupt:
        print()
        raise


def input_yes_no(prompt):
    while True:
        ans = input_line(prompt + " [y/n]: ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'.")


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def wait_for_enter():
    input_line("Press Enter to continue...")


def ensure_int(value, min_v=None, max_v=None):
    try:
        iv = int(value)
    except ValueError:
        return None
    if min_v is not None and iv < min_v:
        return None
    if max_v is not None and iv > max_v:
        return None
    return iv


def ensure_float(value, min_v=None, max_v=None):
    try:
        fv = float(value)
    except ValueError:
        return None
    if min_v is not None and fv < min_v:
        return None
    if max_v is not None and fv > max_v:
        return None
    return fv


def wrap_text(text, width=76):
    return "\n".join(textwrap.wrap(text, width)) if text else ""


def format_date(d: date):
    return d.strftime("%Y-%m-%d")


def parse_date(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def safe_get_terminal_width(default=80):
    try:
        import shutil

        return shutil.get_terminal_size((default, 24)).columns
    except Exception:
        return default


# --------------- Data handling ---------------


def default_settings():
    return {
        "daily_goals": {
            "movement_minutes": 30,
            "water_glasses": 8,
            "mindfulness_minutes": 10,
        },
        "first_run_completed": False,
        "brief_tips_enabled": True,
        "high_contrast": False,
    }


def default_entry(iso_d):
    return {
        "date": iso_d,
        "mood": None,
        "sleep_hours": None,
        "movement_minutes": None,
        "water_glasses": None,
        "mindfulness_minutes": None,
        "nutrition_quality": None,
        "tags": [],
        "notes": "",
    }


def load_data(path: Path):
    if not path.exists():
        return {
            "version": APP_VERSION,
            "entries": {},
            "settings": default_settings(),
        }
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading data file '{path}': {e}")
        print("1) Create new empty data file")
        print("2) Exit (you can fix the file manually)")
        choice = input_line("Choose [1-2]: ").strip()
        if choice == "1":
            return {
                "version": APP_VERSION,
                "entries": {},
                "settings": default_settings(),
            }
        else:
            sys.exit(1)
    if not isinstance(data, dict):
        data = {}
    data.setdefault("version", APP_VERSION)
    data.setdefault("entries", {})
    data.setdefault("settings", default_settings())
    # basic validation
    if not isinstance(data["entries"], dict):
        data["entries"] = {}
    if not isinstance(data["settings"], dict):
        data["settings"] = default_settings()
    # ensure daily_goals
    s = data["settings"]
    s.setdefault("daily_goals", default_settings()["daily_goals"])
    s.setdefault("first_run_completed", False)
    s.setdefault("brief_tips_enabled", True)
    s.setdefault("high_contrast", False)
    return data


def save_data(data, path: Path):
    # strip trailing whitespace from notes
    for e in data.get("entries", {}).values():
        if isinstance(e.get("notes"), str):
            e["notes"] = e["notes"].rstrip()
    text = json.dumps(data, indent=2, sort_keys=True)
    try:
        atomic_write(path, text)
    except Exception as e:
        print(f"Error saving data: {e}")


def create_backup(path: Path):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{BACKUP_PREFIX}{ts}.json"
    backup_path = path.with_name(backup_name)
    try:
        with path.open("r", encoding="utf-8") as f_src, backup_path.open(
            "w", encoding="utf-8"
        ) as f_dst:
            f_dst.write(f_src.read())
        print(f"Backup created: {backup_name}")
    except Exception as e:
        print(f"Failed to create backup: {e}")


# --------------- Undo stack ---------------


class UndoStack:
    def __init__(self, limit=UNDO_LIMIT):
        self.stack = []
        self.limit = limit

    def push(self, description, entries_snapshot, settings_snapshot=None):
        item = {
            "description": description,
            "entries": deepcopy(entries_snapshot),
            "settings": deepcopy(settings_snapshot) if settings_snapshot else None,
        }
        self.stack.append(item)
        if len(self.stack) > self.limit:
            self.stack.pop(0)

    def pop(self):
        if not self.stack:
            return None
        return self.stack.pop()

    def empty(self):
        return not self.stack


# --------------- Rendering helpers ---------------


def hc_line(settings, char="-", width=60):
    if settings.get("high_contrast"):
        return char * width
    return ""


def mood_label(mood):
    labels = {
        1: "Very low",
        2: "Low",
        3: "Neutral",
        4: "Good",
        5: "Excellent",
    }
    return labels.get(mood, "")


def render_entry(entry, settings, width=None):
    if width is None:
        width = safe_get_terminal_width()
    lines = []
    lines.append(hc_line(settings, "=", width))
    lines.append(f"Date: {entry['date']}")
    if entry.get("mood") is not None:
        lines.append(f"Mood: {entry['mood']} ({mood_label(entry['mood'])})")
    else:
        lines.append("Mood: –")
    lines.append(f"Sleep hours: {entry.get('sleep_hours') if entry.get('sleep_hours') is not None else '–'}")
    lines.append(f"Movement minutes: {entry.get('movement_minutes') if entry.get('movement_minutes') is not None else '–'}")
    lines.append(f"Water glasses: {entry.get('water_glasses') if entry.get('water_glasses') is not None else '–'}")
    lines.append(f"Mindfulness minutes: {entry.get('mindfulness_minutes') if entry.get('mindfulness_minutes') is not None else '–'}")
    lines.append(f"Nutrition quality: {entry.get('nutrition_quality') if entry.get('nutrition_quality') is not None else '–'}")
    tags = entry.get("tags") or []
    lines.append("Tags: " + (", ".join(tags) if tags else "–"))
    lines.append("")
    lines.append("Notes:")
    notes = entry.get("notes") or ""
    if notes.strip():
        lines.append(wrap_text(notes, width=width))
    else:
        lines.append("  (none)")
    lines.append(hc_line(settings, "=", width))
    return "\n".join(lines)


# --------------- Journal & input flows ---------------


def prompt_field_int(prompt, current, min_v=None, max_v=None, allow_none=True):
    while True:
        cur_text = f"[{current}]" if current is not None else "[blank]"
        s = input_line(f"{prompt} {cur_text}: ").strip()
        if s.lower() == "q":
            return "q"
        if not s:
            return current
        value = ensure_int(s, min_v, max_v)
        if value is None:
            print("Invalid number.")
            continue
        return value


def prompt_field_float(prompt, current, min_v=None, max_v=None):
    while True:
        cur_text = f"[{current}]" if current is not None else "[blank]"
        s = input_line(f"{prompt} {cur_text}: ").strip()
        if s.lower() == "q":
            return "q"
        if not s:
            return current
        value = ensure_float(s, min_v, max_v)
        if value is None:
            print("Invalid number.")
            continue
        return value


def prompt_tags(current):
    cur_text = ", ".join(current) if current else ""
    s = input_line(f"Tags (comma separated) [{cur_text}]: ")
    if s.strip().lower() == "q":
        return "q"
    if not s.strip():
        return current
    tags = [t.strip() for t in s.split(",") if t.strip()]
    return tags


def prompt_notes(current):
    print("Notes (end with a single '.' on a line, or 'q' to cancel):")
    if current:
        print("[Current notes will be replaced if you enter new notes. Leave empty to keep.]")
    lines = []
    while True:
        line = input_line("")
        if line.strip().lower() == "q" and not lines:
            return "q"
        if line.strip() == ".":
            break
        lines.append(line)
    if not lines:
        return current
    return "\n".join(lines)


def edit_entry_for_date(data, undo_stack, iso_d, settings, today_str):
    entries = data["entries"]
    old_entry = deepcopy(entries.get(iso_d, default_entry(iso_d)))
    entry = deepcopy(old_entry)

    print(hc_line(settings, "=", 60))
    print(f"Logging entry for {iso_d}")
    print("Press Enter to keep current value, or 'q' to cancel and go back.")
    print(hc_line(settings, "-", 60))

    v = prompt_field_int("Mood (1–5, 1=very low, 5=excellent)", entry.get("mood"), 1, 5)
    if v == "q":
        print("Cancelled.")
        return
    entry["mood"] = v

    v = prompt_field_float("Sleep hours (0–24)", entry.get("sleep_hours"), 0, 24)
    if v == "q":
        print("Cancelled.")
        return
    entry["sleep_hours"] = v

    v = prompt_field_int("Movement minutes (0+)", entry.get("movement_minutes"), 0, None)
    if v == "q":
        print("Cancelled.")
        return
    entry["movement_minutes"] = v

    v = prompt_field_int("Water glasses (0+)", entry.get("water_glasses"), 0, None)
    if v == "q":
        print("Cancelled.")
        return
    entry["water_glasses"] = v

    v = prompt_field_int("Mindfulness minutes (0+)", entry.get("mindfulness_minutes"), 0, None)
    if v == "q":
        print("Cancelled.")
        return
    entry["mindfulness_minutes"] = v

    v = prompt_field_int("Nutrition quality (1–5)", entry.get("nutrition_quality"), 1, 5)
    if v == "q":
        print("Cancelled.")
        return
    entry["nutrition_quality"] = v

    v = prompt_tags(entry.get("tags") or [])
    if v == "q":
        print("Cancelled.")
        return
    entry["tags"] = v

    v = prompt_notes(entry.get("notes") or "")
    if v == "q":
        print("Cancelled.")
        return
    entry["notes"] = v.rstrip()

    clear_screen()
    print("Review today's entry:")
    print(render_entry(entry, settings))
    if not input_yes_no("Save this entry?"):
        print("Changes discarded.")
        return

    undo_stack.push(f"Edited entry {iso_d}", entries)
    entries[iso_d] = entry
    print("Entry saved.")
    if data["settings"].get("brief_tips_enabled") and iso_d == today_str:
        show_brief_tips(entry, data["settings"]["daily_goals"])


def show_brief_tips(entry, goals):
    print()
    print("Tips (informational only):")
    if entry.get("movement_minutes") in (None, 0):
        print("- A short walk can help boost energy and mood.")
    elif entry.get("movement_minutes", 0) < goals.get("movement_minutes", 30):
        print("- You are moving today; a little more time could help reach your movement goal.")
    if entry.get("water_glasses") in (None, 0):
        print("- Drinking water regularly can support focus and well-being.")
    elif entry.get("water_glasses", 0) < goals.get("water_glasses", 8):
        print("- Consider a glass of water to move closer to your hydration goal.")
    if entry.get("mindfulness_minutes") in (None, 0):
        print("- A few minutes of quiet breathing can support relaxation.")
    print()


def handle_log_today(data, undo_stack, today_str, settings):
    clear_screen()
    edit_entry_for_date(data, undo_stack, today_str, settings, today_str)
    print()
    print("[q] Back to main menu")
    wait_for_enter()


def handle_view_date(data, undo_stack, today, settings):
    entries = data["entries"]
    while True:
        clear_screen()
        print("View a date's entry")
        print("Enter date as YYYY-MM-DD, or 't' for today, 'y' for yesterday, 'q' to cancel.")
        ans = input_line("Date: ").strip().lower()
        if ans == "q":
            return
        if ans == "t":
            d = today
        elif ans == "y":
            d = today - timedelta(days=1)
        else:
            d = parse_date(ans)
            if not d:
                print("Invalid date format.")
                wait_for_enter()
                continue
        iso_d = format_date(d)
        clear_screen()
        if iso_d in entries:
            print(render_entry(entries[iso_d], settings))
            print("[q] Back")
            wait_for_enter()
            return
        else:
            print(f"No entry for {iso_d}.")
            print("[1] Create it now")
            print("[q] Back")
            choice = input_line("Choose: ").strip().lower()
            if choice == "1":
                edit_entry_for_date(data, undo_stack, iso_d, settings, format_date(today))
                wait_for_enter()
                return
            elif choice == "q":
                return


# --------------- Weekly summary ---------------


def compute_week_range(any_date):
    # Monday as first day
    start = any_date - timedelta(days=any_date.weekday())
    end = start + timedelta(days=6)
    return start, end


def week_id(d):
    return d.isocalendar(), d.isocalendar()[1]


def goals_met_for_entry(entry, goals):
    if not entry:
        return False
    if entry.get("movement_minutes") is None:
        return False
    if entry.get("water_glasses") is None:
        return False
    if entry.get("mindfulness_minutes") is None:
        return False
    if entry["movement_minutes"] < goals.get("movement_minutes", 30):
        return False
    if entry["water_glasses"] < goals.get("water_glasses", 8):
        return False
    if entry["mindfulness_minutes"] < goals.get("mindfulness_minutes", 10):
        return False
    return True


def render_week_summary(data, week_start, week_end, settings):
    entries = data["entries"]
    goals = data["settings"]["daily_goals"]
    width = safe_get_terminal_width()
    lines = []
    lines.append(hc_line(settings, "=", width))
    lines.append(
        f"Week {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"
    )
    lines.append(hc_line(settings, "-", width))
    header = (
        "Day  Date   Mood Sleep  Move   M✓  Water  W✓  Mind   M✓".ljust(width)
    )
    lines.append(header)
    lines.append(hc_line(settings, "-", width))

    days_all_goals = 0
    moods = []
    sleeps = []

    d = week_start
    while d <= week_end:
        iso_d = format_date(d)
        e = entries.get(iso_d)
        mood = e.get("mood") if e else None
        sleep = e.get("sleep_hours") if e else None
        move = e.get("movement_minutes") if e else None
        water = e.get("water_glasses") if e else None
        mind = e.get("mindfulness_minutes") if e else None
        gm = goals_met_for_entry(e, goals)
        if mood is not None:
            moods.append(mood)
        if sleep is not None:
            sleeps.append(sleep)
        if gm:
            days_all_goals += 1
        day_name = d.strftime("%a")
        day_num = d.strftime("%d")
        mood_s = str(mood) if mood is not None else "–"
        sleep_s = f"{sleep:.1f}" if sleep is not None else "–"
        move_s = str(move) if move is not None else "–"
        water_s = str(water) if water is not None else "–"
        mind_s = str(mind) if mind is not None else "–"
        mv = "✓" if (move is not None and move >= goals.get("movement_minutes", 30)) else " "
        wv = "✓" if (water is not None and water >= goals.get("water_glasses", 8)) else " "
        mm = "✓" if (mind is not None and mind >= goals.get("mindfulness_minutes", 10)) else " "
        line = f"{day_name:<3} {day_num:<2}  {mood_s:^4} {sleep_s:^6} {move_s:^6} {mv:^3} {water_s:^5} {wv:^3} {mind_s:^6} {mm:^3}"
        lines.append(line.ljust(width))
        d += timedelta(days=1)

    avg_mood = sum(moods) / len(moods) if moods else None
    avg_sleep = sum(sleeps) / len(sleeps) if sleeps else None
    lines.append(hc_line(settings, "-", width))
    lines.append(f"Days all goals met: {days_all_goals}")
    if avg_mood is not None:
        lines.append(f"Average mood: {avg_mood:.2f}")
    else:
        lines.append("Average mood: –")
    if avg_sleep is not None:
        lines.append(f"Average sleep: {avg_sleep:.2f} hours")
    else:
        lines.append("Average sleep: –")
    lines.append(hc_line(settings, "=", width))
    return "\n".join(lines)


def export_week_summary(data, week_start, week_end, settings):
    year, wk = week_id(week_start)
    filename = f"{WEEKLY_EXPORT_PREFIX}{year}-{wk:02d}.txt"
    path = Path(filename)
    text = render_week_summary(data, week_start, week_end, settings)
    try:
        atomic_write(path, text)
        print(f"Exported to {filename}")
    except Exception as e:
        print(f"Failed to export: {e}")


def handle_weekly_summary(data, today, settings):
    week_start, week_end = compute_week_range(today)
    while True:
        clear_screen()
        print(render_week_summary(data, week_start, week_end, settings))
        print("[p] Previous week  [n] Next week  [d] Choose week by date  [x] Export  [q] Back")
        choice = input_line("Choose: ").strip().lower()
        if choice == "q":
            return
        elif choice == "p":
            week_start -= timedelta(days=7)
            week_end -= timedelta(days=7)
        elif choice == "n":
            next_start = week_start + timedelta(days=7)
            if next_start > today:
                print("Cannot view future weeks.")
                wait_for_enter()
            else:
                week_start = next_start
                week_end = week_start + timedelta(days=6)
        elif choice == "d":
            s = input_line("Enter any date in desired week (YYYY-MM-DD, 'q' to cancel): ").strip()
            if s.lower() == "q":
                continue
            d = parse_date(s)
            if not d:
                print("Invalid date.")
                wait_for_enter()
                continue
            week_start, week_end = compute_week_range(d)
        elif choice == "x":
            export_week_summary(data, week_start, week_end, settings)
            wait_for_enter()


# --------------- Streaks & stats ---------------


def compute_streaks(data):
    entries = data["entries"]
    goals = data["settings"]["daily_goals"]
    if not entries:
        return {
            "current_journal_streak": 0,
            "longest_journal_streak": 0,
            "current_goal_streak": 0,
            "longest_goal_streak": 0,
        }
    dates = sorted(parse_date(d) for d in entries.keys() if parse_date(d))
    if not dates:
        return {
            "current_journal_streak": 0,
            "longest_journal_streak": 0,
            "current_goal_streak": 0,
            "longest_goal_streak": 0,
        }
    # longest streaks backward and forward
    all_dates = sorted(dates)
    # treat absence of entry as broken streak
    # compute longest journal streak
    longest_j = 0
    longest_g = 0
    current_j = 0
    current_g = 0
    prev = None
    for d in all_dates:
        iso_d = format_date(d)
        has_entry = entries.get(iso_d) is not None
        goals_met = goals_met_for_entry(entries.get(iso_d), goals)
        if prev is None or d == prev + timedelta(days=1):
            # continuing sequence
            if has_entry:
                current_j += 1
            else:
                current_j = 0
            if goals_met:
                current_g += 1
            else:
                current_g = 0
        else:
            # gap
            current_j = 1 if has_entry else 0
            current_g = 1 if goals_met else 0
        longest_j = max(longest_j, current_j)
        longest_g = max(longest_g, current_g)
        prev = d

    # current streak from most recent date going backward
    today = max(all_dates)
    cj = 0
    cg = 0
    d = today
    while True:
        iso_d = format_date(d)
        e = entries.get(iso_d)
        if e:
            cj += 1
            if goals_met_for_entry(e, goals):
                cg += 1
            else:
                break
        else:
            break
        d -= timedelta(days=1)
    return {
        "current_journal_streak": cj,
        "longest_journal_streak": longest_j,
        "current_goal_streak": cg,
        "longest_goal_streak": longest_g,
    }


def compute_averages(data, days):
    entries = data["entries"]
    if not entries:
        return {}
    today = max(parse_date(d) for d in entries if parse_date(d))
    start = today - timedelta(days=days - 1)
    mood_vals = []
    sleep_vals = []
    move_vals = []
    water_vals = []
    for i in range(days):
        d = start + timedelta(days=i)
        iso_d = format_date(d)
        e = entries.get(iso_d)
        if not e:
            continue
        if e.get("mood") is not None:
            mood_vals.append(e["mood"])
        if e.get("sleep_hours") is not None:
            sleep_vals.append(e["sleep_hours"])
        if e.get("movement_minutes") is not None:
            move_vals.append(e["movement_minutes"])
        if e.get("water_glasses") is not None:
            water_vals.append(e["water_glasses"])
    def avg(vals):
        return sum(vals) / len(vals) if vals else None
    return {
        "mood": avg(mood_vals),
        "sleep_hours": avg(sleep_vals),
        "movement_minutes": avg(move_vals),
        "water_glasses": avg(water_vals),
    }


def handle_streaks_stats(data, settings):
    clear_screen()
    streaks = compute_streaks(data)
    print(hc_line(settings, "=", 60))
    print("Streaks & Stats")
    print(hc_line(settings, "-", 60))
    print(f"Current journal streak: {streaks['current_journal_streak']} days")
    print(f"Longest journal streak: {streaks['longest_journal_streak']} days")
    print(f"Current goal streak:   {streaks['current_goal_streak']} days")
    print(f"Longest goal streak:   {streaks['longest_goal_streak']} days")
    print(hc_line(settings, "-", 60))
    for span in (7, 30):
        avgs = compute_averages(data, span)
        print(f"{span}-day averages:")
        print(f"  Mood:              {avgs.get('mood'):.2f}" if avgs.get("mood") is not None else "  Mood:              –")
        print(f"  Sleep hours:       {avgs.get('sleep_hours'):.2f}" if avgs.get("sleep_hours") is not None else "  Sleep hours:       –")
        print(f"  Movement minutes:  {avgs.get('movement_minutes'):.2f}" if avgs.get("movement_minutes") is not None else "  Movement minutes:  –")
        print(f"  Water glasses:     {avgs.get('water_glasses'):.2f}" if avgs.get("water_glasses") is not None else "  Water glasses:     –")
        print()
    print(hc_line(settings, "=", 60))
    print("[q] Back")
    wait_for_enter()


# --------------- Settings ---------------


def handle_settings(data, undo_stack, path):
    settings = data["settings"]
    while True:
        clear_screen()
        print(hc_line(settings, "=", 60))
        print("Settings")
        print(hc_line(settings, "-", 60))
        goals = settings["daily_goals"]
        print(f"[1] Edit daily goals (movement={goals['movement_minutes']} min, water={goals['water_glasses']}, mindfulness={goals['mindfulness_minutes']} min)")
        print(f"[2] Toggle brief tips display (currently {'ON' if settings.get('brief_tips_enabled') else 'OFF'})")
        print(f"[3] Toggle high-contrast mode (currently {'ON' if settings.get('high_contrast') else 'OFF'})")
        print("[4] Create backup now")
        print("[q] Back to main menu")
        choice = input_line("Choose: ").strip().lower()
        if choice == "q":
            return
        elif choice == "1":
            edit_daily_goals(data, undo_stack)
        elif choice == "2":
            settings["brief_tips_enabled"] = not settings.get("brief_tips_enabled")
        elif choice == "3":
            settings["high_contrast"] = not settings.get("high_contrast")
        elif choice == "4":
            create_backup(path)
            wait_for_enter()


def edit_daily_goals(data, undo_stack):
    settings = data["settings"]
    goals = settings["daily_goals"]
    old_entries = data["entries"]
    old_settings = deepcopy(settings)
    print("Edit daily goals (press Enter to keep current, 'q' to cancel)")
    mv = prompt_field_int(
        "Movement minutes goal", goals.get("movement_minutes"), 0, None
    )
    if mv == "q":
        print("Cancelled.")
        wait_for_enter()
        return
    wv = prompt_field_int(
        "Water glasses goal", goals.get("water_glasses"), 0, None
    )
    if wv == "q":
        print("Cancelled.")
        wait_for_enter()
        return
    mm = prompt_field_int(
        "Mindfulness minutes goal", goals.get("mindfulness_minutes"), 0, None
    )
    if mm == "q":
        print("Cancelled.")
        wait_for_enter()
        return
    new_goals = {
        "movement_minutes": mv,
        "water_glasses": wv,
        "mindfulness_minutes": mm,
    }
    print("New goals:")
    print(new_goals)
    if not input_yes_no("Save these goals?"):
        print("Changes discarded.")
        wait_for_enter()
        return
    undo_stack.push("Changed daily goals", old_entries, old_settings)
    settings["daily_goals"] = new_goals
    print("Goals updated.")
    wait_for_enter()


# --------------- Undo handler ---------------


def handle_undo(data, undo_stack, settings):
    if undo_stack.empty():
        print("Nothing to undo.")
        wait_for_enter()
        return
    last = undo_stack.pop()
    data["entries"] = last["entries"]
    if last["settings"] is not None:
        data["settings"] = last["settings"]
    print(f"Undone: {last['description']}")
    print("[q] Back")
    wait_for_enter()


# --------------- Main menu ---------------


def show_main_menu(settings):
    clear_screen()
    print(hc_line(settings, "=", 60))
    print("Wellness Journal & Habit Tracker")
    print(hc_line(settings, "-", 60))
    print("[1] Log / edit today's entry")
    print("[2] View a date's entry")
    print("[3] Weekly summary")
    print("[4] Streaks & stats")
    print("[5] Undo last change")
    print("[6] Settings")
    print(" Save & exit")
    print(hc_line(settings, "=", 60))


def main():
    args = parse_args()
    path = Path(args.file)
    today_date = iso_today(args.today)
    today_str = format_date(today_date)
    data = load_data(path)
    settings = data["settings"]
    undo_stack = UndoStack()

    modified = False

    try:
        while True:
            show_main_menu(settings)
            choice = input_line("Choose: ").strip().lower()
            if choice == "0" or choice == "q":
                save_data(data, path)
                print("Data saved. Goodbye.")
                break
            elif choice == "1":
                handle_log_today(data, undo_stack, today_str, settings)
                modified = True
            elif choice == "2":
                handle_view_date(data, undo_stack, today_date, settings)
                modified = True
            elif choice == "3":
                handle_weekly_summary(data, today_date, settings)
            elif choice == "4":
                handle_streaks_stats(data, settings)
            elif choice == "5":
                handle_undo(data, undo_stack, settings)
                modified = True
            elif choice == "6":
                handle_settings(data, undo_stack, path)
                modified = True
            else:
                print("Invalid choice.")
                wait_for_enter()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected.")
        if modified and input_yes_no("Save changes before exiting?"):
            save_data(data, path)
            print("Data saved.")
        print("Goodbye.")


if __name__ == "__main__":
    main()