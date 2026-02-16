# Auto-generated via Perplexity on 2026-02-16T14:59:42.898312Z
#!/usr/bin/env python3
import json
import os
import sys
import datetime
import pathlib
import readline
import curses
import signal
from collections import deque

DATA_FILE = "notes.json"
BACKUP_FILE = "notes.json.bak"
NOTES = []
UNDO_STACK = deque(maxlen=10)
REDO_STACK = deque(maxlen=10)
STATE = {"mode": "cli", "selected": 0, "scroll": 0, "tui": False}
IS_DARK = os.environ.get('TERM', '').lower() in ['xterm', 'xterm-256color', 'screen', 'tmux']

def detect_theme(stdscr=None):
    global IS_DARK
    if not IS_DARK:
        try:
            if stdscr:
                curses.use_default_colors()
                curses.curs_set(1)
            IS_DARK = True
        except:
            pass
    return IS_DARK

def sigint_handler(signum, frame):
    save_notes()
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

def load_notes():
    global NOTES, UNDO_STACK
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                NOTES[:] = json.load(f)
        elif os.path.exists(BACKUP_FILE):
            print("Using backup file...")
            with open(BACKUP_FILE, 'r') as f:
                NOTES[:] = json.load(f)
            save_notes()
    except json.JSONDecodeError:
        print("Corrupted JSON, starting fresh. Backup created.")
        if os.path.exists(DATA_FILE):
            pathlib.Path(DATA_FILE).rename(BACKUP_FILE)
        NOTES[:] = []
    UNDO_STACK.clear()
    REDO_STACK.clear()

def save_notes():
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(NOTES, f, indent=2)
        pathlib.Path(BACKUP_FILE).unlink(missing_ok=True)
    except Exception:
        pathlib.Path(DATA_FILE).rename(BACKUP_FILE)
        with open(DATA_FILE, 'w') as f:
            json.dump(NOTES, f, indent=2)

def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def new_note():
    print(f"\n[{timestamp()}] New note (Ctrl+D to finish, Ctrl+C to cancel):")
    lines = []
    try:
        while True:
            line = input("> ")
            if not line:
                continue
            lines.append(line)
    except EOFError:
        pass
    if lines:
        note = {"timestamp": timestamp(), "content": "\n".join(lines)}
        NOTES.insert(0, note)
        UNDO_STACK.append(("add", [note]))
        REDO_STACK.clear()
        print("Note saved.")
        save_notes()

def list_notes(stdscr=None):
    if not NOTES:
        print("No notes.")
        return
    if stdscr:
        curses.echo()
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        for i in range(min(STATE["scroll"], len(NOTES)), min(STATE["scroll"]+h-2, len(NOTES))):
            note = NOTES[i]
            preview = (note["content"][:w-20] + "...").strip()
            stdscr.addstr(i-STATE["scroll"]+1, 0, f"{i+1:2d}. {note['timestamp']} {preview}")
        stdscr.addstr(0, 0, f"Notes ({len(NOTES)}) ↑↓/PgUp/PgDn, Enter=v, e=edit, d=delete, q=back")
        stdscr.refresh()
        return
    print(f"\nNotes ({len(NOTES)}):")
    for i, note in enumerate(NOTES):
        preview = note["content"].split('\n')[0][:60] + "..." if len(note["content"]) > 60 else note["content"]
        print(f"  {i+1:2d}. {note['timestamp']} {preview}")

def get_note_num(prompt="Note number: "):
    try:
        return int(input(prompt).strip()) - 1
    except:
        return -1

def view_note(num):
    if 0 <= num < len(NOTES):
        note = NOTES[num]
        print(f"\n[{note['timestamp']}]")
        print(note["content"])
        input("\nPress Enter...")
    else:
        print("Invalid note number.")

def edit_note(num):
    if 0 <= num < len(NOTES):
        old_note = NOTES[num].copy()
        print(f"\nEdit note {num+1} [{NOTES[num]['timestamp']}] (Ctrl+D to finish):")
        lines = []
        try:
            while True:
                line = input(f"{NOTES[num]['content'][:60]}... > ")
                if line:
                    lines.append(line)
        except EOFError:
            pass
        if lines:
            old_content = NOTES[num]["content"]
            NOTES[num]["content"] = "\n".join(lines)
            UNDO_STACK.append(("edit", num, old_content))
            REDO_STACK.clear()
            save_notes()
            print("Note updated.")
        else:
            print("Cancelled.")
    else:
        print("Invalid note number.")

def delete_note(num):
    if 0 <= num < len(NOTES):
        if input(f"\nDelete note {num+1} [{NOTES[num]['timestamp']}]? (y/n): ").lower() == 'y':
            deleted = NOTES.pop(num)
            UNDO_STACK.append(("delete", num, deleted))
            REDO_STACK.clear()
            save_notes()
            print("Note deleted.")
    else:
        print("Invalid note number.")

def undo():
    if UNDO_STACK:
        action = UNDO_STACK.pop()
        REDO_STACK.append(action)
        typ, *args = action
        if typ == "add":
            NOTES.pop(0)
        elif typ == "edit":
            num, old_content = args
            NOTES[num]["content"] = old_content
        elif typ == "delete":
            num, deleted = args
            NOTES.insert(num, deleted)
        save_notes()
        print("Undo complete.")
    else:
        print("Nothing to undo.")

def redo():
    if REDO_STACK:
        action = REDO_STACK.pop()
        UNDO_STACK.append(action)
        typ, *args = action
        if typ == "add":
            NOTES.insert(0, args[0])
        elif typ == "edit":
            num, new_content = args
            NOTES[num]["content"] = new_content
        elif typ == "delete":
            num, deleted = args
            NOTES.pop(num)
        save_notes()
        print("Redo complete.")
    else:
        print("Nothing to redo.")

def export_print():
    with open("notes.txt", "w") as f:
        f.write(f"Notes Export - {timestamp()}\n" + "="*60 + "\n\n")
        for i, note in enumerate(reversed(NOTES)):
            f.write(f"Note {len(NOTES)-i}:\n")
            f.write(f"[{note['timestamp']}]\n")
            f.write(note["content"] + "\n\n" + "-"*60 + "\n\n")
    print("Exported to notes.txt")

def show_help():
    print("\nCommands:")
    print("  n          New note")
    print("  l          List notes")
    print("  v <num>    View note")
    print("  e <num>    Edit note")
    print("  d <num>    Delete note")
    print("  p          Export for printing")
    print("  u          Undo (Ctrl+Z)")
    print("  r          Redo (Ctrl+Y)")
    print("  h          Help")
    print("  q          Quit")
    print("Run with --tui for full-screen curses interface")

def cli_loop():
    while True:
        try:
            cmd = input("\n> ").strip().lower()
            if cmd == 'q':
                break
            elif cmd == 'n':
                new_note()
            elif cmd == 'l':
                list_notes()
            elif cmd.startswith('v '):
                view_note(get_note_num("View note: "))
            elif cmd.startswith('e '):
                edit_note(get_note_num("Edit note: "))
            elif cmd.startswith('d '):
                delete_note(get_note_num("Delete note: "))
            elif cmd == 'p':
                export_print()
            elif cmd == 'u':
                undo()
            elif cmd == 'r':
                redo()
            elif cmd == 'h':
                show_help()
            else:
                print("Unknown command. Type 'h' for help.")
        except KeyboardInterrupt:
            print("\nCancelled.")
        except EOFError:
            break
    save_notes()

def tui_loop(stdscr):
    global STATE
    curses.curs_set(0)
    detect_theme(stdscr)
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        if STATE["mode"] == "list":
            list_notes(stdscr)
            stdscr.move(STATE["selected"] - STATE["scroll"] + 1, 0)
            stdscr.clrtoeol()
            stdscr.refresh()
        
        elif STATE["mode"] == "help":
            stdscr.addstr(0, 0, "Commands: h=help, q=quit, n=new, l=list, ↑↓=nav, Enter=v, e=edit, d=delete")
            stdscr.refresh()
            stdscr.getch()
            STATE["mode"] = "list"
            continue
        
        c = stdscr.getch()
        if c == ord('q'):
            break
        elif c == ord('n'):
            stdscr.clear()
            stdscr.addstr(0, 0, "New note (any key to return):")
            stdscr.refresh()
            stdscr.getch()
            new_note()
        elif c == ord('l'):
            STATE["mode"] = "list"
        elif c == ord('h'):
            STATE["mode"] = "help"
        elif STATE["mode"] == "list":
            if c == curses.KEY_UP:
                STATE["selected"] = max(0, STATE["selected"] - 1)
            elif c == curses.KEY_DOWN:
                STATE["selected"] = min(len(NOTES)-1, STATE["selected"] + 1)
            elif c == curses.KEY_PPAGE:
                STATE["selected"] = max(0, STATE["selected"] - h//2)
            elif c == curses.KEY_NPAGE:
                STATE["selected"] = min(len(NOTES)-1, STATE["selected"] + h//2)
            elif c == 10:  # Enter
                view_note(STATE["selected"])
            elif c == ord('e'):
                edit_note(STATE["selected"])
            elif c == ord('d'):
                delete_note(STATE["selected"])
            STATE["scroll"] = max(0, STATE["selected"] - h + 3)
    
    save_notes()

def main():
    global STATE
    load_notes()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--tui':
        STATE["tui"] = True
        curses.wrapper(tui_loop)
    else:
        show_help()
        cli_loop()

if __name__ == "__main__":
    main()