# Auto-generated via Perplexity on 2025-12-25T01:27:28.251537Z
#!/usr/bin/env python3
import sys
import os
import json
import argparse
import re
import math
import time
from urllib.parse import urlencode, parse_qs, urlparse
from collections import deque

# ANSI color codes for accessible output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    BELL = '\a'

def hex_to_rgb(hex_color):
    """Convert hex color to RGB (0-255). Auto-corrects formats."""
    hex_color = str(hex_color).strip().lower()
    hex_color = re.sub(r'^#?', '', hex_color)
    
    if len(hex_color) == 3:
        hex_color = ''.join(c*2 for c in hex_color)
    elif len(hex_color) != 6:
        return None
    
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return None

def rgb_to_srgb(r, g, b):
    """Convert RGB (0-255) to sRGB (0-1)."""
    return (r/255.0, g/255.0, b/255.0)

def srgb_to_linear(c):
    """Convert sRGB channel to linear light."""
    return c/12.92 if c <= 0.03928 else ((c + 0.055)/1.055)**2.4

def relative_luminance(r, g, b):
    """Calculate relative luminance per WCAG formula."""
    srgb = rgb_to_srgb(r, g, b)
    linear = [srgb_to_linear(c) for c in srgb]
    return 0.2126*linear[0] + 0.7152*linear[1] + 0.0722*linear[2]

def contrast_ratio(lum1, lum2):
    """Calculate WCAG contrast ratio."""
    if lum1 < lum2:
        lum1, lum2 = lum2, lum1
    return (lum1 + 0.05) / (lum2 + 0.05)

def wcag_status(ratio):
    """Check WCAG AA/AAA compliance."""
    aa = ratio >= 4.5
    aaa = ratio >= 7.0
    return aa, aaa

def format_ratio(ratio):
    """Format ratio as X:Y."""
    return f"{ratio:.1f}:1"

def suggest_fix(fg_rgb, bg_rgb, ratio):
    """Simple fix suggestions."""
    fg_lum = relative_luminance(*fg_rgb)
    bg_lum = relative_luminance(*bg_rgb)
    
    if ratio >= 7.0:
        return "Perfect"
    elif ratio >= 4.5:
        return "Good (AA)"
    elif fg_lum > bg_lum:
        return "Darken FG or lighten BG"
    else:
        return "Lighten FG or darken BG"

def parse_share_url(url):
    """Parse contrastchecker:// URL."""
    parsed = urlparse(url.replace('contrastchecker://', 'http://'))
    params = parse_qs(parsed.query)
    fg = hex_to_rgb(params.get('fg', [''])[0])
    bg = hex_to_rgb(params.get('bg', [''])[0])
    return fg, bg

def create_share_url(fg_hex, bg_hex, ratio):
    """Create shareable URL."""
    return f"contrastchecker://fg={fg_hex}&bg={bg_hex}&ratio={ratio:.1f}"

class ContrastChecker:
    def __init__(self):
        self.history = deque(maxlen=20)
        self.undo_stack = []
        self.redo_stack = []
        self.history_file = 'contrast_history.json'
        self.load_history()
    
    def load_history(self):
        """Load history from JSON."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.history = deque(data.get('history', []), maxlen=20)
                    self.undo_stack = data.get('undo', [])
                    self.redo_stack = data.get('redo', [])
        except:
            pass
    
    def save_history(self):
        """Save history to JSON."""
        try:
            data = {
                'history': list(self.history),
                'undo': self.undo_stack,
                'redo': self.redo_stack,
                'timestamp': time.time()
            }
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass
    
    def add_check(self, fg_hex, bg_hex, fg_rgb, bg_rgb, ratio, aa, aaa, fix):
        """Add new check to history."""
        entry = {
            'fg_hex': fg_hex,
            'bg_hex': bg_hex,
            'fg_rgb': fg_rgb,
            'bg_rgb': bg_rgb,
            'ratio': ratio,
            'aa': aa,
            'aaa': aaa,
            'fix': fix,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.undo_stack.append(entry)
        self.redo_stack.clear()
        self.history.append(entry)
        self.save_history()
    
    def undo(self):
        """Undo last check."""
        if self.undo_stack:
            entry = self.undo_stack.pop()
            self.redo_stack.append(entry)
            self.history.pop()
            self.save_history()
            return entry
        return None
    
    def redo(self):
        """Redo undone check."""
        if self.redo_stack:
            entry = self.redo_stack.pop()
            self.undo_stack.append(entry)
            self.history.append(entry)
            self.save_history()
            return entry
        return None

def print_status(msg, color=Colors.WHITE):
    """Print status message."""
    print(f"{Colors.BOLD}{color}Status:{Colors.RESET} {msg}")

def print_result(msg, color=Colors.WHITE):
    """Print result message."""
    print(f"{Colors.BOLD}{color}Result:{Colors.RESET} {msg}")

def print_grid_row(fg_hex, bg_hex, ratio, aa, aaa, fix):
    """Print single grid row."""
    aa_mark = Colors.GREEN + "✓" + Colors.RESET if aa else Colors.RED + "✗" + Colors.RESET
    aaa_mark = Colors.GREEN + "✓" + Colors.RESET if aaa else Colors.RED + "✗" + Colors.RESET
    ratio_str = format_ratio(ratio)
    print(f"  {Colors.CYAN}FG{Colors.RESET} {fg_hex:>8} | "
          f"{Colors.MAGENTA}BG{Colors.RESET} {bg_hex:>8} | "
          f"{Colors.YELLOW}{ratio_str:>4}{Colors.RESET} | "
          f"{aa_mark:>2} | {aaa_mark:>2} | {fix}")

def print_history_grid(checker):
    """Print history as grid."""
    print(f"\n{Colors.BOLD}Recent Checks:{Colors.RESET}")
    print("  FG Color    | BG Color    | Ratio | AA  | AAA | Fix")
    print("-" * 70)
    for entry in list(checker.history)[-5:][::-1]:
        print_grid_row(entry['fg_hex'], entry['bg_hex'], entry['ratio'],
                      entry['aa'], entry['aaa'], entry['fix'])

def main():
    checker = ContrastChecker()
    last_check = None
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--share', help='Load from share URL')
    args = parser.parse_args()
    
    if args.test:
        test_cases = [
            ('#000000', '#ffffff', 21.0),
            ('#000000', '#000000', 1.0),
            ('#aa0000', '#00aa00', 2.8),
            ('#ffffff', '#aaaaaa', 3.0),
            ('#0000ff', '#ffff00', 5.6)
        ]
        print("WCAG Test Cases:")
        for fg, bg, expected in test_cases:
            fg_rgb = hex_to_rgb(fg)
            bg_rgb = hex_to_rgb(bg)
            ratio = contrast_ratio(relative_luminance(*fg_rgb), relative_luminance(*bg_rgb))
            print(f"{fg} on {bg}: {format_ratio(ratio)} (expected ~{format_ratio(expected)})")
        return
    
    if args.share:
        fg_rgb, bg_rgb = parse_share_url(args.share)
        if fg_rgb and bg_rgb:
            do_check(checker, fg_rgb, bg_rgb, True)
    
    print(f"{Colors.BOLD}{Colors.CYAN}Color Contrast Checker Pro{Colors.RESET}")
    print("Commands: c=check, s=share, h=history, u=undo, r=redo, l=load, n=new, q=quit")
    
    while True:
        try:
            cmd = input("\n> ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 'c':
                fg_hex = input("Foreground hex (default #000000): ").strip() or '#000000'
                bg_hex = input("Background hex (default #ffffff): ").strip() or '#ffffff'
                do_check(checker, hex_to_rgb(fg_hex), hex_to_rgb(bg_hex))
            elif cmd == 's' and last_check:
                url = create_share_url(last_check['fg_hex'], last_check['bg_hex'], last_check['ratio'])
                print_status(f"Share URL: {url}")
            elif cmd == 'h':
                print_history_grid(checker)
            elif cmd == 'u':
                entry = checker.undo()
                if entry:
                    print_status("Undone last check")
                    print_grid_row(entry['fg_hex'], entry['bg_hex'], entry['ratio'],
                                 entry['aa'], entry['aaa'], entry['fix'])
                else:
                    print_status("No checks to undo", Colors.YELLOW)
            elif cmd == 'r':
                entry = checker.redo()
                if entry:
                    print_status("Redone check")
                    print_grid_row(entry['fg_hex'], entry['bg_hex'], entry['ratio'],
                                 entry['aa'], entry['aaa'], entry['fix'])
                else:
                    print_status("No checks to redo", Colors.YELLOW)
            elif cmd == 'n':
                checker.history.clear()
                checker.undo_stack.clear()
                checker.redo_stack.clear()
                checker.save_history()
                print_status("New session - history cleared")
            elif cmd.startswith('contrastchecker://'):
                fg_rgb, bg_rgb = parse_share_url(cmd)
                if fg_rgb and bg_rgb:
                    do_check(checker, fg_rgb, bg_rgb, True)
                else:
                    print_status("Invalid share URL", Colors.RED)
                    print(Colors.BELL, end='')
            else:
                print_status("Unknown command. Type 'h' for help.", Colors.YELLOW)
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            break
    
    checker.save_history()

def do_check(checker, fg_rgb, bg_rgb, quiet=False):
    """Perform color contrast check."""
    global last_check
    
    if fg_rgb is None:
        print_status("Invalid foreground color", Colors.RED)
        print(Colors.BELL, end='')
        return
    if bg_rgb is None:
        print_status("Invalid background color", Colors.RED)
        print(Colors.BELL, end='')
        return
    
    fg_hex = f"#{fg_rgb[0]:02x}{fg_rgb[1]:02x}{fg_rgb[2]:02x}"
    bg_hex = f"#{bg_rgb[0]:02x}{bg_rgb[1]:02x}{bg_rgb[2]:02x}"
    
    fg_lum = relative_luminance(*fg_rgb)
    bg_lum = relative_luminance(*bg_rgb)
    ratio = contrast_ratio(fg_lum, bg_lum)
    aa, aaa = wcag_status(ratio)
    fix = suggest_fix(fg_rgb, bg_rgb, ratio)
    
    status_color = Colors.GREEN if ratio >= 4.5 else Colors.RED
    result_color = Colors.GREEN if aaa else Colors.YELLOW if aa else Colors.RED
    
    if not quiet:
        print_status(f"Checking {fg_hex} on {bg_hex}", status_color)
        result_msg = f"Ratio {format_ratio(ratio)} "
        result_msg += "PASS AAA" if aaa else "PASS AA" if aa else "FAIL"
        print_result(result_msg, result_color)
        print_grid_row(fg_hex, bg_hex, ratio, aa, aaa, fix)
    
    checker.add_check(fg_hex, bg_hex, fg_rgb, bg_rgb, ratio, aa, aaa, fix)
    last_check = checker.history[-1]

if __name__ == "__main__":
    main()