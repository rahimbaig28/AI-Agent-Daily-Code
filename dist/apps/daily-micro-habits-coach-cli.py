# Auto-generated via Perplexity on 2026-01-08T04:40:23.897909Z
#!/usr/bin/env python3
import argparse
import curses
import datetime as dt
import json
import os
import sys
import textwrap
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

APP_NAME = "Daily Micro-Habits Coach"
DATA_FILENAME = ".micro_habits.json"
VERSION = "1.0"

CATEGORIES = ["movement", "nutrition", "sleep", "mindfulness", "other"]
TARGET_TYPES = ["boolean", "count", "duration_minutes"]
THEMES = ["light", "dark", "auto"]

# ---------- Data Models ----------

@dataclass
class Habit:
    id: str
    name: str
    category: str
    target_type: str
    target_value: Optional[float]
    is_active: bool = True

@dataclass
class DailyHabitResult:
    habit_id: str
    value: Any
    note: Optional[str] = None

@dataclass
class DailyEntry:
    date: str
    habit_results: List[DailyHabitResult] = field(default_factory=list)
    energy_level: Optional[int] = None
    mood: Optional[int] = None
    reflection: Optional[str] = None

@dataclass
class UserProfile:
    display_name: str = "Friend"
    preferred_theme: str = "auto"
    daily_checkin_time: Optional[str] = None  # "HH:MM"
    dashboard_default_days: int = 7
    high_contrast: bool = False

@dataclass
class AppState:
    last_opened: Optional[str] = None

@dataclass
class RootData:
    profile: UserProfile
    habits: List[Habit]
    entries: List[DailyEntry]
    state: AppState

# ---------- Data Layer ----------

def get_data_path() -> Path:
    home = Path.home()
    if os.name == "nt":
        return home / "micro_habits.json"
    return home / DATA_FILENAME

def default_data() -> RootData:
    profile = UserProfile()
    habits = [
        Habit(
            id="drink_water",
            name="Drink water (5 glasses)",
            category="nutrition",
            target_type="count",
            target_value=5.0,
            is_active=True,
        ),
        Habit(
            id="walk_20",
            name="Walk 20 minutes",
            category="movement",
            target_type="duration_minutes",
            target_value=20.0,
            is_active=True,
        ),
        Habit(
            id="evening_unwind",
            name="Evening unwind (no screens 30 min before bed)",
            category="mindfulness",
            target_type="boolean",
            target_value=None,
            is_active=True,
        ),
    ]
    return RootData(profile=profile, habits=habits, entries=[], state=AppState())

def load_data(path: Path) -> RootData:
    if not path.exists():
        return default_data()
    try:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return default_data()
    profile = UserProfile(**raw.get("profile", {}))
    habits = [Habit(**h) for h in raw.get("habits", [])]
    entries = []
    for e in raw.get("entries", []):
        results = [DailyHabitResult(**r) for r in e.get("habit_results", [])]
        entries.append(
            DailyEntry(
                date=e.get("date"),
                habit_results=results,
                energy_level=e.get("energy_level"),
                mood=e.get("mood"),
                reflection=e.get("reflection"),
            )
        )
    state = AppState(**raw.get("state", {}))
    return RootData(profile=profile, habits=habits, entries=entries, state=state)

def save_data(path: Path, data: RootData) -> None:
    serial = {
        "profile": asdict(data.profile),
        "habits": [asdict(h) for h in data.habits],
        "entries": [
            {
                "date": e.date,
                "habit_results": [asdict(r) for r in e.habit_results],
                "energy_level": e.energy_level,
                "mood": e.mood,
                "reflection": e.reflection,
            }
            for e in data.entries
        ],
        "state": asdict(data.state),
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(serial, f, indent=2)

# ---------- Logic Layer ----------

def today_str() -> str:
    return dt.date.today().isoformat()

def parse_time_str(s: str) -> Optional[dt.time]:
    try:
        h, m = s.split(":")
        return dt.time(int(h), int(m))
    except Exception:
        return None

def select_theme(profile: UserProfile, override: Optional[str]) -> str:
    if override in ("light", "dark"):
        return override
    pref = profile.preferred_theme
    if pref == "auto":
        now = dt.datetime.now().time()
        if now >= dt.time(19, 0) or now < dt.time(7, 0):
            return "dark"
        return "light"
    return pref if pref in ("light", "dark") else "light"

def get_entry_map(entries: List[DailyEntry]) -> Dict[str, DailyEntry]:
    return {e.date: e for e in entries}

def get_or_create_entry(data: RootData, date: str) -> DailyEntry:
    emap = get_entry_map(data.entries)
    if date in emap:
        return emap[date]
    e = DailyEntry(date=date)
    data.entries.append(e)
    data.entries.sort(key=lambda x: x.date)
    return e

def get_habit_map(habits: List[Habit]) -> Dict[str, Habit]:
    return {h.id: h for h in habits}

def habit_target_met(habit: Habit, value: Any) -> Tuple[bool, bool]:
    if habit.target_type == "boolean":
        return (bool(value) is True, False)
    try:
        v = float(value)
    except Exception:
        return (False, False)
    if habit.target_value is None:
        return (v > 0, False)
    if v >= habit.target_value:
        return (True, False)
    if v > 0:
        return (False, True)
    return (False, False)

def compute_streaks(data: RootData) -> Dict[str, Dict[str, int]]:
    entries = sorted(data.entries, key=lambda e: e.date)
    habit_ids = [h.id for h in data.habits]
    best = {hid: 0 for hid in habit_ids}
    current = {hid: 0 for hid in habit_ids}
    for hid in habit_ids:
        last_date = None
        streak = 0
        for e in entries:
            results = {r.habit_id: r for r in e.habit_results}
            if hid not in results:
                if streak > best[hid]:
                    best[hid] = streak
                streak = 0
                last_date = None
                continue
            met, _ = habit_target_met(
                next(h for h in data.habits if h.id == hid),
                results[hid].value,
            )
            if not met:
                if streak > best[hid]:
                    best[hid] = streak
                streak = 0
                last_date = None
                continue
            d = dt.date.fromisoformat(e.date)
            if last_date is None or d == last_date + dt.timedelta(days=1):
                streak += 1
            else:
                if streak > best[hid]:
                    best[hid] = streak
                streak = 1
            last_date = d
        if streak > best[hid]:
            best[hid] = streak
        current[hid] = streak
    return {hid: {"current": current[hid], "best": best[hid]} for hid in habit_ids}

def date_range(end_date: dt.date, days: int) -> List[str]:
    return [(end_date - dt.timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]

def completion_for_range(data: RootData, start: dt.date, end: dt.date) -> Dict[str, float]:
    hmap = get_habit_map(data.habits)
    day_map = get_entry_map(data.entries)
    habit_ids = [h.id for h in data.habits if h.is_active]
    total = {hid: 0 for hid in habit_ids}
    met = {hid: 0 for hid in habit_ids}
    cur = start
    while cur <= end:
        ds = cur.isoformat()
        entry = day_map.get(ds)
        rmap = {r.habit_id: r for r in entry.habit_results} if entry else {}
        for hid in habit_ids:
            total[hid] += 1
            r = rmap.get(hid)
            if not r:
                continue
            ok, _ = habit_target_met(hmap[hid], r.value)
            if ok:
                met[hid] += 1
        cur += dt.timedelta(days=1)
    rates = {}
    for hid in habit_ids:
        if total[hid] == 0:
            rates[hid] = 0.0
        else:
            rates[hid] = met[hid] * 100.0 / total[hid]
    return rates

def weekly_summary_logic(data: RootData, week_end: dt.date) -> Dict[str, Any]:
    week_start = week_end - dt.timedelta(days=6)
    rates = completion_for_range(data, week_start, week_end)
    active_ids = [h.id for h in data.habits if h.is_active]
    overall = 0.0
    if active_ids:
        overall = sum(rates.get(hid, 0.0) for hid in active_ids) / len(active_ids)
    sorted_habits = sorted(active_ids, key=lambda hid: rates.get(hid, 0.0), reverse=True)
    top = sorted_habits[:2]
    hmap = get_habit_map(data.habits)
    day_map = get_entry_map(data.entries)
    total_mood_good = []
    total_mood_bad = []
    total_energy_good = []
    total_energy_bad = []
    cur = week_start
    while cur <= week_end:
        ds = cur.isoformat()
        entry = day_map.get(ds)
        if not entry:
            cur += dt.timedelta(days=1)
            continue
        active_day = [h for h in data.habits if h.is_active]
        if not active_day:
            cur += dt.timedelta(days=1)
            continue
        rmap = {r.habit_id: r for r in entry.habit_results}
        met_count = 0
        for h in active_day:
            r = rmap.get(h.id)
            if not r:
                continue
            ok, _ = habit_target_met(h, r.value)
            if ok:
                met_count += 1
        ratio = met_count / max(1, len(active_day))
        if entry.mood is not None:
            if ratio >= 0.7:
                total_mood_good.append(entry.mood)
            else:
                total_mood_bad.append(entry.mood)
        if entry.energy_level is not None:
            if ratio >= 0.7:
                total_energy_good.append(entry.energy_level)
            else:
                total_energy_bad.append(entry.energy_level)
        cur += dt.timedelta(days=1)
    insights = []
    def avg(lst):
        return sum(lst) / len(lst) if lst else None
    mg, mb = avg(total_mood_good), avg(total_mood_bad)
    eg, eb = avg(total_energy_good), avg(total_energy_bad)
    if mg is not None and mb is not None:
        insights.append(
            f"On days you met ≥70% of targets, your average mood was {mg:.1f} vs {mb:.1f} on other days."
        )
    if eg is not None and eb is not None:
        insights.append(
            f"On days you met ≥70% of targets, your average energy was {eg:.1f} vs {eb:.1f} on other days."
        )
    streaks = compute_streaks(data)
    for hid in active_ids:
        if streaks[hid]["current"] >= 3:
            insights.append(
                f"You completed '{hmap[hid].name}' {streaks[hid]['current']} days in a row."
            )
            break
    suggestions = []
    for h in data.habits:
        if not h.is_active:
            continue
        r = rates.get(h.id, 0.0)
        if r < 30.0:
            suggestions.append(
                f"Consider lowering target for '{h.name}' (completion {r:.0f}%)."
            )
            break
    return {
        "week_start": week_start,
        "week_end": week_end,
        "overall": overall,
        "rates": rates,
        "top": top,
        "insights": insights,
        "suggestions": suggestions,
    }

# ---------- UI Helpers ----------

class Theme:
    def __init__(self, mode: str, no_color: bool, high_contrast: bool):
        self.mode = mode
        self.no_color = no_color
        self.high_contrast = high_contrast
        self._set_codes()

    def _set_codes(self):
        if self.no_color:
            self.RESET = ""
            self.BOLD = ""
            self.UNDER = ""
            self.HEADER = ""
            self.ACCENT = ""
            self.GOOD = ""
            self.BAD = ""
            self.MUTED = ""
            return
        self.RESET = "\033[0m"
        self.BOLD = "\033[1m"
        self.UNDER = "\033[4m"
        if self.high_contrast:
            self.HEADER = self.BOLD + self.UNDER
            self.ACCENT = self.BOLD
            self.GOOD = self.BOLD
            self.BAD = self.UNDER
            self.MUTED = ""
            return
        if self.mode == "dark":
            self.HEADER = "\033[95m"
            self.ACCENT = "\033[96m"
            self.GOOD = "\033[92m"
            self.BAD = "\033[91m"
            self.MUTED = "\033[90m"
        else:
            self.HEADER = "\033[94m"
            self.ACCENT = "\033[36m"
            self.GOOD = "\033[32m"
            self.BAD = "\033[31m"
            self.MUTED = "\033[90m"

    def h(self, s: str) -> str:
        return f"{self.HEADER}{s}{self.RESET}"

    def a(self, s: str) -> str:
        return f"{self.ACCENT}{s}{self.RESET}"

    def good(self, s: str) -> str:
        return f"{self.GOOD}{s}{self.RESET}"

    def bad(self, s: str) -> str:
        return f"{self.BAD}{s}{self.RESET}"

    def muted(self, s: str) -> str:
        return f"{self.MUTED}{s}{self.RESET}"

    def bold(self, s: str) -> str:
        return f"{self.BOLD}{s}{self.RESET}"

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def pause(msg: str = "Press Enter to continue..."):
    input(msg)

def prompt_choice(prompt: str, options: List[str], allow_empty=False) -> str:
    while True:
        ans = input(prompt).strip()
        if ans == "" and allow_empty:
            return ""
        if ans in options:
            return ans
        print(f"Please enter one of: {', '.join(options)}")

def prompt_int(prompt: str, min_v: Optional[int] = None, max_v: Optional[int] = None, allow_empty=False) -> Optional[int]:
    while True:
        ans = input(prompt).strip()
        if ans == "" and allow_empty:
            return None
        try:
            v = int(ans)
        except ValueError:
            print("Enter a number.")
            continue
        if min_v is not None and v < min_v:
            print(f"Minimum is {min_v}.")
            continue
        if max_v is not None and v > max_v:
            print(f"Maximum is {max_v}.")
            continue
        return v

def prompt_float(prompt: str, allow_empty=False) -> Optional[float]:
    while True:
        ans = input(prompt).strip()
        if ans == "" and allow_empty:
            return None
        try:
            return float(ans)
        except ValueError:
            print("Enter a number (e.g., 3 or 2.5).")

def wrap(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width))

def input_time(prompt: str, allow_empty=False) -> Optional[str]:
    while True:
        s = input(prompt).strip()
        if s == "" and allow_empty:
            return None
        t = parse_time_str(s)
        if t:
            return f"{t.hour:02d}:{t.minute:02d}"
        print("Use HH:MM (24h), e.g., 08:30 or 19:00.")

# ---------- Screens ----------

HELP_GLOBAL = "Global: q=back/quit, h=help, ?=info"

def show_help(theme: Theme):
    clear_screen()
    print(theme.h("Keyboard help"))
    print()
    print("Navigation:")
    print("  - Enter numbers or first letters shown in menus.")
    print("  - q: Go back / quit from sub-screens.")
    print("  - h: This help.")
    print("  - ?: Short description of current screen.")
    print()
    print("Extras:")
    print("  - In check-in, '.' copies yesterday's values when offered.")
    print()
    pause()

def main_menu_info():
    return "Main menu: choose daily check-in, dashboard, habits, weekly summary, settings, or export."

def checkin_info():
    return "Today’s check-in: log your active habits plus optional energy, mood, and a short reflection."

def dashboard_info():
    return "Dashboard: shows last 7 days grid plus per-habit streaks and completion rates."

def edit_habits_info():
    return "Edit habits: add, rename, adjust targets, activate/deactivate, or delete habits."

def weekly_summary_info():
    return "Weekly summary: adherence score, top habits, and simple insights for a 7-day span."

def settings_info():
    return "Settings: manage your name, theme, reminder time, dashboard range, and data reset."

def export_info():
    return "Export: plain-text report for a date range, shown on screen or saved to a file."

def handle_globals(cmd: str, theme: Theme, info_fn) -> Optional[str]:
    if cmd.lower() == "h":
        show_help(theme)
        return "continue"
    if cmd == "?":
        clear_screen()
        print(info_fn())
        print()
        print(HELP_GLOBAL)
        print()
        pause()
        return "continue"
    if cmd.lower() == "q":
        return "back"
    return None

def today_checkin_screen(data: RootData, theme: Theme):
    while True:
        clear_screen()
        print(theme.h("Today’s check-in"))
        print()
        today = today_str()
        entry = get_or_create_entry(data, today)
        hmap = get_habit_map(data.habits)
        active = [h for h in data.habits if h.is_active]
        entries_map = {r.habit_id: r for r in entry.habit_results}
        day_map = get_entry_map(data.entries)
        yesterday = (dt.date.fromisoformat(today) - dt.timedelta(days=1)).isoformat()
        y_entry = day_map.get(yesterday)
        y_res = {r.habit_id: r for r in y_entry.habit_results} if y_entry else {}
        for h in active:
            prev_value = entries_map.get(h.id).value if h.id in entries_map else None
            y_value = y_res.get(h.id).value if h.id in y_res else None
            label = f"- {h.name} [{h.target_type}"
            if h.target_value is not None:
                label += f" target={h.target_value}]"
            else:
                label += "]"
            print(theme.bold(label))
            default = prev_value
            while True:
                if h.target_type == "boolean":
                    hint = ""
                    if isinstance(default, bool):
                        hint = f" [Y/n] default={'Y' if default else 'N'}"
                    ans = input(f"  Did you complete it? Y/N{hint} ('.' same as yesterday): ").strip()
                    if ans == "." and y_value is not None:
                        val = bool(y_value)
                        break
                    if ans == "" and isinstance(default, bool):
                        val = default
                        break
                    if ans.lower() in ("y", "yes"):
                        val = True
                        break
                    if ans.lower() in ("n", "no"):
                        val = False
                        break
                    if (g := handle_globals(ans, theme, checkin_info)) == "back":
                        return
                    if g == "continue":
                        continue
                    print("Enter Y or N, '.' for same as yesterday, or globals (h, ?, q).")
                else:
                    hint = f" (default={default})" if default not in (None, "") else ""
                    ans = input(f"  Enter value{hint} ('.' same as yesterday): ").strip()
                    if ans == "." and y_value is not None:
                        val = y_value
                        break
                    if ans == "" and default not in (None, ""):
                        val = default
                        break
                    try:
                        val = float(ans)
                        break
                    except ValueError:
                        if (g := handle_globals(ans, theme, checkin_info)) == "back":
                            return
                        if g == "continue":
                            continue
                        print("Enter a number, '.' for same as yesterday, or globals (h, ?, q).")
            if h.id in entries_map:
                entries_map[h.id].value = val
            else:
                entry.habit_results.append(DailyHabitResult(habit_id=h.id, value=val))
        print()
        entry.energy_level = prompt_int("Energy level (1–5, Enter to skip): ", 1, 5, allow_empty=True)
        entry.mood = prompt_int("Mood (1–5, Enter to skip): ", 1, 5, allow_empty=True)
        entry.reflection = input("One sentence reflection about today (optional): ").strip() or None
        streaks = compute_streaks(data)
        print()
        print(theme.h("Summary"))
        for h in active:
            rmap = {r.habit_id: r for r in entry.habit_results}
            v = rmap[h.id].value if h.id in rmap else None
            met, partial = habit_target_met(h, v)
            mark = "."
            if met:
                mark = theme.good("✓")
            elif partial:
                mark = "~"
            else:
                mark = theme.bad("✗")
            st = streaks[h.id]["current"]
            print(f"{mark} {h.name} (streak {st})")
        print()
        pause()
        return

def dashboard_screen(data: RootData, theme: Theme):
    while True:
        clear_screen()
        print(theme.h("Dashboard – last 7 days"))
        print()
        if not data.habits:
            print("No habits defined yet.")
            print()
            print(HELP_GLOBAL)
            print()
            cmd = input("Enter to go back, or h/?/q: ").strip()
            if handle_globals(cmd, theme, dashboard_info) == "back":
                return
            continue
        today = dt.date.today()
        dates = date_range(today, 7)
        habit_indices = [i for i, h in enumerate(data.habits) if h.is_active]
        if not habit_indices:
            print("No active habits. Activate or create some in 'Edit habits'.")
            print()
            print(HELP_GLOBAL)
            print()
            cmd = input("Enter to go back, or h/?/q: ").strip()
            if handle_globals(cmd, theme, dashboard_info) == "back":
                return
            continue
        day_map = get_entry_map(data.entries)
        hmap = get_habit_map(data.habits)
        headers = ["Date"]
        short = []
        for idx in habit_indices:
            h = data.habits[idx]
            s = (h.name[:3]).upper()
            short.append(s)
            headers.append(f"{idx+1}:{s}")
        print("  ".join(headers))
        for d in dates:
            row = [d[5:]]
            entry = day_map.get(d)
            rmap = {r.habit_id: r for r in entry.habit_results} if entry else {}
            for idx in habit_indices:
                h = data.habits[idx]
                r = rmap.get(h.id)
                if not r:
                    row.append(".")
                    continue
                met, partial = habit_target_met(h, r.value)
                if met:
                    row.append(theme.good("✓"))
                elif partial:
                    row.append("~")
                else:
                    row.append(theme.bad("✗"))
            print("  ".join(row))
        print()
        streaks = compute_streaks(data)
        end = today
        start7 = end - dt.timedelta(days=6)
        rates7 = completion_for_range(data, start7, end)
        start30 = end - dt.timedelta(days=29)
        rates30 = completion_for_range(data, start30, end)
        print(theme.h("Per-habit stats"))
        for idx in habit_indices:
            h = data.habits[idx]
            st = streaks[h.id]
            r7 = rates7.get(h.id, 0.0)
            r30 = rates30.get(h.id, 0.0)
            print(
                f"{idx+1}) {h.name}: streak {st['current']} (best {st['best']}), "
                f"{r7:.0f}% last 7d, {r30:.0f}% last 30d"
            )
        print()
        print("Enter habit number for details, or press Enter to go back.")
        print(HELP_GLOBAL)
        cmd = input("> ").strip()
        gl = handle_globals(cmd, theme, dashboard_info)
        if gl == "back":
            return
        if gl == "continue":
            continue
        if cmd == "":
            return
        try:
            idx = int(cmd) - 1
        except ValueError:
            print("Enter a habit number, or use q/h/?.")
            pause()
            continue
        if idx < 0 or idx >= len(data.habits):
            print("Invalid habit number.")
            pause()
            continue
        habit_detail_screen(data, data.habits[idx], theme)

def habit_detail_screen(data: RootData, habit: Habit, theme: Theme):
    while True:
        clear_screen()
        print(theme.h(f"Habit detail – {habit.name}"))
        print()
        print(f"Category: {habit.category}, Target: {habit.target_type} {habit.target_value or ''}")
        print()
        today = dt.date.today()
        dates = date_range(today, 14)
        day_map = get_entry_map(data.entries)
        print("Date   Value  Status")
        for d in dates:
            entry = day_map.get(d)
            rmap = {r.habit_id: r for r in entry.habit_results} if entry else {}
            r = rmap.get(habit.id)
            if not r:
                val = ""
                mark = "."
            else:
                val = r.value
                met, partial = habit_target_met(habit, val)
                if met:
                    mark = theme.good("✓")
                elif partial:
                    mark = "~"
                else:
                    mark = theme.bad("✗")
            print(f"{d[5:]}  {str(val):6} {mark}")
        print()
        print(HELP_GLOBAL)
        cmd = input("Enter to go back, or h/?/q: ").strip()
        gl = handle_globals(cmd, theme, dashboard_info)
        if gl == "back" or cmd == "":
            return

def edit_habits_screen(data: RootData, theme: Theme):
    while True:
        clear_screen()
        print(theme.h("Edit habits"))
        print()
        if data.habits:
            for i, h in enumerate(data.habits, 1):
                status = "active" if h.is_active else "inactive"
                print(
                    f"{i}) {h.name} [{h.category}, {h.target_type}, "
                    f"target={h.target_value or '-'}] ({status})"
                )
        else:
            print("No habits yet.")
        print()
        print("A) Add new habit")
        print("E) Edit habit")
        print("T) Toggle activate/deactivate")
        print("D) Delete habit")
        print("Enter) Back")
        print()
        print(HELP_GLOBAL)
        cmd = input("> ").strip()
        gl = handle_globals(cmd, theme, edit_habits_info)
        if gl == "back" or cmd == "":
            return
        if gl == "continue":
            continue
        c = cmd.lower()
        if c == "a":
            add_habit_wizard(data, theme)
        elif c == "e":
            if not data.habits:
                pause("No habits to edit. Press Enter...")
                continue
            idx = prompt_int("Habit number to edit: ", 1, len(data.habits))
            if idx is None:
                continue
            edit_habit(data, data.habits[idx - 1], theme)
        elif c == "t":
            if not data.habits:
                pause("No habits to toggle. Press Enter...")
                continue
            idx = prompt_int("Habit number to toggle active/inactive: ", 1, len(data.habits))
            if idx is None:
                continue
            h = data.habits[idx - 1]
            h.is_active = not h.is_active
        elif c == "d":
            if not data.habits:
                pause("No habits to delete. Press Enter...")
                continue
            idx = prompt_int("Habit number to delete: ", 1, len(data.habits))
            if idx is None:
                continue
            h = data.habits[idx - 1]
            print(f"Delete '{h.name}'? This keeps historical daily data but removes the habit definition.")
            sure = input("Type 'DELETE' to confirm, anything else to cancel: ").strip()
            if sure == "DELETE":
                del data.habits[idx - 1]
        else:
            print("Unknown command.")
            pause()

def add_habit_wizard(data: RootData, theme: Theme):
    clear_screen()
    print(theme.h("Add new habit"))
    print()
    name = ""
    while not name:
        name = input("Name: ").strip()
        if not name:
            print("Name cannot be empty.")
    print("Category:")
    for i, c in enumerate(CATEGORIES, 1):
        print(f"{i}) {c}")
    while True:
        idx = prompt_int("Choose category number: ", 1, len(CATEGORIES))
        if idx is not None:
            category = CATEGORIES[idx - 1]
            break
    print("Target type:")
    for i, t in enumerate(TARGET_TYPES, 1):
        print(f"{i}) {t}")
    while True:
        idx = prompt_int("Choose target type: ", 1, len(TARGET_TYPES))
        if idx is not None:
            target_type = TARGET_TYPES[idx - 1]
            break
    target_value = None
    if target_type != "boolean":
        target_value = prompt_float("Target value (number, e.g., 5): ")
    base_id = "".join(ch.lower() for ch in name if ch.isalnum() or ch == " ").strip().replace(" ", "_")
    if not base_id:
        base_id = f"habit_{len(data.habits)+1}"
    hid = base_id
    existing = {h.id for h in data.habits}
    suffix = 1
    while hid in existing:
        hid = f"{base_id}_{suffix}"
        suffix += 1
    data.habits.append(
        Habit(
            id=hid,
            name=name,
            category=category,
            target_type=target_type,
            target_value=target_value,
            is_active=True,
        )
    )
    print("Habit added.")
    pause()

def edit_habit(data: RootData, habit: Habit, theme: Theme):
    while True:
        clear_screen()
        print(theme.h(f"Edit habit – {habit.name}"))
        print()
        print(f"1) Name: {habit.name}")
        print(f"2) Category: {habit.category}")
        print(f"3) Target type: {habit.target_type}")
        print(f"4) Target value: {habit.target_value}")
        print("Enter) Back")
        print()
        print(HELP_GLOBAL)
        cmd = input("> ").strip()
        gl = handle_globals(cmd, theme, edit_habits_info)
        if gl == "back" or cmd == "":
            return
        if gl == "continue":
            continue
        if cmd == "1":
            new_name = input("New name (blank to keep): ").strip()
            if new_name:
                habit.name = new_name
        elif cmd == "2":
            print("Categories:")
            for i, c in enumerate(CATEGORIES, 1):
                print(f"{i}) {c}")
            idx = prompt_int("Choose category: ", 1, len(CATEGORIES), allow_empty=True)
            if idx is not None:
                habit.category = CATEGORIES[idx - 1]
        elif cmd == "3":
            print("Target types:")
            for i, t in enumerate(TARGET_TYPES, 1):
                print(f"{i}) {t}")
            idx = prompt_int("Choose target type: ", 1, len(TARGET_TYPES), allow_empty=True)
            if idx is not None:
                habit.target_type = TARGET_TYPES[idx - 1]
                if habit.target_type == "boolean":
                    habit.target_value = None
        elif cmd == "4":
            if habit.target_type == "boolean":
                print("Boolean habits do not use numeric target.")
                pause()
            else:
                habit.target_value = prompt_float("New target value: ", allow_empty=True)
        else:
            print("Unknown choice.")
            pause()

def weekly_summary_screen(data: RootData, theme: Theme):
    if not data.entries:
        clear_screen()
        print(theme.h("Weekly summary"))
        print()
        print("No entries yet.")
        print()
        pause()
        return
    last_date = dt.date.fromisoformat(data.entries[-1].date)
    offset = 0
    while True:
        week_end = last_date - dt.timedelta(days=7 * offset)
        ws = weekly_summary_logic(data, week_end)
        clear_screen()
        print(
            theme.h(
                f"Weekly summary {ws['week_start'].isoformat()} – {ws['week_end'].isoformat()}"
            )
        )
        print()
        print(f"Overall adherence: {ws['overall']:.0f}%")
        hmap = get_habit_map(data.habits)
        if ws["top"]:
            print("Top habits by consistency:")
            for hid in ws["top"]:
                print(f"  - {hmap[hid].name}: {ws['rates'][hid]:.0f}%")
        else:
            print("No active habits.")
        print()
        if ws["insights"]:
            print(theme.h("Insights"))
            for ins in ws["insights"]:
                print(f"- {wrap(ins, 76)}")
            print()
        if ws["suggestions"]:
            print(theme.h("Suggestion"))
            for s in ws["suggestions"]:
                print(f"- {wrap(s, 76)}")
            print()
        print("n) Next (later) week    p) Previous (earlier) week    Enter) Back")
        print(HELP_GLOBAL)
        cmd = input("> ").strip().lower()
        gl = handle_globals(cmd, theme, weekly_summary_info)
        if gl == "back" or cmd == "":
            return
        if gl == "continue":
            continue
        if cmd == "n":
            if offset > 0:
                offset -= 1
        elif cmd == "p":
            offset += 1
        else:
            print("Use n/p, Enter, or globals.")
            pause()

def settings_screen(data: RootData, theme: Theme, data_path: Path):
    while True:
        clear_screen()
        p = data.profile
        print(theme.h("Settings"))
        print()
        print(f"1) Display name: {p.display_name}")
        print(f"2) Preferred theme: {p.preferred_theme}")
        print(f"3) Daily check-in reminder time: {p.daily_checkin_time or 'disabled'}")
        print(f"4) Dashboard default timeframe (days): {p.dashboard_default_days}")
        print(f"5) High contrast mode: {'on' if p.high_contrast else 'off'}")
        print("6) Show data file path")
        print("7) Reset all data")
        print("Enter) Back")
        print()
        print(HELP_GLOBAL)
        cmd = input("> ").strip()
        gl = handle_globals(cmd, theme, settings_info)
        if gl == "back" or cmd == "":
            return
        if gl == "continue":
            continue
        if cmd == "1":
            name = input("Display name: ").strip()
            if name:
                p.display_name = name
        elif cmd == "2":
            print("Theme options: light, dark, auto")
            t = prompt_choice("Preferred theme: ", THEMES)
            p.preferred_theme = t
        elif cmd == "3":
            t = input_time("Reminder time HH:MM (empty to disable): ", allow_empty=True)
            p.daily_checkin_time = t
        elif cmd == "4":
            days = prompt_int("Dashboard range in days (7/14/30): ", 1, 365)
            if days is not None:
                p.dashboard_default_days = days
        elif cmd == "5":
            p.high_contrast = not p.high_contrast
            theme.high_contrast = p.high_contrast
            theme._set_codes()
        elif cmd == "6":
            print(f"Data file: {data_path}")
            print()
            pause()
        elif cmd == "7":
            print("Reset ALL data? This removes profile, habits, and entries.")
            sure = input("Type 'DELETE ALL' to confirm: ").strip()
            if sure == "DELETE ALL":
                new = default_data()
                data.profile = new.profile
                data.habits = new.habits
                data.entries = new.entries
                data.state = new.state
                print("All data reset.")
                pause()
        else:
            print("Unknown choice.")
            pause()

def export_screen(data: RootData, theme: Theme):
    clear_screen()
    print(theme.h("Export / Print view"))
    print()
    if not data.entries:
        print("No data to export yet.")
        print()
        pause()
        return
    last_date = dt.date.fromisoformat(data.entries[-1].date)
    default_start = last_date - dt.timedelta(days=29)
    print(f"Default range: {default_start.isoformat()} to {last_date.isoformat()}")
    s = input("Start date (YYYY-MM-DD, Enter for default): ").strip()
    if s:
        try:
            start = dt.date.fromisoformat(s)
        except ValueError:
            print("Invalid start date.")
            pause()
            return
    else:
        start = default_start
    e = input("End date (YYYY-MM-DD, Enter for default): ").strip()
    if e:
        try:
            end = dt.date.fromisoformat(e)
        except ValueError:
            print("Invalid end date.")
            pause()
            return
    else:
        end = last_date
    if end < start:
        print("End date must be after start date.")
        pause()
        return
    report = build_export_report(data, start, end)
    print()
    print("1) Show on screen")
    print("2) Save to file")
    choice = prompt_choice("> ", ["1", "2"])
    if choice == "1":
        clear_screen()
        print(report)
        print()
        pause("End of report. Press Enter...")
    else:
        path = input("Output file path (Enter for 'micro_habits_export.txt'): ").strip()
        if not path:
            path = "micro_habits_export.txt"
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"Saved to {path}")
        except Exception as ex:
            print(f"Failed to save: {ex}")
        pause()

def build_export_report(data: RootData, start: dt.date, end: dt.date) -> str:
    width = 80
    lines = []
    lines.append(APP_NAME)
    lines.append(f"Export range: {start.isoformat()} to {end.isoformat()}")
    lines.append("-" * width)
    hmap = get_habit_map(data.habits)
    day_map = get_entry_map(data.entries)
    cur = start
    while cur <= end:
        ds = cur.isoformat()
        lines.append(f"Date: {ds}")
        entry = day_map.get(ds)
        if not entry:
            lines.append("  (no entry)")
            lines.append("")
            cur += dt.timedelta(days=1)
            continue
        rmap = {r.habit_id: r for r in entry.habit_results}
        for h in data.habits:
            r = rmap.get(h.id)
            if not r:
                status = "."
                val = ""
            else:
                val = r.value
                met, partial = habit_target_met(h, val)
                if met:
                    status = "✓"
                elif partial:
                    status = "~"
                else:
                    status = "✗"
            line = f"  [{status}] {h.name}"
            if val not in ("", None):
                line += f" – {val}"
            lines.append(wrap(line, width))
        if entry.energy_level is not None:
            lines.append(f"  Energy: {entry.energy_level}")
        if entry.mood is not None:
            lines.append(f"  Mood: {entry.mood}")
        if entry.reflection:
            lines.append("  Reflection:")
            for w in textwrap.wrap(entry.reflection, width=width - 4):
                lines.append(f"    {w}")
        lines.append("")
        cur += dt.timedelta(days=1)
    lines.append("=" * width)
    cur = start
    while cur <= end:
        ws = weekly_summary_logic(data, cur)
        lines.append(
            f"Week {ws['week_start'].isoformat()} to {ws['week_end'].isoformat()}: "
            f"overall {ws['overall']:.0f}%"
        )
        cur = ws["week_end"] + dt.timedelta(days=1)
        if cur > end:
            break
    lines.append("=" * width)
    moods = []
    energies = []
    cur = start
    while cur <= end:
        ds = cur.isoformat()
        entry = day_map.get(ds)
        if entry:
            if entry.mood is not None:
                moods.append(entry.mood)
            if entry.energy_level is not None:
                energies.append(entry.energy_level)
        cur += dt.timedelta(days=1)
    if moods:
        lines.append(f"Average mood: {sum(moods)/len(moods):.2f}")
    if energies:
        lines.append(f"Average energy: {sum(energies)/len(energies):.2f}")
    return "\n".join(lines)

# ---------- Reminder ----------

def maybe_show_reminder(data: RootData, theme: Theme, auto_today: bool) -> bool:
    p = data.profile
    if not p.daily_checkin_time:
        return False
    now = dt.datetime.now()
    t = parse_time_str(p.daily_checkin_time)
    if not t:
        return False
    reminder_time = now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
    if now <= reminder_time + dt.timedelta(hours=1):
        return False
    day_map = get_entry_map(data.entries)
    if today_str() in day_map and day_map[today_str()].habit_results:
        return False
    clear_screen()
    print(theme.h("Gentle reminder"))
    print()
    print("You haven’t checked in today.")
    ans = input("Start a quick check-in now? [Y/n]: ").strip().lower()
    if ans in ("", "y", "yes"):
        today_checkin_screen(data, theme)
        return True
    return False

# ---------- Main Menu / Entry ----------

def run_main_loop(data: RootData, theme: Theme, data_path: Path, auto_today: bool):
    if auto_today:
        today_checkin_screen(data, theme)
        return
    reminder_shown = maybe_show_reminder(data, theme, auto_today)
    while True:
        clear_screen()
        print(theme.h(APP_NAME))
        print()
        print("1) Today’s check-in")
        print("2) View dashboard")
        print("3) Edit habits")
        print("4) Weekly summary")
        print("5) Settings")
        print("6) Export / Print view")
        print("0) Quit")
        print()
        print("Shortcuts: T,D,E,W,S,X,Q")
        print(HELP_GLOBAL)
        print()
        cmd = input("> ").strip()
        if cmd == "":
            continue
        if cmd == "0" or cmd.lower() == "q":
            return
        if cmd.lower() == "t" or cmd == "1":
            today_checkin_screen(data, theme)
        elif cmd.lower() == "d" or cmd == "2":
            dashboard_screen(data, theme)
        elif cmd.lower() == "e" or cmd == "3":
            edit_habits_screen(data, theme)
        elif cmd.lower() == "w" or cmd == "4":
            weekly_summary_screen(data, theme)
        elif cmd.lower() == "s" or cmd == "5":
            settings_screen(data, theme, data_path)
        elif cmd.lower() == "x" or cmd == "6":
            export_screen(data, theme)
        elif cmd.lower() == "h":
            show_help(theme)
        elif cmd == "?":
            clear_screen()
            print(main_menu_info())
            print()
            print(HELP_GLOBAL)
            print()
            pause()
        else:
            print("Unknown choice. Use number or shortcut.")
            pause()

def parse_args():
    p = argparse.ArgumentParser(description="Daily Micro-Habits Coach (CLI)")
    p.add_argument("--theme", choices=["light", "dark"], help="Override theme for this run")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    p.add_argument("--today", action="store_true", help="Jump directly into today’s check-in")
    return p.parse_args()

def main():
    args = parse_args()
    data_path = get_data_path()
    data = load_data(data_path)
    data.state.last_opened = today_str()
    theme_mode = select_theme(data.profile, args.theme)
    theme = Theme(theme_mode, args.no_color, data.profile.high_contrast)
    try:
        run_main_loop(data, theme, data_path, auto_today=args.today)
    finally:
        save_data(data_path, data)

if __name__ == "__main__":
    main()