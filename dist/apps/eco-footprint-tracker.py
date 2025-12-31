# Auto-generated via Perplexity on 2025-12-31T01:28:54.243149Z
#!/usr/bin/env python3
import json
import os
import datetime
from curses import wrapper, initscr, noecho, raw, KEY_DOWN, KEY_UP, KEY_LEFT, KEY_RIGHT, KEY_ENTER
from curses.textpad import Textbox, rectangle
from curses import wrapper as curses_wrapper
import statistics
try:
    import curses
    HAS_CURSES = True
except ImportError:
    HAS_CURSES = False

DATA_FILE = 'footprint_data.json'
BACKUP_FILE = 'footprint_data_backup.json'

CATEGORIES = ['transport', 'energy', 'food', 'waste']
CATEGORY_LABELS = {
    'transport': 'Transport (km)',
    'energy': 'Energy (kWh)',
    'food': 'Food (meals: l/m/h)',
    'waste': 'Waste (kg non-rec)'
}
FACTORS = {
    'transport': 0.2,  # kg/km
    'energy': 0.5,     # kg/kWh
    'food': {'low':1, 'medium':2.5, 'high':4},
    'waste': 0.1       # kg/non-recycled
}

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        return {date: entry for date, entry in data.items() if isinstance(entry, dict)}
    except:
        if os.path.exists(BACKUP_FILE):
            print("Corrupted data, restoring backup...")
            os.replace(BACKUP_FILE, DATA_FILE)
            return load_data()
        return {}

def save_data(data):
    backup_made = False
    if os.path.exists(DATA_FILE):
        os.replace(DATA_FILE, BACKUP_FILE)
        backup_made = True
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        if backup_made:
            os.remove(BACKUP_FILE)
    except Exception as e:
        print(f"Save failed: {e}")

def get_today():
    return datetime.date.today().isoformat()

def calculate_category_value(cat, input_val):
    if cat == 'transport':
        try:
            km = float(input_val)
            return km * FACTORS['transport']
        except:
            return 0
    elif cat == 'energy':
        try:
            kwh = float(input_val)
            return kwh * FACTORS['energy']
        except:
            return 0
    elif cat == 'food':
        if input_val.lower().startswith('l'): return FACTORS['food']['low']
        elif input_val.lower().startswith('m'): return FACTORS['food']['medium']
        elif input_val.lower().startswith('h'): return FACTORS['food']['high']
        return 0
    elif cat == 'waste':
        try:
            kg = float(input_val)
            return kg * FACTORS['waste']
        except:
            return 0
    return 0

def get_last_7_days(data):
    today = datetime.date.today()
    dates = []
    for i in range(7):
        date = (today - datetime.timedelta(days=i)).isoformat()
        dates.append(date)
    return sorted([d for d in dates if d in data], reverse=True)

def get_stats(data):
    days = get_last_7_days(data)
    if not days:
        return 0, 0, '→'
    totals = [data[d]['total'] for d in days if 'total' in data[d]]
    if len(totals) < 2:
        return statistics.mean(totals) if totals else 0, 0, '→'
    avg = statistics.mean(totals)
    med = statistics.median(totals)
    trend = '↓' if totals[0] < totals[-1] else '↑' if totals[0] > totals[-1] else '→'
    return avg, med, trend

def print_summary(data):
    print("\n" + "="*60)
    print("ECO FOOTPRINT - LAST 7 DAYS SUMMARY")
    print("="*60)
    days = get_last_7_days(data)
    for date in days[:7]:
        if date in data and 'total' in data[date]:
            print(f"{date}: {data[date]['total']:.1f}kg CO2")
        else:
            print(f"{date}: No data")
    
    avg, med, trend = get_stats(data)
    print(f"\nWeekly Average: {avg:.1f}kg/day {trend}")
    print(f"Weekly Median:  {med:.1f}kg/day")
    status = "🟢 Green!" if avg < 5 else "🟡 Reduce!"
    print(f"Status: {status}")
    
    print("\nTIPS:")
    print("- Switch to train: save 0.15kg/km")
    print("- LED bulbs: save 0.3kg/kWh")
    print("- Plant-based meals: save 2kg/meal")
    print("- Recycle more: save 0.08kg/kg")

def new_year_reset(stdscr, data):
    today = datetime.date.today()
    if today.year >= 2026:
        yearly_total = sum(data[d].get('total', 0) for d in data)
        stdscr.clear()
        stdscr.addstr(0, 0, "🌍 2026 ECO RESET 🌍")
        stdscr.addstr(2, 0, f"2025 Total: {yearly_total:.0f}kg CO2")
        stdscr.addstr(4, 0, "Reset all data? (y/n)")
        stdscr.refresh()
        c = stdscr.getch()
        if chr(c).lower() == 'y':
            data.clear()
            save_data(data)
            stdscr.addstr(6, 0, "Data reset! Happy New Year!")
        else:
            stdscr.addstr(6, 0, "Continuing...")
        stdscr.refresh()
        stdscr.getch()

def console_mode(data):
    today = get_today()
    if today not in data:
        data[today] = {cat: '0' for cat in CATEGORIES}
    
    while True:
        print("\n=== ECO FOOTPRINT TRACKER (Console) ===")
        print_summary(data)
        
        for i, cat in enumerate(CATEGORIES):
            val = data[today][cat]
            print(f"{i+1}. {CATEGORY_LABELS[cat]}: {val}")
        
        total = sum(calculate_category_value(cat, data[today][cat]) for cat in CATEGORIES)
        data[today]['total'] = total
        print(f"Daily Total: {total:.1f}kg CO2")
        
        cmd = input("\n(e=edit category, s=save, v=view, q=quit): ").lower()
        if cmd == 'q':
            save_data(data)
            break
        elif cmd == 's':
            save_data(data)
            print("Saved!")
        elif cmd == 'v':
            print_summary(data)
        elif cmd == 'e':
            cat_idx = input("Category (0-3): ")
            try:
                idx = int(cat_idx)
                if 0 <= idx < 4:
                    new_val = input(f"New value for {CATEGORY_LABELS[CATEGORIES[idx]]}: ")
                    data[today][CATEGORIES[idx]] = new_val
            except:
                print("Invalid input")

def curses_main(stdscr):
    curses.curs_set(1)
    stdscr.timeout(100)
    sh, sw = stdscr.getmaxyx()
    
    data = load_data()
    today = get_today()
    if today not in data:
        data[today] = {cat: '0' for cat in CATEGORIES}
    
    selected = 0
    edit_mode = False
    edit_win = None
    edit_box = None
    
    # New year check
    new_year_reset(stdscr, data)
    
    while True:
        stdscr.clear()
        
        # Header
        stdscr.addstr(0, 0, "🌍 ECO FOOTPRINT TRACKER 🌍", curses.A_BOLD)
        stdscr.addstr(1, 0, f"Today: {today} | Use ↑↓ to navigate, ENTER to edit, s=save, v=view, q=quit")
        
        # Calculate current totals
        values = {cat: calculate_category_value(cat, data[today][cat]) for cat in CATEGORIES}
        total = sum(values.values())
        data[today]['total'] = total
        
        # Stats
        avg, med, trend = get_stats(data)
        stdscr.addstr(3, 0, f"TODAY: {total:.1f}kg | 7d AVG: {avg:.1f}kg {trend} | Goal: {'🟢' if avg<5 else '🟡'}", curses.A_BOLD)
        
        # Categories grid
        for i, cat in enumerate(CATEGORIES):
            y = 5 + i*2
            attr = curses.A_REVERSE if i == selected else 0
            label = CATEGORY_LABELS[cat]
            val = data[today][cat]
            co2 = values[cat]
            stdscr.addstr(y, 0, f"{i+1:>2}. {label:<20} {val:>8} = {co2:>5.1f}kg", attr)
        
        # Controls
        stdscr.addstr(sh-3, 0, "↑↓: Select | ENTER: Edit | TAB: Next | s: Save | v: View History | q: Quit")
        
        # Screen reader announcements
        if edit_mode:
            stdscr.addstr(sh-1, 0, f"Editing {CATEGORY_LABELS[CATEGORIES[selected]]} (Enter to confirm)")
        
        stdscr.refresh()
        
        if edit_mode and edit_win:
            edit_win.refresh()
        
        try:
            c = stdscr.getch()
        except:
            continue
            
        if 0 <= c <= 255:
            char = chr(c).lower()
            if char == 'q':
                save_data(data)
                break
            elif char == 's':
                save_data(data)
                stdscr.addstr(sh-2, 0, "Saved!          ")
                stdscr.refresh()
                stdscr.getch()
            elif char == 'v':
                print_summary(data)
            elif char == 't':
                print_summary(data)
        elif c == KEY_UP:
            selected = (selected - 1) % len(CATEGORIES)
        elif c == KEY_DOWN:
            selected = (selected + 1) % len(CATEGORIES)
        elif c == KEY_ENTER or c == 10 or c == 13:
            if not edit_mode:
                # Start editing
                edit_y = 5 + selected * 2 + 1
                edit_win = stdscr.derwin(3, 25, edit_y, 35)
                rectangle(stdscr, edit_y-1, 34, edit_y+3, 34+25+1)
                edit_win.addstr(1, 1, data[today][CATEGORIES[selected]])
                stdscr.refresh()
                edit_box = Textbox(edit_win)
                edit_mode = True
                print(f"Editing {CATEGORY_LABELS[CATEGORIES[selected]]}")
            else:
                # Finish editing
                edit_box.edit()
                new_val = edit_box.gather().strip()
                data[today][CATEGORIES[selected]] = new_val
                edit_mode = False
                edit_win = None
                edit_box = None
        elif c == 9:  # TAB
            selected = (selected + 1) % len(CATEGORIES)

def main():
    if HAS_CURSES and os.isatty(0):
        curses_wrapper(curses_main)
    else:
        data = load_data()
        console_mode(data)

if __name__ == "__main__":
    main()