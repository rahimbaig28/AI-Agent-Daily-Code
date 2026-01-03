# Auto-generated via Perplexity on 2026-01-03T01:24:48.113845Z
#!/usr/bin/env python3
import random
import json
import os
import sys
from pathlib import Path

HOME = Path.home()
STATS_FILE = HOME / ".number_guess_stats.json"

def load_stats():
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'easy': {'games': 0, 'wins': 0, 'total_guesses': 0, 'streak': 0, 'best_streak': 0},
        'normal': {'games': 0, 'wins': 0, 'total_guesses': 0, 'streak': 0, 'best_streak': 0},
        'hard': {'games': 0, 'wins': 0, 'total_guesses': 0, 'streak': 0, 'best_streak': 0}
    }

def save_stats(stats):
    try:
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
    except:
        pass

def get_color_support():
    bg = os.environ.get('COLORFGBG', '').split(';')[0] if os.environ.get('COLORFGBG') else None
    return bg == '0' or bg == '231' or not bg  # Assume dark by default

def print_colored(text, color, bold=False, end='\n'):
    if not get_color_support():
        print(text, end=end)
        return
    
    colors = {'green': 32, 'red': 31, 'yellow': 33, 'reset': 0, 'bold': 1}
    code = f"\033[{colors['bold'] if bold else ''};{colors[color]}m{ text }\033[{colors['reset']}m"
    print(code, end=end)

def print_stats(mode_stats):
    print(f"\n📊 **Current Stats ({list(mode_stats.keys())[0].title()} mode):**")
    for mode, data in mode_stats.items():
        win_rate = (data['wins'] / max(data['games'], 1) * 100)
        avg_guesses = data['total_guesses'] / max(data['wins'], 1)
        print(f"  {mode.title()}: {data['games']} games, {data['wins']} wins "
              f"({win_rate:.0f}%), streak: {data['streak']}, best: {data['best_streak']}, "
              f"avg: {avg_guesses:.1f}")

def get_performance_rating(guesses, max_num):
    optimal = int(max_num.bit_length()) + 1
    if guesses <= optimal:
        return "🏆 Excellent!", "green"
    elif guesses <= optimal * 2:
        return "👍 Good!", "yellow"
    elif guesses <= optimal * 3:
        return "👌 Fair!", "yellow"
    else:
        return "😅 Needs practice!", "red"

def select_mode():
    modes = {'1': ('easy', 1, 50), '2': ('normal', 1, 100), '3': ('hard', 1, 500)}
    print("\n🎮 **Select difficulty:**")
    print("1. Easy (1-50)")
    print("2. Normal (1-100)") 
    print("3. Hard (1-500)")
    
    while True:
        try:
            choice = input("Enter choice (1-3): ").strip()
            if choice in modes:
                return modes[choice]
            print("Invalid choice. Try 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)

def main_game_loop():
    stats = load_stats()
    
    while True:
        mode_name, low, high = select_mode()
        mode_stats = stats[mode_name]
        
        print_stats({mode_name: mode_stats})
        
        target = random.randint(low, high)
        guesses = 0
        print(f"\n🎯 **{mode_name.title()} mode: Guess number between {low}-{high}**")
        print("↑↓ arrows or type number, Enter to submit | q=quit | r=restart | c=clear stats")
        
        while True:
            try:
                inp = input(f"Guess ({guesses+1}) [{low}-{high}]: ").strip().lower()
                
                if inp == 'q':
                    print("👋 Goodbye!")
                    save_stats(stats)
                    sys.exit(0)
                elif inp == 'r':
                    break
                elif inp == 'c':
                    stats[mode_name] = {'games': 0, 'wins': 0, 'total_guesses': 0, 'streak': 0, 'best_streak': 0}
                    print_colored("📊 Stats cleared!", "yellow")
                    save_stats(stats)
                    continue
                
                guess = int(inp) if inp.isdigit() else None
                
                if guess is None or not (low <= guess <= high):
                    print_colored("❌ Enter number in range or use controls!", "red")
                    continue
                
                guesses += 1
                
                if guess < target:
                    print_colored("🔼 Too low!", "yellow")
                elif guess > target:
                    print_colored("🔽 Too high!", "red")
                else:
                    mode_stats['games'] += 1
                    mode_stats['total_guesses'] += guesses
                    mode_stats['streak'] += 1
                    mode_stats['best_streak'] = max(mode_stats['best_streak'], mode_stats['streak'])
                    mode_stats['wins'] += 1
                    
                    rating, color = get_performance_rating(guesses, high)
                    print_colored(f"\n🎉 CORRECT! {rating} ({guesses} guesses)", color, bold=True)
                    print_stats({mode_name: mode_stats})
                    save_stats(stats)
                    input("\nPress Enter to continue...")
                    break
                    
            except ValueError:
                print_colored("❌ Invalid input!", "red")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                save_stats(stats)
                sys.exit(0)

if __name__ == "__main__":
    try:
        main_game_loop()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)