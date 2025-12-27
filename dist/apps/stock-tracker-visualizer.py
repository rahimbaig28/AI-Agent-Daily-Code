# Auto-generated via Perplexity on 2025-12-27T04:32:01.688151Z
import json
import os
import random
import statistics
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import time

# Seed for reproducibility
random.seed(79447)

STOCKS = ['AAPL-like', 'TSLA-like', 'GOOG-like', 'MSFT-like', 'NVDA-like']
DATA_FILE = 'stocks.json'
NUM_DAYS = 200

def is_dark_theme():
    term = os.environ.get('TERM', '')
    return 'dark' in term.lower() or os.environ.get('COLORTERM') == 'truecolor'

def generate_initial_data():
    data = {}
    start_date = datetime(2025, 12, 1)
    for stock in STOCKS:
        prices = [random.uniform(50, 200)]
        volumes = [random.randint(1000000, 10000000)]
        dates = [start_date]
        
        for _ in range(NUM_DAYS - 1):
            change = random.uniform(-0.05, 0.05)
            new_price = prices[-1] * (1 + change)
            prices.append(max(1.0, new_price))
            volumes.append(random.randint(1000000, 10000000))
            dates.append(dates[-1] + timedelta(days=1))
        
        data[stock] = {
            'dates': [d.isoformat() for d in dates],
            'prices': prices,
            'volumes': volumes
        }
    return data

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f)
    except Exception:
        print("Warning: Could not save data")

def parse_date(date_str):
    return datetime.fromisoformat(date_str)

def print_chart_summary(chart_type):
    print(f"\n📊 **{chart_type.upper()} CHART SUMMARY**")
    print("=" * 50)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_chart(chart_func, filename, summary_func):
    plt.style.use('dark_background' if is_dark_theme() else 'default')
    
    print_chart_summary(summary_func.__name__.replace('_', ' ').title())
    summary_func()
    
    fig = plt.figure(figsize=(12, 8))
    chart_func(fig)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.show(block=False)
    
    print(f"\n💾 Chart saved as '{filename}'")
    print("⏳ Chart will close in 10 seconds or press Enter...")
    time.sleep(10)
    plt.close('all')
    input("Press Enter to continue...")

def line_chart_summary():
    data = load_data()
    if not data:
        print("No data available")
        return
    print("📈 Price trends over time:")
    for stock in STOCKS:
        prices = data[stock]['prices']
        start_p = prices[0]
        end_p = prices[-1]
        change = ((end_p - start_p) / start_p) * 100
        peak = max(prices)
        print(f"  {stock}: ${start_p:.1f} → ${end_p:.1f} ({change:+.1f}%), peak ${peak:.1f}")

def line_chart(fig):
    data = load_data()
    if not data:
        return
    
    ax = fig.add_subplot(111)
    for stock in STOCKS:
        dates = [parse_date(d) for d in data[stock]['dates']]
        prices = data[stock]['prices']
        ax.plot(dates, prices, marker='o', markersize=2, label=stock)
    
    ax.set_title('Stock Prices Dec 2025', fontsize=16, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Price ($)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

def volume_chart_summary():
    data = load_data()
    if not data:
        return
    print("📊 Latest daily volumes:")
    latest_day = -1
    for stock in STOCKS:
        vol = data[stock]['volumes'][latest_day]
        price_change = ((data[stock]['prices'][latest_day] - data[stock]['prices'][latest_day-1]) 
                       / data[stock]['prices'][latest_day-1]) * 100
        color = "🟢" if price_change >= 0 else "🔴"
        print(f"  {stock}: {vol/1e6:.1f}M shares {color} ({price_change:+.1f}%)")

def volume_chart(fig):
    data = load_data()
    if not data:
        return
    
    ax = fig.add_subplot(111)
    x_pos = range(len(STOCKS))
    volumes = [data[stock]['volumes'][-1] for stock in STOCKS]
    changes = []
    for stock in STOCKS:
        p1, p2 = data[stock]['prices'][-2], data[stock]['prices'][-1]
        changes.append((p2 - p1) / p1)
    
    colors = ['red' if c < 0 else 'blue' for c in changes]
    bars = ax.bar(x_pos, volumes, color=colors, alpha=0.7)
    
    ax.set_title('Latest Trading Volumes', fontsize=16, fontweight='bold')
    ax.set_xlabel('Stocks')
    ax.set_ylabel('Volume (shares)')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(STOCKS)
    ax.grid(True, alpha=0.3)
    
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{volumes[i]/1e6:.1f}M', ha='center', va='bottom')

def scatter_chart_summary():
    data = load_data()
    if not data:
        return
    print("📈 Price vs Volume correlation:")
    for stock in STOCKS:
        prices = data[stock]['prices']
        volumes = data[stock]['volumes']
        corr = statistics.correlation(prices, volumes)
        avg_price = statistics.mean(prices)
        print(f"  {stock}: avg ${avg_price:.1f}, vol corr {corr:.3f}")

def scatter_chart(fig):
    data = load_data()
    if not data:
        return
    
    ax = fig.add_subplot(111)
    colors = ['red', 'blue', 'green', 'orange', 'purple']
    for i, stock in enumerate(STOCKS):
        prices = data[stock]['prices']
        volumes = [v/1e6 for v in data[stock]['volumes']]
        ax.scatter(prices, volumes, c=colors[i], label=stock, alpha=0.7, s=30)
    
    ax.set_title('Price vs Volume (all stocks)', fontsize=16, fontweight='bold')
    ax.set_xlabel('Price ($)')
    ax.set_ylabel('Volume (millions)')
    ax.legend()
    ax.grid(True, alpha=0.3)

def stats_table():
    data = load_data()
    if not data:
        print("No data available")
        return
    
    print("\n📋 **STATS TABLE**")
    print("=" * 80)
    print(f"{'Stock':<12} {'Avg Price':<10} {'Volatility':<12} {'Today':<12}")
    print("-" * 80)
    
    today_idx = -1
    for stock in STOCKS:
        prices = data[stock]['prices']
        avg_price = statistics.mean(prices)
        stdev = statistics.stdev(prices)
        volatility = (stdev / avg_price) * 100
        
        today_price = prices[today_idx]
        yesterday_price = prices[today_idx-1]
        today_change = ((today_price - yesterday_price) / yesterday_price) * 100
        
        print(f"{stock:<12} ${avg_price:>8.1f}   {volatility:>7.1f}%    "
              f"{today_change:+6.1f}%  ${today_price:>6.1f}")
    
    # Top performer
    top_stock = max(STOCKS, key=lambda s: (
        (data[s]['prices'][-1] - data[s]['prices'][-2]) / data[s]['prices'][-2]
    ))
    print(f"\n🏆 **Top performer today**: {top_stock}")

def simulate_next_day():
    data = load_data()
    if not data:
        print("No data to simulate")
        return
    
    print("\n⚡ Simulating next trading day...")
    for stock in STOCKS:
        last_price = data[stock]['prices'][-1]
        change = random.uniform(-0.05, 0.05)
        new_price = last_price * (1 + change)
        data[stock]['prices'].append(max(1.0, new_price))
        data[stock]['volumes'].append(random.randint(1000000, 10000000))
        
        last_date = parse_date(data[stock]['dates'][-1])
        data[stock]['dates'].append((last_date + timedelta(days=1)).isoformat())
    
    save_data(data)
    print("✅ Day simulated and saved!")

def main():
    data = load_data()
    if not data:
        print("🌟 Generating initial 200 days of stock data...")
        data = generate_initial_data()
        save_data(data)
        print("✅ Data generated and saved to stocks.json")
    
    while True:
        clear_screen()
        print("📈 STOCK TRACKER VISUALIZER")
        print("=" * 40)
        print("1. Line chart (all prices)")
        print("2. Bar chart (latest volumes)")
        print("3. Scatter plot (price vs volume)")
        print("4. Stats table")
        print("5. Simulate next day")
        print("q. Quit")
        print("-" * 40)
        
        choice = input("Enter choice (1-5,q): ").strip().lower()
        
        if choice == 'q':
            print("👋 Goodbye!")
            break
        elif choice == '1':
            show_chart(line_chart, 'chart1_line.png', line_chart_summary)
        elif choice == '2':
            show_chart(volume_chart, 'chart2_volume.png', volume_chart_summary)
        elif choice == '3':
            show_chart(scatter_chart, 'chart3_scatter.png', scatter_chart_summary)
        elif choice == '4':
            stats_table()
            input("\nPress Enter to continue...")
        elif choice == '5':
            simulate_next_day()
            input("\nPress Enter to continue...")
        else:
            print("❌ Invalid choice. Please enter 1-5 or q.")
            time.sleep(1)

if __name__ == "__main__":
    main()