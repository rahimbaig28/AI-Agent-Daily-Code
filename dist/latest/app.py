# Auto-generated via Perplexity on 2025-12-30T08:27:47.215574Z
#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

HOME_DIR = Path.home()
DATA_FILE = HOME_DIR / ".color_contrast_history.json"

def hex_to_rgb(hex_color):
    """Convert hex color (#RRGGBB or RRGGBB) to RGB tuple (0-255)."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) not in (3, 6):
        raise ValueError("Invalid hex color format")
    if len(hex_color) == 3:
        hex_color = ''.join(c*2 for c in hex_color)
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_srgb(r, g, b):
    """Convert linear RGB (0-255) to sRGB (0-1)."""
    return (r/255, g/255, b/255)

def srgb_to_linear(c):
    """Convert sRGB (0-1) to linear RGB using WCAG formula."""
    if c <= 0.03928:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4

def relative_luminance(r, g, b):
    """Calculate relative luminance per WCAG 2.1 formula."""
    r_lin = srgb_to_linear(r)
    g_lin = srgb_to_linear(g)
    b_lin = srgb_to_linear(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

def contrast_ratio(lum1, lum2):
    """Calculate contrast ratio (L1 + 0.05) / (L2 + 0.05) where L1 >= L2."""
    if lum1 < lum2:
        lum1, lum2 = lum2, lum1
    return (lum1 + 0.05) / (lum2 + 0.05)

def get_compliance(ratio):
    """Determine WCAG compliance levels."""
    aa = ratio >= 4.5
    aaa = ratio >= 7.0
    aa_large = ratio >= 3.0
    aaa_large = ratio >= 4.5
    return {
        'AA': 'PASS' if aa else 'FAIL',
        'AAA': 'PASS' if aaa else 'FAIL',
        'AA Large': 'PASS' if aa_large else 'FAIL',
        'AAA Large': 'PASS' if aaa_large else 'FAIL'
    }

def print_banner():
    """Print startup banner with WCAG reference."""
    print("\n" + "="*70)
    print("🔍 ACCESSIBLE COLOR CONTRAST CHECKER (WCAG 2.1)")
    print("="*70)
    print("WCAG Success Criteria:")
    print("• **AA Normal Text**: 4.5:1 ratio required")
    print("• **AAA Normal Text**: 7:1 ratio required") 
    print("• **AA Large Text**: 3:1 ratio required")
    print("• **AAA Large Text**: 4.5:1 ratio required")
    print("\nCommands: TAB=next field | ENTER=check | ↑↓=history | U=undo | R=redo | Q=quit")
    print("="*70 + "\n")

def print_results(fg_hex, bg_hex, fg_lum, bg_lum, ratio, compliance):
    """Print formatted results table."""
    print("\n" + "─"*80)
    print(f"{'Foreground':<12} {fg_hex:<10} Luminance: {fg_lum:.4f}")
    print(f"{'Background':<12} {bg_hex:<10} Luminance: {bg_lum:.4f}")
    print(f"{'Contrast Ratio':<12} {ratio:.2f}:1")
    print("─"*80)
    
    print(f"{'Level':<12} {'Status':<8} {'Badge'}")
    print("─"*80)
    for level, status in compliance.items():
        badge = "✅" if status == "PASS" else "❌"
        color = "\033[92m" if status == "PASS" else "\033[91m"
        reset = "\033[0m"
        print(f"{level:<12} {color}{status:<8}{reset} {badge}")
    print("─"*80 + "\n")

def load_history():
    """Load history from JSON file."""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    """Save history to JSON file."""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(history[-100:], f, indent=2)  # Keep last 100
    except Exception as e:
        print(f"Warning: Could not save history: {e}")

def main():
    print_banner()
    
    history = load_history()
    history_pos = len(history)
    
    # Current pair being edited
    fg_color = "#000000"
    bg_color = "#FFFFFF"
    
    print(f"Current: FG={fg_color} BG={bg_color}")
    
    while True:
        try:
            cmd = input("\n> fg/bg/u/r/a/q: ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 'u' and history_pos > 0:
                history_pos -= 1
                result = history[history_pos]
                fg_color, bg_color = result['fg'], result['bg']
                print(f"← Undo to: FG={fg_color} BG={bg_color}")
            elif cmd == 'r' and history_pos < len(history) - 1:
                history_pos += 1
                result = history[history_pos]
                fg_color, bg_color = result['fg'], result['bg']
                print(f"→ Redo to: FG={fg_color} BG={bg_color}")
            elif cmd == 'a':
                if history:
                    print("\nRecent checks:")
                    for i, h in enumerate(history[-10:], 1):
                        print(f"{i:2d}. {h['fg']:<8} on {h['bg']:<8} → {h['ratio']:.2f}:1")
                else:
                    print("No history yet!")
            elif '/' in cmd:
                parts = cmd.split('/', 1)
                if len(parts) == 2:
                    fg_input, bg_input = parts
                    fg_color = fg_input.strip()
                    bg_color = bg_input.strip()
            elif cmd:
                if len(cmd.split()) == 2:
                    fg_color, bg_color = cmd.split()
                else:
                    fg_color = cmd
                    bg_color = bg_color  # Keep existing BG
            
            # Validate and check colors
            try:
                fg_rgb = hex_to_rgb(fg_color)
                bg_rgb = hex_to_rgb(bg_color)
                
                fg_srgb = rgb_to_srgb(*fg_rgb)
                bg_srgb = rgb_to_srgb(*bg_rgb)
                
                fg_lum = relative_luminance(*fg_srgb)
                bg_lum = relative_luminance(*bg_srgb)
                ratio = contrast_ratio(fg_lum, bg_lum)
                compliance = get_compliance(ratio)
                
                print_results(fg_color, bg_color, fg_lum, bg_lum, ratio, compliance)
                
                # Save to history (avoid duplicates)
                result = {
                    'fg': fg_color, 'bg': bg_color,
                    'fg_lum': fg_lum, 'bg_lum': bg_lum,
                    'ratio': ratio, 'compliance': compliance
                }
                
                if not history or history[-1] != result:
                    history.append(result)
                    history_pos = len(history)
                    save_history(history)
                
            except ValueError as e:
                print(f"❌ Error: {e}")
                print("Use format: #RRGGBB or RRGGBB (e.g., #FF0000 ffffff)")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            break
    
    save_history(history)

if __name__ == "__main__":
    main()