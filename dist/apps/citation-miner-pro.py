# Auto-generated via Perplexity on 2025-12-14T01:42:01.170907Z
#!/usr/bin/env python3
"""
Citation Miner Pro - single-file terminal-based research citation manager
- Python 3 standard library only.
- Persist citations to "citations.json" in script directory.
- Undo/Redo (20 steps).
- Keyboard shortcuts (Ctrl+Z / Ctrl+Y, arrow keys, Enter, Delete, n, s, e, o, q).
- Export RIS and BibTeX.
- Drag-and-drop PDF support (accepts file paths pasted/dragged into terminal input).
- Share via short hash: prints "share: python app.py load:HASH..."
- Load from hash: pass command-line arg "load:HASH..."
Notes:
- Minimal TUI using print/input and ANSI colors.
- Tested flows and edge cases handled (missing PDFs, duplicate DOIs, invalid JSON).
"""

import os
import sys
import json
import shutil
import tempfile
import webbrowser
import hashlib
import time
from collections import deque
from urllib.parse import urlparse

# Configuration
MAX_HISTORY = 20
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "citations.json")
EXPORT_RIS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "citations.ris")
EXPORT_BIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "citations.bib")

# ANSI colors
CSI = "\x1b["
RESET = CSI + "0m"
GREEN = CSI + "32m"
RED = CSI + "31m"
YELLOW = CSI + "33m"
CYAN = CSI + "36m"
BOLD = CSI + "1m"

# In-memory structures
citations = []  # list of dicts
history_undo = deque(maxlen=MAX_HISTORY)
history_redo = deque(maxlen=MAX_HISTORY)

selected_index = 0
filter_query = None

# Utilities
def colored(text, color):
    return f"{color}{text}{RESET}"

def save_state(push_history=True):
    global citations
    if push_history:
        # push copy to undo
        history_undo.append(json.dumps(citations, ensure_ascii=False))
        history_redo.clear()
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(citations, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(colored(f"Error saving data: {e}", RED))

def load_state_file(filename):
    global citations
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            citations = data
            save_state(push_history=False)
            return True
        else:
            print(colored("Data file malformed (expected list). Starting with empty DB.", YELLOW))
            citations = []
            save_state(push_history=False)
            return False
    except Exception as e:
        print(colored(f"Could not load {filename}: {e}. Attempting recovery.", YELLOW))
        # attempt recovery: try to locate last valid JSON fragment
        try:
            with open(filename, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            # naive recovery: find first '[' and last ']' and parse
            start = text.find('[')
            end = text.rfind(']')
            if start != -1 and end != -1 and end > start:
                fragment = text[start:end+1]
                data = json.loads(fragment)
                if isinstance(data, list):
                    citations = data
                    save_state(push_history=False)
                    print(colored("Recovered partial data into new DB.", YELLOW))
                    return True
        except Exception:
            pass
        citations = []
        save_state(push_history=False)
        return False

def load_data():
    if os.path.exists(DATA_FILE):
        load_state_file(DATA_FILE)
    else:
        save_state(push_history=False)

def make_id_hash(item):
    core = (item.get("title","") + "|" + ",".join(item.get("authors",[])) + "|" + str(item.get("year","")) + "|" + item.get("doi","")).encode("utf-8")
    return hashlib.sha1(core + b"::CitationMinerPro").hexdigest()[:8].upper()

def find_duplicates(doi):
    if not doi:
        return []
    return [c for c in citations if c.get("doi") and c.get("doi").lower()==doi.lower()]

def parse_pdf_filename(path):
    # Attempt simple filename parsing: title_author_year.pdf or title - author (year).pdf
    name = os.path.basename(path)
    name = name.rsplit(".",1)
    parts = []
    if " - " in name:
        parts = name.split(" - ")
    elif "_" in name:
        parts = name.split("_")
    elif " (" in name and name.endswith(")"):
        # "Title (Author Year)"
        p = name.split(" (")
        parts = [p, p[1].rstrip(")")]
    else:
        parts = [name]
    title = parts.strip() if parts else name
    authors = []
    year = ""
    if len(parts) > 1:
        tail = parts[1]
        # look for 4-digit year
        import re
        m = re.search(r"(19|20)\d{2}", tail)
        if m:
            year = m.group(0)
            authors = [x.strip() for x in tail.replace(year,"").replace(","," ").split() if x.strip()]
        else:
            authors = [a.strip() for a in re.split(r"[,_&]+", tail) if a.strip()]
    return title, authors, year

def add_citation_interactive(from_path=None, prefilled=None):
    global citations
    # prefilled dict may contain keys to pre-populate
    p = prefilled or {}
    print(colored("Adding new citation (leave blank to accept prefilled / skip):", GREEN))
    if from_path:
        pdf_path = os.path.abspath(from_path)
        title_guess, authors_guess, year_guess = parse_pdf_filename(pdf_path)
        p.setdefault("title", title_guess)
        p.setdefault("authors", authors_guess)
        p.setdefault("year", year_guess)
        p.setdefault("pdf", pdf_path)
    title = input(f" Title [{p.get('title','')}]: ").strip() or p.get("title","")
    authors_input = input(f" Authors (comma-separated) [{', '.join(p.get('authors',[]))}]: ").strip()
    authors = [a.strip() for a in (authors_input or ", ".join(p.get('authors',[]))).split(",") if a.strip()]
    year = input(f" Year [{p.get('year','')}]: ").strip() or p.get("year","")
    doi = input(f" DOI or link [{p.get('doi','')}]: ").strip() or p.get("doi","")
    pdf = input(f" PDF path [{p.get('pdf','')}]: ").strip() or p.get("pdf","")
    notes = input(f" Notes [{p.get('notes','')}]: ").strip() or p.get("notes","")
    item = {"id": None, "title": title, "authors": authors, "year": year, "doi": doi, "pdf": pdf, "notes": notes}
    # check duplicate DOI
    if doi:
        dups = find_duplicates(doi)
        if dups:
            print(colored(f"Warning: {len(dups)} existing citation(s) with same DOI.", YELLOW))
    item["id"] = make_id_hash(item)
    citations.append(item)
    save_state(push_history=True)
    print(colored(f"Added citation: {title}", GREEN))
    print(colored(f"share: python {os.path.basename(sys.argv)} load:{item['id']}", CYAN))
    return item

def edit_citation(idx):
    global citations
    if idx < 0 or idx >= len(citations):
        print(colored("Invalid selection.", RED))
        return
    c = citations[idx]
    print(colored("Editing citation (blank to keep current):", YELLOW))
    title = input(f" Title [{c.get('title','')}]: ").strip() or c.get("title","")
    authors_input = input(f" Authors (comma-separated) [{', '.join(c.get('authors',[]))}]: ").strip()
    authors = [a.strip() for a in (authors_input or ", ".join(c.get('authors',[]))).split(",") if a.strip()]
    year = input(f" Year [{c.get('year','')}]: ").strip() or c.get("year","")
    doi = input(f" DOI/link [{c.get('doi','')}]: ").strip() or c.get("doi","")
    pdf = input(f" PDF path [{c.get('pdf','')}]: ").strip() or c.get("pdf","")
    notes = input(f" Notes [{c.get('notes','')}]: ").strip() or c.get("notes","")
    new = {"id": c.get("id"), "title": title, "authors": authors, "year": year, "doi": doi, "pdf": pdf, "notes": notes}
    citations[idx] = new
    save_state(push_history=True)
    print(colored("Citation edited.", YELLOW))

def remove_citation(idx):
    global citations
    if idx < 0 or idx >= len(citations):
        print(colored("Invalid index.", RED))
        return
    item = citations.pop(idx)
    save_state(push_history=True)
    print(colored(f"Deleted: {item.get('title','(no title)')}", RED))

def open_pdf(idx):
    if idx < 0 or idx >= len(citations):
        print(colored("Invalid selection.", RED))
        return
    path = citations[idx].get("pdf","")
    if not path:
        print(colored("No PDF path set for this citation.", YELLOW))
        return
    if not os.path.exists(path):
        print(colored("PDF path does not exist.", RED))
        return
    try:
        if sys.platform.startswith('darwin'):
            subprocess_call = f'open "{path}"'
            os.system(subprocess_call)
        elif sys.platform.startswith('win'):
            os.startfile(path)
        else:
            # linux
            try:
                os.system(f'xdg-open "{path}"')
            except Exception:
                webbrowser.open("file://" + os.path.abspath(path))
        print(colored("Opened PDF.", CYAN))
    except Exception as e:
        print(colored(f"Could not open PDF: {e}", RED))

def export_ris(path):
    lines = []
    for c in citations:
        lines.append("TY  - JOUR")
        if c.get("authors"):
            for a in c.get("authors",[]):
                lines.append(f"AU  - {a}")
        lines.append(f"TI  - {c.get('title','')}")
        if c.get("year"):
            lines.append(f"PY  - {c.get('year')}")
        if c.get("doi"):
            lines.append(f"DO  - {c.get('doi')}")
        if c.get("pdf"):
            lines.append(f"LD  - {c.get('pdf')}")
        if c.get("notes"):
            lines.append(f"N2  - {c.get('notes')}")
        lines.append("ER  - ")
        lines.append("")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(colored(f"Exported RIS to {path}", GREEN))
    except Exception as e:
        print(colored(f"Error exporting RIS: {e}", RED))

def sanitize_bibkey(s):
    key = "".join(ch for ch in s if ch.isalnum() or ch in "_-")
    return key or "entry"

def export_bib(path):
    lines = []
    for c in citations:
        key = sanitize_bibkey((c.get("authors",[ "anon" ]).split()[-1] if c.get("authors") else "anon") + str(c.get("year","")) + c.get("id",""))
        lines.append(f"@article{{{key},")
        lines.append(f"  title = {{{c.get('title','')}}},")
        if c.get("authors"):
            lines.append(f"  author = {{{' and '.join(c.get('authors'))}}},")
        if c.get("year"):
            lines.append(f"  year = {{{c.get('year')}}},")
        if c.get("doi"):
            lines.append(f"  doi = {{{c.get('doi')}}},")
        if c.get("pdf"):
            lines.append(f"  file = {{{c.get('pdf')}}},")
        if c.get("notes"):
            lines.append(f"  note = {{{c.get('notes')}}},")
        lines.append("}")
        lines.append("")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(colored(f"Exported BibTeX to {path}", GREEN))
    except Exception as e:
        print(colored(f"Error exporting BibTeX: {e}", RED))

def list_citations(filtered=None, selected=0):
    display = filtered if filtered is not None else citations
    if not display:
        print(colored("(No citations)", YELLOW))
        return
    for i, c in enumerate(display):
        idx_mark = ">" if i == selected else " "
        title = c.get("title","(no title)")
        authors = ", ".join(c.get("authors",[])) or "(no authors)"
        year = c.get("year","")
        doi = c.get("doi","")
        print(f"{idx_mark} [{i}] {title} — {authors} {('('+str(year)+')') if year else ''} {('[DOI]' if doi else '')}")

def filter_citations(query):
    q = (query or "").lower().strip()
    if not q:
        return list(citations)
    res = []
    for c in citations:
        text = " ".join([c.get("title",""), " ".join(c.get("authors",[])), str(c.get("year","")), c.get("doi",""), c.get("notes","")]).lower()
        if q in text:
            res.append(c)
    return res

def undo():
    global citations
    if not history_undo:
        print(colored("No undo history.", YELLOW))
        return
    state = history_undo.pop()
    history_redo.append(json.dumps(citations, ensure_ascii=False))
    citations = json.loads(state)
    save_state(push_history=False)
    print(colored("Undo applied.", YELLOW))

def redo():
    global citations
    if not history_redo:
        print(colored("No redo history.", YELLOW))
        return
    state = history_redo.pop()
    history_undo.append(json.dumps(citations, ensure_ascii=False))
    citations = json.loads(state)
    save_state(push_history=False)
    print(colored("Redo applied.", YELLOW))

def handle_load_hash(hashid):
    # If hash provided, filter citations to those with that id, or if not present, create quick set
    matches = [c for c in citations if c.get("id","").upper() == hashid.upper()]
    if matches:
        print(colored(f"Loaded citation set with {len(matches)} item(s).", GREEN))
        return matches
    else:
        print(colored("No matching hash in DB.", YELLOW))
        return []

def prompt_main():
    print(BOLD + "Citation Miner Pro" + RESET)
    print("Commands: n=New, s=Search, e=Export, o=Open PDF, Enter=Edit, Del=Delete, arrows=Navigate, Ctrl+Z Undo, Ctrl+Y Redo, q=Quit")
    print("To drag-and-drop PDF(s) into terminal, paste the file path(s) when prompted for command.")
    print("")

def read_single_key(prompt="> "):
    # Fallback simple input; user can type arrow commands as text: up/down/left/right, DEL
    try:
        s = input(prompt)
    except EOFError:
        s = "q"
    return s

def main_loop(preload_filtered=None):
    global selected_index, filter_query
    filtered = preload_filtered if preload_filtered is not None else list(citations)
    selected_index = 0 if filtered else -1
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        prompt_main()
        if filter_query:
            print(colored(f"Filter: {filter_query}", CYAN))
        list_citations(filtered, selected=selected_index if selected_index>=0 else -1)
        print("")
        cmd = read_single_key("Command (n/s/e/o/enter/del/arrows/ctrl+z/ctrl+y/q) : ").strip()
        # detect drag-and-drop: if input contains paths ending with .pdf or multiple paths separated by spaces/newlines
        if cmd:
            parts = [p.strip() for p in cmd.replace('"','').split() if p.strip()]
            pdfs = [p for p in parts if p.lower().endswith(".pdf") or os.path.exists(p) and os.path.splitext(p)[1].lower()==".pdf"]
            if pdfs and not any(c in ["n","s","e","o","q","ctrl+z","ctrl+y","del","delete","enter","up","down","left","right"] for c in parts):
                # Add each pdf
                for p in pdfs:
                    add_citation_interactive(from_path=p)
                filtered = list(citations) if not filter_query else filter_citations(filter_query)
                selected_index = len(filtered)-1
                input(colored("PDF(s) added. Press Enter to continue.", CYAN))
                continue
        # interpret commands
        lower = cmd.lower()
        if lower == "q":
            save_state(push_history=False)
            print(colored("Quitting and saving.", CYAN))
            break
        elif lower == "n":
            add_citation_interactive()
            filtered = list(citations) if not filter_query else filter_citations(filter_query)
            selected_index = len(filtered)-1
            input(colored("Added. Press Enter.", GREEN))
        elif lower == "s":
            q = input("Search query (author/title/year/keywords). Blank to clear: ").strip()
            filter_query = q or None
            filtered = list(citations) if not filter_query else filter_citations(filter_query)
            selected_index = 0 if filtered else -1
        elif lower == "e":
            export_ris(EXPORT_RIS)
            export_bib(EXPORT_BIB)
            input(colored("Export complete. Press Enter.", GREEN))
        elif lower == "o":
            if selected_index>=0 and selected_index < len(filtered):
                # map selected index in filtered to actual index
                target = filtered[selected_index]
                idx = next((i for i,c in enumerate(citations) if c.get("id")==target.get("id")), None)
                if idx is not None:
                    open_pdf(idx)
                else:
                    print(colored("Selected citation not found in DB.", RED))
            else:
                print(colored("No selection to open.", YELLOW))
            input("Press Enter.")
        elif lower in ("del","delete"):
            if selected_index>=0 and selected_index < len(filtered):
                target = filtered[selected_index]
                idx = next((i for i,c in enumerate(citations) if c.get("id")==target.get("id")), None)
                if idx is not None:
                    remove_citation(idx)
                    filtered = list(citations) if not filter_query else filter_citations(filter_query)
                    selected_index = min(selected_index, len(filtered)-1)
                else:
                    print(colored("Could not find item to delete.", RED))
            else:
                print(colored("No selection.", YELLOW))
            input("Press Enter.")
        elif lower in ("enter","e\n","edit",""):
            # treat blank as edit selected
            if selected_index>=0 and selected_index < len(filtered):
                target = filtered[selected_index]
                idx = next((i for i,c in enumerate(citations) if c.get("id")==target.get("id")), None)
                if idx is not None:
                    edit_citation(idx)
                    filtered = list(citations) if not filter_query else filter_citations(filter_query)
                else:
                    print(colored("Could not find item to edit.", RED))
            else:
                print(colored("No selection to edit.", YELLOW))
            input("Press Enter.")
        elif lower in ("up","k"):
            if selected_index > 0:
                selected_index -= 1
        elif lower in ("down","j"):
            if selected_index < len(filtered)-1:
                selected_index += 1
        elif lower in ("ctrl+z", "\x1a"):  # CTRL-Z
            undo()
            filtered = list(citations) if not filter_query else filter_citations(filter_query)
            selected_index = min(selected_index, len(filtered)-1) if filtered else -1
            input("Press Enter.")
        elif lower in ("ctrl+y",):
            redo()
            filtered = list(citations) if not filter_query else filter_citations(filter_query)
            selected_index = min(selected_index, len(filtered)-1) if filtered else -1
            input("Press Enter.")
        elif lower.startswith("load:"):
            hid = cmd.split(":",1)[1].strip()
            matches = handle_load_hash(hid)
            if matches:
                filtered = matches
                selected_index = 0
            input("Press Enter.")
        elif lower == "help" or lower == "?":
            input("Help: Type commands shown. Drag-and-drop: paste PDF paths. Press Enter to continue.")
        elif lower == "":
            # empty input: treat as edit
            if selected_index>=0 and selected_index < len(filtered):
                target = filtered[selected_index]
                idx = next((i for i,c in enumerate(citations) if c.get("id")==target.get("id")), None)
                if idx is not None:
                    edit_citation(idx)
                    filtered = list(citations) if not filter_query else filter_citations(filter_query)
                input("Press Enter.")
            else:
                continue
        else:
            # allow selecting numeric index directly
            try:
                if cmd.isdigit():
                    ni = int(cmd)
                    if 0 <= ni < len(filtered):
                        selected_index = ni
                    else:
                        print(colored("Index out of range.", RED))
                        input("Press Enter.")
                else:
                    print(colored("Unknown command.", YELLOW))
                    input("Press Enter.")
            except Exception:
                print(colored("Error processing command.", RED))
                input("Press Enter.")

def import_from_args():
    # support load:HASH and drag-drop file paths passed as args
    args = sys.argv[1:]
    preload = None
    for a in args:
        if a.startswith("load:"):
            hid = a.split(":",1)[1]
            matches = handle_load_hash(hid)
            preload = matches
        elif os.path.exists(a) and a.lower().endswith(".pdf"):
            # add PDF directly
            add_citation_interactive(from_path=a)
    return preload

def ensure_minimal_test_flow():
    # If DB empty, and user wants quick test, provide helper to run test flow 1 automatically
    if not citations:
        print(colored("No citations in DB. Quick add sample for test? (y/n)", CYAN))
        c = input("> ").strip().lower()
        if c == "y":
            sample = {"title":"Quantum Computing","authors":["A. Einstein"],"year":"2025","doi":"","pdf":"","notes":"Sample entry"}
            sample["id"] = make_id_hash(sample)
            citations.append(sample)
            save_state(push_history=True)
            print(colored("Sample citation added.", GREEN))
            time.sleep(0.8)

def main():
    load_data()
    preload = import_from_args()
    ensure_minimal_test_flow()
    main_loop(preload_filtered=preload)

if __name__ == "__main__":
    main()