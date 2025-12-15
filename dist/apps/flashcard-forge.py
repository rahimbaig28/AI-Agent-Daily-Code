# Auto-generated via Perplexity on 2025-12-15T08:30:52.822016Z
import json
import os
import sys
import random
import datetime
import curses
import readline
from collections import defaultdict

DATA_FILE = "flashcards.json"

def load_deck():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_deck(deck):
    backup_file = f"{DATA_FILE}.backup"
    if os.path.exists(DATA_FILE):
        os.rename(DATA_FILE, backup_file)
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(deck, f, indent=2)
        if os.path.exists(backup_file):
            os.remove(backup_file)
    except:
        if os.path.exists(backup_file):
            os.rename(backup_file, DATA_FILE)

def get_stats(deck):
    total = len(deck)
    if total == 0:
        return {"total": 0, "avg_streak": 0, "hardest_tags": []}
    
    streaks = [card.get("streak", 0) for card in deck]
    avg_streak = sum(streaks) / total
    
    tag_stats = defaultdict(lambda: {"total": 0, "fails": 0})
    for card in deck:
        tag = card.get("tag", "untagged")
        streak = card.get("streak", 0)
        tag_stats[tag]["total"] += 1
        if streak < 2:
            tag_stats[tag]["fails"] += 1
    
    hardest_tags = sorted(
        [(tag, stats["fails"] / stats["total"]) for tag, stats in tag_stats.items()],
        key=lambda x: x[1], reverse=True
    )[:5]
    
    return {
        "total": total,
        "avg_streak": round(avg_streak, 1),
        "hardest_tags": hardest_tags
    }

class FlashcardApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(1)
        self.deck = load_deck()
        self.current_menu = "main"
        self.selected = 0
        self.study_cards = []
        self.current_card_idx = 0
        self.flipped = False
        self.session_stats = {"total": 0, "easy": 0, "hard": 0, "again": 0}
        self.main_loop()
    
    def draw_border(self, y, x, h, w, title=""):
        self.stdscr.addch(y, x, curses.ACS_ULCORNER)
        self.stdscr.addch(y, x + w - 1, curses.ACS_URCORNER)
        self.stdscr.addch(y + h - 1, x, curses.ACS_LLCORNER)
        self.stdscr.addch(y + h - 1, x + w - 1, curses.ACS_URCORNER)
        for i in range(x + 1, x + w - 1):
            self.stdscr.addch(y, i, curses.ACS_HLINE)
            self.stdscr.addch(y + h - 1, i, curses.ACS_HLINE)
        for i in range(y + 1, y + h - 1):
            self.stdscr.addch(i, x, curses.ACS_VLINE)
            self.stdscr.addch(i, x + w - 1, curses.ACS_VLINE)
        if title:
            self.stdscr.addstr(y, x + 2, title[:w-5])
    
    def draw_menu(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        self.draw_border(1, 2, 10, w-4, "Flashcard Forge")
        
        menu_items = [
            "1) Add Card",
            "2) Study Session", 
            "3) Edit Deck",
            "4) Delete Deck",
            "5) Stats",
            "6) Quit"
        ]
        
        for i, item in enumerate(menu_items):
            y = 3 + i * 2
            attr = curses.A_REVERSE if i == self.selected else 0
            self.stdscr.addstr(y, 5, item, attr)
        
        self.stdscr.addstr(h-2, 5, "↑↓: Navigate  Enter: Select  ?: Help  Ctrl+C: Quit")
        self.stdscr.refresh()
    
    def draw_stats(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        self.draw_border(1, 2, h-4, w-4, "Statistics")
        
        stats = get_stats(self.deck)
        y = 3
        
        self.stdscr.addstr(y, 5, f"Total cards: {stats['total']}", curses.A_BOLD); y += 2
        self.stdscr.addstr(y, 5, f"Avg streak: {stats['avg_streak']}", curses.A_BOLD); y += 2
        
        self.stdscr.addstr(y, 5, "Hardest tags:", curses.A_BOLD); y += 2
        for tag, fail_rate in stats['hardest_tags']:
            color = curses.color_pair(1) if fail_rate > 0.5 else 0
            self.stdscr.addstr(y, 7, f"{tag}: {fail_rate:.1%}", color); y += 1
        
        self.stdscr.addstr(h-2, 5, "Enter: Main Menu")
        self.stdscr.refresh()
    
    def draw_add_card(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        self.draw_border(1, 2, h-4, w-4, "Add Card")
        
        y = 4
        self.stdscr.addstr(y, 5, "Front (question):"); y += 2
        self.stdscr.addstr(y, 5, "Back (answer):"); y += 2
        self.stdscr.addstr(y, 5, "Tag (optional):"); y += 2
        
        self.stdscr.move(6, 23)
        self.stdscr.clrtoeol()
        self.stdscr.move(8, 22)
        self.stdscr.clrtoeol()
        self.stdscr.move(10, 23)
        self.stdscr.clrtoeol()
        
        self.stdscr.refresh()
    
    def readline_input(self, prompt):
        def completer(text, state):
            return None
        
        readline.set_completer(completer)
        readline.parse_and_bind('tab: complete')
        try:
            return input(prompt)
        except:
            return ""
    
    def add_card(self):
        try:
            front = self.readline_input("Front (question): ").strip()
            if not front:
                return
            
            back = self.readline_input("Back (answer): ").strip()
            if not back:
                return
                
            tag = self.readline_input("Tag (optional): ").strip()
            
            card = {
                "front": front,
                "back": back,
                "tag": tag,
                "streak": 0,
                "last_seen": datetime.datetime.now().isoformat()
            }
            self.deck.append(card)
            save_deck(self.deck)
        except KeyboardInterrupt:
            pass
    
    def draw_edit_deck(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        self.draw_border(1, 2, h-4, w-4, "Edit Deck")
        
        if not self.deck:
            self.stdscr.addstr(h//2, w//2 - 10, "No cards to edit")
            self.stdscr.refresh()
            return
        
        for i, card in enumerate(self.deck):
            y = 3 + i
            if y >= h-4:
                break
            attr = curses.A_REVERSE if i == self.selected else 0
            front = card["front"][:w-20]
            self.stdscr.addstr(y, 5, f"{i+1:2d}. {front}", attr)
        
        self.stdscr.addstr(h-3, 5, f"Selected: {self.selected + 1}/{len(self.deck)}")
        self.stdscr.addstr(h-2, 5, "↑↓: Navigate  Enter: Edit  D: Delete  Q: Back")
        self.stdscr.refresh()
    
    def edit_card(self):
        if not self.deck or self.selected >= len(self.deck):
            return
        
        card = self.deck[self.selected]
        try:
            front = self.readline_input(f"Front [{card['front']}]: ").strip()
            if front:
                card['front'] = front
                
            back = self.readline_input(f"Back [{card['back']}]: ").strip()
            if back:
                card['back'] = back
            
            tag = self.readline_input(f"Tag [{card.get('tag', '')}]: ").strip()
            if tag:
                card['tag'] = tag
            
            card['last_seen'] = datetime.datetime.now().isoformat()
            save_deck(self.deck)
        except KeyboardInterrupt:
            pass
    
    def delete_card(self):
        if self.deck and self.selected < len(self.deck):
            del self.deck[self.selected]
            if self.selected >= len(self.deck):
                self.selected = max(0, len(self.deck) - 1)
            save_deck(self.deck)
    
    def start_study_session(self):
        if not self.deck:
            return
        
        self.study_cards = self.deck[:]
        random.shuffle(self.study_cards)
        self.current_card_idx = 0
        self.flipped = False
        self.session_stats = {"total": 0, "easy": 0, "hard": 0, "again": 0}
        self.current_menu = "study"
    
    def draw_study_session(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        self.draw_border(1, 2, h-4, w-4, "Study Session")
        
        if self.current_card_idx >= len(self.study_cards):
            # Session complete
            self.draw_session_results()
            return
        
        card = self.study_cards[self.current_card_idx]
        y = 4
        
        # Progress bar
        progress = (self.current_card_idx + 1) / len(self.study_cards)
        bar_width = w - 12
        filled = int(progress * bar_width)
        self.stdscr.addstr(y, 5, f"Progress: [{ '#' * filled + ' ' * (bar_width - filled) }]");
        y += 1
        self.stdscr.addstr(y, 5, f"Card {self.current_card_idx + 1}/{len(self.study_cards)}"); y += 2
        
        text = card["front"][:w-10]
        if self.flipped:
            text = card["back"][:w-10]
            streak_color = curses.color_pair(2) if card.get("streak", 0) >= 3 else curses.color_pair(1)
            self.stdscr.addstr(y, 5, text, curses.A_BOLD | streak_color)
        else:
            self.stdscr.addstr(y, 5, text, curses.A_BOLD)
        
        y += 2
        self.stdscr.addstr(y, 5, f"Tag: {card.get('tag', 'untagged')}"); y += 2
        
        if self.flipped:
            self.stdscr.addstr(y, 5, "1:EASY  2:HARD  3:AGAIN  SPACE:Next  Q:Quit", curses.A_BOLD)
        else:
            self.stdscr.addstr(y, 5, "SPACE: Flip", curses.A_BOLD)
        
        self.stdscr.addstr(h-2, 5, f"Session: {self.session_stats['total']} cards")
        self.stdscr.refresh()
    
    def draw_session_results(self):
        h, w = self.stdscr.getmaxyx()
        y = 4
        self.stdscr.addstr(y, 5, "Session Complete!", curses.A_BOLD); y += 2
        
        total = self.session_stats['total']
        if total > 0:
            easy_pct = self.session_stats['easy'] / total * 100
            self.stdscr.addstr(y, 5, f"Easy: {easy_pct:.0f}%"); y += 1
            self.stdscr.addstr(y, 5, f"Hard: {self.session_stats['hard']/total*100:.0f}%"); y += 1
            self.stdscr.addstr(y, 5, f"Again: {self.session_stats['again']/total*100:.0f}%")
        
        self.stdscr.addstr(h-2, 5, "Enter: Main Menu")
        self.stdscr.refresh()
    
    def rate_card(self, rating):
        if self.current_card_idx >= len(self.study_cards):
            return
        
        card = self.study_cards[self.current_card_idx]
        current_streak = card.get("streak", 0)
        
        if rating == 1:  # EASY
            card["streak"] = current_streak + 1
            self.session_stats["easy"] += 1
        elif rating == 2:  # HARD
            card["streak"] = max(0, current_streak - 1)
            self.session_stats["hard"] += 1
        else:  # AGAIN
            card["streak"] = 0
            self.session_stats["again"] += 1
        
        card["last_seen"] = datetime.datetime.now().isoformat()
        self.session_stats["total"] += 1
        save_deck(self.deck)
    
    def next_card(self):
        self.flipped = False
        self.current_card_idx += 1
        if self.current_card_idx >= len(self.study_cards):
            return
    
    def draw_help(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        self.draw_border(1, 2, h-4, w-4, "Help")
        
        help_text = [
            "MAIN MENU: ↑↓ Navigate, Enter Select",
            "ADD CARD: Type front/back/tag, Enter to save",
            "STUDY: SPACE flip, 1=EASY 2=HARD 3=AGAIN, SPACE next",
            "EDIT: ↑↓ select, Enter edit, D delete",
            "STATS: Shows deck statistics",
            "",
            "Global: Q=Back/Quit, ? =Help, Ctrl+C=Quit"
        ]
        
        for i, line in enumerate(help_text):
            self.stdscr.addstr(4 + i, 5, line)
        
        self.stdscr.addstr(h-2, 5, "Enter: Continue")
        self.stdscr.refresh()
        self.stdscr.getch()
    
    def main_loop(self):
        curses.curs_set(0)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)     # Hard/fail
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Easy/success
        
        while True:
            try:
                if self.current_menu == "main":
                    self.draw_menu()
                    key = self.stdscr.getch()
                    if key == curses.KEY_UP and self.selected > 0:
                        self.selected -= 1
                    elif key == curses.KEY_DOWN and self.selected < 5:
                        self.selected += 1
                    elif key == 10 or key == curses.KEY_ENTER:  # Enter
                        if self.selected == 0:
                            self.add_card()
                        elif self.selected == 1:
                            self.start_study_session()
                        elif self.selected == 2:
                            self.current_menu = "edit"
                            self.selected = 0
                        elif self.selected == 3:
                            self.delete_card()
                        elif self.selected == 4:
                            self.current_menu = "stats"
                        elif self.selected == 5:
                            break
                    elif key == ord('?'):
                        self.draw_help()
                    elif key == ord('q') or key == 3:  # Ctrl+C
                        break
                
                elif self.current_menu == "stats":
                    self.draw_stats()
                    if self.stdscr.getch() == 10:
                        self.current_menu = "main"
                        self.selected = 0
                
                elif self.current_menu == "edit":
                    self.draw_edit_deck()
                    key = self.stdscr.getch()
                    if key == curses.KEY_UP and self.selected > 0:
                        self.selected -= 1
                    elif key == curses.KEY_DOWN and self.selected < len(self.deck) - 1:
                        self.selected += 1
                    elif key == 10 or key == curses.KEY_ENTER:
                        self.edit_card()
                    elif key == ord('d') or key == ord('D'):
                        self.delete_card()
                    elif key == ord('q') or key == 3:
                        self.current_menu = "main"
                        self.selected = 0
                
                elif self.current_menu == "study":
                    self.draw_study_session()
                    key = self.stdscr.getch()
                    if key == ord(' '):  # Space
                        if self.flipped:
                            self.next_card()
                        else:
                            self.flipped = True
                    elif self.flipped:
                        if key == ord('1'):
                            self.rate_card(1)
                            self.next_card()
                        elif key == ord('2'):
                            self.rate_card(2)
                            self.next_card()
                        elif key == ord('3'):
                            self.rate_card(3)
                            self.next_card()
                        elif key == ord('q') or key == 3:
                            self.current_menu = "main"
                            self.selected = 1
                    else:
                        if key == ord('q') or key == 3:
                            self.current_menu = "main"
                            self.selected = 1
                
            except KeyboardInterrupt:
                break
        
        curses.endwin()

def console_fallback():
    print("Flashcard Forge (Console Mode)")
    deck = load_deck()
    
    while True:
        print("\n1) Add Card  2) Study  3) Edit  4) Stats  5) Quit")
        choice = input("Choose: ").strip()
        
        if choice == "1":
            front = input("Front: ").strip()
            back = input("Back: ").strip()
            tag = input("Tag: ").strip()
            deck.append({"front": front, "back": back, "tag": tag, "streak": 0})
            save_deck(deck)
        elif choice == "5":
            break

if __name__ == "__main__":
    try:
        os.environ.setdefault('ESCDELAY', '25')
        curses.wrapper(FlashcardApp)
    except:
        console_fallback()