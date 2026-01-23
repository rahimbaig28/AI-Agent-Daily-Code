# Auto-generated via Perplexity on 2026-01-23T15:39:56.125943Z
import json
import os
import sys
import hashlib
import random
from datetime import datetime
from pathlib import Path

FLASHCARDS_FILE = "flashcards.json"
BACKUP_FILE = "flashcards.backup.json"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def color(text, code):
    return f"\033[{code}m{text}\033[0m"

def green(text):
    return color(text, "92")

def red(text):
    return color(text, "91")

def yellow(text):
    return color(text, "93")

def cyan(text):
    return color(text, "96")

def load_flashcards():
    if os.path.exists(FLASHCARDS_FILE):
        try:
            with open(FLASHCARDS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except (json.JSONDecodeError, IOError):
            if os.path.exists(BACKUP_FILE):
                try:
                    with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    pass
    return {}

def save_flashcards(data):
    try:
        if os.path.exists(FLASHCARDS_FILE):
            with open(FLASHCARDS_FILE, 'r', encoding='utf-8') as f:
                with open(BACKUP_FILE, 'w', encoding='utf-8') as bf:
                    bf.write(f.read())
    except:
        pass
    
    with open(FLASHCARDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_card(decks):
    clear_screen()
    print(cyan("=== Add Card ==="))
    deck_name = input("Deck name: ").strip()
    if not deck_name:
        print(red("Deck name cannot be empty."))
        input("Press Enter to continue...")
        return
    
    term = input("Term/Question: ").strip()
    if not term:
        print(red("Term cannot be empty."))
        input("Press Enter to continue...")
        return
    
    definition = input("Definition/Answer: ").strip()
    if not definition:
        print(red("Definition cannot be empty."))
        input("Press Enter to continue...")
        return
    
    if deck_name not in decks:
        decks[deck_name] = []
    
    for card in decks[deck_name]:
        if card['term'].lower() == term.lower():
            print(yellow("Term already exists in this deck."))
            input("Press Enter to continue...")
            return
    
    decks[deck_name].append({
        'term': term,
        'definition': definition,
        'added': datetime.utcnow().isoformat(),
        'correct': 0,
        'total': 0
    })
    
    save_flashcards(decks)
    print(green("Card added successfully!"))
    input("Press Enter to continue...")

def study_session(decks):
    clear_screen()
    print(cyan("=== Study Session ==="))
    
    if not decks:
        print(red("No decks available."))
        input("Press Enter to continue...")
        return
    
    deck_names = list(decks.keys())
    for i, name in enumerate(deck_names, 1):
        print(f"{i}. {name} ({len(decks[name])} cards)")
    
    try:
        choice = int(input("Select deck (number): ")) - 1
        if choice < 0 or choice >= len(deck_names):
            print(red("Invalid selection."))
            input("Press Enter to continue...")
            return
    except ValueError:
        print(red("Invalid input."))
        input("Press Enter to continue...")
        return
    
    deck_name = deck_names[choice]
    cards = decks[deck_name]
    
    if not cards:
        print(red("Deck is empty."))
        input("Press Enter to continue...")
        return
    
    print("\n1. Show term, hide definition")
    print("2. Show definition, hide term")
    try:
        mode = int(input("Select mode (1 or 2): "))
        if mode not in [1, 2]:
            raise ValueError
    except ValueError:
        print(red("Invalid mode."))
        input("Press Enter to continue...")
        return
    
    shuffled = cards.copy()
    random.shuffle(shuffled)
    
    correct_count = 0
    total_count = len(shuffled)
    
    for idx, card in enumerate(shuffled, 1):
        clear_screen()
        print(cyan(f"=== {deck_name} - Card {idx}/{total_count} ==="))
        
        if mode == 1:
            print(f"\n{green('Term:')} {card['term']}")
            input("Press Enter to reveal answer...")
            print(f"{green('Definition:')} {card['definition']}")
        else:
            print(f"\n{green('Definition:')} {card['definition']}")
            input("Press Enter to reveal term...")
            print(f"{green('Term:')} {card['term']}")
        
        result = input("\nCorrect? (y/n): ").strip().lower()
        if result == 'y':
            correct_count += 1
            card['correct'] = card.get('correct', 0) + 1
        
        card['total'] = card.get('total', 0) + 1
    
    save_flashcards(decks)
    
    accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
    clear_screen()
    print(cyan("=== Session Complete ==="))
    print(f"Cards reviewed: {total_count}")
    print(f"Correct: {correct_count}")
    print(f"Accuracy: {accuracy:.1f}%")
    input("Press Enter to continue...")

def list_decks(decks):
    clear_screen()
    print(cyan("=== Decks & Cards ==="))
    
    if not decks:
        print(red("No decks available."))
        input("Press Enter to continue...")
        return
    
    for deck_name, cards in decks.items():
        print(f"\n{green(deck_name)} ({len(cards)} cards)")
        for card in cards:
            mastery = f"{card.get('correct', 0)}/{card.get('total', 0)}" if card.get('total', 0) > 0 else "0/0"
            print(f"  • {card['term']} → {card['definition']} [{mastery}]")
    
    input("\nPress Enter to continue...")

def delete_card_or_deck(decks):
    clear_screen()
    print(cyan("=== Delete ==="))
    
    if not decks:
        print(red("No decks available."))
        input("Press Enter to continue...")
        return
    
    print("1. Delete card")
    print("2. Delete deck")
    choice = input("Select (1 or 2): ").strip()
    
    if choice == '1':
        deck_names = list(decks.keys())
        for i, name in enumerate(deck_names, 1):
            print(f"{i}. {name}")
        
        try:
            deck_idx = int(input("Select deck: ")) - 1
            if deck_idx < 0 or deck_idx >= len(deck_names):
                print(red("Invalid selection."))
                input("Press Enter to continue...")
                return
        except ValueError:
            print(red("Invalid input."))
            input("Press Enter to continue...")
            return
        
        deck_name = deck_names[deck_idx]
        cards = decks[deck_name]
        
        for i, card in enumerate(cards, 1):
            print(f"{i}. {card['term']}")
        
        try:
            card_idx = int(input("Select card to delete: ")) - 1
            if card_idx < 0 or card_idx >= len(cards):
                print(red("Invalid selection."))
                input("Press Enter to continue...")
                return
        except ValueError:
            print(red("Invalid input."))
            input("Press Enter to continue...")
            return
        
        del decks[deck_name][card_idx]
        save_flashcards(decks)
        print(green("Card deleted!"))
        input("Press Enter to continue...")
    
    elif choice == '2':
        deck_names = list(decks.keys())
        for i, name in enumerate(deck_names, 1):
            print(f"{i}. {name}")
        
        try:
            deck_idx = int(input("Select deck to delete: ")) - 1
            if deck_idx < 0 or deck_idx >= len(deck_names):
                print(red("Invalid selection."))
                input("Press Enter to continue...")
                return
        except ValueError:
            print(red("Invalid input."))
            input("Press Enter to continue...")
            return
        
        confirm = input(f"Delete '{deck_names[deck_idx]}'? (y/n): ").strip().lower()
        if confirm == 'y':
            del decks[deck_names[deck_idx]]
            save_flashcards(decks)
            print(green("Deck deleted!"))
        
        input("Press Enter to continue...")

def export_deck(decks):
    clear_screen()
    print(cyan("=== Export Deck ==="))
    
    if not decks:
        print(red("No decks available."))
        input("Press Enter to continue...")
        return
    
    deck_names = list(decks.keys())
    for i, name in enumerate(deck_names, 1):
        print(f"{i}. {name}")
    
    try:
        choice = int(input("Select deck: ")) - 1
        if choice < 0 or choice >= len(deck_names):
            print(red("Invalid selection."))
            input("Press Enter to continue...")
            return
    except ValueError:
        print(red("Invalid input."))
        input("Press Enter to continue...")
        return
    
    deck_name = deck_names[choice]
    filename = input("Export filename (default: deck_name.json): ").strip()
    if not filename:
        filename = f"{deck_name}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({deck_name: decks[deck_name]}, f, indent=2, ensure_ascii=False)
        print(green(f"Deck exported to {filename}"))
    except IOError as e:
        print(red(f"Export failed: {e}"))
    
    input("Press Enter to continue...")

def import_deck(decks):
    clear_screen()
    print(cyan("=== Import Deck ==="))
    
    filename = input("Import filename: ").strip()
    
    if not os.path.exists(filename):
        print(red("File not found."))
        input("Press Enter to continue...")
        return
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            imported = json.load(f)
        
        if not isinstance(imported, dict):
            print(red("Invalid JSON structure."))
            input("Press Enter to continue...")
            return
        
        for deck_name, cards in imported.items():
            if not isinstance(cards, list):
                print(red("Invalid deck structure."))
                input("Press Enter to continue...")
                return
            
            if deck_name in decks:
                confirm = input(f"Deck '{deck_name}' exists. Overwrite? (y/n): ").strip().lower()
                if confirm != 'y':
                    continue
            
            decks[deck_name] = cards
        
        save_flashcards(decks)
        print(green("Deck(s) imported successfully!"))
    except (json.JSONDecodeError, IOError) as e:
        print(red(f"Import failed: {e}"))
    
    input("Press Enter to continue...")

def share_deck(decks):
    clear_screen()
    print(cyan("=== Share Deck ==="))
    
    if not decks:
        print(red("No decks available."))
        input("Press Enter to continue...")
        return
    
    deck_names = list(decks.keys())
    for i, name in enumerate(deck_names, 1):
        print(f"{i}. {name}")
    
    try:
        choice = int(input("Select deck: ")) - 1
        if choice < 0 or choice >= len(deck_names):
            print(red("Invalid selection."))
            input("Press Enter to continue...")
            return
    except ValueError:
        print(red("Invalid input."))
        input("Press Enter to continue...")
        return
    
    deck_name = deck_names[choice]
    deck_data = json.dumps(decks[deck_name], ensure_ascii=False)
    deck_hash = hashlib.sha256(deck_data.encode()).hexdigest()[:8]
    
    script_path = os.path.abspath(__file__)
    share_url = f"file://{script_path}?deck={deck_hash}"
    
    print(f"\n{green('Share URL:')}")
    print(share_url)
    print(f"\n{yellow('Hash:')} {deck_hash}")
    
    input("Press Enter to continue...")

def main():
    decks = load_flashcards()
    
    deck_hash = None
    for arg in sys.argv[1:]:
        if arg.startswith('?deck='):
            deck_hash = arg.split('=')[1]
            break
    
    if deck_hash:
        matching_deck = None
        for deck_name, cards in decks.items():
            deck_data = json.dumps(cards, ensure_ascii=False)
            if hashlib.sha256(deck_data.encode()).hexdigest()[:8] == deck_hash:
                matching_deck = deck_name
                break
        
        if matching_deck:
            decks_copy = {matching_deck: decks[matching_deck]}
            study_session(decks_copy)
            return
    
    while True:
        clear_screen()
        print(cyan("╔════════════════════════════════════╗"))
        print(cyan("║     FLASHCARD FORGE v1.0          ║"))
        print(cyan("╚════════════════════════════════════╝"))
        print(f"\nDecks: {len(decks)}")
        print("\n1. Add card")
        print("2. Study session")
        print("3. List decks & cards")
        print("4. Delete card/deck")
        print("5. Export deck")
        print("6. Import deck")
        print("7. Share deck")
        print("8. Quit")
        
        choice = input("\nSelect option (1-8): ").strip()
        
        if choice == '1':
            add_card(decks)
        elif choice == '2':
            study_session(decks)
        elif choice == '3':
            list_decks(decks)
        elif choice == '4':
            delete_card_or_deck(decks)
        elif choice == '5':
            export_deck(decks)
        elif choice == '6':
            import_deck(decks)
        elif choice == '7':
            share_deck(decks)
        elif choice == '8':
            print(green("Goodbye!"))
            break
        else:
            print(red("Invalid option."))
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()