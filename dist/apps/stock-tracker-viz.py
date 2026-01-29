# Auto-generated via Perplexity on 2026-01-29T13:23:38.668809Z
import tkinter as tk
from tkinter import ttk, messagebox, Menu
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import json
import threading
import time
import datetime
import random
import queue
from collections import deque

class StockTracker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Stock Tracker Viz")
        self.root.geometry("1920x1080")
        self.root.minsize(800, 600)
        
        # Theme state (dark after 18:00 UTC)
        self.is_dark = datetime.datetime.now(datetime.timezone.utc).hour >= 18
        self.colors = {
            'light': {'bg': 'white', 'fg': 'black', 'line': 'navy', 'panel': '#f0f0f0'},
            'dark': {'bg': '#2b2b2b', 'fg': 'white', 'line': 'cyan', 'panel': '#3c3c3c'}
        }
        self.current_theme = self.colors['dark'] if self.is_dark else self.colors['light']
        
        # Data
        self.stocks = {}  # {symbol: deque(maxlen=30)}
        self.stock_prices = {}  # {symbol: current_price}
        self.selected_stock = None
        
        # Undo/Redo
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = 50
        
        # Threading
        self.update_queue = queue.Queue()
        self.running = True
        self.auto_save_time = 0
        
        # Setup UI
        self.setup_ui()
        self.load_data()
        self.start_update_thread()
        self.start_queue_processor()
        
        # Bind events
        self.root.bind('<Configure>', self.on_resize)
        self.root.bind('<Key>', self.on_key)
        self.root.after(1000, self.theme_transition)
        
    def get_theme(self):
        now = datetime.datetime.now(datetime.timezone.utc).hour
        return 'dark' if now >= 18 else 'light'
    
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(toolbar, text="Symbol:").pack(side=tk.LEFT)
        self.symbol_entry = ttk.Entry(toolbar, width=10)
        self.symbol_entry.pack(side=tk.LEFT, padx=(5,5))
        self.symbol_entry.bind('<Return>', lambda e: self.add_stock())
        
        ttk.Button(toolbar, text="Add", command=self.add_stock).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(toolbar, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(toolbar, text="Export JSON", command=self.export_json).pack(side=tk.LEFT)
        
        # Split panels
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel (40%)
        left_frame = ttk.Frame(paned, width=400)
        paned.add(left_frame, weight=4)
        
        ttk.Label(left_frame, text="Stocks", font=('Arial', 12, 'bold')).pack(pady=5)
        self.stock_listbox = tk.Listbox(left_frame, font=('Courier', 10))
        self.stock_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.stock_listbox.bind('<<ListboxSelect>>', self.on_stock_select)
        self.stock_listbox.bind('<Button-3>', self.show_context_menu)
        
        # Right panel (60%)
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=6)
        
        # Chart frame
        self.chart_frame = ttk.Frame(right_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(10, 6), facecolor=self.current_theme['bg'])
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Empty state
        self.empty_label = ttk.Label(self.chart_frame, text="Add stocks to visualize")
        self.empty_label.pack(expand=True)
        
        self.apply_theme()
    
    def apply_theme(self):
        theme = self.current_theme
        self.root.configure(bg=theme['bg'])
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=theme['panel'])
        style.configure('TLabel', background=theme['panel'], foreground=theme['fg'])
        style.configure('TButton', background=theme['panel'], foreground=theme['fg'])
        style.configure('TEntry', fieldbackground=theme['bg'], foreground=theme['fg'])
        style.configure('TListbox', background=theme['bg'], foreground=theme['fg'], fieldbackground=theme['bg'])
        style.map('TButton', background=[('active', theme['line'])])
        
        self.fig.patch.set_facecolor(theme['bg'])
        self.ax.set_facecolor(theme['panel'])
    
    def theme_transition(self):
        new_theme = self.get_theme()
        if new_theme != ('dark' if self.is_dark else 'light'):
            self.is_dark = not self.is_dark
            self.current_theme = self.colors['dark'] if self.is_dark else self.colors['light']
            self.apply_theme()
            self.update_chart()
        self.root.after(60000, self.theme_transition)  # Check every minute
    
    def add_stock(self):
        symbol = self.symbol_entry.get().strip().upper()
        if not symbol or symbol in self.stocks:
            return
        
        # Generate initial prices
        base_price = random.uniform(100, 200)
        self.stock_prices[symbol] = base_price
        self.stocks[symbol] = deque(maxlen=30)
        
        for _ in range(30):
            volatility = base_price * random.uniform(-0.05, 0.05)
            base_price += volatility
            self.stocks[symbol].append(base_price)
        
        self.record_action('add', symbol)
        self.update_listbox()
        self.update_chart()
        self.symbol_entry.delete(0, tk.END)
    
    def update_listbox(self):
        self.stock_listbox.delete(0, tk.END)
        if not self.stocks:
            self.empty_label.pack(expand=True)
            return
        
        self.empty_label.pack_forget()
        for symbol, prices in self.stocks.items():
            price = self.stock_prices.get(symbol, prices[-1] if prices else 0)
            self.stock_listbox.insert(tk.END, f"{symbol}: ${price:.2f}")
    
    def on_stock_select(self, event):
        selection = self.stock_listbox.curselection()
        if selection:
            items = self.stock_listbox.get(0, tk.END)
            self.selected_stock = items[selection[0]].split(':')[0]
            self.update_chart()
    
    def show_context_menu(self, event):
        try:
            self.selected_stock = self.stock_listbox.get(self.stock_listbox.nearest(event.y)).split(':')[0]
        except:
            return
        
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="Edit Price", command=self.edit_price)
        menu.add_command(label="Delete", command=self.delete_stock)
        menu.post(event.x_root, event.y_root)
    
    def edit_price(self):
        if not self.selected_stock:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit {self.selected_stock}")
        dialog.geometry("300x150")
        
        ttk.Label(dialog, text="New Price:").pack(pady=10)
        entry = ttk.Entry(dialog)
        entry.insert(0, str(self.stock_prices[self.selected_stock]))
        entry.pack(pady=5)
        entry.focus()
        
        def save():
            try:
                new_price = float(entry.get())
                old_price = self.stock_prices[self.selected_stock]
                self.stock_prices[self.selected_stock] = new_price
                self.stocks[self.selected_stock].append(new_price)
                self.record_action('edit_price', self.selected_stock, old_price, new_price)
                self.update_listbox()
                self.update_chart()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid price")
        
        ttk.Button(dialog, text="Save", command=save).pack(pady=10)
        entry.bind('<Return>', lambda e: save())
    
    def delete_stock(self):
        if self.selected_stock and messagebox.askyesno("Confirm", f"Delete {self.selected_stock}?"):
            self.record_action('delete', self.selected_stock)
            del self.stocks[self.selected_stock]
            self.stock_prices.pop(self.selected_stock, None)
            self.selected_stock = None
            self.update_listbox()
            self.update_chart()
    
    def clear_all(self):
        if self.stocks and messagebox.askyesno("Confirm", "Clear all stocks?"):
            self.record_action('clear_all')
            self.stocks.clear()
            self.stock_prices.clear()
            self.selected_stock = None
            self.update_listbox()
            self.update_chart()
    
    def update_chart(self):
        self.ax.clear()
        theme = self.current_theme
        
        if not self.stocks:
            self.ax.text(0.5, 0.5, 'Add stocks to visualize', 
                        ha='center', va='center', transform=self.ax.transAxes,
                        fontsize=16, color=theme['fg'])
        elif self.selected_stock and self.selected_stock in self.stocks:
            prices = list(self.stocks[self.selected_stock])
            dates = [datetime.datetime.now() - datetime.timedelta(minutes=30-i) for i in range(len(prices))]
            self.ax.plot(dates, prices, color=theme['line'], linewidth=2, label=self.selected_stock)
            self.ax.set_title(f"{self.selected_stock} Price History", color=theme['fg'])
            self.ax.set_ylabel("Price ($)", color=theme['fg'])
            self.ax.tick_params(colors=theme['fg'])
            self.ax.grid(True, alpha=0.3)
            self.ax.legend()
        else:
            # Show all stocks lightly
            for symbol, prices in self.stocks.items():
                if len(prices) > 0:
                    dates = [datetime.datetime.now() - datetime.timedelta(minutes=30-i) for i in range(len(prices))]
                    self.ax.plot(dates, list(prices), color=theme['line'], alpha=0.5, linewidth=1, label=symbol)
        
        self.fig.patch.set_facecolor(theme['bg'])
        self.ax.set_facecolor(theme['panel'])
        self.ax.tick_params(colors=theme['fg'])
        self.ax.spines['bottom'].set_color(theme['fg'])
        self.ax.spines['top'].set_color(theme['fg']) 
        self.ax.spines['right'].set_color(theme['fg'])
        self.ax.spines['left'].set_color(theme['fg'])
        self.canvas.draw()
    
    def simulate_update(self):
        while self.running:
            time.sleep(5)
            if not self.stocks:
                continue
            
            for symbol in list(self.stocks.keys()):
                if symbol in self.stock_prices:
                    current = self.stock_prices[symbol]
                    volatility = current * random.uniform(-0.05, 0.05)
                    new_price = max(1, current + volatility)
                    self.stock_prices[symbol] = new_price
                    self.stocks[symbol].append(new_price)
                    self.update_queue.put(('update_list', symbol))
            
            self.update_queue.put(('update_chart',))
    
    def process_queue(self):
        try:
            while True:
                cmd, *args = self.update_queue.get_nowait()
                if cmd == 'update_list':
                    self.update_listbox()
                elif cmd == 'update_chart':
                    self.update_chart()
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)
    
    def record_action(self, action, *args):
        self.undo_stack.append((action, args))
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
    
    def undo(self):
        if self.undo_stack:
            action, args = self.undo_stack.pop()
            self.redo_stack.append((action, args))
            
            if action == 'add':
                symbol = args[0]
                del self.stocks[symbol]
                self.stock_prices.pop(symbol, None)
            elif action == 'delete':
                symbol = args[0]
                base_price = self.stock_prices.get(symbol, 100)
                self.stock_prices[symbol] = base_price
                self.stocks[symbol] = deque([base_price] * 30, maxlen=30)
            elif action == 'edit_price':
                symbol, old_price, _ = args
                self.stock_prices[symbol] = old_price
            elif action == 'clear_all':
                pass  # Nothing to restore
            
            self.update_listbox()
            self.update_chart()
    
    def on_key(self, event):
        if event.state & 0x4:  # Ctrl
            if event.keysym == 'z':
                self.undo()
            elif event.keysym == 'y':
                # Redo (simplified)
                pass
        elif event.keysym == 'Return' and self.stock_listbox.selection():
            self.edit_price()
        elif event.keysym == 'Delete' and self.stock_listbox.selection():
            self.delete_stock()
    
    def on_resize(self, event):
        pass  # Handled by pack/grid weights
    
    def save_data(self):
        data = {symbol: list(prices) for symbol, prices in self.stocks.items()}
        data['prices'] = self.stock_prices
        try:
            with open('stocks.json', 'w') as f:
                json.dump(data, f)
            self.auto_save_time = time.time()
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")
    
    def load_data(self):
        try:
            with open('stocks.json', 'r') as f:
                data = json.load(f)
                self.stocks = {k: deque(v, maxlen=30) for k, v in data.items() if k != 'prices'}
                self.stock_prices = data.get('prices', {})
                self.update_listbox()
        except:
            pass
    
    def export_json(self):
        self.save_data()
        messagebox.showinfo("Export", "Data exported to stocks.json")
    
    def start_update_thread(self):
        thread = threading.Thread(target=self.simulate_update, daemon=True)
        thread.start()
    
    def start_queue_processor(self):
        self.process_queue()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = StockTracker()
    app.run()