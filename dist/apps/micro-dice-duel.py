# Auto-generated via Perplexity on 2026-01-07T01:38:48.800100Z
#!/usr/bin/env python3
import curses
import random
import os
import json
import sys
import argparse
import time

GRID_W, GRID_H = 20, 10
SAVE_FILE = "dice_duel.json"

class MicroDiceDuel:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.grid = [[0 for _ in range(GRID_W)] for _ in range(GRID_H)]
        self.hp1, self.hp2 = 20, 20
        self.turn = 0
        self.cursor_x, self.cursor_y = GRID_W//2, GRID_H//2
        self.player1_cursor = True
        self.space_held = False
        self.drag_start = None
        self.dice_placed = 0
        self.turn_start_time = time.time()
        self.game_over = False
        self.winner = None
        self.load_game()
        curses.curs_set(0)
        curses.cbreak()
        self.stdscr.keypad(True)
        curses.noecho()
        curses.halfdelay(3)  # ~60 FPS

    def save_game(self):
        state = {
            'grid': self.grid,
            'hp1': self.hp1, 'hp2': self.hp2,
            'turn': self.turn,
            'cursor_x': self.cursor_x, 'cursor_y': self.cursor_y,
            'player1_cursor': self.player1_cursor
        }
        with open(SAVE_FILE, 'w') as f:
            json.dump(state, f)

    def load_game(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r') as f:
                    state = json.load(f)
                self.grid = [row[:] for row in state['grid']]
                self.hp1 = state['hp1']
                self.hp2 = state['hp2']
                self.turn = state['turn']
                self.cursor_x = state['cursor_x']
                self.cursor_y = state['cursor_y']
                self.player1_cursor = state.get('player1_cursor', True)
            except:
                pass

    def new_game(self):
        self.grid = [[0 for _ in range(GRID_W)] for _ in range(GRID_H)]
        self.hp1 = self.hp2 = 20
        self.turn = 0
        self.cursor_x, self.cursor_y = GRID_W//2, GRID_H//2
        self.player1_cursor = True
        self.game_over = False
        self.winner = None

    def get_king_pos(self):
        k1x, k1y = GRID_W//4, GRID_H//2
        k2x, k2y = 3*GRID_W//4, GRID_H//2
        return (k1x, k1y), (k2x, k2y)

    def count_surrounded(self, kx, ky, player):
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]
        count = 0
        for dx, dy in dirs:
            nx, ny = kx + dx, ky + dy
            if 0 <= nx < GRID_W and 0 <= ny < GRID_H and self.grid[ny][nx] > 0 and self.grid[ny][nx] % 2 == player:
                count += 1
        return count

    def update_hp(self):
        (k1x, k1y), (k2x, k2y) = self.get_king_pos()
        surround1 = self.count_surrounded(k1x, k1y, 1)
        surround2 = self.count_surrounded(k2x, k2y, 2)
        self.hp1 = max(0, self.hp1 - surround1)
        self.hp2 = max(0, self.hp2 - surround2)
        if self.hp1 == 0:
            self.game_over = True
            self.winner = "Player 2"
        elif self.hp2 == 0:
            self.game_over = True
            self.winner = "Player 1"
        elif self.turn >= 50:
            self.game_over = True
            self.winner = "Draw"

    def get_score(self, player):
        return sum(cell for row in self.grid for cell in row if cell % 2 == player)

    def can_place(self, x, y):
        return 0 <= x < GRID_W and 0 <= y < GRID_H and self.grid[y][x] == 0

    def move_cursor(self, dx, dy):
        nx, ny = self.cursor_x + dx, self.cursor_y + dy
        if self.can_place(nx, ny):
            self.cursor_x, self.cursor_y = nx, ny

    def handle_input(self, key):
        if self.game_over:
            if key == ord('q') or key == 27:  # ESC
                self.save_game()
                return False
            return True

        if key == 32:  # SPACE
            if not self.space_held:
                self.space_held = True
                self.drag_start = (self.cursor_x, self.cursor_y)
                self.dice_placed = 0
            return True

        if key == 10 or key == 13:  # ENTER - pass turn
            self.next_turn()
            return True

        if key == ord('p') or key == ord('P'):  # P - print grid
            self.print_grid()
            return True

        if key == 27:  # ESC - quit
            self.save_game()
            return False

        if self.space_held:
            if self.dice_placed < 3 and self.can_place(self.cursor_x, self.cursor_y):
                roll = random.randint(1, 6)
                player_val = (1 if self.player1_cursor else 2) * 10 + roll
                self.grid[self.cursor_y][self.cursor_x] = player_val
                self.dice_placed += 1
                self.move_cursor(1, 0)  # Auto-move right
            self.space_held = False
            self.drag_start = None
            return True

        # Movement
        if self.player1_cursor:  # WASD
            if key == ord('w'): self.move_cursor(0, -1)
            elif key == ord('s'): self.move_cursor(0, 1)
            elif key == ord('a'): self.move_cursor(-1, 0)
            elif key == ord('d'): self.move_cursor(1, 0)
        else:  # Arrows
            if key == curses.KEY_UP: self.move_cursor(0, -1)
            elif key == curses.KEY_DOWN: self.move_cursor(0, 1)
            elif key == curses.KEY_LEFT: self.move_cursor(-1, 0)
            elif key == curses.KEY_RIGHT: self.move_cursor(1, 0)

        return True

    def next_turn(self):
        self.update_hp()
        if not self.game_over:
            self.turn += 1
            self.player1_cursor = not self.player1_cursor
            self.cursor_x, self.cursor_y = GRID_W//2, GRID_H//2
        self.save_game()

    def print_grid(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        (k1x, k1y), (k2x, k2y) = self.get_king_pos()
        print("Micro Dice Duel Grid (P1:left, P2:right, K1/K2=kings):")
        for y in range(GRID_H):
            row = []
            for x in range(GRID_W):
                if x == k1x and y == k1y:
                    row.append('K1')
                elif x == k2x and y == k2y:
                    row.append('K2')
                elif self.grid[y][x] > 0:
                    val = self.grid[y][x] % 10
                    row.append(str(val))
                else:
                    row.append('.')
            print(' '.join(row))
        print(f"\nP1 HP:{self.hp1:2d} Score:{self.get_score(1):2d} | P2 HP:{self.hp2:2d} Score:{self.get_score(2):2d} | Turn:{self.turn}")

    def draw(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        
        # Title & Status
        title = f"Micro Dice Duel - Turn {self.turn} - {'P1' if self.player1_cursor else 'P2'}"
        self.stdscr.addstr(0, 0, title[:w-1])
        
        (k1x, k1y), (k2x, k2y) = self.get_king_pos()
        
        # Grid
        for y in range(GRID_H):
            for x in range(GRID_W):
                gx, gy = 2 + x*2, 2 + y*2
                if x == self.cursor_x and y == self.cursor_y:
                    self.stdscr.addstr(gy, gx, "()", curses.A_REVERSE)
                elif x == k1x and y == k1y:
                    self.stdscr.addstr(gy, gx, "K1", curses.color_pair(1))
                elif x == k2x and y == k2y:
                    self.stdscr.addstr(gy, gx, "K2", curses.color_pair(2))
                elif self.grid[y][x] > 0:
                    val = self.grid[y][x] % 10
                    color = 1 if self.grid[y][x] % 2 == 1 else 2
                    self.stdscr.addstr(gy, gx, str(val), curses.color_pair(color))
                else:
                    self.stdscr.addstr(gy, gx, "..")
        
        # HP Bars
        self.stdscr.addstr(GRID_H*2 + 3, 0, f"P1 HP: [{'█'*self.hp1}{'░'*(20-self.hp1)}] {self.hp1}")
        self.stdscr.addstr(GRID_H*2 + 4, 0, f"P2 HP: [{'█'*self.hp2}{'░'*(20-self.hp2)}] {self.hp2}")
        
        # Scores
        score1, score2 = self.get_score(1), self.get_score(2)
        self.stdscr.addstr(GRID_H*2 + 6, 0, f"P1 Score: {score1:3d}  P2 Score: {score2:3d}")
        
        # Controls
        ctrl_y = GRID_H*2 + 8
        controls = [
            "P1: WASD+SPACE(hold=drag dice) ENTER=pass P=print ESC=quit",
            "P2: ARROWS+SPACE(hold=drag dice)             Max 3 dice/turn"
        ]
        for i, ctrl in enumerate(controls):
            self.stdscr.addstr(ctrl_y + i, 0, ctrl[:w-1])
        
        if self.game_over:
            msg = f"GAME OVER! {self.winner} wins! (q=quit)"
            self.stdscr.addstr(h//2, (w-len(msg))//2, msg, curses.A_BOLD | curses.A_REVERSE)
        
        self.stdscr.refresh()

    def run(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)   # P1
        curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # P2
        
        while True:
            self.draw()
            try:
                key = self.stdscr.getch()
                if not self.handle_input(key):
                    break
            except KeyboardInterrupt:
                break
        
        self.save_game()

def print_grid_only(grid, hp1, hp2, turn):
    (k1x, k1y), (k2x, k2y) = (5, 5), (15, 5)
    print("Current Game State:")
    for y in range(10):
        row = []
        for x in range(20):
            if x == k1x and y == k1y: row.append('K1')
            elif x == k2x and y == k2y: row.append('K2')
            elif grid[y][x] > 0: row.append(str(grid[y][x] % 10))
            else: row.append('.')
        print(' '.join(row))
    print(f"P1 HP:{hp1} P2 HP:{hp2} Turn:{turn}")

def main():
    parser = argparse.ArgumentParser(description="Micro Dice Duel")
    parser.add_argument('--new', action='store_true', help="Start new game")
    parser.add_argument('--print', action='store_true', help="Print current grid and exit")
    args = parser.parse_args()
    
    if args.print:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                state = json.load(f)
            print_grid_only(state['grid'], state['hp1'], state['hp2'], state['turn'])
        else:
            print("No save file found.")
        return
    
    curses.wrapper(lambda stdscr: MicroDiceDuel(stdscr).run() if not args.new else 
                   (game := MicroDiceDuel(stdscr)).new_game() or game.run())

if __name__ == "__main__":
    main()