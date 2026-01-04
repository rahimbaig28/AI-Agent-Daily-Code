# Auto-generated via Perplexity on 2026-01-04T01:47:31.869713Z
#!/usr/bin/env python3
import json
import os
import sys
import datetime
from collections import defaultdict, deque
import hashlib
import urllib.parse
import webbrowser
import threading
import time
import signal

HOME = os.path.expanduser("~")
NOTES_FILE = os.path.join(HOME, "research_notes.json")

class NoteVault:
    def __init__(self):
        self.notes = []
        self.note_id_counter = 0
        self.selected = 0
        self.search_filter = ""
        self.tag_filters = set()
        self.undo_stack = deque(maxlen=50)
        self.redo_stack = deque(maxlen=50)
        self.edit_history = defaultdict(list)
        self.edit_pos = defaultdict(int)
        self.auto_save_thread = None
        self.running = True
        self.load_notes()
        if len(sys.argv) > 1 and sys.argv[1].startswith("--load="):
            hash_val = sys.argv[1][7:]
            self.load_by_hash(hash_val)
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        self.save_notes()
        sys.exit(0)

    def get_note_path(self):
        return NOTES_FILE + ".tmp" if os.path.exists(NOTES_FILE + ".tmp") else NOTES_FILE

    def load_notes(self):
        path = self.get_note_path()
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                    self.notes = data.get('notes', [])
                    self.note_id_counter = data.get('counter', 0)
                    self.selected = min(self.selected, len(self.notes) - 1)
        except:
            self.notes = []

    def save_notes(self):
        try:
            path = NOTES_FILE + ".tmp"
            with open(path, 'w') as f:
                json.dump({
                    'notes': self.notes,
                    'counter': self.note_id_counter
                }, f, indent=2)
            if os.path.exists(path):
                os.replace(path, NOTES_FILE)
        except Exception as e:
            print(f"Save failed: {e}")

    def start_auto_save(self):
        def autosave():
            while self.running:
                time.sleep(30)
                if self.running:
                    self.save_notes()
        self.auto_save_thread = threading.Thread(target=autosave, daemon=True)
        self.auto_save_thread.start()

    def get_filtered_notes(self):
        filtered = self.notes[:]
        if self.search_filter:
            filtered = [n for n in filtered if (
                self.search_filter.lower() in n['title'].lower() or
                self.search_filter.lower() in n['content'].lower() or
                self.search_filter.lower() in n['tags'].lower()
            )]
        if self.tag_filters:
            filtered = [n for n in filtered if any(t.strip() in n['tags'] for t in self.tag_filters)]
        return filtered

    def get_all_tags(self):
        tags = set()
        for note in self.notes:
            tags.update(t.strip() for t in note['tags'].split(',') if t.strip())
        return sorted(tags)

    def get_stats(self):
        filtered = self.get_filtered_notes()
        all_tags = self.get_all_tags()
        undo_len = len(self.undo_stack)
        redo_len = len(self.redo_stack)
        return f"{len(filtered)} notes | {len(all_tags)} tags | '{self.search_filter}' | U:{undo_len}/R:{redo_len}"

    def add_note(self, title="", content="", tags=""):
        note = {
            'id': self.note_id_counter,
            'title': title,
            'content': content,
            'tags': tags,
            'timestamp': datetime.datetime.now().isoformat()
        }
        self.notes.append(note)
        self.note_id_counter += 1
        self.undo_stack.append(('add', note['id']))
        self.redo_stack.clear()
        self.selected = len(self.notes) - 1

    def delete_note(self, idx):
        note_id = self.notes[idx]['id']
        self.undo_stack.append(('delete', note_id, self.notes[idx]))
        self.redo_stack.clear()
        del self.notes[idx]
        if self.selected >= len(self.notes):
            self.selected = max(0, len(self.notes) - 1)

    def edit_note(self, idx, field, old_value, new_value):
        note_id = self.notes[idx]['id']
        self.undo_stack.append(('edit', note_id, field, old_value))
        self.redo_stack.clear()
        self.notes[idx][field] = new_value

    def undo(self):
        if not self.undo_stack:
            return
        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        typ, *args = action
        if typ == 'add':
            for i, note in enumerate(self.notes):
                if note['id'] == args[0]:
                    del self.notes[i]
                    break
        elif typ == 'delete':
            note_id, note = args[0], args[1]
            self.notes.append(note)
            self.notes.sort(key=lambda x: x['id'])
        elif typ == 'edit':
            note_id, field, old_value = args[0], args[1], args[2]
            for note in self.notes:
                if note['id'] == note_id:
                    note[field] = old_value
                    break

    def redo(self):
        if not self.redo_stack:
            return
        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        typ, *args = action
        if typ == 'add':
            note_id = args[0]
            note = next((n for n in self.notes if n['id'] == note_id), None)
            if note:
                self.notes.append(note)
                self.notes.sort(key=lambda x: x['id'])
        elif typ == 'delete':
            note_id, note = args[0], args[1]
            for i, n in enumerate(self.notes):
                if n['id'] == note_id:
                    del self.notes[i]
                    break
        elif typ == 'edit':
            note_id, field, new_value = args[0], args[1], args[2]
            for note in self.notes:
                if note['id'] == note_id:
                    note[field] = new_value
                    break

    def get_note_hash(self, note):
        data = f"{note['title']}{note['tags']}"
        return hashlib.sha256(data.encode()).hexdigest()[:8]

    def load_by_hash(self, hash_val):
        for i, note in enumerate(self.notes):
            if self.get_note_hash(note) == hash_val:
                self.selected = i
                return True
        return False

    def share_note(self, idx):
        note = self.notes[idx]
        md_content = f"# {note['title']}\n\n{note['content']}\n\n**Tags:** {note['tags']}"
        b64 = ""
        try:
            import base64
            b64 = base64.b64encode(md_content.encode()).decode()
        except:
            pass
        print(f"Markdown (base64): {b64}")
        hash_val = self.get_note_hash(note)
        print(f"Share hash: {hash_val}")
        print(f"URL param: ?note={hash_val}")

    def simple_editor(self, prompt, initial="", history_key=None):
        lines = self.edit_history[history_key] if history_key else []
        line_idx = 0
        line = initial
        print(prompt + line)
        while True:
            char = sys.stdin.read(1)
            if char == '\x1b':  # ESC
                seq = ""
                while True:
                    char = sys.stdin.read(1)
                    seq += char
                    if char in '\n\r':
                        break
                if seq.startswith('[A'):  # Up
                    if lines and line_idx > 0:
                        line_idx -= 1
                        line = lines[line_idx]
                        os.system('clear')
                        print(prompt + line)
                elif seq.startswith('[B'):  # Down
                    if lines and line_idx < len(lines) - 1:
                        line_idx += 1
                        line = lines[line_idx]
                        os.system('clear')
                        print(prompt + line)
            elif char == '\r' or char == '\n':  # Enter
                if line not in lines:
                    lines.append(line)
                self.edit_history[history_key] = lines
                return line
            elif char == '\x7f':  # Backspace
                line = line[:-1]
                os.system('clear')
                print(prompt + line)
            else:
                line += char
                os.system('clear')
                print(prompt + line)

    def run(self):
        self.start_auto_save()
        os.system('clear')
        while self.running:
            filtered = self.get_filtered_notes()
            print("\n".join([
                f"Notes: {self.get_stats()}",
                "-" * 60
            ] + [
                f"[{i:2d}] {n['title'][:30]:<30} | {n['tags'][:20]:<20} | {n['timestamp'][:10]}"
                for i, n in enumerate(filtered)
            ] + [
                "",
                f"Selected: {self.selected}  ↑↓ navigate  ←→ tags  Enter edit  d delete  u undo  r redo  s search  x share  q quit",
                "Ctrl+T toggle tag filter" if self.get_all_tags() else ""
            ]))
            
            try:
                char = sys.stdin.read(1)
            except:
                continue

            if char == 'q':
                break
            elif char == 's':
                os.system('clear')
                self.search_filter = self.simple_editor("Search: ")
            elif char == 'd' and filtered:
                self.delete_note(self.selected)
            elif char == 'u':
                self.undo()
            elif char == 'r':
                self.redo()
            elif char == 'x' and filtered:
                self.share_note(self.selected)
            elif char == '\r':  # Enter
                if filtered:
                    os.system('clear')
                    note = filtered[self.selected]
                    print(f"Editing note {note['id']}:")
                    new_title = self.simple_editor("Title: ", note['title'], 'title')
                    new_content = self.simple_editor("Content: ", note['content'], 'content')
                    new_tags = self.simple_editor("Tags: ", note['tags'], 'tags')
                    self.edit_note(filtered.index(note), 'title', note['title'], new_title)
                    self.edit_note(filtered.index(note), 'content', note['content'], new_content)
                    self.edit_note(filtered.index(note), 'tags', note['tags'], new_tags)
            elif char == '\x1b':  # ESC sequence
                seq = sys.stdin.read(3)
                if seq == '[A':  # Up
                    self.selected = max(0, self.selected - 1)
                elif seq == '[B':  # Down
                    self.selected = min(len(filtered) - 1, self.selected + 1)
                elif seq == '[D':  # Left - cycle tag filters
                    tags = self.get_all_tags()
                    if tags:
                        if self.tag_filters:
                            tag = sorted(self.tag_filters)[0]
                            self.tag_filters.remove(tag)
                        else:
                            self.tag_filters.add(tags[0])
                elif seq == '[C':  # Right - add next tag
                    tags = self.get_all_tags()
                    if tags:
                        current_tags = set(self.tag_filters)
                        for tag in tags:
                            if tag not in current_tags:
                                self.tag_filters.add(tag)
                                break
            elif char.lower() == '\x14':  # Ctrl+T
                tags = self.get_all_tags()
                if tags:
                    print("\nTags:", ", ".join(tags))
                    print("Press tag letter to toggle (Enter when done):")
                    while True:
                        tchar = sys.stdin.read(1).lower()
                        if tchar == '\r':
                            break
                        for tag in tags:
                            if tag[0].lower() == tchar:
                                if tag in self.tag_filters:
                                    self.tag_filters.remove(tag)
                                else:
                                    self.tag_filters.add(tag)
                                break

        self.running = False
        self.save_notes()

if __name__ == "__main__":
    vault = NoteVault()
    vault.run()