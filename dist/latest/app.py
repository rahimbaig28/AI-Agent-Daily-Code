# Auto-generated via Perplexity on 2026-02-07T14:43:45.184917Z
import curses
import json
import os
import datetime
import time
import random
import statistics
import signal
import sys

DATA_FILE = 'stock_data.json'
SEED = 60016
NUM_STOCKS = 10
DAYS_HISTORY = 30
CHART_WIDTH = 60
CHART_HEIGHT = 20

class Stock:
    def __init__(self, name, history):
        self.name = name
        self.history = history[:]  # Daily close prices

    def current_price(self):
        return self.history[-1]

    def day_change_pct(self):
        if len(self.history) < 2:
            return 0.0
        return ((self.history[-1] - self.history[-2]) / self.history[-2]) * 100

    def seven_day_avg(self):
        if len(self.history) < 7:
            return self.current_price()
        return statistics.mean(self.history[-7:])

    def volatility(self):
        if len(self.history) < 8:
            return 0.0
        changes = [(self.history[i] - self.history[i-1]) / self.history[i-1] * 100
                  for i in range(-7, 0)]
        return statistics.stdev(changes)

    def update_price(self):
        change = random.uniform(-0.05, 0.05)
        new_price = self.history[-1] * (1 + change)
        self.history.append(new_price)

def generate_initial_data():
    random.seed(SEED)
    stocks = []
    for i in range(NUM_STOCKS):
        name = f"STOCK-{i+1:02d}"
        history = [100.0]
        for _ in range(DAYS_HISTORY - 1):
            change = random.uniform(-0.02, 0.02)
            history.append(history[-1] * (1 + change))
        stocks.append(Stock(name, history))
    return stocks

def save_data(stocks, settings):
    data = {
        'stocks': [{'name': s.name, 'history': s.history} for s in stocks],
        'settings': settings
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def load_data():
    if not os.path.exists(DATA_FILE):
        return generate_initial_data(), {'selected': 0, 'time_range': 7, 'viz_mode': 0, 'theme': 'auto'}
    
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        stocks = [Stock(s['name'], s['history']) for s in data['stocks']]
        settings = data.get('settings', {'selected': 0, 'time_range': 7, 'viz_mode': 0, 'theme': 'auto'})
        return stocks, settings
    except:
        return generate_initial_data(), {'selected': 0, 'time_range': 7, 'viz_mode': 0, 'theme': 'auto'}

def detect_theme(stdscr):
    if not curses.has_colors():
        return 'light'
    curses.start_color()
    try:
        curses.use_default_colors()
        # Sample background color (approximate)
        bg = curses.COLOR_BLACK if stdscr.getbkgd() & curses.A_COLOR == 0 else curses.COLOR_WHITE
        return 'dark' if bg == curses.COLOR_BLACK else 'light'
    except:
        return 'light'

def get_color_pair(theme, is_green):
    if theme == 'dark':
        return curses.COLOR_GREEN if is_green else curses.COLOR_RED
    else:
        return curses.COLOR_BLACK if is_green else curses.COLOR_RED

def render_chart(stdscr, stock, time_range, viz_mode, theme, chart_x, chart_y, width, height):
    data = stock.history[-time_range:]
    if not data:
        return
    
    min_val, max_val = min(data), max(data)
    if max_val == min_val:
        max_val += 1
    
    scale_y = (height - 1) / (max_val - min_val)
    
    # Clear chart area
    for y in range(height):
        stdscr.move(chart_y + y, chart_x)
        stdscr.clrtoeol()
    
    chars = {'line': ['*'], 'bar': ['#'], 'sparkline': ['▁','▂','▃','▄','▅','▆','▇','█']}
    
    for x in range(width):
        idx = min(x * len(data) // width, len(data) - 1)
        val = data[idx]
        y = height - 1 - int((val - min_val) * scale_y)
        
        if viz_mode == 0:  # line
            stdscr.addch(chart_y + y, chart_x + x, ord('*'))
        elif viz_mode == 1:  # bar
            for by in range(y, height):
                stdscr.addch(chart_y + by, chart_x + x, ord('#'))
        else:  # sparkline
            level = int((val - min_val) / (max_val - min_val) * 7)
            stdscr.addch(chart_y + height//2, chart_x + x, ord(chars['sparkline'][level]))

def main(stdscr):
    global stocks, settings
    
    # Signal handler for graceful exit
    def signal_handler(sig, frame):
        save_data(stocks, settings)
        curses.endwin()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    curses.curs_set(0)
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.timeout(5000)  # Update every 5s
    
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
    
    stocks, settings = load_data()
    selected = settings['selected']
    time_range = settings['time_range']
    viz_mode = settings['viz_mode']
    theme_mode = settings['theme']
    
    help_overlay = False
    last_time = time.time()
    
    while True:
        height, width = stdscr.getmaxyx()
        if height < 25 or width < 100:
            stdscr.addstr(0, 0, "Terminal too small! Need 25x100 minimum.")
            stdscr.refresh()
            stdscr.getch()
            continue
        
        theme = detect_theme(stdscr) if theme_mode == 'auto' else theme_mode
        
        stdscr.clear()
        
        # Top: Date/time and theme
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stdscr.addstr(0, 0, f"Stock Tracker | {now} | Theme: {theme_mode} | Selected: {selected+1}/{NUM_STOCKS}", 
                     curses.A_BOLD)
        
        # STATUS announcement area (lines 1-2)
        stdscr.addstr(1, 0, "STATUS: Ready", curses.A_STANDOUT)
        
        # Left panel: Stock list (rows 3-22)
        list_y = 3
        for i, stock in enumerate(stocks):
            attrs = curses.A_NORMAL
            if i == selected:
                attrs |= curses.A_REVERSE
            change = stock.day_change_pct()
            color = curses.color_pair(1) if change >= 0 else curses.color_pair(2)
            if i == selected:
                color |= curses.A_BOLD
            stdscr.addstr(list_y + i, 2, f"{stock.name}  ${stock.current_price():6.2f}  {change:+6.2f}%", 
                         attrs | color)
        
        # Right panel: Chart (cols 65-124, rows 3-22)
        chart_x, chart_y = 65, 3
        render_chart(stdscr, stocks[selected], time_range, viz_mode, theme, chart_x, chart_y, CHART_WIDTH, CHART_HEIGHT)
        stdscr.addstr(chart_y - 1, chart_x, f"Chart ({['Line','Bar','Sparkline'][viz_mode]}, {time_range} days):", curses.A_BOLD)
        
        # Bottom: Stats and controls (rows height-4 to end)
        stats_y = height - 6
        stock = stocks[selected]
        stdscr.addstr(stats_y, 2, f"Price: ${stock.current_price():7.2f}", curses.A_BOLD)
        stdscr.addstr(stats_y, 25, f"7d Avg: ${stock.seven_day_avg():6.2f}")
        vol = stock.volatility()
        vol_color = curses.color_pair(1) if vol < 2 else curses.color_pair(2)
        stdscr.addstr(stats_y, 45, f"Volatility: {vol:.2f}%", vol_color | curses.A_BOLD)
        
        stdscr.addstr(stats_y + 1, 2, "↑↓: Navigate | ←→: Zoom time | r: Refresh | v: Viz mode | Enter: Stats | Tab: Theme")
        stdscr.addstr(stats_y + 2, 2, "Esc: Help | s: Save & Exit")
        
        # Help overlay
        if help_overlay:
            overlay_attrs = curses.A_REVERSE | curses.A_BOLD
            for i, line in enumerate([
                "HELP - Stock Tracker Controls",
                "↑↓ arrows: Navigate stocks (10 total)",
                "←→ arrows: Zoom time range (7/30 days)",
                "r: Refresh all prices (+-5% random)",
                "v: Toggle viz: Line -> Bar -> Sparkline",
                "Enter: Announce current stock stats",
                "Tab: Cycle theme (light/dark/auto)",
                "s: Save data and exit",
                "Esc: Toggle this help",
                "Ctrl+C: Emergency save & exit",
                "",
                "Press any key to continue..."
            ]):
                stdscr.addstr(height//2 - 6 + i, width//2 - 30, line.center(60), overlay_attrs)
        
        stdscr.refresh()
        
        key = stdscr.getch()
        current_time = time.time()
        
        if key == ord('s'):
            save_data(stocks, {'selected': selected, 'time_range': time_range, 'viz_mode': viz_mode, 'theme': theme_mode})
            break
        elif key == 27:  # Esc
            help_overlay = not help_overlay
        elif key == curses.KEY_UP and selected > 0:
            selected -= 1
        elif key == curses.KEY_DOWN and selected < NUM_STOCKS - 1:
            selected += 1
        elif key == curses.KEY_LEFT and time_range > 7:
            time_range = 7
        elif key == curses.KEY_RIGHT and time_range < DAYS_HISTORY:
            time_range = DAYS_HISTORY
        elif key == ord('r'):
            for stock in stocks:
                stock.update_price()
            stdscr.addstr(1, 0, "STATUS: Prices refreshed", curses.A_STANDOUT)
        elif key == ord('v'):
            viz_mode = (viz_mode + 1) % 3
        elif key == 10 or key == curses.KEY_ENTER:  # Enter
            stock = stocks[selected]
            msg = f"STATUS: {stock.name} ${stock.current_price():.2f} | 7d: ${stock.seven_day_avg():.2f} | Vol: {stock.volatility():.2f}%"
            stdscr.addstr(1, 0, msg[:80], curses.A_STANDOUT)
        elif key == 9:  # Tab
            themes = ['light', 'dark', 'auto']
            idx = (themes.index(theme_mode) + 1) % 3
            theme_mode = themes[idx]
        
        # Auto-save settings every 30s
        if current_time - last_time > 30:
            settings = {'selected': selected, 'time_range': time_range, 'viz_mode': viz_mode, 'theme': theme_mode}
            save_data(stocks, settings)
            last_time = current_time

if __name__ == "__main__":
    curses.wrapper(main)