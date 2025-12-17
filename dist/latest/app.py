# Auto-generated via Perplexity on 2025-12-17T01:25:53.835377Z
#!/usr/bin/env python3
"""
micro_arcade.py — Single-file micro-arcade hub (standard library only)

Features:
- Three terminal micro-games: Reaction Tap, Grid Dodge, Memory Pairs
- curses-powered TUI when available; fallback console mode otherwise
- Settings & high scores persisted atomically to JSON in XDG-config or ~/.config
- Keyboard-first accessibility; arrow and alternative keys supported
- --report prints last-played summary; --demo runs automated short runs; --no-curses forces fallback
- Single entrypoint main() guarded by if __name__ == "__main__"

Dependencies: Python 3.8+ standard library only.
"""
from __future__ import annotations
import sys
import os
import time
import json
import random
import argparse
import tempfile
import shutil
import pathlib
import datetime
import threading

# Optional imports handled at runtime
try:
    import curses
    from curses import wrapper
    HAS_CURSES = True
except Exception:
    curses = None
    HAS_CURSES = False

# Windows msvcrt for fallback key reading
try:
    import msvcrt
    HAS_MSVCRT = True
except Exception:
    msvcrt = None
    HAS_MSVCRT = False

APP_NAME = "micro_arcade"
DEFAULT_CONFIG = {
    "settings": {
        "beep": True,
        "theme": "auto",  # auto / light / dark
        "difficulty": "normal",  # easy / normal / hard (used per-game)
        "grid_size": [8, 6],  # default Grid Dodge width x height
        "mem_size": [4, 4],  # Memory pairs grid
        "tick_ms": 200
    },
    "scores": {
        "reaction_tap": {},
        "grid_dodge": {},
        "memory_pairs": {}
    },
    "last_result": None
}

# --- Persistence helpers (atomic JSON writes) ---
def config_path() -> pathlib.Path:
    xdg = os.environ.get("XDG_CONFIG_HOME") or ""
    if xdg:
        base = pathlib.Path(xdg)
    else:
        base = pathlib.Path.home() / ".config"
    cfgdir = base / APP_NAME
    cfgdir.mkdir(parents=True, exist_ok=True)
    return cfgdir / "config.json"

def atomic_write_json(path: pathlib.Path, data):
    fd, tmp = tempfile.mkstemp(prefix=path.name, dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        # atomic rename
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass

def load_config() -> dict:
    p = config_path()
    if p.exists():
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # simple schema fill
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(data)
            return cfg
        except Exception:
            return DEFAULT_CONFIG.copy()
    else:
        return DEFAULT_CONFIG.copy()

def save_config(cfg: dict):
    try:
        atomic_write_json(config_path(), cfg)
    except Exception as e:
        # Last ditch: try simple write
        try:
            with open(config_path(), "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

# --- Utility: simple beep ---
def beep(enabled=True):
    if not enabled:
        return
    # Terminal bell
    sys.stdout.write("\a")
    sys.stdout.flush()

# --- Terminal abstraction layer ---
class Term:
    def __init__(self, use_curses=True, force_no_curses=False):
        self.use_curses = use_curses and HAS_CURSES and not force_no_curses
        self.lock = threading.Lock()
        self.screen = None
        self.height = 24
        self.width = 80
        self.color = True if HAS_CURSES else False
        self._std_mode = not self.use_curses
        self._running = False
        if self.use_curses:
            # will initialize later in context
            pass

    def start(self):
        if self.use_curses:
            # curses.wrapper will call main function; we provide init separately
            pass
        else:
            # fallback simple mode: determine size heuristically
            try:
                import shutil as _shutil
                s = _shutil.get_terminal_size()
                self.width, self.height = s.columns, s.lines
            except Exception:
                self.width, self.height = 80, 24

    # Curses-specific helpers (wrapped at runtime)
    def init_curses(self, stdscr):
        self.screen = stdscr
        curses.curs_set(0)
        self.screen.nodelay(False)
        self.screen.keypad(True)
        self.height, self.width = self.screen.getmaxyx()
        self.color = curses.has_colors()
        if self.color:
            curses.start_color()
            curses.use_default_colors()
            # define few color pairs
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)
            curses.init_pair(3, curses.COLOR_RED, -1)
            curses.init_pair(4, curses.COLOR_GREEN, -1)
        self._std_mode = False

    def get_size(self):
        if self.screen:
            h, w = self.screen.getmaxyx()
            return w, h
        return self.width, self.height

    def clear(self):
        if self.use_curses and self.screen:
            self.screen.erase()
        else:
            os.system("cls" if os.name == "nt" else "clear")

    def draw_text(self, y, x, text, attr=None):
        if self.use_curses and self.screen:
            try:
                if attr:
                    self.screen.addstr(y, x, text[:max(0, self.screen.getmaxyx()[1]-x)], attr)
                else:
                    self.screen.addstr(y, x, text)
            except Exception:
                pass
        else:
            # fallback: print with offsets (inefficient)
            print((" " * x) + text)

    def refresh(self):
        if self.use_curses and self.screen:
            try:
                self.screen.refresh()
            except Exception:
                pass

    def getkey(self, timeout=None):
        # return normalized key strings
        if self.use_curses and self.screen:
            if timeout is not None:
                self.screen.nodelay(True)
                start = time.time()
                while True:
                    try:
                        ch = self.screen.get_wch()
                    except Exception:
                        ch = -1
                    if ch != -1:
                        break
                    if (time.time() - start) * 1000 >= timeout:
                        ch = None
                        break
                    time.sleep(0.01)
                self.screen.nodelay(False)
            else:
                try:
                    ch = self.screen.get_wch()
                except Exception:
                    ch = None
            if ch is None:
                return None
            # map special keys
            if isinstance(ch, str):
                return ch
            else:
                # integer key
                if ch == curses.KEY_UP:
                    return "KEY_UP"
                if ch == curses.KEY_DOWN:
                    return "KEY_DOWN"
                if ch == curses.KEY_LEFT:
                    return "KEY_LEFT"
                if ch == curses.KEY_RIGHT:
                    return "KEY_RIGHT"
                return str(ch)
        else:
            # fallback blocking read via msvcrt or input
            if HAS_MSVCRT:
                start = time.time()
                if timeout is not None:
                    end = start + timeout/1000.0
                while True:
                    if msvcrt.kbhit():
                        b = msvcrt.getwch()
                        return b
                    if timeout is not None and time.time() > end:
                        return None
                    time.sleep(0.01)
            else:
                # use input() as last resort (blocking)
                try:
                    return input()
                except KeyboardInterrupt:
                    return "\x03"

    def stop(self):
        if self.use_curses and self.screen:
            try:
                curses.curs_set(1)
            except Exception:
                pass

# --- Small helpers ---
def clamp(n, a, b):
    return max(a, min(b, n))

def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

# --- Simple scoring helpers ---
def record_score(cfg, game_key, result: dict):
    scores = cfg.setdefault("scores", {})
    game_scores = scores.setdefault(game_key, {})
    # For simplicity store best under "best" key, and append last_result separately
    best = game_scores.get("best")
    # compare based on 'better_is_lower' flag if provided
    if best is None:
        game_scores["best"] = result
        result["is_personal_best"] = True
    else:
        better_lower = result.get("better_is_lower", False)
        curv = result.get("score")
        bestv = best.get("score")
        if curv is None:
            # maybe time-based
            curv = result.get("time")
            bestv = best.get("time")
        is_better = False
        if curv is not None and bestv is not None:
            if better_lower:
                is_better = curv < bestv
            else:
                is_better = curv > bestv
        if is_better:
            game_scores["best"] = result
            result["is_personal_best"] = True
        else:
            result["is_personal_best"] = False
    cfg["last_result"] = result
    save_config(cfg)

# --- Launcher UI (curses or fallback) ---
MENU_ITEMS = [
    ("Reaction Tap", "reaction_tap"),
    ("Grid Dodge", "grid_dodge"),
    ("Memory Pairs", "memory_pairs"),
    ("High Scores", "high_scores"),
    ("Settings", "settings"),
    ("Quit", "quit")
]

ASCII_TITLE = [
"  __  __ _             _    _                       ",
" |  \\/  (_)  _ __ ___ | |  / \\   _ __  _ __   _   _ ",
" | |\\/| | | | '_ ` _ \\| | / _ \\ | '__|| '_ \\ | | | |",
" | |  | | | | | | | | | |/ ___ \\| |   | | | || |_| |",
" |_|  |_|_| |_| |_| |_|_/_/   \\_\\_|   |_| |_| \\__,_|",
"                    Micro-Arcade"
]

def draw_menu(term: Term, cfg: dict, sel=0):
    term.clear()
    w, h = term.get_size()
    # render title
    y = 1
    for line in ASCII_TITLE:
        x = max(0, (w - len(line)) // 2)
        term.draw_text(y, x, line)
        y += 1
    y += 1
    # compact menu
    for i, (label, key) in enumerate(MENU_ITEMS):
        marker = "▶ " if i == sel else "  "
        text = f"{marker}{label}"
        x = max(2, (w - 40) // 2)
        term.draw_text(y + i, x, text)
    # footer
    footer = "Use ↑/↓ or j/k to navigate. Enter to select. Esc/Ctrl-C to quit."
    term.draw_text(h - 2, max(0, (w - len(footer)) // 2), footer)
    term.refresh()

# --- Simple UI helpers for prompts ---
def prompt_confirm(term: Term, message: str, timeout=None) -> bool:
    term.clear()
    w, h = term.get_size()
    term.draw_text(h//2 - 1, max(0, (w - len(message))//2), message)
    term.draw_text(h//2 + 1, max(0, (w - 20)//2), "Press y to confirm, any other to cancel")
    term.refresh()
    k = term.getkey(timeout=timeout)
    if not k:
        return False
    if isinstance(k, str) and k.lower().startswith("y"):
        return True
    return False

# --- Games implementations ---

# Reaction Tap
def reaction_tap(term: Term, cfg: dict, autoplay=False) -> dict:
    settings = cfg.get("settings", {})
    beep_on = settings.get("beep", True)
    # intro
    term.clear()
    w, h = term.get_size()
    instructions = [
        "Reaction Tap",
        "Wait for GO! then press any key as fast as you can.",
        "Press Esc to cancel."
    ]
    for i, l in enumerate(instructions):
        term.draw_text(2 + i, max(0, (w - len(l))//2), l)
    term.refresh()
    time.sleep(0.8)
    # countdown
    for s in ("3", "2", "1"):
        term.clear()
        term.draw_text(h//2, max(0, (w - len(s))//2), s)
        term.refresh()
        time.sleep(0.6)
    # random delay then GO!
    delay = random.uniform(0.8, 3.0)
    term.clear()
    term.draw_text(h//2, max(0, (w - 20)//2), "Get ready...")
    term.refresh()
    start_wait = time.time()
    # if autoplay, simulate short reaction
    if autoplay:
        time.sleep(0.2 + random.random()*0.2)
        rt = 0.2 + random.random()*0.2
        result = {"game": "reaction_tap", "time": rt, "score": None, "timestamp": now_iso(), "better_is_lower": True}
        record_score(cfg, "reaction_tap", result)
        return result
    time.sleep(delay)
    term.clear()
    term.draw_text(h//2, max(0, (w - 4)//2), "GO!")
    term.refresh()
    start = time.time()
    # wait for first key
    while True:
        k = term.getkey(timeout=500)
        if k is None:
            continue
        if isinstance(k, str) and k == "\x1b":
            return {"game": "reaction_tap", "time": None, "score": None, "timestamp": now_iso()}
        rt = time.time() - start
        beep(beep_on)
        result = {"game": "reaction_tap", "time": round(rt, 3), "score": None, "timestamp": now_iso(), "better_is_lower": True}
        # display
        term.clear()
        term.draw_text(h//2 - 1, max(0, (w - 20)//2), f"Reaction time: {result['time']}s")
        term.refresh()
        record_score(cfg, "reaction_tap", result)
        time.sleep(1.2)
        return result

# Grid Dodge
class GridDodge:
    def __init__(self, term: Term, cfg: dict, autoplay=False):
        self.term = term
        self.cfg = cfg
        self.settings = cfg.get("settings", {})
        gs = self.settings.get("grid_size", [8,6])
        self.width = gs
        self.height = gs[1]
        # grid clamp to terminal
        tw, th = term.get_size()
        # leave room for borders/instructions
        maxw = max(5, tw - 10)
        maxh = max(5, th - 8)
        self.width = clamp(self.width, 5, maxw)
        self.height = clamp(self.height, 5, maxh)
        self.player_x = self.width // 2
        self.player_y = self.height - 1
        self.hazards = []  # list of (x,y)
        self.tick_ms = max(50, int(self.settings.get("tick_ms", 200)))
        diff = self.settings.get("difficulty", "normal")
        if diff == "easy":
            self.spawn_rate = 0.15
        elif diff == "hard":
            self.spawn_rate = 0.35
        else:
            self.spawn_rate = 0.25
        self.score = 0
        self.running = True
        self.autoplay = autoplay

    def step(self):
        # move hazards down
        new = []
        for x,y in self.hazards:
            ny = y + 1
            if ny >= self.height:
                # passed bottom: increase score
                self.score += 1
            else:
                new.append((x, ny))
        self.hazards = new
        # maybe spawn new hazard at top
        if random.random() < self.spawn_rate:
            self.hazards.append((random.randrange(0, self.width), 0))
        # check collision
        for x,y in self.hazards:
            if x == self.player_x and y == self.player_y:
                self.running = False

    def move_left(self):
        self.player_x = max(0, self.player_x - 1)

    def move_right(self):
        self.player_x = min(self.width - 1, self.player_x + 1)

    def render(self):
        t = self.term
        t.clear()
        w, h = t.get_size()
        base_x = max(0, (w - self.width) // 2)
        base_y = 2
        # draw top info
        t.draw_text(0, 2, f"Grid Dodge — Score: {self.score}")
        t.draw_text(1, 2, "Move with ←/→ or a/d. Survive as long as you can. Esc to quit.")
        # draw grid
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                ch = "."
                for hx, hy in self.hazards:
                    if hx == x and hy == y:
                        ch = "*"
                        break
                if x == self.player_x and y == self.player_y:
                    ch = "@"
                line += ch
            t.draw_text(base_y + y, base_x, line)
        t.refresh()

    def run(self):
        # intro
        self.term.clear()
        w, h = self.term.get_size()
        inst = f"Grid Dodge — {self.width}x{self.height}"
        self.term.draw_text(2, max(0, (w - len(inst))//2), inst)
        self.term.draw_text(4, max(0, (w - 40)//2), "Avoid falling '*' hazards. Press any key to start.")
        self.term.refresh()
        if not self.autoplay:
            self.term.getkey()
        else:
            time.sleep(0.5)
        start = time.time()
        # loop
        last_tick = 0
        while self.running:
            now = time.time()
            if (now - last_tick) * 1000 >= self.tick_ms:
                self.step()
                self.render()
                last_tick = now
            # input handling non-blocking
            k = self.term.getkey(timeout=10)
            if k:
                if isinstance(k, str) and k in ("\x1b", "\x03"):
                    # quit
                    self.running = False
                    break
                if k in ("KEY_LEFT", "h", "a", "A"):
                    self.move_left()
                if k in ("KEY_RIGHT", "l", "d", "D"):
                    self.move_right()
            if self.autoplay:
                # simple autopilot: move randomly to avoid hazards
                if random.random() < 0.3:
                    if random.random() < 0.5:
                        self.move_left()
                    else:
                        self.move_right()
            time.sleep(0.01)
        elapsed = time.time() - start
        result = {"game": "grid_dodge", "time": round(elapsed, 2), "score": self.score, "timestamp": now_iso(), "better_is_lower": False}
        record_score(self.cfg, "grid_dodge", result)
        return result

def grid_dodge(term: Term, cfg: dict, autoplay=False):
    gd = GridDodge(term, cfg, autoplay=autoplay)
    return gd.run()

# Memory Pairs
class MemoryPairs:
    def __init__(self, term: Term, cfg: dict, autoplay=False):
        self.term = term
        self.cfg = cfg
        self.settings = cfg.get("settings", {})
        ms = self.settings.get("mem_size", [4,4])
        self.cols = clamp(ms, 2, 8)
        self.rows = clamp(ms[1], 2, 6)
        # clamp to terminal
        tw, th = term.get_size()
        max_cols = max(2, (tw - 10) // 3)
        max_rows = max(2, (th - 8))
        self.cols = clamp(self.cols, 2, max_cols)
        self.rows = clamp(self.rows, 2, max_rows)
        total = self.cols * self.rows
        if total %2 != 0:
            total -= 1
        self.total = total
        # create pairs
        letters = [chr(ord('A') + i) for i in range(26)]
        needed_pairs = total // 2
        pool = letters[:needed_pairs]
        cards = pool + pool
        random.shuffle(cards)
        # grid indexable 0..total-1
        self.cards = cards
        self.revealed = [False]*total
        self.matched = [False]*total
        self.moves = 0
        self.start_time = None
        self.autoplay = autoplay

    def render(self):
        t = self.term
        t.clear()
        w, h = t.get_size()
        t.draw_text(0, 2, f"Memory Pairs — Moves: {self.moves}")
        t.draw_text(1, 2, "Select cards by number (1..N) or use arrows + Enter. Esc to quit.")
        base_x = 4
        base_y = 3
        idx = 0
        for r in range(self.rows):
            line = ""
            for c in range(self.cols):
                if idx >= self.total:
                    line += "   "
                else:
                    if self.matched[idx] or self.revealed[idx]:
                        line += f" {self.cards[idx]} "
                    else:
                        line += f"[{(idx+1)%100:2d}]"
                idx += 1
            t.draw_text(base_y + r, base_x, line)
        t.refresh()

    def run(self):
        self.start_time = time.time()
        first_sel = None
        while True:
            self.render()
            # check win
            if all(self.matched[:self.total]):
                break
            if self.autoplay:
                # pick random unrevealed
                choices = [i for i in range(self.total) if not self.matched[i]]
                if not choices:
                    break
                pick = random.choice(choices)
                time.sleep(0.2)
                if first_sel is None:
                    first_sel = pick
                    self.revealed[pick] = True
                    self.moves += 1
                    time.sleep(0.2)
                else:
                    self.revealed[pick] = True
                    self.moves += 1
                    time.sleep(0.2)
                    # check
                    if self.cards[first_sel] == self.cards[pick]:
                        self.matched[first_sel] = True
                        self.matched[pick] = True
                    else:
                        self.revealed[first_sel] = False
                        self.revealed[pick] = False
                    first_sel = None
                continue
            k = self.term.getkey()
            if not k:
                continue
            if isinstance(k, str) and k == "\x1b":
                return {"game":"memory_pairs","time":None,"score":None,"timestamp":now_iso()}
            # allow entering a number
            sel = None
            if isinstance(k, str) and k.isdigit():
                try:
                    v = int(k)
                    sel = v - 1
                except Exception:
                    sel = None
            else:
                # try to parse as raw input (fallback)
                if isinstance(k, str):
                    try:
                        v = int(k.strip())
                        sel = v - 1
                    except Exception:
                        pass
            if sel is None or sel < 0 or sel >= self.total or self.matched[sel]:
                # ignore invalid
                continue
            if first_sel is None:
                first_sel = sel
                self.revealed[sel] = True
                self.moves += 1
            else:
                # second pick
                self.revealed[sel] = True
                self.moves += 1
                self.render()
                time.sleep(0.5)
                if self.cards[first_sel] == self.cards[sel]:
                    self.matched[first_sel] = True
                    self.matched[sel] = True
                else:
                    self.revealed[first_sel] = False
                    self.revealed[sel] = False
                first_sel = None
        elapsed = time.time() - self.start_time
        correct = sum(1 for m in self.matched[:self.total] if m)
        accuracy = correct / self.total if self.total else 0
        result = {"game":"memory_pairs","time":round(elapsed,2),"score": self.moves, "timestamp": now_iso(), "better_is_lower": True}
        record_score(self.cfg, "memory_pairs", result)
        return result

def memory_pairs(term: Term, cfg: dict, autoplay=False):
    mp = MemoryPairs(term, cfg, autoplay=autoplay)
    return mp.run()

# --- High scores viewer ---
def show_high_scores(term: Term, cfg: dict):
    term.clear()
    w, h = term.get_size()
    term.draw_text(1, 2, "High Scores")
    scores = cfg.get("scores", {})
    y = 3
    for game_key in ("reaction_tap", "grid_dodge", "memory_pairs"):
        g = scores.get(game_key, {})
        best = g.get("best")
        if best:
            line = f"{game_key}: score={best.get('score')} time={best.get('time')} at {best.get('timestamp')}"
        else:
            line = f"{game_key}: (no record)"
        term.draw_text(y, 4, line)
        y += 1
    term.draw_text(h - 2, 2, "Press any key to return.")
    term.refresh()
    term.getkey()

# --- Settings UI ---
def settings_ui(term: Term, cfg: dict):
    s = cfg.setdefault("settings", {})
    sel = 0
    options = ["beep", "theme", "difficulty", "grid_size", "mem_size", "tick_ms", "Reset Data", "Back"]
    while True:
        term.clear()
        w, h = term.get_size()
        term.draw_text(1, 2, "Settings")
        for i, opt in enumerate(options):
            marker = "▶ " if i == sel else "  "
            val = ""
            if opt in ("beep", "theme", "difficulty", "tick_ms"):
                val = str(s.get(opt))
            elif opt == "grid_size":
                val = f"{s.get('grid_size')}"
            elif opt == "mem_size":
                val = f"{s.get('mem_size')}"
            line = f"{marker}{opt}: {val}"
            term.draw_text(3 + i, 4, line)
        term.draw_text(h - 2, 2, "Use ↑/↓, Enter to edit, Esc to back.")
        term.refresh()
        k = term.getkey()
        if not k:
            continue
        if k in ("KEY_UP", "k", "K"):
            sel = (sel - 1) % len(options)
        elif k in ("KEY_DOWN", "j", "J"):
            sel = (sel + 1) % len(options)
        elif k in ("\n", "\r", "KEY_ENTER"):
            opt = options[sel]
            if opt == "beep":
                s["beep"] = not s.get("beep", True)
            elif opt == "theme":
                cur = s.get("theme", "auto")
                s["theme"] = {"auto":"light","light":"dark","dark":"auto"}[cur]
            elif opt == "difficulty":
                cur = s.get("difficulty","normal")
                s["difficulty"] = {"easy":"normal","normal":"hard","hard":"easy"}[cur]
            elif opt == "grid_size":
                # simple toggle presets
                s["grid_size"] = [8,6] if s.get("grid_size") != [8,6] else [10,8]
            elif opt == "mem_size":
                s["mem_size"] = [4,4] if s.get("mem_size") != [4,4] else [6,4]
            elif opt == "tick_ms":
                cur = int(s.get("tick_ms",200))
                cur = 150 if cur==200 else 200
                s["tick_ms"] = cur
            elif opt == "Reset Data":
                if prompt_confirm(term, "Reset all scores and settings to defaults?"):
                    cfg.clear()
                    cfg.update(DEFAULT_CONFIG.copy())
            elif opt == "Back":
                save_config(cfg)
                return
            save_config(cfg)
        elif k in ("\x1b", "\x03"):
            save_config(cfg)
            return

# --- Report flag output ---
def print_report(cfg: dict):
    lr = cfg.get("last_result")
    if not lr:
        print("No last result found.")
        return 1
    game = lr.get("game","?")
    score = lr.get("score")
    timev = lr.get("time")
    ts = lr.get("timestamp")
    pb = lr.get("is_personal_best", False)
    print(f"Game: {game}")
    print(f"Score: {score}")
    print(f"Time: {timev}")
    print(f"Timestamp: {ts}")
    print(f"Personal best: {'YES' if pb else 'NO'}")
    return 0

# --- Demo mode runs short automated plays ---
def run_demo(term: Term, cfg: dict):
    # run each game in autoplay for quick verification
    results = []
    results.append(reaction_tap(term, cfg, autoplay=True))
    results.append(grid_dodge(term, cfg, autoplay=True))
    results.append(memory_pairs(term, cfg, autoplay=True))
    # ensure saved
    save_config(cfg)
    return results

# --- Main loop handling curses vs fallback ---
def interactive_main(term: Term, cfg: dict, start_index=0):
    sel = start_index
    while True:
        draw_menu(term, cfg, sel)
        k = term.getkey()
        if not k:
            continue
        if k in ("KEY_UP", "k", "K"):
            sel = (sel - 1) % len(MENU_ITEMS)
        elif k in ("KEY_DOWN", "j", "J"):
            sel = (sel + 1) % len(MENU_ITEMS)
        elif k in ("\n", "\r", "KEY_ENTER"):
            label, key = MENU_ITEMS[sel]
            if key == "reaction_tap":
                try:
                    reaction_tap(term, cfg)
                except Exception as e:
                    # save and continue
                    save_config(cfg)
                continue
            if key == "grid_dodge":
                try:
                    grid_dodge(term, cfg)
                except Exception:
                    save_config(cfg)
                continue
            if key == "memory_pairs":
                try:
                    memory_pairs(term, cfg)
                except Exception:
                    save_config(cfg)
                continue
            if key == "high_scores":
                show_high_scores(term, cfg)
                continue
            if key == "settings":
                settings_ui(term, cfg)
                continue
            if key == "quit":
                save_config(cfg)
                break
        elif k in ("\x1b",):
            # Esc quits
            save_config(cfg)
            break
        elif k in ("\x03",):
            save_config(cfg)
            break

# --- Curses wrapper entrypoint ---
def curses_entry(stdscr, cfg):
    term = Term(use_curses=True)
    term.init_curses(stdscr)
    try:
        interactive_main(term, cfg)
    except Exception as e:
        # ensure config saved before re-raising
        save_config(cfg)
        raise
    finally:
        term.stop()

# --- Fallback console interactive loop ---
def fallback_interactive(cfg):
    term = Term(use_curses=False)
    term.start()
    try:
        interactive_main(term, cfg)
    except KeyboardInterrupt:
        save_config(cfg)

# --- Argument parsing and main ---
def main():
    parser = argparse.ArgumentParser(description="Micro-Arcade: terminal micro-games hub (single-file).")
    parser.add_argument("--no-curses", action="store_true", help="Force fallback non-curses mode.")
    parser.add_argument("--report", action="store_true", help="Print last-played game summary.")
    parser.add_argument("--demo", action="store_true", help="Run automated demo plays (no input).")
    args = parser.parse_args()

    cfg = load_config()
    # On exit always attempt to save state
    try:
        if args.report:
            rc = print_report(cfg)
            sys.exit(rc)
        if args.demo:
            # run demo in fallback or curses depending on availability
            term = Term(use_curses=HAS_CURSES, force_no_curses=args.no_curses)
            term.start()
            results = run_demo(term, cfg)
            # print concise demo summary
            for r in results:
                print(json.dumps(r))
            save_config(cfg)
            sys.exit(0)
        # Interactive mode
        if HAS_CURSES and not args.no_curses:
            # use curses wrapper
            try:
                wrapper(lambda stdscr: curses_entry(stdscr, cfg))
            except Exception:
                # fallback
                fallback_interactive(cfg)
        else:
            fallback_interactive(cfg)
    except KeyboardInterrupt:
        save_config(cfg)
    except Exception as e:
        # attempt save and print minimal error
        try:
            save_config(cfg)
        finally:
            print("Unexpected error:", e, file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()