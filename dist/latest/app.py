# Auto-generated via Perplexity on 2026-01-10T12:38:25.790345Z
#!/usr/bin/env python3
import sys
import json
import os
import shutil
import uuid
from pathlib import Path
from datetime import datetime, date, timedelta
from collections import defaultdict, Counter
import argparse
import textwrap
import csv

APP_NAME = "Eco Footprint Tracker"
DATA_FILE = "eco_data.json"
DATE_FMT = "%Y-%m-%d"
ISO_FMT = "%Y-%m-%dT%H:%M:%S"

EMISSION_FACTORS = {
    "transport": {
        "_default_unit": "km",
        "_fallback": 0.15,
        "car": 0.18,
        "bus": 0.08,
        "train": 0.04,
        "flight": 0.25,
    },
    "energy": {
        "_default_unit": "kWh",
        "_fallback": 0.5,
        "electricity": 0.4,
        "gas": 2.0,
    },
    "food": {
        "_default_unit": "meals",
        "_fallback": 3.0,
        "beef": 27.0,
        "chicken": 6.9,
        "vegetarian": 2.0,
    },
    "purchases": {
        "_default_unit": "items",
        "_fallback": 10.0,
        "_default": 10.0,
    },
    "other": {
        "_default_unit": "unit",
        "_fallback": 1.0,
        "_default": 1.0,
    },
}
CATEGORIES = ["transport", "energy", "food", "purchases", "other"]

MENU_TEXT = """
[{app}] Active profile: {profile}

1) Add entry
2) Summary
3) Trend
4) Goals
5) Profiles
6) List entries
7) Help
0) Quit
""".strip()


def data_path():
    return Path(__file__).with_name(DATA_FILE)


def load_data():
    path = data_path()
    if not path.exists():
        return {"profiles": {}, "last_profile": None}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        backup = path.with_suffix(path.suffix + ".bak")
        try:
            shutil.copy2(path, backup)
        except Exception:
            pass
        return {"profiles": {}, "last_profile": None}


def atomic_write_json(path: Path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def save_data(data):
    atomic_write_json(data_path(), data)


def ensure_profile(data, name=None):
    if name is None:
        name = data.get("last_profile")
    if not data["profiles"]:
        default_name = "default"
        data["profiles"][default_name] = {
            "entries": [],
            "goals": {},
            "metadata": {
                "created_at": datetime.now().strftime(ISO_FMT),
                "last_used": datetime.now().strftime(ISO_FMT),
                "units": "metric",
                "next_id": 1,
            },
        }
        data["last_profile"] = default_name
        save_data(data)
        return default_name
    if name is None or name not in data["profiles"]:
        # pick arbitrary existing
        name = sorted(data["profiles"].keys())
    data["last_profile"] = name
    data["profiles"][name]["metadata"]["last_used"] = datetime.now().strftime(ISO_FMT)
    save_data(data)
    return name


def get_profile(data, name=None):
    name = ensure_profile(data, name)
    return name, data["profiles"][name]


def next_entry_id(profile):
    meta = profile.setdefault("metadata", {})
    nid = meta.get("next_id", 1)
    meta["next_id"] = nid + 1
    return nid


def compute_co2e(category, subcategory, amount):
    sub = subcategory.strip().lower() if subcategory else ""
    cat_factors = EMISSION_FACTORS.get(category, {})
    if category in ("purchases", "other"):
        factor = cat_factors.get(sub, cat_factors.get("_default", cat_factors.get("_fallback", 1.0)))
    else:
        factor = cat_factors.get(sub, cat_factors.get("_fallback", 1.0))
    return round(amount * factor, 3)


def prompt(text, default=None, validator=None, allow_empty=False):
    while True:
        if default is not None:
            s = input(f"{text} [{default}]: ").strip()
            if not s:
                s = str(default)
        else:
            s = input(f"{text}: ").strip()
            if not s and allow_empty:
                return ""
        if validator:
            ok, val_or_err = validator(s)
            if ok:
                return val_or_err
            print(f"  {val_or_err}")
        else:
            return s


def validate_float(s):
    try:
        v = float(s)
        if v < 0:
            return False, "Value must be non-negative."
        return True, v
    except ValueError:
        return False, "Enter a valid number."


def validate_date(s):
    try:
        d = datetime.strptime(s, DATE_FMT).date()
        return True, d
    except ValueError:
        return False, "Enter date as YYYY-MM-DD."


def choose_category():
    print("Select category:")
    for i, c in enumerate(CATEGORIES, start=1):
        print(f"  {i}) {c}")
    while True:
        s = input("Category number or name: ").strip().lower()
        if not s:
            print("  Please choose a category.")
            continue
        if s.isdigit():
            i = int(s)
            if 1 <= i <= len(CATEGORIES):
                return CATEGORIES[i - 1]
            print("  Invalid number.")
            continue
        if s in CATEGORIES:
            return s
        print("  Unknown category; valid: " + ", ".join(CATEGORIES))


def add_entry_interactive(data, profile_name=None):
    profile_name, profile = get_profile(data, profile_name)
    print("\nAdd new entry")
    category = choose_category()
    default_sub = {
        "transport": "car",
        "energy": "electricity",
        "food": "vegetarian",
        "purchases": "",
        "other": "",
    }.get(category, "")
    sub = input(f"Subcategory (e.g. car, train) [{default_sub or 'none'}]: ").strip()
    if not sub:
        sub = default_sub
    amount = prompt("Amount", validator=validate_float)
    default_unit = EMISSION_FACTORS.get(category, {}).get("_default_unit", "unit")
    unit = input(f"Unit [{default_unit}]: ").strip() or default_unit
    notes = input("Notes (optional): ").rstrip()
    today = date.today()
    d = prompt("Date (YYYY-MM-DD)", default=today.strftime(DATE_FMT), validator=validate_date)
    if isinstance(d, date):
        entry_date = d
    else:
        entry_date = d
    ts = datetime.now()
    co2 = compute_co2e(category, sub, amount)
    entry = {
        "id": next_entry_id(profile),
        "timestamp": ts.strftime(ISO_FMT),
        "date": entry_date.strftime(DATE_FMT),
        "category": category,
        "subcategory": sub,
        "amount": amount,
        "unit": unit,
        "notes": notes,
        "co2e_estimate_kg": co2,
    }
    profile["entries"].append(entry)
    profile["metadata"]["last_used"] = ts.strftime(ISO_FMT)
    save_data(data)
    print(f"\nEntry added. Estimated CO₂e: {co2} kg\n")


def parse_date(s):
    return datetime.strptime(s, DATE_FMT).date()


def filter_entries(entries, days=None, category=None, since=None, until=None):
    res = []
    if days is not None:
        since = date.today() - timedelta(days=days - 1)
    for e in entries:
        d = parse_date(e["date"])
        if since and d < since:
            continue
        if until and d > until:
            continue
        if category and e["category"] != category:
            continue
        res.append(e)
    return res


def terminal_width(default=80):
    try:
        import shutil as _sh

        return _sh.get_terminal_size((default, 20)).columns
    except Exception:
        return default


def truncate(text, width):
    if len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    return text[: width - 3] + "..."


def list_entries_cmd(data, args, profile_name=None):
    profile_name, profile = get_profile(data, profile_name)
    days = args.days
    category = args.category
    limit = args.limit
    entries = sorted(profile["entries"], key=lambda e: (e["date"], e["timestamp"]), reverse=True)
    if days or category:
        entries = filter_entries(entries, days=days, category=category)
    if limit:
        entries = entries[:limit]
    if not entries:
        print("No entries found.")
        return
    width = terminal_width()
    headers = ["Date", "Cat", "Subcat", "Amount", "CO₂e kg", "Notes"]
    col_widths = [10, 8, 12, 16, 10, max(10, width - (10 + 8 + 12 + 16 + 10 + 5))]
    fmt = "{:<10} {:<8} {:<12} {:>16} {:>10}  {}"
    print(fmt.format(*headers))
    print("-" * width)
    for e in entries:
        amt = f"{e['amount']} {e['unit']}"
        notes = truncate(e.get("notes", ""), col_widths[5])
        print(
            fmt.format(
                e["date"],
                e["category"],
                truncate(e.get("subcategory", ""), col_widths[2]),
                amt,
                f"{e['co2e_estimate_kg']:.2f}",
                notes,
            )
        )


def summary_cmd(data, args, profile_name=None):
    profile_name, profile = get_profile(data, profile_name)
    entries = profile["entries"]
    if not entries:
        print("No entries to summarize.")
        return
    days = None
    since = None
    until = None
    if args.days:
        days = args.days
    elif args.week:
        # last 7 days
        since = date.today() - timedelta(days=6)
    elif args.month:
        today = date.today()
        since = today.replace(day=1)
    category = args.category
    filtered = filter_entries(entries, days=days, category=category, since=since, until=until)
    if not filtered:
        print("No entries in selected period.")
        return
    total = sum(e["co2e_estimate_kg"] for e in filtered)
    print(f"Summary for profile '{profile_name}':")
    print(f"Total CO₂e: {total:.2f} kg")
    by_cat = defaultdict(float)
    for e in filtered:
        by_cat[e["category"]] += e["co2e_estimate_kg"]
    print("\nBy category:")
    for cat, val in sorted(by_cat.items(), key=lambda kv: -kv[1]):
        pct = (val / total * 100) if total else 0
        print(f"  {cat:<10} {val:8.2f} kg  ({pct:5.1f}%)")
    print("\nTop 3 highest-emission entries:")
    top = sorted(filtered, key=lambda e: e["co2e_estimate_kg"], reverse=True)[:3]
    for e in top:
        print(
            f"  {e['date']} {e['category']} {e.get('subcategory','') or ''} "
            f"{e['amount']} {e['unit']} -> {e['co2e_estimate_kg']:.2f} kg"
        )
    # ASCII bar chart
    width = terminal_width()
    print("\nCategory emissions (relative):")
    max_val = max(by_cat.values()) if by_cat else 0
    bar_max = max(10, width - 20)
    if max_val <= 0:
        print("  No data.")
        return
    for cat, val in sorted(by_cat.items(), key=lambda kv: -kv[1]):
        bar_len = int(val / max_val * bar_max)
        bar = "#" * bar_len
        print(f"  {cat:<10} | {bar} {val:.2f} kg")


def start_of_week(d):
    # ISO week: Monday
    return d - timedelta(days=d.weekday())


def last_full_weeks(n=4):
    today = date.today()
    this_week_start = start_of_week(today)
    last_week_end = this_week_start - timedelta(days=1)
    last_week_start = start_of_week(last_week_end)
    weeks = []
    cur = last_week_start
    for _ in range(n):
        weeks.append(cur)
        cur = cur - timedelta(days=7)
    return sorted(weeks)


def trend_cmd(data, args, profile_name=None):
    profile_name, profile = get_profile(data, profile_name)
    entries = profile["entries"]
    if not entries:
        print("No entries for trend.")
        return
    weeks = last_full_weeks(4)
    week_totals = []
    for ws in weeks:
        we = ws + timedelta(days=6)
        total = sum(
            e["co2e_estimate_kg"]
            for e in entries
            if ws <= parse_date(e["date"]) <= we
        )
        week_totals.append((ws, total))
    max_total = max((t for _, t in week_totals), default=0)
    width = terminal_width()
    bar_max = max(10, width - 25)
    print(f"4-week trend for profile '{profile_name}':")
    prev = None
    for ws, total in week_totals:
        if prev is None:
            direction = "N/A"
        else:
            if total > prev + 1e-6:
                direction = "UP"
            elif total < prev - 1e-6:
                direction = "DOWN"
            else:
                direction = "SAME"
        prev = total
        if max_total > 0:
            bar_len = int(total / max_total * bar_max)
        else:
            bar_len = 0
        bar = "#" * bar_len
        print(f"  {ws.strftime(DATE_FMT)} | {bar:<{bar_max}} {total:8.2f} kg  {direction}")


def goal_set_cmd(data, args, profile_name=None):
    profile_name, profile = get_profile(data, profile_name)
    cat = args.category
    if cat not in CATEGORIES:
        print("Unknown category. Valid: " + ", ".join(CATEGORIES))
        return
    try:
        val = float(args.value)
    except ValueError:
        print("Goal value must be a number (kg per week).")
        return
    if val < 0:
        print("Goal must be non-negative.")
        return
    profile.setdefault("goals", {})[cat] = val
    save_data(data)
    print(f"Set goal for {cat}: {val} kg/week")


def goal_clear_cmd(data, args, profile_name=None):
    profile_name, profile = get_profile(data, profile_name)
    goals = profile.setdefault("goals", {})
    target = args.category
    if target == "all":
        goals.clear()
        print("Cleared all goals.")
    else:
        if target not in goals:
            print("No goal set for that category.")
            return
        del goals[target]
        print(f"Cleared goal for {target}.")
    save_data(data)


def goal_show_cmd(data, args, profile_name=None):
    profile_name, profile = get_profile(data, profile_name)
    goals = profile.get("goals", {})
    if not goals:
        print("No goals set.")
        return
    today = date.today()
    last_week_end = start_of_week(today) - timedelta(days=1)
    last_week_start = start_of_week(last_week_end)
    entries = filter_entries(
        profile["entries"],
        since=last_week_start,
        until=last_week_end,
    )
    by_cat = defaultdict(float)
    for e in entries:
        by_cat[e["category"]] += e["co2e_estimate_kg"]
    print(
        f"Goals for profile '{profile_name}' (last full week {last_week_start} to {last_week_end}):"
    )
    for cat, goal in goals.items():
        actual = by_cat.get(cat, 0.0)
        status = "UNDER" if actual <= goal else "OVER"
        print(f"  {cat:<10} goal {goal:8.2f} kg, actual {actual:8.2f} kg -> {status}")


def profile_list_cmd(data, args):
    if not data["profiles"]:
        print("No profiles. Create one with: profile create NAME")
        return
    active = data.get("last_profile")
    print("Profiles:")
    for name in sorted(data["profiles"].keys()):
        mark = "*" if name == active else " "
        print(f" {mark} {name}")


def profile_create_cmd(data, args):
    name = args.name
    if name in data["profiles"]:
        print("Profile already exists.")
        return
    data["profiles"][name] = {
        "entries": [],
        "goals": {},
        "metadata": {
            "created_at": datetime.now().strftime(ISO_FMT),
            "last_used": datetime.now().strftime(ISO_FMT),
            "units": "metric",
            "next_id": 1,
        },
    }
    data["last_profile"] = name
    save_data(data)
    print(f"Created and switched to profile '{name}'.")


def profile_switch_cmd(data, args):
    name = args.name
    if name not in data["profiles"]:
        print("No such profile.")
        return
    data["last_profile"] = name
    data["profiles"][name]["metadata"]["last_used"] = datetime.now().strftime(ISO_FMT)
    save_data(data)
    print(f"Switched to profile '{name}'.")


def profile_rename_cmd(data, args):
    old = args.old
    new = args.new
    if old not in data["profiles"]:
        print("No such profile.")
        return
    if new in data["profiles"]:
        print("Target name already exists.")
        return
    data["profiles"][new] = data["profiles"].pop(old)
    if data.get("last_profile") == old:
        data["last_profile"] = new
    save_data(data)
    print(f"Renamed profile '{old}' to '{new}'.")


def profile_delete_cmd(data, args):
    name = args.name
    if name not in data["profiles"]:
        print("No such profile.")
        return
    confirm = input(f"Delete profile '{name}' and all its data? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return
    del data["profiles"][name]
    if data.get("last_profile") == name:
        data["last_profile"] = None
    save_data(data)
    print(f"Deleted profile '{name}'.")


def find_entry_by_id(profile, eid):
    for e in profile["entries"]:
        if str(e["id"]) == str(eid):
            return e
    return None


def edit_cmd(data, args, profile_name=None):
    profile_name, profile = get_profile(data, profile_name)
    entry = find_entry_by_id(profile, args.id)
    if not entry:
        print("No entry with that id.")
        return
    print("Editing entry:")
    print(json.dumps(entry, indent=2))
    print("Press Enter to keep current value.")
    cat = input(f"Category [{entry['category']}]: ").strip().lower()
    if cat:
        if cat not in CATEGORIES:
            print("Invalid category; keeping original.")
        else:
            entry["category"] = cat
    sub = input(f"Subcategory [{entry.get('subcategory','') or 'none'}]: ").strip()
    if sub:
        entry["subcategory"] = sub
    amt_in = input(f"Amount [{entry['amount']}]: ").strip()
    if amt_in:
        ok, val = validate_float(amt_in)
        if ok:
            entry["amount"] = val
        else:
            print("Invalid amount; keeping original.")
    unit = input(f"Unit [{entry['unit']}]: ").strip()
    if unit:
        entry["unit"] = unit
    notes = input(f"Notes [{entry.get('notes','')}]: ").rstrip()
    if notes:
        entry["notes"] = notes
    d_in = input(f"Date [{entry['date']}]: ").strip()
    if d_in:
        ok, val = validate_date(d_in)
        if ok:
            entry["date"] = val.strftime(DATE_FMT)
        else:
            print("Invalid date; keeping original.")
    entry["co2e_estimate_kg"] = compute_co2e(entry["category"], entry.get("subcategory", ""), entry["amount"])
    save_data(data)
    print("Entry updated.")


def delete_cmd(data, args, profile_name=None):
    profile_name, profile = get_profile(data, profile_name)
    entry = find_entry_by_id(profile, args.id)
    if not entry:
        print("No entry with that id.")
        return
    print("Entry to delete:")
    print(
        f"{entry['date']} {entry['category']} {entry.get('subcategory','')} "
        f"{entry['amount']} {entry['unit']} -> {entry['co2e_estimate_kg']:.2f} kg"
    )
    confirm = input("Delete this entry? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return
    profile["entries"] = [e for e in profile["entries"] if e is not entry]
    save_data(data)
    print("Entry deleted.")


def export_cmd(data, args, profile_name=None):
    profile_name, profile = get_profile(data, profile_name)
    filename = args.filename
    path = Path(filename)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "profile",
                "entry_id",
                "date",
                "timestamp",
                "category",
                "subcategory",
                "amount",
                "unit",
                "co2e_kg",
                "notes",
            ]
        )
        for e in profile["entries"]:
            writer.writerow(
                [
                    profile_name,
                    e["id"],
                    e["date"],
                    e["timestamp"],
                    e["category"],
                    e.get("subcategory", ""),
                    e["amount"],
                    e["unit"],
                    e["co2e_estimate_kg"],
                    e.get("notes", ""),
                ]
            )
    print(f"Exported {len(profile['entries'])} entries to {filename}.")


def help_cmd(*_args, **__kwargs):
    text = """
Commands:
  add
      Add a new entry interactively.
  list [--days N] [--category C] [--limit N]
      List entries in a compact table.
  summary [--days N|--week|--month] [--category C]
      Show total emissions, breakdown, and top entries.
  trend
      Show last 4 full weeks with ASCII bars and direction.
  goal set <category> <kg_per_week>
  goal show
  goal clear <category|all>
  profile list
  profile create <name>
  profile switch <name>
  profile rename <old> <new>
  profile delete <name>
  edit <id>
      Edit an entry by id.
  delete <id>
      Delete an entry by id.
  export <filename.csv>
      Export entries of current profile to CSV.
  demo
      Populate current profile with sample data (with confirmation).

Examples:
  eco.py add
  eco.py list --days 7
  eco.py summary --week
  eco.py goal set transport 50
"""
    print(textwrap.dedent(text).strip())


def demo_cmd(data, args, profile_name=None):
    profile_name, profile = get_profile(data, profile_name)
    if profile["entries"]:
        confirm = input("Demo will add sample entries to current profile. Continue? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return
    today = date.today()
    samples = [
        # transport
        {"offset": 0, "cat": "transport", "sub": "car", "amt": 15, "unit": "km", "notes": "Commute"},
        {"offset": 1, "cat": "transport", "sub": "train", "amt": 80, "unit": "km", "notes": "Trip"},
        # energy
        {"offset": 0, "cat": "energy", "sub": "electricity", "amt": 8, "unit": "kWh", "notes": "Home"},
        {"offset": 2, "cat": "energy", "sub": "gas", "amt": 3, "unit": "unit", "notes": "Heating"},
        # food
        {"offset": 0, "cat": "food", "sub": "beef", "amt": 1, "unit": "meal", "notes": "Dinner"},
        {"offset": 1, "cat": "food", "sub": "vegetarian", "amt": 2, "unit": "meals", "notes": "Lunch"},
        # purchases
        {"offset": 3, "cat": "purchases", "sub": "electronics", "amt": 1, "unit": "item", "notes": "Gadget"},
        # other
        {"offset": 4, "cat": "other", "sub": "misc", "amt": 5, "unit": "unit", "notes": "Other"},
    ]
    for s in samples:
        d = today - timedelta(days=s["offset"])
        co2 = compute_co2e(s["cat"], s["sub"], s["amt"])
        entry = {
            "id": next_entry_id(profile),
            "timestamp": datetime.now().strftime(ISO_FMT),
            "date": d.strftime(DATE_FMT),
            "category": s["cat"],
            "subcategory": s["sub"],
            "amount": s["amt"],
            "unit": s["unit"],
            "notes": s["notes"],
            "co2e_estimate_kg": co2,
        }
        profile["entries"].append(entry)
    save_data(data)
    print(f"Added {len(samples)} demo entries to profile '{profile_name}'.")


def build_arg_parser():
    p = argparse.ArgumentParser(add_help=False)
    sub = p.add_subparsers(dest="command")

    sub.add_parser("add")
    lp = sub.add_parser("list")
    lp.add_argument("--days", type=int)
    lp.add_argument("--category")
    lp.add_argument("--limit", type=int)

    sp = sub.add_parser("summary")
    g = sp.add_mutually_exclusive_group()
    g.add_argument("--days", type=int)
    g.add_argument("--week", action="store_true")
    g.add_argument("--month", action="store_true")
    sp.add_argument("--category")

    sub.add_parser("trend")

    gp = sub.add_parser("goal")
    gsub = gp.add_subparsers(dest="subcommand")
    gset = gsub.add_parser("set")
    gset.add_argument("category")
    gset.add_argument("value")
    gsub.add_parser("show")
    gclr = gsub.add_parser("clear")
    gclr.add_argument("category")

    prof = sub.add_parser("profile")
    psub = prof.add_subparsers(dest="subcommand")
    psub.add_parser("list")
    pcreate = psub.add_parser("create")
    pcreate.add_argument("name")
    pswitch = psub.add_parser("switch")
    pswitch.add_argument("name")
    prename = psub.add_parser("rename")
    prename.add_argument("old")
    prename.add_argument("new")
    pdel = psub.add_parser("delete")
    pdel.add_argument("name")

    eedit = sub.add_parser("edit")
    eedit.add_argument("id")
    edel = sub.add_parser("delete")
    edel.add_argument("id")

    exp = sub.add_parser("export")
    exp.add_argument("filename")

    sub.add_parser("help")
    sub.add_parser("demo")

    return p


def handle_args(data, args):
    if args.command == "add":
        add_entry_interactive(data)
    elif args.command == "list":
        list_entries_cmd(data, args)
    elif args.command == "summary":
        summary_cmd(data, args)
    elif args.command == "trend":
        trend_cmd(data, args)
    elif args.command == "goal":
        if args.subcommand == "set":
            goal_set_cmd(data, args)
        elif args.subcommand == "show":
            goal_show_cmd(data, args)
        elif args.subcommand == "clear":
            goal_clear_cmd(data, args)
        else:
            print("Missing goal subcommand. Use: goal set/show/clear")
    elif args.command == "profile":
        if args.subcommand == "list":
            profile_list_cmd(data, args)
        elif args.subcommand == "create":
            profile_create_cmd(data, args)
        elif args.subcommand == "switch":
            profile_switch_cmd(data, args)
        elif args.subcommand == "rename":
            profile_rename_cmd(data, args)
        elif args.subcommand == "delete":
            profile_delete_cmd(data, args)
        else:
            print("Missing profile subcommand. Use: profile list/create/switch/rename/delete")
    elif args.command == "edit":
        edit_cmd(data, args)
    elif args.command == "delete":
        delete_cmd(data, args)
    elif args.command == "export":
        export_cmd(data, args)
    elif args.command == "help":
        help_cmd()
    elif args.command == "demo":
        demo_cmd(data, args)
    else:
        help_cmd()


def interactive_loop():
    data = load_data()
    profile_name = ensure_profile(data)
    while True:
        os.system("")  # no-op, keeps compatibility
        print(MENU_TEXT.format(app=APP_NAME, profile=profile_name))
        cmd = input("> ").strip()
        if not cmd:
            continue
        if cmd in ("0", "quit", "exit"):
            break
        mapping = {
            "1": "add",
            "2": "summary",
            "3": "trend",
            "4": "goal show",
            "5": "profile list",
            "6": "list",
            "7": "help",
        }
        if cmd in mapping:
            cmd = mapping[cmd]
        argv = cmd.split()
        parser = build_arg_parser()
        try:
            args = parser.parse_args(argv)
        except SystemExit:
            print("Invalid command.")
            help_cmd()
            continue
        if args.command is None:
            print("Unknown command.")
            help_cmd()
            continue
        data = load_data()
        profile_name = ensure_profile(data)
        handle_args(data, args)
        data = load_data()
        profile_name = ensure_profile(data)


def main():
    data = load_data()
    if len(sys.argv) == 1:
        interactive_loop()
        return
    parser = build_arg_parser()
    args = parser.parse_args(sys.argv[1:])
    if not args.command:
        help_cmd()
        sys.exit(1)
    handle_args(data, args)


if __name__ == "__main__":
    main()