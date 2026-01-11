# Auto-generated via Perplexity on 2026-01-11T01:48:38.281713Z
#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import sys
import textwrap
import tempfile
import shutil
from pathlib import Path

# Optional readline for REPL history
try:
    import readline  # type: ignore
except Exception:  # pragma: no cover
    readline = None

APP_FILENAME = ".study_sessions.json"


def get_data_path() -> Path:
    home = Path(os.path.expanduser("~"))
    return home / APP_FILENAME


def load_data() -> dict:
    path = get_data_path()
    if not path.exists():
        data = {
            "sessions": [],
            "config": {
                "time_format": "24h",
                "default_print_width": 80,
                "default_daily_goal_minutes": 300,
            },
        }
        save_data(data)
        return data
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        # backup
        backup = path.with_suffix(path.suffix + ".bak")
        try:
            shutil.copy2(path, backup)
        except Exception:
            pass
        print(f"Data file corrupted. Backup saved to {backup}. Starting fresh.", file=sys.stderr)
        data = {
            "sessions": [],
            "config": {
                "time_format": "24h",
                "default_print_width": 80,
                "default_daily_goal_minutes": 300,
            },
        }
        save_data(data)
        return data
    if "sessions" not in data or "config" not in data:
        data.setdefault("sessions", [])
        data.setdefault(
            "config",
            {
                "time_format": "24h",
                "default_print_width": 80,
                "default_daily_goal_minutes": 300,
            },
        )
    return data


def save_data(data: dict) -> None:
    path = get_data_path()
    tmp_fd, tmp_name = tempfile.mkstemp(prefix="study_", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        shutil.move(tmp_name, path)
    except Exception as e:
        print(f"Error writing data file: {e}", file=sys.stderr)
        try:
            os.unlink(tmp_name)
        except Exception:
            pass
        sys.exit(1)


def next_session_id(data: dict) -> int:
    sessions = data.get("sessions", [])
    if not sessions:
        return 1
    return max(s.get("id", 0) for s in sessions) + 1


def parse_date(s: str, allow_keywords: bool = False) -> dt.date:
    s = s.strip().lower()
    if allow_keywords:
        today = dt.date.today()
        if s in ("today", ""):
            return today
        if s == "yesterday":
            return today - dt.timedelta(days=1)
    try:
        return dt.date.fromisoformat(s)
    except Exception:
        raise ValueError("Invalid date format, expected YYYY-MM-DD")


def parse_time(s: str) -> dt.time:
    try:
        return dt.datetime.strptime(s.strip(), "%H:%M").time()
    except Exception:
        raise ValueError("Invalid time format, expected HH:MM (24h)")


def compute_duration_minutes(start: dt.time, end: dt.time) -> int:
    start_dt = dt.datetime.combine(dt.date.today(), start)
    end_dt = dt.datetime.combine(dt.date.today(), end)
    if end_dt <= start_dt:
        raise ValueError("End time must be after start time")
    return int((end_dt - start_dt).total_seconds() // 60)


def format_time(t: str, config: dict) -> str:
    # t is "HH:MM"
    if config.get("time_format", "24h") != "12h":
        return t
    try:
        tm = dt.datetime.strptime(t, "%H:%M")
        return tm.strftime("%I:%M%p").lstrip("0")
    except Exception:
        return t


def confirm(prompt: str, default: bool = True) -> bool:
    if default:
        suffix = " [Y/n]: "
    else:
        suffix = " [y/N]: "
    while True:
        ans = input(prompt + suffix).strip()
        if not ans:
            return default
        if ans.lower() in ("y", "yes"):
            return True
        if ans.lower() in ("n", "no"):
            return False
        print("Please answer y or n.")


def input_with_default(prompt: str, default: str) -> str:
    if default:
        full = f"{prompt} [{default}]: "
    else:
        full = f"{prompt}: "
    val = input(full)
    if not val.strip():
        return default
    return val.strip()


def parse_tags(s: str) -> list:
    if not s.strip():
        return []
    return [t.strip() for t in s.split(",") if t.strip()]


def get_session_by_id(data: dict, sid: int):
    for s in data.get("sessions", []):
        if s.get("id") == sid:
            return s
    return None


def list_sessions_filtered(
    data: dict,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    subject: str | None = None,
    tag: str | None = None,
):
    sessions = data.get("sessions", [])
    result = []
    for s in sessions:
        s_date = dt.date.fromisoformat(s["date"])
        if date_from and s_date < date_from:
            continue
        if date_to and s_date > date_to:
            continue
        if subject and s["subject"].lower() != subject.lower():
            continue
        if tag:
            tags = [t.lower() for t in s.get("tags", [])]
            if tag.lower() not in tags:
                continue
        result.append(s)
    result.sort(key=lambda x: (x["date"], x["start_time"]))
    return result


def print_sessions_table(sessions: list, config: dict) -> None:
    if not sessions:
        print("No sessions.")
        return
    headers = ["ID", "Date", "Time", "Dur", "Subject", "F", "Tags"]
    col_widths = [4, 10, 13, 6, 20, 3, 20]

    def trunc(s, w):
        return s if len(s) <= w else s[: w - 1] + "…"

    line = []
    for h, w in zip(headers, col_widths):
        line.append(trunc(h, w).ljust(w))
    print(" ".join(line))
    print("-" * (sum(col_widths) + len(col_widths) - 1))

    total_minutes = 0
    for s in sessions:
        total_minutes += s["duration_minutes"]
        row = []
        row.append(str(s["id"]).rjust(col_widths))
        row.append(s["date"].ljust(col_widths[1]))
        time_range = f"{format_time(s['start_time'], config)}-{format_time(s['end_time'], config)}"
        row.append(trunc(time_range, col_widths[2]).ljust(col_widths[2]))
        row.append(f"{s['duration_minutes']}m".rjust(col_widths[3]))
        row.append(trunc(s["subject"], col_widths[4]).ljust(col_widths[4]))
        fr = s.get("focus_rating")
        row.append((str(fr) if fr is not None else "").center(col_widths[5]))
        tags = ", ".join(s.get("tags", []))
        row.append(trunc(tags, col_widths[6]).ljust(col_widths[6]))
        print(" ".join(row))
    print("-" * (sum(col_widths) + len(col_widths) - 1))
    print(f"Total sessions: {len(sessions)}")
    print(f"Total minutes: {total_minutes}")


def aggregate_stats(sessions: list) -> dict:
    total_minutes = sum(s["duration_minutes"] for s in sessions)
    focus_vals = [s["focus_rating"] for s in sessions if isinstance(s.get("focus_rating"), int)]
    avg_focus = sum(focus_vals) / len(focus_vals) if focus_vals else None
    subjects = {}
    for s in sessions:
        subj = s["subject"]
        subjects.setdefault(subj, 0)
        subjects[subj] += s["duration_minutes"]
    top_subjects = sorted(subjects.items(), key=lambda x: x[1], reverse=True)
    return {
        "total_minutes": total_minutes,
        "session_count": len(sessions),
        "avg_focus": avg_focus,
        "top_subjects": top_subjects,
    }


def print_progress_bar(current: int, goal: int, width: int = 10) -> str:
    if goal <= 0:
        return "[----------] 0% (0/0 min)"
    ratio = max(0.0, min(1.0, current / goal))
    filled = int(round(ratio * width))
    bar = "[" + "#" * filled + "-" * (width - filled) + "]"
    percent = int(round(ratio * 100))
    return f"{bar} {percent}% ({current}/{goal} min)"


def cmd_add(args, data):
    today = dt.date.today().isoformat()
    date_str = args.date or today
    while True:
        try:
            date = parse_date(date_str, allow_keywords=True)
            break
        except ValueError as e:
            if any([args.date, args.start, args.end, args.subject, args.tags, args.focus is not None]):
                print(e, file=sys.stderr)
                sys.exit(1)
            print(e)
            date_str = input_with_default("Date (YYYY-MM-DD or today/yesterday)", today)

    def prompt_time(name, default_val=None):
        val = getattr(args, name) or default_val
        while True:
            if any([getattr(args, "date"), getattr(args, "start"), getattr(args, "end"), getattr(args, "subject"), getattr(args, "tags"), args.focus is not None]) and getattr(args, name):
                try:
                    return parse_time(val)
                except ValueError as e:
                    print(e, file=sys.stderr)
                    sys.exit(1)
            val = input_with_default(f"{name.replace('_', ' ').title()} (HH:MM 24h)", val or "")
            try:
                return parse_time(val)
            except ValueError as e:
                print(e)

    now = dt.datetime.now()
    default_start = now.replace(minute=0, second=0, microsecond=0).time().strftime("%H:%M")
    start = prompt_time("start", default_start)
    default_end = (dt.datetime.combine(dt.date.today(), start) + dt.timedelta(minutes=60)).time().strftime("%H:%M")
    end = prompt_time("end", default_end)

    try:
        duration = compute_duration_minutes(start, end)
    except ValueError as e:
        if any([args.date, args.start, args.end, args.subject, args.tags, args.focus is not None]):
            print(e, file=sys.stderr)
            sys.exit(1)
        print(e)
        # re-prompt times
        start = prompt_time("start")
        end = prompt_time("end")
        duration = compute_duration_minutes(start, end)

    subject = args.subject or ""
    while not subject.strip():
        subject = input("Subject (required): ").strip()
        if not subject:
            print("Subject is required.")
    tags = parse_tags(args.tags or "")
    if not args.tags:
        t_in = input_with_default("Tags (comma-separated, optional)", "")
        tags = parse_tags(t_in)

    focus = args.focus
    def prompt_focus(current):
        if current is not None:
            return current
        while True:
            v = input_with_default("Focus rating 1-5 (optional)", "")
            if not v.strip():
                return None
            try:
                iv = int(v)
                if 1 <= iv <= 5:
                    return iv
            except Exception:
                pass
            print("Please enter integer 1-5 or leave blank.")
    focus = prompt_focus(focus)

    print("Enter notes (end with blank line or EOF):")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "":
            break
        lines.append(line)
    notes = "\n".join(lines)

    session = {
        "id": next_session_id(data),
        "date": date.isoformat(),
        "start_time": start.strftime("%H:%M"),
        "end_time": end.strftime("%H:%M"),
        "duration_minutes": duration,
        "subject": subject,
        "tags": tags,
        "notes": notes,
        "focus_rating": focus,
    }

    print("\nNew session:")
    cfg = data.get("config", {})
    print(f"ID: {session['id']}")
    print(f"Date: {session['date']}")
    print(f"Time: {format_time(session['start_time'], cfg)} - {format_time(session['end_time'], cfg)} ({duration} min)")
    print(f"Subject: {session['subject']}")
    print(f"Tags: {', '.join(session['tags']) if session['tags'] else ''}")
    print(f"Focus: {session['focus_rating'] if session['focus_rating'] is not None else ''}")
    if session["notes"]:
        print("Notes:")
        print(session["notes"])
    if not confirm("Save this session?", default=True):
        print("Cancelled.")
        return
    data["sessions"].append(session)
    save_data(data)
    print("Session saved.")


def cmd_list(args, data):
    date_from = date_to = None
    if args.date:
        try:
            d = parse_date(args.date, allow_keywords=True)
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        date_from = date_to = d
    if args.date_from:
        try:
            date_from = parse_date(args.date_from, allow_keywords=False)
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
    if args.date_to:
        try:
            date_to = parse_date(args.date_to, allow_keywords=False)
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
    sessions = list_sessions_filtered(data, date_from, date_to, args.subject, args.tag)
    print_sessions_table(sessions, data.get("config", {}))


def cmd_edit(args, data):
    try:
        sid = int(args.id)
    except Exception:
        print("ID must be integer.", file=sys.stderr)
        sys.exit(1)
    session = get_session_by_id(data, sid)
    if not session:
        print(f"No session with ID {sid}.", file=sys.stderr)
        existing_ids = [s["id"] for s in data.get("sessions", [])]
        if existing_ids:
            print(f"Existing IDs: {min(existing_ids)} - {max(existing_ids)}", file=sys.stderr)
        sys.exit(1)

    print("Editing session. Press Enter to keep current value.")
    date_str = input_with_default("Date (YYYY-MM-DD)", session["date"])
    while True:
        try:
            date = parse_date(date_str, allow_keywords=False)
            break
        except ValueError as e:
            print(e)
            date_str = input_with_default("Date (YYYY-MM-DD)", session["date"])

    st_str = input_with_default("Start time (HH:MM 24h)", session["start_time"])
    while True:
        try:
            start = parse_time(st_str)
            break
        except ValueError as e:
            print(e)
            st_str = input_with_default("Start time (HH:MM 24h)", session["start_time"])

    et_str = input_with_default("End time (HH:MM 24h)", session["end_time"])
    while True:
        try:
            end = parse_time(et_str)
            break
        except ValueError as e:
            print(e)
            et_str = input_with_default("End time (HH:MM 24h)", session["end_time"])

    try:
        duration = compute_duration_minutes(start, end)
    except ValueError as e:
        print(e)
        sys.exit(1)

    subject = input_with_default("Subject", session["subject"])
    tags_str = input_with_default("Tags (comma-separated)", ", ".join(session.get("tags", [])))
    tags = parse_tags(tags_str)
    focus_current = session.get("focus_rating")
    while True:
        fr_str = input_with_default("Focus rating 1-5 (optional)", "" if focus_current is None else str(focus_current))
        if not fr_str.strip():
            focus = None
            break
        try:
            iv = int(fr_str)
            if 1 <= iv <= 5:
                focus = iv
                break
        except Exception:
            pass
        print("Please enter integer 1-5 or leave blank.")

    print("Current notes (will be replaced). Leave blank to keep existing.")
    print("Enter new notes (end with blank line).")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "":
            break
        lines.append(line)
    if lines:
        notes = "\n".join(lines)
    else:
        notes = session.get("notes", "")

    new_session = {
        "id": session["id"],
        "date": date.isoformat(),
        "start_time": start.strftime("%H:%M"),
        "end_time": end.strftime("%H:%M"),
        "duration_minutes": duration,
        "subject": subject,
        "tags": tags,
        "notes": notes,
        "focus_rating": focus,
    }

    print("\nUpdated session:")
    cfg = data.get("config", {})
    print(f"ID: {new_session['id']}")
    print(f"Date: {new_session['date']}")
    print(f"Time: {format_time(new_session['start_time'], cfg)} - {format_time(new_session['end_time'], cfg)} ({duration} min)")
    print(f"Subject: {new_session['subject']}")
    print(f"Tags: {', '.join(new_session['tags']) if new_session['tags'] else ''}")
    print(f"Focus: {new_session['focus_rating'] if new_session['focus_rating'] is not None else ''}")
    if new_session["notes"]:
        print("Notes:")
        print(new_session["notes"])
    if not confirm("Save changes?", default=True):
        print("Cancelled.")
        return
    # replace
    for i, s in enumerate(data["sessions"]):
        if s["id"] == sid:
            data["sessions"][i] = new_session
            break
    save_data(data)
    print("Session updated.")


def cmd_delete(args, data):
    try:
        sid = int(args.id)
    except Exception:
        print("ID must be integer.", file=sys.stderr)
        sys.exit(1)
    session = get_session_by_id(data, sid)
    if not session:
        print(f"No session with ID {sid}.", file=sys.stderr)
        existing_ids = [s["id"] for s in data.get("sessions", [])]
        if existing_ids:
            print(f"Existing IDs: {min(existing_ids)} - {max(existing_ids)}", file=sys.stderr)
        sys.exit(1)
    if not args.force:
        cfg = data.get("config", {})
        print("Delete session:")
        print(f"ID {session['id']} {session['date']} {format_time(session['start_time'], cfg)}-{format_time(session['end_time'], cfg)} {session['subject']} ({session['duration_minutes']} min)")
        if not confirm("Are you sure?", default=False):
            print("Cancelled.")
            return
    data["sessions"] = [s for s in data["sessions"] if s["id"] != sid]
    save_data(data)
    print("Session deleted.")


def date_range_for_period(args):
    today = dt.date.today()
    if args.day:
        if args.day.lower() in ("today", ""):
            return today, today
        try:
            d = parse_date(args.day, allow_keywords=True)
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        return d, d
    if args.week:
        val = args.week.lower()
        if val == "this":
            iso_year, iso_week, _ = today.isocalendar()
        else:
            try:
                iso_year, iso_week = today.year, int(val)
            except Exception:
                print("Invalid week value. Use ISO week number or 'this'.", file=sys.stderr)
                sys.exit(1)
        # Monday of ISO week
        first = dt.date.fromisocalendar(iso_year, iso_week, 1)
        last = first + dt.timedelta(days=6)
        return first, last
    if args.month:
        val = args.month.lower()
        if val == "this":
            year, month = today.year, today.month
        else:
            try:
                year, month = map(int, val.split("-"))
            except Exception:
                print("Invalid month format, expected YYYY-MM or 'this'.", file=sys.stderr)
                sys.exit(1)
        first = dt.date(year, month, 1)
        if month == 12:
            next_first = dt.date(year + 1, 1, 1)
        else:
            next_first = dt.date(year, month + 1, 1)
        last = next_first - dt.timedelta(days=1)
        return first, last
    # default day=today
    return today, today


def cmd_summary(args, data):
    if sum(bool(x) for x in [args.day, args.week, args.month]) > 1:
        print("Only one of --day, --week, --month allowed.", file=sys.stderr)
        sys.exit(1)
    start, end = date_range_for_period(args)
    sessions = list_sessions_filtered(data, start, end, None, None)
    stats = aggregate_stats(sessions)
    print(f"Summary {start.isoformat()} to {end.isoformat()}:")
    print(f"Total minutes: {stats['total_minutes']} ({stats['total_minutes']/60:.2f} h)")
    print(f"Total sessions: {stats['session_count']}")
    if stats["avg_focus"] is not None:
        print(f"Average focus: {stats['avg_focus']:.2f}")
    if stats["top_subjects"]:
        print("Top subjects by minutes:")
        for subj, mins in stats["top_subjects"][:5]:
            print(f"  {subj}: {mins} min")

    goal = data.get("config", {}).get("default_daily_goal_minutes", 300)
    days = (end - start).days + 1
    if days <= 0:
        days = 1
    avg_per_day = stats["total_minutes"] / days if days else 0
    if start == end:
        bar = print_progress_bar(stats["total_minutes"], goal)
        print(f"Daily goal: {goal} min")
        print(bar)
    else:
        print(f"Average per day: {avg_per_day:.1f} min (goal {goal} min/day)")


def cmd_today(args, data):
    today = dt.date.today()
    start = end = today
    sessions = list_sessions_filtered(data, start, end, None, None)
    print("Today's sessions:")
    print_sessions_table(sessions, data.get("config", {}))
    stats = aggregate_stats(sessions)
    goal = data.get("config", {}).get("default_daily_goal_minutes", 300)
    print()
    print("Today's total:")
    print(f"Minutes: {stats['total_minutes']} ({stats['total_minutes']/60:.2f} h)")
    bar = print_progress_bar(stats["total_minutes"], goal)
    print(f"Goal: {goal} min")
    print(bar)


def cmd_subject(args, data):
    try:
        df = parse_date(args.date_from, allow_keywords=False) if args.date_from else None
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    try:
        dt_to = parse_date(args.date_to, allow_keywords=False) if args.date_to else None
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    sessions = list_sessions_filtered(data, df, dt_to, args.subject, None)
    if not sessions:
        print("No sessions for subject in given range.")
        return
    stats = aggregate_stats(sessions)
    print(f"Subject: {args.subject}")
    rng_desc = ""
    if df and dt_to:
        rng_desc = f"{df.isoformat()} to {dt_to.isoformat()}"
    elif df:
        rng_desc = f"from {df.isoformat()}"
    elif dt_to:
        rng_desc = f"up to {dt_to.isoformat()}"
    if rng_desc:
        print(f"Range: {rng_desc}")
    print(f"Total minutes: {stats['total_minutes']} ({stats['total_minutes']/60:.2f} h)")
    print(f"Sessions: {stats['session_count']}")
    if stats["avg_focus"] is not None:
        print(f"Average focus: {stats['avg_focus']:.2f}")
    print("Last 5 sessions:")
    sessions_sorted = sorted(sessions, key=lambda x: (x["date"], x["start_time"]), reverse=True)
    for s in sessions_sorted[:5]:
        fr = s.get("focus_rating")
        print(f"  {s['date']} {s['duration_minutes']} min focus {fr if fr is not None else ''}")


def make_print_report(sessions: list, start: dt.date, end: dt.date, subject_filter: str | None, width: int, config: dict) -> str:
    wrap = textwrap.TextWrapper(width=width)
    lines = []
    title = "Study Sessions Report"
    lines.append(title)
    lines.append("=" * len(title))
    period = f"Period: {start.isoformat()} to {end.isoformat()}"
    lines.append(period)
    if subject_filter:
        lines.append(f"Subject filter: {subject_filter}")
    lines.append("")

    stats = aggregate_stats(sessions)
    lines.append("Summary")
    lines.append("-------")
    lines.append(f"Total sessions: {stats['session_count']}")
    lines.append(f"Total minutes: {stats['total_minutes']} ({stats['total_minutes']/60:.2f} h)")
    if stats["avg_focus"] is not None:
        lines.append(f"Average focus: {stats['avg_focus']:.2f}")
    if stats["top_subjects"]:
        lines.append("Top subjects:")
        for subj, mins in stats["top_subjects"][:5]:
            lines.append(f"  {subj}: {mins} min")
    lines.append("")

    lines.append("Sessions")
    lines.append("--------")
    if not sessions:
        lines.append("No sessions in this period.")
    else:
        for s in sorted(sessions, key=lambda x: (x["date"], x["start_time"])):
            header = f"{s['date']} {format_time(s['start_time'], config)}-{format_time(s['end_time'], config)} ({s['duration_minutes']} min)"
            subj_line = f"Subject: {s['subject']}"
            tags = ", ".join(s.get("tags", []))
            focus = s.get("focus_rating")
            lines.append(header)
            lines.append(subj_line)
            if tags:
                lines.append(f"Tags: {tags}")
            if focus is not None:
                lines.append(f"Focus: {focus}")
            if s.get("notes"):
                lines.append("Notes:")
                for note_line in s["notes"].splitlines():
                    for wline in wrap.wrap(note_line) or [""]:
                        lines.append("  " + wline)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def cmd_print(args, data):
    if args.day and (args.date_from or args.date_to):
        print("Use either --day or --from/--to, not both.", file=sys.stderr)
        sys.exit(1)
    if args.day:
        try:
            d = parse_date(args.day, allow_keywords=True)
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        start = end = d
    else:
        if not args.date_from or not args.date_to:
            print("For range, both --from and --to are required.", file=sys.stderr)
            sys.exit(1)
        try:
            start = parse_date(args.date_from, allow_keywords=False)
            end = parse_date(args.date_to, allow_keywords=False)
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        if end < start:
            print("--to date must be after or equal to --from.", file=sys.stderr)
            sys.exit(1)
    sessions = list_sessions_filtered(data, start, end, args.subject, None)
    width = args.width or data.get("config", {}).get("default_print_width", 80)
    report = make_print_report(sessions, start, end, args.subject, width, data.get("config", {}))
    sys.stdout.write(report)


def cmd_config(args, data):
    cfg = data.setdefault("config", {})
    if args.action == "show":
        print("Configuration:")
        for k in ("time_format", "default_print_width", "default_daily_goal_minutes"):
            print(f"  {k}: {cfg.get(k)}")
    elif args.action == "set":
        key = args.key
        val = args.value
        if key not in ("time_format", "default_print_width", "default_daily_goal_minutes"):
            print("Unknown config key.", file=sys.stderr)
            sys.exit(1)
        if key == "time_format":
            if val not in ("24h", "12h"):
                print("time_format must be '24h' or '12h'.", file=sys.stderr)
                sys.exit(1)
            cfg["time_format"] = val
        elif key == "default_print_width":
            try:
                iv = int(val)
                if iv < 40:
                    raise ValueError
            except Exception:
                print("default_print_width must be integer >= 40.", file=sys.stderr)
                sys.exit(1)
            cfg["default_print_width"] = iv
        elif key == "default_daily_goal_minutes":
            try:
                iv = int(val)
                if iv <= 0:
                    raise ValueError
            except Exception:
                print("default_daily_goal_minutes must be positive integer.", file=sys.stderr)
                sys.exit(1)
            cfg["default_daily_goal_minutes"] = iv
        save_data(data)
        print("Config updated.")


def cmd_import(args, data):
    path = Path(args.path)
    if not path.exists():
        print("Import file does not exist.", file=sys.stderr)
        sys.exit(1)
    try:
        with path.open("r", encoding="utf-8") as f:
            incoming = json.load(f)
    except Exception as e:
        print(f"Error reading import file: {e}", file=sys.stderr)
        sys.exit(1)
    if isinstance(incoming, dict):
        sessions_in = incoming.get("sessions", [])
        config_in = incoming.get("config")
    elif isinstance(incoming, list):
        sessions_in = incoming
        config_in = None
    else:
        print("Invalid import format.", file=sys.stderr)
        sys.exit(1)
    if not isinstance(sessions_in, list):
        print("Invalid import format: sessions must be a list.", file=sys.stderr)
        sys.exit(1)
    print(f"About to import {len(sessions_in)} sessions.")
    if config_in:
        print("Config from file will be ignored (current config kept).")
    if not confirm("Proceed with import?", default=False):
        print("Cancelled.")
        return
    existing_ids = {s["id"] for s in data.get("sessions", []) if "id" in s}
    next_id = next_session_id(data)
    imported_count = 0
    for s in sessions_in:
        if "id" in s and s["id"] in existing_ids:
            s["id"] = next_id
            next_id += 1
        elif "id" not in s:
            s["id"] = next_id
            next_id += 1
        imported_count += 1
        data["sessions"].append(s)
    save_data(data)
    print(f"Imported {imported_count} sessions.")


def cmd_export(args, data):
    path = Path(args.path)
    payload = None
    if args.sessions_only:
        payload = data.get("sessions", [])
    else:
        payload = data
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing export file: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Exported to {path}.")


def build_arg_parser():
    p = argparse.ArgumentParser(description="Study Session Planner CLI")
    sub = p.add_subparsers(dest="command")

    # add
    ap = sub.add_parser("add", help="Add a study session")
    ap.add_argument("--date", help="Date (YYYY-MM-DD or 'today')")
    ap.add_argument("--start", help="Start time HH:MM")
    ap.add_argument("--end", help="End time HH:MM")
    ap.add_argument("--subject", help="Subject")
    ap.add_argument("--tags", help="Comma-separated tags")
    ap.add_argument("--focus", type=int, help="Focus rating 1-5")
    ap.set_defaults(func=cmd_add)

    # list
    lp = sub.add_parser("list", help="List sessions")
    lp.add_argument("--date", help="Specific date (YYYY-MM-DD or 'today')")
    lp.add_argument("--from", dest="date_from", help="From date YYYY-MM-DD")
    lp.add_argument("--to", dest="date_to", help="To date YYYY-MM-DD")
    lp.add_argument("--subject", help="Filter by subject (case-insensitive)")
    lp.add_argument("--tag", help="Filter by tag")
    lp.set_defaults(func=cmd_list)

    # edit
    ep = sub.add_parser("edit", help="Edit a session")
    ep.add_argument("id", help="Session ID")
    ep.set_defaults(func=cmd_edit)

    # delete
    dp = sub.add_parser("delete", help="Delete a session")
    dp.add_argument("id", help="Session ID")
    dp.add_argument("--force", action="store_true", help="Skip confirmation")
    dp.set_defaults(func=cmd_delete)

    # summary
    sp = sub.add_parser("summary", help="Show summary over a period")
    sp.add_argument("--day", help="Date (YYYY-MM-DD or 'today')")
    sp.add_argument("--week", help="ISO week number or 'this'")
    sp.add_argument("--month", help="YYYY-MM or 'this'")
    sp.set_defaults(func=cmd_summary)

    # today
    tp = sub.add_parser("today", help="Today's summary and sessions")
    tp.set_defaults(func=cmd_today)

    # subject
    sbp = sub.add_parser("subject", help="Subject statistics")
    sbp.add_argument("subject", help="Subject name")
    sbp.add_argument("--from", dest="date_from", help="From date YYYY-MM-DD")
    sbp.add_argument("--to", dest="date_to", help="To date YYYY-MM-DD")
    sbp.set_defaults(func=cmd_subject)

    # print
    prp = sub.add_parser("print", help="Print-friendly text report")
    prp.add_argument("--day", help="Date (YYYY-MM-DD or 'today')")
    prp.add_argument("--from", dest="date_from", help="From date YYYY-MM-DD")
    prp.add_argument("--to", dest="date_to", help="To date YYYY-MM-DD")
    prp.add_argument("--subject", help="Subject filter")
    prp.add_argument("--width", type=int, help="Line width")
    prp.set_defaults(func=cmd_print)

    # config
    cfgp = sub.add_parser("config", help="Show or set configuration")
    cfg_sub = cfgp.add_subparsers(dest="action", required=True)

    cfg_show = cfg_sub.add_parser("show", help="Show configuration")
    cfg_show.set_defaults(func=cmd_config)

    cfg_set = cfg_sub.add_parser("set", help="Set configuration key")
    cfg_set.add_argument("key", help="Key name")
    cfg_set.add_argument("value", help="Value")
    cfg_set.set_defaults(func=cmd_config)

    # import
    imp = sub.add_parser("import", help="Import sessions from JSON")
    imp.add_argument("path", help="Path to JSON file")
    imp.set_defaults(func=cmd_import)

    # export
    exp = sub.add_parser("export", help="Export data to JSON")
    exp.add_argument("path", help="Output path")
    exp.add_argument("--sessions-only", action="store_true", help="Export only sessions")
    exp.set_defaults(func=cmd_export)

    return p


def repl():
    data = load_data()
    parser = build_arg_parser()
    commands_help = {
        "add": "Add a study session",
        "list": "List sessions",
        "edit": "Edit a session: edit ID",
        "delete": "Delete a session: delete ID",
        "summary": "Summary over a period",
        "today": "Today's sessions and summary",
        "subject": "Subject stats: subject NAME",
        "print": "Print-friendly report",
        "config": "View/set configuration",
        "import": "Import data from JSON",
        "export": "Export data to JSON",
        "help": "Show this help",
        "quit": "Exit",
        "exit": "Exit",
        "a": "Alias for add",
        "l": "Alias for list",
        "s": "Alias for summary",
        "t": "Alias for today",
    }
    print("Study Session Planner REPL. Type 'help' for commands. Ctrl-D to exit.")
    while True:
        try:
            line = input("study> ")
        except EOFError:
            print()
            break
        if not line.strip():
            continue
        parts = line.strip().split()
        cmd = parts
        rest = parts[1:]

        if cmd in ("quit", "exit"):
            break
        if cmd == "help":
            print("Commands:")
            for c in sorted(commands_help):
                print(f"  {c:8} {commands_help[c]}")
            continue
        # aliases
        if cmd == "a":
            cmd = "add"
        elif cmd == "l":
            cmd = "list"
        elif cmd == "s":
            cmd = "summary"
        elif cmd == "t":
            cmd = "today"

        argv = [cmd] + rest
        try:
            args = parser.parse_args(argv)
        except SystemExit:
            continue
        if not hasattr(args, "func"):
            print("Unknown command; type 'help' for options.")
            continue
        # re-load for each command to keep in sync, then save through functions
        data = load_data()
        try:
            args.func(args, data)
        except TypeError:
            # commands with different signature (none here, but safe)
            args.func(args)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        repl()
        return
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    data = load_data()
    args.func(args, data)


if __name__ == "__main__":
    main()