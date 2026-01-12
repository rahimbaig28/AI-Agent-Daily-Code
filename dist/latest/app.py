# Auto-generated via Perplexity on 2026-01-12T12:43:45.060843Z
#!/usr/bin/env python3
import curses
import json
import random
import os
import sys
import base64
import argparse

GRID_SIZE = 5
CELL_WIDTH = 3
CELL_HEIGHT = 1
SAVE_FILE = 'puzzle.json'
AUTO_SAVE_MOVES = 5

def grid_to_hash(grid):
    flat = ''.join(''.join(map(str, row)) for row in grid)
    return base64.urlsafe_b64encode(flat.encode()).decode()[:8]

def hash_to_grid(h):
    flat = base64.urlsafe_b64decode(h.encode()).decode()
    grid = [[int(flat[i*GRID_SIZE+j]) for j in range(GRID_SIZE)] for i in range(GRID_SIZE)]
    return grid

def load_puzzle():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                return data['target'], data['player']
        except:
            pass
    return None, None

def save_puzzle(target, player, moves):
    data = {'target': target, 'player': player, 'moves': moves}
    with open(SAVE_FILE, 'w') as f:
        json.dump(data, f)

def generate_target():
    return [[random.randint(0,1) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

def is_solved(target, player):
    return all(target[i][j] == player[i][j] for i in range(GRID_SIZE) for j in range(GRID_SIZE))

def count_diffs(target, player):
    return sum(target[i][j] != player[i][j] for i in range(GRID_SIZE) for j in range(GRID_SIZE))

def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    
    # Colors
    curses.init_pair(1, curses.COLOR_GREEN, -1)      # Target filled
    curses.init_pair(2, curses.COLOR_BLUE, -1)       # Player filled
    curses.init_pair(3, curses.COLOR_YELLOW, -1)     # Cursor
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_GREEN)  # Solved bg
    curses.init_pair(5, curses.COLOR_WHITE, -1)      # Empty/default
    
    # Parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('--load', nargs='?')
    args = parser.parse_args(sys.argv[1:])
    
    # Load or generate puzzle
    target, player = load_puzzle()
    if args.load:
        target = hash_to_grid(args.load)
        player = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
    elif target is None:
        target = generate_target()
        player = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
    
    cx, cy = 0, 0  # Cursor position
    moves = 0
    move_count = 0
    solved = False
    
    while True:
        h, w = stdscr.getmaxyx()
        if h < 24 or w < 80:
            stdscr.clear()
            stdscr.addstr(0, 0, "Terminal too small (need 80x24+)", curses.A_BOLD)
            stdscr.refresh()
            stdscr.getch()
            return
        
        stdscr.clear()
        
        # Title
        title = "Micro Grid Puzzle" + (" - SOLVED!" if solved else "")
        stdscr.addstr(0, (w-len(title))//2, title, curses.A_BOLD)
        
        # Status line
        diffs = count_diffs(target, player)
        status = f"Moves: {moves} | Diffs: {diffs} | Cursor: ({cy},{cx}) | Q=Quit R=New S=Save"
        if solved:
            status += f" | Best: {move_count} moves | Share: python gridgame.py --load {grid_to_hash(target)}"
        stdscr.addstr(1, (w-len(status))//2, status)
        
        # Grid display area
        grid_top = 4
        grid_left = (w - GRID_SIZE * CELL_WIDTH) // 2
        
        # Target grid (green/white)
        stdscr.addstr(grid_top-1, grid_left-4, "TARGET", curses.color_pair(1) | curses.A_BOLD)
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                y = grid_top + i * CELL_HEIGHT
                x = grid_left + j * CELL_WIDTH
                ch = '███' if target[i][j] else '   '
                color = curses.color_pair(1) if target[i][j] else curses.color_pair(5)
                stdscr.addstr(y, x, ch, color)
        
        # Player grid (blue/white)
        stdscr.addstr(grid_top+GRID_SIZE+1, grid_left-6, "PLAYER", curses.color_pair(2) | curses.A_BOLD)
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                y = grid_top + GRID_SIZE + 2 + i * CELL_HEIGHT
                x = grid_left + j * CELL_WIDTH
                ch = '███' if player[i][j] else '   '
                color = curses.color_pair(2) if player[i][j] else curses.color_pair(5)
                if i == cy and j == cx:
                    color |= curses.color_pair(3) | curses.A_BOLD
                stdscr.addstr(y, x, ch, color)
        
        # Instructions
        instr = "WASD/Arrows: Move | SPACE/Enter: Toggle | R: New Puzzle | S: Save | Q/ESC: Quit"
        stdscr.addstr(h-2, (w-len(instr))//2, instr)
        
        if solved:
            solved_y = h//2
            solved_msg = "PUZZLE SOLVED!"
            stdscr.addstr(solved_y, (w-len(solved_msg))//2, solved_msg, 
                         curses.color_pair(4) | curses.A_BOLD | curses.A_UNDERLINE)
            stdscr.addstr(solved_y+1, (w-len("R for new puzzle"))//2, "R for new puzzle")
        
        stdscr.refresh()
        
        # Auto-save
        if move_count % AUTO_SAVE_MOVES == 0 and move_count > 0:
            save_puzzle(target, player, moves)
        
        # Input handling
        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            break
        
        if solved and key != ord('r') and key != ord('R'):
            continue
            
        if key == ord('q') or key == 27:  # Q or ESC
            break
        elif key == ord('r') or key == ord('R'):  # New puzzle
            target = generate_target()
            player = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
            cx, cy = 0, 0
            moves = 0
            move_count = 0
            solved = False
        elif key == ord('s') or key == ord('S'):  # Save
            save_puzzle(target, player, moves)
            stdscr.addstr(h-1, 0, "Saved!          ", curses.A_BOLD)
            stdscr.refresh()
            curses.napms(500)
        elif key in (ord(' '), 10, 13):  # Toggle
            player[cy][cx] = 1 - player[cy][cx]
            moves += 1
            move_count += 1
            solved = is_solved(target, player)
            if solved:
                move_count = min(move_count, moves)
        elif key == curses.KEY_UP or key == ord('w') or key == ord('W'):
            cy = max(0, cy-1)
        elif key == curses.KEY_DOWN or key == ord('s') or key == ord('S'):
            cy = min(GRID_SIZE-1, cy+1)
        elif key == curses.KEY_LEFT or key == ord('a') or key == ord('A'):
            cx = max(0, cx-1)
        elif key == curses.KEY_RIGHT or key == ord('d') or key == ord('D'):
            cx = min(GRID_SIZE-1, cx+1)
        else:
            curses.beep()
    
    save_puzzle(target, player, moves)

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass