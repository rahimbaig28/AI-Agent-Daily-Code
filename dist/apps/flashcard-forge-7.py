# Auto-generated via Perplexity on 2026-02-08T18:54:40.317189Z
#!/usr/bin/env python3
import json
import os
import pickle
import random
import readline
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque

HOME_DIR = Path.home() / ".flashcard_forge"
DECKS_DIR = HOME_DIR / "decks"
UNDO_STACK = deque(maxlen=10)
REDO_STACK = deque(maxlen=10)

COLORS = {
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'RED': '\033[91m',
    'BLUE': '\033[94m',
    'RESET': '\033[0m'
}

def printc(text, color=''):
    print(f"{COLORS.get(color, '')}{text}{COLORS['RESET']}")

def get_decks_dir():
    DECKS_DIR.mkdir(parents=True, exist_ok=True)
    return DECKS_DIR

def load_deck(name):
    deck_path = get_decks_dir() / f"{name}.json"
    if deck_path.exists():
        with open(deck_path, 'r') as f:
            return json.load(f)
    return {"cards": [], "name": name}

def save_deck(deck):
    deck_path = get_decks_dir() / f"{deck['name']}.json"
    with open(deck_path, 'w') as f:
        json.dump(deck, f, indent=2)

def card_due_date(card):
    if 'due_date' not in card:
        return datetime.now()
    return datetime.fromisoformat(card['due_date'])

def parse_card_args(args):
    if len(args) < 3:
        return None, None, None
    deck = args[0]
    front = ' '.join(args[1:-1]).strip('"\'')
    back = args[-1].strip('"\'')
    return deck, front, back

def cmd_new_deck(args):
    if len(args) != 1:
        printc("Usage: new deck <name>", 'RED')
        return
    name = args[0]
    if (get_decks_dir() / f"{name}.json").exists():
        printc(f"Deck '{name}' already exists!", 'YELLOW')
        return
    deck = {"name": name, "cards": []}
    save_deck(deck)
    printc(f"Created empty deck '{name}'", 'GREEN')

def cmd_add(args):
    global UNDO_STACK, REDO_STACK
    deck_name, front, back = parse_card_args(args)
    if not deck_name or not front or not back:
        printc("Usage: add <deck> \"front\" \"back\"", 'RED')
        return
    
    deck = load_deck(deck_name)
    card = {
        "front": front,
        "back": back,
        "due_date": datetime.now().isoformat(),
        "reviews": []
    }
    deck["cards"].append(card)
    save_deck(deck)
    
    UNDO_STACK.append(("add", deck_name, card))
    REDO_STACK.clear()
    printc(f"Added card to '{deck_name}'", 'GREEN')

def cmd_list(args):
    decks = []
    for path in get_decks_dir().glob("*.json"):
        deck = load_deck(path.stem)
        decks.append((path.stem, len(deck["cards"])))
    
    if not decks:
        printc("No decks found", 'YELLOW')
        return
    
    printc("Decks:", 'BLUE')
    for name, count in sorted(decks):
        printc(f"  {name}: {count} cards", 'GREEN' if count > 0 else '')

def cmd_stats(args):
    if len(args) != 1:
        printc("Usage: stats <deck>", 'RED')
        return
    
    deck = load_deck(args[0])
    now = datetime.now()
    due_count = sum(1 for c in deck["cards"] if card_due_date(c) <= now)
    total = len(deck["cards"])
    
    if total == 0:
        printc("No cards in deck", 'YELLOW')
        return
    
    success_rate = 0
    total_reviews = sum(len(c.get("reviews", [])) for c in deck["cards"])
    if total_reviews > 0:
        success = sum(r for c in deck["cards"] for r in c.get("reviews", []) if r >= 2)
        success_rate = (success / total_reviews) * 100
    
    printc(f"{args[0]}: {due_count}/{total} due ({success_rate:.1f}% success)", 'BLUE')

def cmd_delete(args):
    global UNDO_STACK, REDO_STACK
    if len(args) != 1:
        printc("Usage: del <deck>", 'RED')
        return
    
    deck_path = get_decks_dir() / f"{args[0]}.json"
    if deck_path.exists():
        deck_backup = load_deck(args[0])
        deck_path.unlink()
        UNDO_STACK.append(("delete", args[0], deck_backup))
        REDO_STACK.clear()
        printc(f"Deleted deck '{args[0]}'", 'RED')
    else:
        printc(f"Deck '{args[0]}' not found", 'YELLOW')

def cmd_undo(args):
    global UNDO_STACK, REDO_STACK
    if not UNDO_STACK:
        printc("Nothing to undo", 'YELLOW')
        return
    
    action = UNDO_STACK.pop()
    REDO_STACK.append(action)
    
    if action[0] == "add":
        _, deck_name, card = action
        deck = load_deck(deck_name)
        deck["cards"] = [c for c in deck["cards"] if c != card]
        save_deck(deck)
        printc("Undone: card removal", 'GREEN')
    elif action[0] == "delete":
        _, deck_name, deck_backup = action
        save_deck(deck_backup)
        printc("Undone: deck restoration", 'GREEN')

def cmd_redo(args):
    global UNDO_STACK, REDO_STACK
    if not REDO_STACK:
        printc("Nothing to redo", 'YELLOW')
        return
    
    action = REDO_STACK.pop()
    UNDO_STACK.append(action)
    
    if action[0] == "add":
        _, deck_name, card = action
        deck = load_deck(deck_name)
        deck["cards"].append(card)
        save_deck(deck)
        printc("Redone: card addition", 'GREEN')
    elif action[0] == "delete":
        _, deck_name, _ = action
        deck_path = get_decks_dir() / f"{deck_name}.json"
        deck_path.unlink()
        printc("Redone: deck deletion", 'RED')

def study_mode(deck_name):
    deck = load_deck(deck_name)
    cards = deck["cards"][:]
    
    if not cards:
        printc("No cards to study", 'YELLOW')
        return
    
    # Sort by due date (overdue first)
    cards.sort(key=card_due_date)
    
    printc(f"\n=== Studying {deck_name} ({len(cards)} cards) ===", 'BLUE')
    printc("Press Enter to reveal answer, then 1-4 to rate (1=easy,4=again)", 'YELLOW')
    printc("Ctrl+C or 'q' to quit", 'YELLOW')
    
    try:
        for i, card in enumerate(cards, 1):
            printc(f"\n{i}. {card['front']}", 'GREEN')
            input("Press Enter to reveal...")
            printc(f"Answer: {card['back']}", 'BLUE')
            
            while True:
                try:
                    rating = input("Rate (1-4, q=quit): ").strip()
                    if rating.lower() == 'q':
                        save_deck(deck)
                        return
                    rating = int(rating)
                    if 1 <= rating <= 4:
                        break
                    printc("Please enter 1-4", 'RED')
                except ValueError:
                    printc("Please enter 1-4", 'RED')
            
            # Update card based on rating
            now = datetime.now()
            card["reviews"].append(rating)
            
            intervals = [timedelta(days=0), timedelta(days=1), timedelta(days=3), timedelta(days=7)]
            due_delta = intervals[rating - 1]
            card["due_date"] = (now + due_delta).isoformat()
            
            if i % 5 == 0:  # Auto-save every 5 cards
                save_deck(deck)
                printc("Auto-saved progress", 'GREEN')
        
        save_deck(deck)
        printc("\nStudy session complete!", 'GREEN')
        
    except KeyboardInterrupt:
        save_deck(deck)
        printc("\n\nStudy session interrupted - progress saved", 'YELLOW')

def cmd_study(args):
    if len(args) != 1:
        printc("Usage: study <deck>", 'RED')
        return
    study_mode(args[0])

def complete_commands(text, state):
    commands = {
        'new deck ': [''],
        'add ': [''],
        'study ': [p.stem for p in get_decks_dir().glob("*.json")],
        'stats ': [p.stem for p in get_decks_dir().glob("*.json")],
        'del ': [p.stem for p in get_decks_dir().glob("*.json")],
        '': ['new deck', 'add', 'study', 'list', 'stats', 'del', 'undo', 'redo', 'quit']
    }
    
    matches = []
    for prefix, options in commands.items():
        if text.startswith(prefix):
            for opt in options:
                if opt.startswith(text[len(prefix):]):
                    matches.append(prefix + opt)
    
    try:
        return matches[state]
    except IndexError:
        return []

def main():
    readline.set_completer(complete_commands)
    readline.parse_and_bind('tab: complete')
    
    printc("=== Flashcard Forge ===", 'BLUE')
    printc("Commands: new deck, add, study, list, stats, del, undo, redo, quit", 'YELLOW')
    
    while True:
        try:
            line = input("\n> ").strip()
            if not line:
                continue
            
            parts = line.split(maxsplit=0)[0].split()
            cmd = parts[0].lower()
            args = line.split()[1:] if len(parts) > 1 else []
            
            if cmd == 'quit' or cmd == 'q':
                printc("Goodbye!", 'GREEN')
                break
            elif cmd == 'new' and len(parts) > 1 and parts[1] == 'deck':
                cmd_new_deck(args)
            elif cmd == 'add':
                cmd_add(args)
            elif cmd == 'study':
                cmd_study(args)
            elif cmd == 'list':
                cmd_list(args)
            elif cmd == 'stats':
                cmd_stats(args)
            elif cmd == 'del':
                cmd_delete(args)
            elif cmd == 'undo':
                cmd_undo(args)
            elif cmd == 'redo':
                cmd_redo(args)
            else:
                printc(f"Unknown command: {cmd}", 'RED')
                
        except KeyboardInterrupt:
            printc("\n\nGoodbye!", 'GREEN')
            break
        except EOFError:
            printc("\nGoodbye!", 'GREEN')
            break

if __name__ == "__main__":
    main()