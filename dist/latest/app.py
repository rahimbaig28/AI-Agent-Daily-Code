# Auto-generated via Perplexity on 2026-01-03T12:37:23.086088Z
#!/usr/bin/env python3
import curses
import json
import os
import sys
import argparse
import urllib.parse
import webbrowser
import random
import math
from pathlib import Path

CONFIG_DIR = Path.home() / ".colorpalettes"
CONFIG_FILE = CONFIG_DIR / "palettes.json"

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb

def rgb_to_luminance(r, g, b):
    def srgb_to_linear(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * srgb_to_linear(r) + 0.7152 * srgb_to_linear(g) + 0.0722 * srgb_to_linear(b)

def contrast_ratio(rgb1, rgb2):
    l1 = rgb_to_luminance(*rgb1)
    l2 = rgb_to_luminance(*rgb2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

def hsv_to_rgb(h, s, v):
    h *= 6
    i = int(h)
    f = h - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    i %= 6
    if i == 0: return int(v*255), int(t*255), int(p*255)
    if i == 1: return int(q*255), int(v*255), int(p*255)
    if i == 2: return int(p*255), int(v*255), int(t*255)
    if i == 3: return int(p*255), int(q*255), int(v*255)
    if i == 4: return int(t*255), int(p*255), int(v*255)
    return int(v*255), int(p*255), int(q*255)

def rgb_to_hsv(r, g, b):
    r, g, b = r/255.0, g/255.0, b/255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx - mn
    if mx == mn: h = 0
    elif mx == r: h = (60 * ((g - b)/df) + 360) % 360
    elif mx == g: h = (60 * ((b - r)/df) + 120) % 360
    elif mx == b: h = (60 * ((r - g)/df) + 240) % 360
    s = 0 if mx == 0 else df / mx
    return h/360.0, s, mx

def generate_palette(base_hex, scheme='random', num_colors=6):
    base_rgb = hex_to_rgb(base_hex)
    h, s, v = rgb_to_hsv(*base_rgb)
    
    if scheme == 'random':
        return [(random.randint(0,255), random.randint(0,255), random.randint(0,255)) for _ in range(num_colors)]
    elif scheme == 'analogous':
        colors = []
        for i in range(num_colors):
            dh = (i - num_colors//2) * 30 / 360.0
            colors.append(hsv_to_rgb((h + dh) % 1.0, s, v))
        return colors
    elif scheme == 'complementary':
        colors = [base_rgb]
        comp_h = (h + 0.5) % 1.0
        for i in range(1, num_colors):
            dh = (i - 1) * 60 / 360.0
            colors.append(hsv_to_rgb((comp_h + dh) % 1.0, s, v))
        return colors
    elif scheme == 'triadic':
        colors = [base_rgb]
        for i in range(1, num_colors):
            dh = i * 120 / 360.0
            colors.append(hsv_to_rgb((h + dh) % 1.0, s, v))
        return colors
    return [base_rgb] * num_colors

class ColorPaletteApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.palette = []
        self.selected = 0
        self.mode = 'palette'  # 'palette', 'picker', 'contrast'
        self.base_hex = '#007BFF'
        self.scheme = 'analogous'
        self.dragging = False
        self.drag_pos = 0
        self.status = "Welcome to ColorPaletteApp - Arrow keys: navigate, Enter: select, Tab: mode, Esc: quit"
        self.load_palettes()
        
    def load_palettes(self):
        CONFIG_DIR.mkdir(exist_ok=True)
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    if data.get('palette'):
                        self.palette = [tuple(c) for c in data['palette']]
            except:
                pass
    
    def save_palettes(self):
        try:
            data = {
                'palette': self.palette,
                'base_hex': self.base_hex,
                'scheme': self.scheme
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def generate_share_url(self):
        data = {
            'p': [rgb_to_hex(c) for c in self.palette],
            'b': self.base_hex,
            's': self.scheme
        }
        encoded = urllib.parse.urlencode(data)
        b64 = urllib.parse.quote(encoded)
        return f"https://colorpalettes.app/#/{b64}"
    
    def draw(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        
        # Status bar
        self.stdscr.addstr(0, 0, self.status[:w-1], curses.A_REVERSE)
        
        if self.mode == 'picker':
            self.draw_picker()
        elif self.mode == 'contrast':
            self.draw_contrast()
        else:
            self.draw_palette()
        
        self.stdscr.refresh()
    
    def draw_picker(self):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.addstr(2, 2, "COLOR PICKER - Enter hex (#RRGGBB):", curses.A_BOLD)
        self.stdscr.addstr(4, 2, f"Current: {self.base_hex}")
        
        try:
            rgb = hex_to_rgb(self.base_hex)
            block_w = 40
            for i, c in enumerate(generate_palette(self.base_hex, self.scheme)):
                x = 2 + i * (block_w + 2)
                if x + block_w > w: break
                attr = curses.color_pair(10 + i % 8) if i == self.selected else 0
                self.stdscr.addstr(6, x, " " * block_w, attr | curses.A_REVERSE)
                self.stdscr.addstr(7, x, rgb_to_hex(c)[:7].center(block_w))
        except:
            self.stdscr.addstr(6, 2, "Invalid hex color")
    
    def draw_contrast(self):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.addstr(2, 2, "CONTRAST CHECKER - Test FG/BG pairs:", curses.A_BOLD)
        
        if len(self.palette) >= 2:
            fg = self.palette[self.selected]
            bg = self.palette[(self.selected + 1) % len(self.palette)]
            ratio = contrast_ratio(fg, bg)
            passes_aa = ratio >= 4.5
            status = f"✓ PASS" if passes_aa else "✗ FAIL"
            color_attr = curses.color_pair(1) if passes_aa else curses.color_pair(2)
            
            self.stdscr.addstr(4, 2, f"FG: {rgb_to_hex(fg)} on BG: {rgb_to_hex(bg)}", color_attr)
            self.stdscr.addstr(5, 2, f"Ratio: {ratio:.2f}:1 {status}", color_attr)
            
            # Preview
            self.stdscr.addstr(7, 2, "AaBbCc123"[:w-5], curses.color_pair(11) | curses.A_BOLD)
    
    def draw_palette(self):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.addstr(2, 2, f"PALETTE ({self.scheme.upper()}) - Arrows: nav, Shift+Arrows: drag", curses.A_BOLD)
        
        if not self.palette:
            self.generate_palette()
        
        block_h, block_w = 3, 12
        for i, rgb in enumerate(self.palette):
            row = 4 + (i // 4) * (block_h + 1)
            col = 2 + (i % 4) * (block_w + 2)
            
            if row + block_h > h - 5: break
            
            if i == self.selected:
                attr = curses.color_pair(9) | curses.A_REVERSE | curses.A_BOLD
            elif self.dragging and i == self.drag_pos:
                attr = curses.color_pair(2) | curses.A_BLINK
            else:
                attr = 0
            
            self.stdscr.addstr(row, col, " " * block_w, attr)
            self.stdscr.addstr(row+1, col, rgb_to_hex(rgb)[:7].center(block_w), attr)
    
    def generate_palette(self):
        self.palette = generate_palette(self.base_hex, self.scheme)
        self.status = f"Palette generated: {self.scheme.title()} from {self.base_hex}"
    
    def handle_key(self, key):
        if key == 27:  # Esc
            self.save_palettes()
            return False
        
        elif key == ord('\t'):  # Tab - cycle modes
            modes = ['palette', 'picker', 'contrast']
            idx = (modes.index(self.mode) + 1) % 3
            self.mode = modes[idx]
            self.status = f"Mode: {self.mode.title()}"
        
        elif self.mode == 'picker':
            self.handle_picker(key)
        elif self.mode == 'contrast':
            self.handle_contrast(key)
        else:
            self.handle_palette(key)
        
        return True
    
    def handle_picker(self, key):
        if key == 10 or key == 13:  # Enter
            try:
                rgb = hex_to_rgb(self.base_hex)
                self.generate_palette()
                self.mode = 'palette'
            except:
                self.status = "Invalid hex format"
        elif 48 <= key <= 57 or 65 <= key <= 70 or key == 35:  # 0-9, A-F, #
            self.base_hex += chr(key)
            if len(self.base_hex) > 7: self.base_hex = self.base_hex[-7:]
            self.status = f"Input: {self.base_hex}"
        elif key == 8 or key == 127:  # Backspace
            self.base_hex = self.base_hex[:-1]
            self.status = f"Input: {self.base_hex}"
        elif key == ord('g'):  # Generate
            self.generate_palette()
    
    def handle_contrast(self, key):
        if key == 10 or key == 13:  # Enter
            self.mode = 'palette'
        elif key in (curses.KEY_LEFT, ord('h')):
            self.selected = (self.selected - 1) % max(1, len(self.palette))
    
    def handle_palette(self, key):
        n = len(self.palette)
        if n == 0: return
        
        if key == ord('g'):  # Generate new
            self.generate_palette()
        elif key == ord('s'):  # Share
            url = self.generate_share_url()
            webbrowser.open(url)
            self.status = "Opened share URL in browser"
        elif key == ord('r'):  # Random
            self.scheme = 'random'
            self.generate_palette()
        elif key == ord('a'):  # Analogous
            self.scheme = 'analogous'
            self.generate_palette()
        elif key == ord('c'):  # Complementary
            self.scheme = 'complementary'
            self.generate_palette()
        elif key == ord('t'):  # Triadic
            self.scheme = 'triadic'
            self.generate_palette()
        elif key == curses.KEY_UP:
            self.selected = (self.selected - 4) % n
        elif key == curses.KEY_DOWN:
            self.selected = (self.selected + 4) % n
        elif key == curses.KEY_LEFT:
            self.selected = (self.selected - 1) % n
        elif key == curses.KEY_RIGHT:
            self.selected = (self.selected + 1) % n
        elif key == 16:  # Shift (simulate with key combos)
            self.dragging = not self.dragging
            if self.dragging: self.drag_pos = self.selected
        elif self.dragging and key == curses.KEY_LEFT:
            self.drag_pos = (self.drag_pos - 1) % n
        elif self.dragging and key == curses.KEY_RIGHT:
            self.drag_pos = (self.drag_pos + 1) % n
        elif key == 10 and self.dragging:  # Enter to swap
            self.palette[self.selected], self.palette[self.drag_pos] = self.palette[self.drag_pos], self.palette[self.selected]
            self.dragging = False
            self.status = "Colors swapped"
    
    def run(self):
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        
        # Setup color pairs
        for i in range(1, 12):
            curses.init_pair(i, i-1, -1)
        
        # Extra colors for truecolor simulation
        if curses.can_change_color():
            for i in range(8, 12):
                r = int(255 * (i-7)/5)
                curses.init_color(i, r*1000//255, 0, 0)
                curses.init_pair(i+1, i, -1)
        
        self.draw()
        while True:
            try:
                key = self.stdscr.getch()
                if not self.handle_key(key):
                    break
                self.draw()
            except KeyboardInterrupt:
                break
        self.save_palettes()

def main_cli(args):
    if args.base:
        app = ColorPaletteApp(None)
        app.base_hex = args.base
        app.scheme = args.scheme or 'analogous'
        app.generate_palette()
        
        if args.share:
            url = app.generate_share_url()
            print(f"Share URL: {url}")
            webbrowser.open(url)
        else:
            print("Generated palette:")
            for i, c in enumerate(app.palette):
                print(f"  {i}: {rgb_to_hex(c)}")
            print(f"Base: {app.base_hex}, Scheme: {app.scheme}")

def test_cases():
    tests = [
        ('#000000', 'analogous'),  # Dark mode
        ('#FFFFFF', 'complementary'),  # Light mode
        ('#007BFF', 'triadic'),  # Blue test
    ]
    print("Running test cases...")
    for base, scheme in tests:
        app = ColorPaletteApp(None)
        app.base_hex = base
        app.scheme = scheme
        app.generate_palette()
        ratios = [contrast_ratio(app.palette[0], app.palette[i]) for i in range(1, len(app.palette))]
        print(f"Test {base} {scheme}: min contrast {min(ratios):.2f}")
    print("Tests complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Accessible Color Palette Generator")
    parser.add_argument('--base', default='#007BFF', help='Base color (hex)')
    parser.add_argument('--scheme', choices=['random','analogous','complementary','triadic'], help='Color scheme')
    parser.add_argument('--share', action='store_true', help='Generate and open share URL')
    parser.add_argument('--test', action='store_true', help='Run test cases')
    
    args = parser.parse_args()
    
    if args.test:
        test_cases()
    elif not sys.stdin.isatty() or not curses.is_term_resized(24, 80):
        main_cli(args)
    else:
        try:
            curses.wrapper(ColorPaletteApp().run)
        except curses.error:
            print("Terminal not supported. Use CLI mode.")
            main_cli(args)