# Auto-generated via Perplexity on 2025-12-30T01:27:51.123903Z
#!/usr/bin/env python3
import json
import os
import sys
import base64
import shutil
from typing import List, Tuple, Dict, Any
import subprocess
import shlex

DATA_FILE = "chart_data.json"

SAMPLE_DATASETS = {
    "1": {
        "name": "Sales Trends",
        "data": [[1, 120], [2, 150], [3, 140], [4, 180], [5, 200], [6, 190], [7, 220], [8, 250], [9, 240], [10, 280]]
    },
    "2": {
        "name": "Temperature Readings",
        "data": [[1, 22.5], [2, 23.1], [3, 21.8], [4, 24.2], [5, 25.0], [6, 26.3], [7, 24.9], [8, 23.7], [9, 22.1], [10, 21.5]]
    },
    "3": {
        "name": "Survey Results",
        "data": [[1, 45], [2, 52], [3, 38], [4, 60], [5, 55], [6, 48], [7, 62], [8, 70], [9, 65], [10, 58]]
    }
}

CHART_TYPES = {
    "1": ("Line Chart", "line_chart"),
    "2": ("Bar Chart", "bar_chart"), 
    "3": ("Histogram", "histogram"),
    "4": ("Scatter Plot", "scatter_plot")
}

def get_terminal_size():
    try:
        size = shutil.get_terminal_size()
        return size.columns, size.lines
    except:
        return 80, 24

def load_prefs():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"dark_mode": True, "recent": []}

def save_prefs(prefs):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(prefs, f)
    except:
        pass

def detect_dark_mode():
    try:
        result = subprocess.run(['osascript', '-e', 'tell app "System Events" to tell appearance preferences to get dark mode'], 
                              capture_output=True, text=True)
        return 'true' in result.stdout.lower()
    except:
        return os.environ.get('COLORTERM', '').lower() in ['truecolor', '24bit']

def get_colors(dark_mode):
    if dark_mode:
        return {
            'bg': '\033[48;5;233m', 'fg': '\033[38;5;252m', 'grid': '\033[38;5;240m',
            'data': '\033[38;5;45m', 'axis': '\033[38;5;250m', 'reset': '\033[0m'
        }
    else:
        return {
            'bg': '\033[48;5;231m', 'fg': '\033[38;5;0m', 'grid': '\033[38;5;242m',
            'data': '\033[38;5;28m', 'axis': '\033[38;5;240m', 'reset': '\033[0m'
        }

def clear_screen():
    print('\033[2J\033[H', end='')

def truncate_data(data: List[List[float]], max_points=50) -> List[List[float]]:
    if len(data) > max_points:
        step = len(data) // max_points
        return [data[i] for i in range(0, len(data), step)][:max_points]
    return data

def normalize_data(data: List[List[float]], height: int) -> List[int]:
    if not data:
        return []
    values = [p[1] for p in data]
    min_val, max_val = min(values), max(values)
    if max_val == min_val:
        return [height // 2] * len(data)
    range_val = max_val - min_val
    return [(int((v - min_val) / range_val * (height - 1))) for v in values]

def line_chart(width: int, height: int, data: List[List[float]], colors: Dict[str, str]):
    data = truncate_data(data, width // 4)
    y_vals = normalize_data(data, height - 2)
    x_vals = [i * (width - 1) // max(len(data) - 1, 1) for i in range(len(data))]
    
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Plot points and lines
    for i in range(len(data) - 1):
        x1, y1 = x_vals[i], height - 2 - y_vals[i]
        x2, y2 = x_vals[i + 1], height - 2 - y_vals[i + 1]
        
        if x1 == x2:
            for y in range(min(y1, y2), max(y1, y2) + 1):
                grid[y][x1] = '*'
        else:
            slope = (y2 - y1) / (x2 - x1)
            for x in range(x1, x2 + 1):
                y = int(y1 + slope * (x - x1))
                grid[y][x] = '*'
    
    # Axes
    for i in range(height):
        grid[i][0] = '|'
    for j in range(width):
        grid[height - 2][j] = '-'
    grid[height - 2][0] = '+'
    
    return grid, x_vals, y_vals

def bar_chart(width: int, height: int, data: List[List[float]], colors: Dict[str, str]):
    data = truncate_data(data, (width - 1) // 3)
    y_vals = normalize_data(data, height - 2)
    
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    bar_width = max(1, (width - 1) // len(data))
    for i, y in enumerate(y_vals):
        x_start = 1 + i * bar_width
        for h in range(height - 2 - y, height - 2):
            for x in range(x_start, min(x_start + bar_width - 1, width)):
                grid[h][x] = '#'
    
    # Axes
    for i in range(height):
        grid[i][0] = '|'
    for j in range(width):
        grid[height - 2][j] = '-'
    grid[height - 2][0] = '+'
    
    return grid, None, y_vals

def histogram(width: int, height: int, data: List[List[float]], colors: Dict[str, str]):
    values = [p[1] for p in truncate_data(data, width // 2)]
    if not values:
        return [[' ' for _ in range(width)] for _ in range(height)], None, []
    
    bins = width - 2
    bin_size = max((max(values) - min(values)) / bins, 0.1)
    hist = [0] * bins
    
    for v in values:
        bin_idx = min(int((v - min(values)) / bin_size), bins - 1)
        hist[bin_idx] += 1
    
    y_vals = normalize_data([[i, h] for i, h in enumerate(hist)], height - 2)
    
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    for i, y in enumerate(y_vals):
        for h in range(height - 2 - y, height - 2):
            grid[h][i + 1] = '█'
    
    # Axes
    for i in range(height):
        grid[i][0] = '|'
    for j in range(width):
        grid[height - 2][j] = '-'
    grid[height - 2][0] = '+'
    
    return grid, None, y_vals

def scatter_plot(width: int, height: int, data: List[List[float]], colors: Dict[str, str]):
    data = truncate_data(data, width * height // 4)
    x_norm = normalize_data([[p[0], 0] for p in data], width - 1)
    y_norm = normalize_data([[0, p[1]] for p in data], height - 2)
    
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    for i, (x, y) in enumerate(zip(x_norm, y_norm)):
        grid[height - 2 - y][x] = '*'
    
    # Axes
    for i in range(height):
        grid[i][0] = '|'
    for j in range(width):
        grid[height - 2][j] = '-'
    grid[height - 2][0] = '+'
    
    return grid, x_norm, y_norm

def render_chart(chart_type: str, width: int, height: int, data: List[List[float]], colors: Dict[str, str]):
    renderers = {
        "line_chart": line_chart,
        "bar_chart": bar_chart,
        "histogram": histogram,
        "scatter_plot": scatter_plot
    }
    
    grid, x_vals, y_vals = renderers[chart_type](width, height, data, colors)
    
    # Render with colors
    output = []
    for row in grid:
        output.append(''.join(row))
    
    return output, x_vals, y_vals, data

def get_stats(data: List[List[float]]) -> str:
    if not data:
        return "No data"
    values = [p[1] for p in data]
    return f"Min: {min(values):.1f}, Max: {max(values):.1f}, Avg: {sum(values)/len(values):.1f}"

def generate_shareable_config(dataset_name: str, chart_type: str, width: int, height: int, dark_mode: bool) -> str:
    config = {
        "dataset": dataset_name,
        "chart_type": chart_type,
        "width": width,
        "height": height,
        "dark_mode": dark_mode
    }
    return base64.b64encode(json.dumps(config).encode()).decode()

def parse_shareable_config(config_str: str) -> Dict[str, Any]:
    try:
        config = json.loads(base64.b64decode(config_str).decode())
        return config
    except:
        return None

def print_help():
    print("\n" + "="*50)
    print("📊 ASCII Data Chart Generator - Controls")
    print("="*50)
    print("↑↓ Arrow keys: Navigate datasets")
    print("1-4: Select chart type (1:Line, 2:Bar, 3:Hist, 4:Scatter)")
    print("c: Enter custom CSV data (x1,y1,x2,y2...)")
    print("d: Toggle dark/light mode")
    print("s: Save/Share config")
    print("h: Show this help")
    print("q: Quit")
    print("="*50 + "\n")

def main():
    prefs = load_prefs()
    dark_mode = prefs.get("dark_mode", detect_dark_mode())
    colors = get_colors(dark_mode)
    
    tw, th = get_terminal_size()
    chart_width = max(40, tw - 4)
    chart_height = max(15, th - 10)
    
    # Current state
    current_dataset = "1"
    current_chart_type = "line_chart"
    custom_data = None
    
    recent_datasets = prefs.get("recent", [])
    
    while True:
        clear_screen()
        
        # Header
        print(f"{colors['fg']}📊 ASCII Chart Generator{colors['reset']}")
        print(f"Dataset: {SAMPLE_DATASETS[current_dataset]['name']} | Chart: {dict(CHART_TYPES)[current_chart_type]}{colors['reset']}")
        print(f"Size: {chart_width}x{chart_height} | Mode: {'🌙 Dark' if dark_mode else '☀️ Light'}{colors['reset']}")
        
        # Render chart
        data = custom_data or SAMPLE_DATASETS[current_dataset]["data"]
        chart_output, _, _, full_data = render_chart(current_chart_type, chart_width, chart_height, data, colors)
        
        print("\n" + colors['bg'] + colors['fg'])
        for line in chart_output:
            print(line)
        print(colors['reset'])
        
        # Stats and legend
        print(f"{colors['axis']}{'─' * chart_width}{colors['reset']}")
        print(f"{colors['fg']}Stats: {get_stats(full_data)}{colors['reset']}")
        print(f"{colors['data']}*█#: Data points{colors['reset']} {colors['axis']} |─+: Axes{colors['reset']}")
        
        # Recent datasets
        if recent_datasets:
            print(f"\nRecent: {', '.join(recent_datasets[-3:])}")
        
        # Input prompt
        try:
            import termios, tty
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            
            key = sys.stdin.read(1)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        except:
            key = input("\nPress key (↑↓1-4cdshq): ").lower()
        
        if key == 'q':
            break
        elif key == 'h':
            print_help()
            input("Press Enter...")
            continue
        elif key == 'd':
            dark_mode = not dark_mode
            prefs["dark_mode"] = dark_mode
            colors = get_colors(dark_mode)
        elif key == 's':
            config = generate_shareable_config(
                SAMPLE_DATASETS[current_dataset]["name"], 
                current_chart_type, chart_width, chart_height, dark_mode
            )
            print(f"\n📤 Shareable config: {config}")
            print("Paste this anywhere to recreate!")
            prefs["recent"].append(SAMPLE_DATASETS[current_dataset]["name"])
            input("Press Enter...")
        elif key == 'c':
            csv_input = input("Enter CSV data (x1,y1,x2,y2...): ").strip()
            try:
                points = [float(x.strip()) for x in csv_input.split(',')]
                if len(points) % 2 == 0:
                    custom_data = [[points[i], points[i+1]] for i in range(0, len(points), 2)]
                    current_dataset = "Custom"
                    prefs["recent"].append("Custom")
                else:
                    print("Invalid format! Use: x1,y1,x2,y2...")
            except:
                print("Invalid numbers!")
            input("Press Enter...")
        elif key in CHART_TYPES:
            current_chart_type = CHART_TYPES[key][1]
        elif key == '\x1b[D' or key == '\x1b[A':  # Left/Up
            idx = int(current_dataset) - 1
            current_dataset = str((idx - 1) % len(SAMPLE_DATASETS) + 1)
        elif key == '\x1b[C' or key == '\x1b[B':  # Right/Down
            idx = int(current_dataset) - 1
            current_dataset = str((idx + 1) % len(SAMPLE_DATASETS) + 1)
    
    save_prefs(prefs)
    print("👋 Thanks for using ASCII Chart Generator!")

if __name__ == "__main__":
    main()