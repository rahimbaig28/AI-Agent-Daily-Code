# Auto-generated via Perplexity on 2026-01-18T09:33:01.232427Z
#!/usr/bin/env python3
import json
import os
import sys
import random
import hashlib
import base64
import urllib.parse
import webbrowser

HOME_DIR = os.path.expanduser("~")
FLASHCARDS_FILE = os.path.join(HOME_DIR, "flashcards.json")

def load_flashcards():
    try:
        if os.path.exists(FLASHCARDS_FILE):
            with open(FLASHCARDS_FILE, 'r') as f:
                return json.load(f)
        return []
    except (json.JSONDecodeError, PermissionError, OSError):
        print("Warning: Could not load flashcards file. Starting with empty deck.")
        return []

def save_flashcards(flashcards):
    try:
        os.makedirs(os.path.dirname(FLASHCARDS_FILE), exist_ok=True)
        with open(FLASHCARDS_FILE, 'w') as f:
            json.dump(flashcards, f, indent=2)
    except (PermissionError, OSError) as e:
        print(f"Warning: Could not save flashcards: {e}")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_menu():
    print("\n=== Flashcard Forge ===")
    print("a - Add card")
    print("s - Study")
    print("v - View all")
    print("e - Edit")
    print("d - Delete")
    print("q - Quit")
    print("======================")

def add_card(flashcards):
    front = input("Front (question): ").strip()
    if not front:
        print("Empty front. Card not added.")
        return
    back = input("Back (answer): ").strip()
    if not back:
        print("Empty back. Card not added.")
        return
    flashcards.append({"front": front, "back": back})
    print("Card added!")
    save_flashcards(flashcards)

def view_flashcards(flashcards):
    if not flashcards:
        print("No cards.")
        return
    print("\n--- All Cards ---")
    for i, card in enumerate(flashcards, 1):
        print(f"{i:2d}. {card['front']}")
        print(f"    {card['back']}")
    print("-----------------")

def get_valid_index(prompt, max_idx):
    while True:
        try:
            idx = int(input(prompt)) - 1
            if 0 <= idx < max_idx:
                return idx
            print(f"Please enter a number between 1 and {max_idx}")
        except ValueError:
            print("Please enter a valid number")

def edit_card(flashcards):
    if not flashcards:
        print("No cards to edit.")
        return
    view_flashcards(flashcards)
    idx = get_valid_index("Enter card number to edit: ", len(flashcards))
    front = input(f"New front (current: {flashcards[idx]['front']}): ").strip()
    if front:
        flashcards[idx]['front'] = front
    back = input(f"New back (current: {flashcards[idx]['back']}): ").strip()
    if back:
        flashcards[idx]['back'] = back
    print("Card updated!")
    save_flashcards(flashcards)

def delete_card(flashcards):
    if not flashcards:
        print("No cards to delete.")
        return
    view_flashcards(flashcards)
    idx = get_valid_index("Enter card number to delete: ", len(flashcards))
    removed = flashcards.pop(idx)
    print(f"Deleted: {removed['front']}")
    save_flashcards(flashcards)

def study_mode(flashcards):
    if not flashcards:
        print("No cards to study.")
        return
    
    # Shuffle and track bad cards
    deck = flashcards[:]
    random.shuffle(deck)
    bad_cards = []
    
    while deck:
        clear_screen()
        print("\n=== Study Mode ===")
        print("Enter - reveal | s - skip | g - good | b - bad")
        print("=" * 30)
        
        card = deck.pop(0)
        print(f"Q: {card['front']}")
        
        cmd = input("\n> ").strip().lower()
        
        if cmd == 's':
            deck.append(card)
            continue
        elif cmd == 'g':
            continue
        elif cmd == 'b':
            bad_cards.append(card)
            continue
        else:
            # Enter or any other key: reveal
            print(f"A: {card['back']}")
            cmd = input("g - good | b - bad | s - skip: ").strip().lower()
            if cmd == 'g':
                continue
            elif cmd == 'b':
                bad_cards.append(card)
            else:
                deck.append(card)
    
    # Put bad cards at front for next session
    flashcards[:] = bad_cards + flashcards
    save_flashcards(flashcards)
    print("\nStudy session complete!")

def generate_share_url(flashcards):
    if not flashcards:
        print("No cards to share.")
        return
    
    data = json.dumps(flashcards)
    # Create short hash for readability
    hash_obj = hashlib.sha256(data.encode()).digest()[:8]
    hash_str = base64.urlsafe_b64encode(hash_obj).decode()[:8]
    
    # Base64 encode the data
    encoded = base64.urlsafe_b64encode(data.encode()).decode()
    url = f"data:text/plain;base64,{encoded}"
    
    print(f"\nShare URL (copy this):")
    print(f"flashcardforge://{hash_str}#{encoded[:50]}...")
    print("(Full URL opened in browser)")
    
    try:
        webbrowser.open(url)
    except:
        print("Could not open browser. Copy the full data:URL above.")
    
    # Also save to clipboard-like output
    print("\nFull data:URL (for manual copy):")
    print(url)

def main():
    flashcards = load_flashcards()
    
    while True:
        clear_screen()
        print_menu()
        
        cmd = input("\n> ").strip().lower()
        
        if cmd == 'a':
            add_card(flashcards)
        elif cmd == 's':
            study_mode(flashcards)
        elif cmd == 'v':
            view_flashcards(flashcards)
            input("\nPress Enter to continue...")
        elif cmd == 'e':
            edit_card(flashcards)
        elif cmd == 'd':
            delete_card(flashcards)
        elif cmd == 'q':
            print("Goodbye!")
            save_flashcards(flashcards)
            break
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()