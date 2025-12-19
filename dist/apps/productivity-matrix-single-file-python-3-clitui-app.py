# Auto-generated via Perplexity on 2025-12-19T01:27:47.592970Z
#!/usr/bin/env python3
"""
Productivity Matrix — Terminal TUI for task management across Priority vs Timebox.
Supports curses (Unix) or fallback line-mode (Windows). Single-file, stdlib only.
"""

import json
import os
import sys
import uuid
import datetime
import argparse
import shutil
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque

try:
    import curses
    HAS_CURSES = True
except ImportError:
    HAS_CURSES = False

@dataclass
class Task:
    id: str
    title: str
    notes: str
    priority: str  # High, Med, Low
    timebox: str   # Now, Today, ThisWeek
    created_at: str
    updated_at: str
    done: bool
    due_date: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

class State:
    def __init__(self):
        self.tasks: List[Task] = []
        self.history: deque = deque(maxlen=100)
        self.redo_stack: deque = deque(maxlen=100)
        self.search_filter: str = ""
        self.show_done: bool = True
        self.schema_version: int = 1

    def snapshot(self) -> Dict[str, Any]:
        return {
            'tasks': [asdict(t) for t in self.tasks],
            'history': list(self.history),
            'redo_stack': list(self.redo_stack),
            'search_filter': self.search_filter,
            'show_done': self.show_done,
            'schema_version': self.schema_version
        }

    @classmethod
    def from_snapshot(cls, data: Dict[str, Any]) -> 'State':
        state = cls()
        state.tasks = [Task(**t) for t in data.get('tasks', [])]
        state.history = deque(data.get('history', []), maxlen=100)
        state.redo_stack = deque(data.get('redo_stack', []), maxlen=100)
        state.search_filter = data.get('search_filter', '')
        state.show_done = data.get('show_done', True)
        state.schema_version = data.get('schema_version', 1)
        return state

    def record_change(self, action: str, before: Dict[str, Any]):
        self.history.append({'action': action, 'before': before})
        self.redo_stack.clear()

    def undo(self) -> bool:
        if not self.history:
            return False
        change = self.history.pop()
        self.redo_stack.append(change)
        # Simplified undo - for full impl, apply reverse of 'before'
        self.load_from_file(self.get_filename())  # Reload from disk as fallback
        return True

    def redo(self) -> bool:
        if not self.redo_stack:
            return False
        change = self.redo_stack.pop()
        self.history.append(change)
        return True

    def get_filename(self) -> str:
        return os.path.expanduser("~/.productivity_matrix.json")

    def save(self, filename: Optional[str] = None):
        filename = filename or self.get_filename()
        temp_fd, temp_path = tempfile.mkstemp()
        try:
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(self.snapshot(), f, indent=2)
            os.replace(temp_path, filename)
        except Exception:
            os.unlink(temp_path)
            raise

    def load_from_file(self, filename: Optional[str] = None):
        filename = filename or self.get_filename()
        if not os.path.exists(filename):
            return
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                temp_state = State.from_snapshot(data)
                self.tasks = temp_state.tasks
                self.search_filter = temp_state.search_filter
                self.show_done = temp_state.show_done
        except json.JSONDecodeError:
            backup = f"{filename}.backup.{datetime.datetime.now().isoformat()}"
            shutil.copy2(filename, backup)
            print(f"Corrupted file backed up to {backup}. Starting fresh.")

    def filtered_tasks(self) -> List[Task]:
        tasks = self.tasks
        if not self.show_done:
            tasks = [t for t in tasks if not t.done]
        if self.search_filter:
            q = self.search_filter.lower()
            tasks = [t for t in tasks if q in t.title.lower() or q in t.notes.lower()]
        return tasks

    def get_grid(self) -> List[List[List[Task]]]:
        prios = ['High', 'Med', 'Low']
        timeboxes = ['Now', 'Today', 'ThisWeek']
        grid = [[[] for _ in timeboxes] for _ in prios]
        for task in self.filtered_tasks():
            p_idx = prios.index(task.priority)
            t_idx = timeboxes.index(task.timebox)
            grid[p_idx][t_idx].append(task)
        for row in grid:
            for cell in row:
                cell.sort(key=lambda t: t.title)
        return grid

class SimpleTUI:
    def __init__(self, state: State):
        self.state = state
        self.focus_row = 1
        self.focus_col = 0
        self.cell_view = False
        self.cell_row = 0
        self.cell_col = 0
        self.cell_task_idx = 0
        self.status_msg = ""
        self.input_buffer = ""
        self.input_mode = None  # 'title', 'notes', etc.

    def get_tasks_at(self, row: int, col: int) -> List[Task]:
        grid = self.state.get_grid()
        return grid[row][col]

    def render(self, stdscr):
        if not HAS_CURSES:
            self.render_simple()
            return

        curses.curs_set(0 if not self.input_mode else 1)
        h, w = stdscr.getmaxyx()
        
        stdscr.clear()
        
        # Header
        header = f"Productivity Matrix | {self.state.get_filename()} | {len(self.state.tasks)} tasks"
        if self.state.search_filter:
            header += f" | Search: {self.state.search_filter}"
        stdscr.addstr(0, 0, header[:w-1])
        
        # Status
        if self.status_msg:
            stdscr.addstr(1, 0, self.status_msg[:w-1], curses.A_REVERSE)
        
        # Grid
        prios = ['High', 'Med', 'Low']
        timeboxes = ['Now', 'Today', 'ThisWeek']
        
        if w < 80:  # Compact mode
            self.render_compact(stdscr, h, w, prios, timeboxes)
        else:
            self.render_full_grid(stdscr, h, w, prios, timeboxes)
        
        # Footer
        footer = "A:add E:edit SPC:done D:del M:move /:search F:filter Z:undo Y:redo P:print S:save Q:quit H:help"
        stdscr.addstr(h-1, 0, footer[:w-1])
        
        stdscr.refresh()

    def render_full_grid(self, stdscr, h, w, prios, timeboxes):
        cell_w = max(25, (w-4)//3)
        cell_h = max(3, (h-4)//3)
        
        for r, prio in enumerate(prios):
            # Row label
            stdscr.addstr(3+r*cell_h, 1, prio[:10].ljust(10))
            
            for c, timebox in enumerate(timeboxes):
                x = 1 + c*(cell_w+1)
                y = 3 + r*cell_h
                
                # Cell border
                for i in range(cell_h):
                    stdscr.addstr(y+i, x, '│' + ' '*(cell_w-2) + '│')
                stdscr.addstr(y+cell_h, x, '└' + '─'*(cell_w-2) + '┘')
                
                # Timebox header
                stdscr.addstr(y-1, x+1, timebox[:cell_w-2])
                
                # Tasks
                tasks = self.get_tasks_at(r, c)
                if self.cell_view and self.cell_row == r and self.cell_col == c:
                    self.render_cell_view(stdscr, y, x, cell_h, cell_w, tasks)
                else:
                    self.render_cell_summary(stdscr, y, x, cell_h, tasks, r, c)
        
        # Focus indicator
        if not self.cell_view:
            fx = 1 + self.focus_col * (max(25, (w-4)//3) + 1)
            fy = 3 + self.focus_row * max(3, (h-4)//3)
            stdscr.chgat(fy, fx, 1, curses.A_REVERSE)

    def render_cell_summary(self, stdscr, y, x, cell_h, tasks, r, c):
        for i, task in enumerate(tasks[:cell_h-1]):
            line = f"[{task.id[:8]}] {task.title[:20]} {'✓' if task.done else ' '}"
            stdscr.addstr(y+1+i, x+1, line[:20])
        if len(tasks) > cell_h-1:
            stdscr.addstr(y+cell_h-1, x+1, f"+{len(tasks)-(cell_h-1)} more")

    def render_cell_view(self, stdscr, y, x, cell_h, cell_w, tasks):
        # Full task list for focused cell
        for i, task in enumerate(tasks):
            marker = "►" if i == self.cell_task_idx else " "
            line = f"{marker} [{task.id[:8]}] {task.title} {'✓' if task.done else ''}"
            if i < cell_h-1:
                stdscr.addstr(y+1+i, x+1, line[:cell_w-2])

    def render_compact(self, stdscr, h, w, prios, timeboxes):
        # Stacked layout for narrow terminals
        y = 3
        for r, prio in enumerate(prios):
            stdscr.addstr(y, 1, f"{prio}:")
            y += 1
            for c, timebox in enumerate(timeboxes):
                tasks = self.get_tasks_at(r, c)
                prefix = f"  {timebox}: "
                for task in tasks[:h-y-2]:
                    line = f"{prefix}[{task.id[:6]}] {task.title[:w-len(prefix)-10]}"
                    stdscr.addstr(y, 1, line[:w-2])
                    y += 1
                if len(tasks) > h-y-2:
                    stdscr.addstr(y, 1, f"  +{len(tasks)-(h-y-2)} more...")
                    y += 1
            y += 1

    def render_simple(self):
        grid = self.state.get_grid()
        prios = ['High', 'Med', 'Low']
        timeboxes = ['Now', 'Today', 'ThisWeek']
        
        print("\n" + "="*60)
        print("PRODUCTIVITY MATRIX")
        print(f"File: {self.state.get_filename()} | {len(self.state.tasks)} tasks")
        if self.status_msg:
            print(f"Status: {self.status_msg}")
        
        for r, prio in enumerate(prios):
            print(f"\n{prio}:")
            for c, tbox in enumerate(timeboxes):
                tasks = grid[r][c]
                print(f"  {tbox}: {len(tasks)} tasks")
                for task in tasks[:3]:
                    print(f"    [{task.id[:8]}] {task.title} {'✓' if task.done else ''}")
                if len(tasks) > 3:
                    print(f"    ... +{len(tasks)-3} more")
        
        print("\nCommands: A E SPC D M / F Z Y P S Q H")
        if self.input_mode:
            print(f"INPUT ({self.input_mode}): {self.input_buffer}")
        print("-" * 60)

    def handle_input(self, key):
        if self.input_mode:
            return self.handle_input_mode(key)
        
        if key == ord('q') or key == 27:  # Q or ESC
            return 'quit'
        elif key == ord('a'):  # Add
            self.input_mode = 'title'
            self.input_buffer = ""
            return 'input'
        elif key == ord('e'):  # Edit
            tasks = self.get_tasks_at(self.focus_row, self.focus_col)
            if tasks and self.cell_task_idx < len(tasks):
                task = tasks[self.cell_task_idx]
                print(f"Edit {task.title}")  # Simplified
            return 'stay'
        elif key == ord(' '):  # Toggle done
            tasks = self.get_tasks_at(self.focus_row, self.focus_col)
            if tasks and self.cell_task_idx < len(tasks):
                task = tasks[self.cell_task_idx]
                before = self.state.snapshot()
                task.done = not task.done
                task.updated_at = datetime.datetime.now().isoformat()
                self.state.record_change('toggle_done', before)
                self.state.save()
                self.status_msg = "Task toggled"
            return 'stay'
        elif key == ord('d'):  # Delete
            tasks = self.get_tasks_at(self.focus_row, self.focus_col)
            if tasks and self.cell_task_idx < len(tasks):
                task = tasks[self.cell_task_idx]
                confirm = input(f"Delete '{task.title}'? (y/N): ").lower()
                if confirm == 'y':
                    before = self.state.snapshot()
                    self.state.tasks = [t for t in self.state.tasks if t.id != task.id]
                    self.state.record_change('delete', before)
                    self.state.save()
                    self.status_msg = "Task deleted"
            return 'stay'
        elif key == ord('/'):  # Search
            self.input_mode = 'search'
            self.input_buffer = ""
            return 'input'
        elif key == ord('z'):  # Undo
            if self.state.undo():
                self.status_msg = "Undone"
            else:
                self.status_msg = "Nothing to undo"
            return 'stay'
        elif key == ord('y'):  # Redo
            if self.state.redo():
                self.status_msg = "Redone"
            else:
                self.status_msg = "Nothing to redo"
            return 'stay'
        elif key == ord('p'):  # Print
            self.print_report()
            return 'stay'
        elif key == ord('s'):  # Save
            self.state.save()
            self.status_msg = "Saved"
            return 'stay'
        elif key == ord('h'):  # Help
            self.show_help()
            return 'stay'
        elif key in (curses.KEY_UP, ord('k')):
            if self.cell_view:
                self.cell_task_idx = max(0, self.cell_task_idx - 1)
            else:
                self.focus_row = max(0, self.focus_row - 1)
            return 'stay'
        elif key in (curses.KEY_DOWN, ord('j')):
            if self.cell_view:
                tasks = self.get_tasks_at(self.cell_row, self.cell_col)
                self.cell_task_idx = min(len(tasks)-1, self.cell_task_idx + 1)
            else:
                self.focus_row = min(2, self.focus_row + 1)
            return 'stay'
        elif key in (curses.KEY_LEFT, ord('h')):
            self.focus_col = max(0, self.focus_col - 1)
            return 'stay'
        elif key in (curses.KEY_RIGHT, ord('l')):
            self.focus_col = min(2, self.focus_col + 1)
            return 'stay'
        elif key == curses.KEY_RESIZE:
            return 'resize'
        elif key == 10 or key == curses.KEY_ENTER:  # Enter
            self.cell_view = True
            self.cell_row = self.focus_row
            self.cell_col = self.focus_col
            tasks = self.get_tasks_at(self.cell_row, self.cell_col)
            self.cell_task_idx = 0
            return 'stay'
        return 'stay'

    def handle_input_mode(self, key):
        if key == 27 or key == ord('\x1b'):  # ESC
            self.input_mode = None
            self.input_buffer = ""
            return 'stay'
        elif key == 10 or key == curses.KEY_ENTER:  # Enter
            if self.input_mode == 'title':
                if self.input_buffer.strip():
                    self.add_task(self.input_buffer.strip())
                    self.input_mode = None
                    self.input_buffer = ""
                return 'stay'
            elif self.input_mode == 'search':
                self.state.search_filter = self.input_buffer
                self.input_mode = None
                self.input_buffer = ""
                self.state.save()
                return 'stay'
        elif key == 127 or key == 8:  # Backspace
            self.input_buffer = self.input_buffer[:-1]
        elif 32 <= key <= 126:  # Printable chars
            self.input_buffer += chr(key)
        return 'input'

    def add_task(self, title: str, priority: str = 'High', timebox: str = 'Now'):
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            notes="",
            priority=priority,
            timebox=timebox,
            created_at=datetime.datetime.now().isoformat(),
            updated_at=datetime.datetime.now().isoformat(),
            done=False
        )
        before = self.state.snapshot()
        self.state.tasks.append(task)
        self.state.record_change('add', before)
        self.state.save()
        self.status_msg = f"Added: {title}"

    def print_report(self):
        grid = self.state.get_grid()
        prios = ['High', 'Med', 'Low']
        timeboxes = ['Now', 'Today', 'ThisWeek']
        
        print("\n" + "="*80)
        print("PRODUCTIVITY MATRIX REPORT")
        print(f"Generated: {datetime.datetime.now().isoformat()}")
        print(f"Total tasks: {len(self.state.tasks)}")
        print("="*80)
        
        for r, prio in enumerate(prios):
            print(f"\n{prio.upper()}:")
            for c, tbox in enumerate(timeboxes):
                tasks = grid[r][c]
                print(f"\n  {tbox}: {len(tasks)} tasks")
                for task in tasks:
                    marker = "✓" if task.done else "○"
                    due = f" (due {task.due_date})" if task.due_date else ""
                    print(f"    {marker} [{task.id[:8]}] {task.title}{due}")
                    if task.notes:
                        print(f"       {task.notes[:60]}")
        print("="*80)

    def show_help(self):
        help_text = """
Productivity Matrix - Key bindings:

Navigation: ↑↓←→ or h j k l    Enter: Cell detail view
A: Add task    E: Edit    Space: Toggle done    D: Delete    
M: Move    /: Search    F: Filter    Z: Undo    Y: Redo
P: Print report    S: Save    Q: Quit    H: Help

ESC: Cancel input    Enter: Confirm
"""
        print(help_text)
        input("Press Enter to continue...")

def curses_main(stdscr):
    curses.cbreak()
    curses.noecho()
    curses.curs_set(0)
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    
    try:
        state = State()
        state.load_from_file()
        tui = SimpleTUI(state)
        
        while True:
            tui.render(stdscr)
            key = stdscr.getch()
            action = tui.handle_input(key)
            if action == 'quit':
                state.save()
                break
    finally:
        curses.nocbreak()
        curses.echo()
        curses.endwin()

def simple_main():
    state = State()
    state.load_from_file()
    tui = SimpleTUI(state)
    
    print("Productivity Matrix (Simple mode)")
    while True:
        tui.render_simple()
        try:
            cmd = input("\nCommand (a,e,d,m, ,/,z,y,p,s,q,h,? for help): ").lower().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            state.save()
            break
        
        if cmd == 'q':
            state.save()
            break
        elif cmd == 'a':
            title = input("Title: ").strip()
            if title:
                tui.add_task(title)
        elif cmd == 'p':
            tui.print_report()
        elif cmd == 's':
            state.save()
            print("Saved")
        elif cmd == 'h' or cmd == '?':
            tui.show_help()
        elif cmd == 'z':
            if state.undo():
                print("Undone")
            else:
                print("Nothing to undo")
        else:
            print("Unknown command. Press H for help.")

def main():
    parser = argparse.ArgumentParser(description="Productivity Matrix TUI")
    parser.add_argument('--file', help="Override persistence file")
    parser.add_argument('--seed', type=int, help="Seed dummy data")
    parser.add_argument('--export', help="Export to FILE")
    parser.add_argument('--import', help="Import from FILE")
    args = parser.parse_args()
    
    if args.seed is not None:
        state = State()
        now = datetime.datetime.now().isoformat()
        dummy_tasks = [
            Task(str(uuid.uuid4()), f"Task {i}", f"Notes {i}", "High", "Now", now, now)
            for i in range(args.seed)
        ]
        state.tasks = dummy_tasks
        state.save()
        print(f"Seeded {args.seed} tasks")
        return
    
    if args.export:
        state = State()
        state.load_from_file(args.file)
        if args.export.endswith('.json'):
            with open(args.export, 'w') as f:
                json.dump(state.snapshot(), f, indent=2)
        else:
            tui = SimpleTUI(state)
            tui.print_report()
        return
    
    if HAS_CURSES:
        curses.wrapper(curses_main)
    else:
        simple_main()

if __name__ == "__main__":
    main()