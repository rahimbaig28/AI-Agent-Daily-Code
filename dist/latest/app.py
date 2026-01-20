# Auto-generated via Perplexity on 2026-01-20T09:47:15.848471Z
#!/usr/bin/env python3
import json
import os
import sys
import datetime
import hashlib
import urllib.parse
import webbrowser
import subprocess
import shutil

# ANSI color codes
COLORS = {
    'reset': '\033[0m',
    'bold': '\033[1m',
    'green': '\033[92m',
    'red': '\033[91m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'cyan': '\033[96m'
}

HOME_DIR = os.path.expanduser('~/flashcards')
os.makedirs(HOME_DIR, exist_ok=True)

def print_colored(text, color='reset'):
    print(f"{COLORS[color]}{text}{COLORS['reset']}", end='')

def load_deck(deck_name):
    path = os.path.join(HOME_DIR, f"{deck_name}.json")
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        print("Invalid JSON file.")
        return None

def save_deck(deck, backup=True):
    path = os.path.join(HOME_DIR, f"{deck['name']}.json")
    bak_path = f"{path}.bak"
    try:
        if backup and os.path.exists(path):
            shutil.copy2(path, bak_path)
        with open(path, 'w') as f:
            json.dump(deck, f, indent=2)
        return True
    except Exception:
        return False

def hash_deck(deck):
    cards_str = json.dumps(sorted((c['front'], c['back']) for c in deck['cards']), sort_keys=True)
    return hashlib.sha256(f"{deck['name']}{cards_str}".encode()).hexdigest()[:16]

def find_deck_by_hash(hsh):
    for file in os.listdir(HOME_DIR):
        if file.endswith('.json'):
            deck = load_deck(file[:-5])
            if deck and hash_deck(deck) == hsh:
                return deck
    return None

def get_decks():
    decks = []
    for file in os.listdir(HOME_DIR):
        if file.endswith('.json'):
            deck = load_deck(file[:-5])
            if deck:
                decks.append(deck)
    return decks

def show_stats():
    decks = get_decks()
    total_decks = len(decks)
    total_cards = sum(d['stats']['total'] for d in decks)
    mastered_cards = sum(d['stats']['mastered'] for d in decks)
    avg_mastery = (mastered_cards / total_cards * 100) if total_cards else 0
    
    print_colored(f"\nGlobal Stats:", 'cyan')
    print(f"Total decks: {total_decks}")
    print(f"Total cards: {total_cards}")
    print(f"Mastered cards: {mastered_cards}")
    print(f"Average mastery: {avg_mastery:.1f}%")

def list_decks():
    decks = get_decks()
    decks.sort(key=lambda d: d['stats']['mastered'] / d['stats']['total'] if d['stats']['total'] else 0, reverse=True)
    
    print_colored("\nDecks (Mastery %):", 'cyan')
    for i, deck in enumerate(decks, 1):
        mastery = deck['stats']['mastered'] / deck['stats']['total'] * 100 if deck['stats']['total'] else 0
        print_colored(f"{i:2d}. ", 'yellow')
        print_colored(f"{deck['name']}", 'yellow')
        print_colored(f": {deck['stats']['mastered']}/{deck['stats']['total']} ", 'blue')
        print(f"({mastery:.0f}%)")

def create_deck():
    name = input("\nDeck name: ").strip()
    if not name:
        print("Deck name cannot be empty.")
        return
    
    if load_deck(name):
        print("Deck already exists.")
        return
    
    deck = {
        'name': name,
        'cards': [],
        'created': datetime.datetime.now().isoformat(),
        'stats': {'total': 0, 'mastered': 0}
    }
    
    print("Enter cards (front/back pairs). Empty line to finish:")
    while True:
        front = input("Front: ").strip()
        if not front:
            break
        back = input("Back: ").strip()
        if not back:
            print("Back cannot be empty.")
            continue
        deck['cards'].append({'front': front, 'back': back, 'mastered': False})
        deck['stats']['total'] += 1
    
    if save_deck(deck):
        print_colored("Deck created and saved!", 'green')
    else:
        print("Failed to save deck.")

def study_deck():
    decks = get_decks()
    if not decks:
        print("No decks found.")
        return
    
    list_decks()
    try:
        choice = int(input("\nSelect deck (0=back): ")) - 1
        if choice < 0 or choice >= len(decks):
            print("Invalid choice.")
            return
        deck = decks[choice]
    except ValueError:
        print("Invalid input.")
        return
    
    print_colored(f"\nStudying '{deck['name']}'", 'cyan')
    print("Commands: m=Mastered, a=Again, s=Skip, q=Quit, n=Next")
    
    unmastered = [c for c in deck['cards'] if not c['mastered']]
    if not unmastered:
        print("All cards mastered!")
        return
    
    import random
    random.shuffle(unmastered)
    count = 0
    
    for card in unmastered:
        print(f"\nFront: {card['front']}")
        input("Press Enter to reveal...")
        print(f"Back: {card['back']}")
        
        while True:
            cmd = input("Score (m/a/s/q/n): ").lower().strip()
            if cmd == 'm':
                card['mastered'] = True
                deck['stats']['mastered'] += 1
                print_colored("✓ Mastered!", 'green')
                count += 1
                break
            elif cmd == 'a':
                print_colored("✗ Again", 'red')
                break
            elif cmd == 's':
                print("→ Skipped")
                break
            elif cmd in ('q', 'n'):
                save_deck(deck)
                return
            else:
                print("Invalid: m/a/s/q/n")
        
        count += 1
        if count % 10 == 0:
            save_deck(deck)
    
    save_deck(deck)
    print_colored("\nStudy session complete!", 'cyan')

def import_deck():
    filename = input("\nJSON filename (.json): ").strip()
    if not filename.endswith('.json'):
        filename += '.json'
    
    path = os.path.join(HOME_DIR, filename)
    try:
        with open(path, 'r') as f:
            deck = json.load(f)
        if not all(k in deck for k in ['name', 'cards', 'stats']):
            print("Invalid deck format.")
            return
        if save_deck(deck):
            print_colored("Deck imported!", 'green')
    except Exception as e:
        print("Import failed.")

def export_deck():
    list_decks()
    decks = get_decks()
    try:
        choice = int(input("\nSelect deck to export (0=back): ")) - 1
        if choice < 0 or choice >= len(decks):
            return
        deck = decks[choice]
    except:
        return
    
    filename = input("Export filename (.json): ").strip()
    if not filename.endswith('.json'):
        filename += '.json'
    
    path = os.path.join(HOME_DIR, filename)
    if save_deck(deck.replace('name', filename[:-5]), False):  # temp name change
        print_colored("Deck exported!", 'green')

def print_deck():
    decks = get_decks()
    if not decks:
        print("No decks.")
        return
    
    list_decks()
    try:
        choice = int(input("\nSelect deck to print (0=back): ")) - 1
        if choice < 0 or choice >= len(decks):
            return
        deck = decks[choice]
    except:
        return
    
    output = "Front | Back | Status\n" + "-"*50 + "\n"
    for card in deck['cards']:
        status = "Mastered" if card['mastered'] else "Learning"
        output += f"{card['front'][:30]:30} | {card['back'][:30]:30} | {status}\n"
    
    try:
        if os.name == 'nt':  # Windows
            with open('temp_print.txt', 'w') as f:
                f.write(output)
            subprocess.call(['notepad', '/p', 'temp_print.txt'])
            os.remove('temp_print.txt')
        else:  # Unix
            p = subprocess.Popen(['lpr', '-'], stdin=subprocess.PIPE, text=True)
            p.communicate(input=output)
    except:
        print("Print failed, showing content:")
        print(output)

def share_deck():
    decks = get_decks()
    if not decks:
        print("No decks.")
        return
    
    list_decks()
    try:
        choice = int(input("\nSelect deck to share (0=back): ")) - 1
        if choice < 0 or choice >= len(decks):
            return
        deck = decks[choice]
    except:
        return
    
    hsh = hash_deck(deck)
    url = f"flashcardforge://{hsh}"
    print_colored(f"\nShare link: {url}", 'cyan')
    
    # Try clipboard (Unix)
    try:
        subprocess.run(['xclip', '-selection', 'clipboard'], input=url.encode())
        print("(Copied to clipboard)")
    except:
        pass  # Fallback to print

def main_menu():
    # Check for share link
    if len(sys.argv) > 1:
        hsh = sys.argv[1].replace('flashcardforge://', '')
        deck = find_deck_by_hash(hsh)
        if deck:
            print_colored(f"Loaded deck from link: {deck['name']}", 'green')
            study_deck_from_arg(deck)
            return
    
    while True:
        print_colored("\n" + "="*50, 'bold')
        print_colored("Flashcard Forge - Create, Study, Master", 'cyan')
        print("="*50)
        print("1. New Deck")
        print("2. Study Deck")
        print("3. List Decks")
        print("4. Import JSON")
        print("5. Export JSON")
        print("6. Print Deck")
        print("7. Share Link")
        print("8. Stats")
        print("0. Quit")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            create_deck()
        elif choice == '2':
            study_deck()
        elif choice == '3':
            list_decks()
        elif choice == '4':
            import_deck()
        elif choice == '5':
            export_deck()
        elif choice == '6':
            print_deck()
        elif choice == '7':
            share_deck()
        elif choice == '8':
            show_stats()
        elif choice == '0':
            print("Goodbye!")
            break
        else:
            print_colored("Invalid choice, try again.", 'red')

def study_deck_from_arg(deck):
    # Simplified study for shared decks
    print_colored(f"\nStudying '{deck['name']}' from share link", 'cyan')
    unmastered = [c for c in deck['cards'] if not c['mastered']]
    for card in unmastered[:10]:  # First 10 cards
        print(f"\nFront: {card['front']}")
        input("Press Enter...")
        print(f"Back: {card['back']}")
        cmd = input("m=Mastered/a=Again/q=Quit: ").lower()
        if cmd == 'm':
            card['mastered'] = True
            deck['stats']['mastered'] += 1
        elif cmd == 'q':
            break
    save_deck(deck)

if __name__ == "__main__":
    main_menu()