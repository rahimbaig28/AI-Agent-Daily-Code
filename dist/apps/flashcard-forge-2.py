# Auto-generated via Perplexity on 2025-12-22T08:28:44.063275Z
#!/usr/bin/env python3
import argparse
import json
import os
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

HOME = Path.home()
DATA_FILE = HOME / "flashcard_forge.json"
BACKUP_FILE = HOME / "flashcard_forge.json.backup"

def load_data():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            if BACKUP_FILE.exists():
                os.replace(BACKUP_FILE, DATA_FILE)
                with open(DATA_FILE, 'r') as f:
                    return json.load(f)
            return {}
    return {}

def save_data(data):
    backup = load_data()
    with open(BACKUP_FILE, 'w') as f:
        json.dump(backup, f)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def today():
    return datetime.now().date().isoformat()

def is_due(card):
    if 'last_review' not in card:
        return True
    due_date = datetime.fromisoformat(card['last_review']).date()
    return due_date + timedelta(days=card['interval_days']) <= datetime.now().date()

def update_card(card, rating):
    if rating == -1:  # Never again
        card['interval_days'] = 99999
    else:
        easiness = max(1.3, card.get('easiness', 2.5) + (0.1 - (5-rating)*0.08*(5-card.get('easiness', 2.5))))
        interval = card.get('interval_days', 1) * easiness
        card['interval_days'] = max(1, min(365, int(interval)))
        card['easiness'] = easiness
    card['last_review'] = datetime.now().isoformat()
    card['reviews'] = card.get('reviews', 0) + 1

def clear_screen():
    os.system('cls||clear')

def study_deck(decks, deck_name):
    if deck_name not in decks:
        print(f"Deck '{deck_name}' not found.")
        return
    
    cards = decks[deck_name]
    due_cards = [c for c in cards if is_due(c)]
    other_cards = [c for c in cards if not is_due(c)]
    
    session_cards = due_cards[:10]
    if len(session_cards) < 10 and other_cards:
        session_cards.extend(random.sample(other_cards, min(10-len(session_cards), len(other_cards))))
    
    if not session_cards:
        print("No cards to study.")
        return
    
    random.shuffle(session_cards)
    for i, card in enumerate(session_cards, 1):
        clear_screen()
        print(f"Card {i}/{len(session_cards)}")
        print(f"Front: {card['front']}")
        input("\nPress Enter to flip...")
        clear_screen()
        print(f"Back: {card['back']}")
        print("\nRate 0-5 (0=never, 5=perfect) or 'q' to quit: ", end="")
        sys.stdout.flush()
        resp = input()
        if resp.lower() == 'q':
            break
        try:
            rating = int(resp)
            if 0 <= rating <= 5:
                update_card(card, rating)
            else:
                print("Invalid rating. Skipping.")
        except ValueError:
            print("Invalid input. Skipping.")
    
    save_data(decks)

def print_stats(decks, deck_name):
    if deck_name not in decks:
        print(f"Deck '{deck_name}' not found.")
        return
    
    cards = decks[deck_name]
    total = len(cards)
    due = sum(1 for c in cards if is_due(c))
    reviewed = sum(1 for c in cards if 'reviews' in c and c['reviews'] > 0)
    
    print(f"Deck: {deck_name}")
    print(f"Total cards: {total}")
    print(f"Due today: {due}")
    print(f"Success rate: {reviewed/total*100:.1f}%" if total else "Success rate: N/A")

def main():
    parser = argparse.ArgumentParser(description="Flashcard Forge - Spaced Repetition CLI")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    add_parser = subparsers.add_parser('add', help='Add card to deck')
    add_parser.add_argument('deck', help='Deck name')
    add_parser.add_argument('front', help='Front of card')
    add_parser.add_argument('back', help='Back of card')
    
    study_parser = subparsers.add_parser('study', help='Study deck')
    study_parser.add_argument('deck', help='Deck name')
    
    list_parser = subparsers.add_parser('list', help='List all decks')
    
    stats_parser = subparsers.add_parser('stats', help='Show deck stats')
    stats_parser.add_argument('deck', help='Deck name')
    
    args = parser.parse_args()
    decks = load_data()
    
    if args.command == 'add':
        if args.deck not in decks:
            decks[args.deck] = []
        decks[args.deck].append({
            'front': args.front,
            'back': args.back,
            'interval_days': 1,
            'easiness': 2.5,
            'reviews': 0
        })
        save_data(decks)
        print(f"Added card to '{args.deck}'")
    
    elif args.command == 'study':
        study_deck(decks, args.deck)
    
    elif args.command == 'list':
        if not decks:
            print("No decks found.")
        else:
            for deck, cards in decks.items():
                print(f"{deck}: {len(cards)} cards")
    
    elif args.command == 'stats':
        print_stats(decks, args.deck)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()