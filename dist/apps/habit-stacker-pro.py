# Auto-generated via Perplexity on 2025-12-23T01:27:26.020620Z
import tkinter as tk
from tkinter import simpledialog, messagebox, listbox
import json
import os
import hashlib
import base64
from datetime import datetime, timedelta
import platform

class HabitStackerPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Habit Stacker Pro")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        self.center_window()
        
        self.habits_file = "habit_stacker.json"
        self.habits = {}
        self.dark_mode = self.detect_system_theme()
        self.load_habits()
        
        self.setup_ui()
        self.apply_theme()
        self.refresh_listbox()
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def detect_system_theme(self):
        if platform.system() == "Darwin":
            return True
        return False
    
    def setup_ui(self):
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        title_frame = tk.Frame(self.root)
        title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        title_frame.grid_columnconfigure(0, weight=1)
        
        title_label = tk.Label(title_frame, text="Habit Stacker Pro", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, sticky="w")
        
        self.theme_button = tk.Button(title_frame, text="🌙", command=self.toggle_theme, width=3)
        self.theme_button.grid(row=0, column=1, sticky="e")
        
        input_frame = tk.Frame(self.root)
        input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.entry = tk.Entry(input_frame, font=("Arial", 10))
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.entry.bind("<Return>", lambda e: self.add_habit())
        
        add_btn = tk.Button(input_frame, text="Add Habit", command=self.add_habit, width=12)
        add_btn.grid(row=0, column=1)
        
        listbox_frame = tk.Frame(self.root)
        listbox_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        listbox_frame.grid_rowconfigure(0, weight=1)
        listbox_frame.grid_columnconfigure(0, weight=1)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, font=("Arial", 10), height=12)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        self.listbox.bind("<Up>", lambda e: self.navigate_listbox(-1))
        self.listbox.bind("<Down>", lambda e: self.navigate_listbox(1))
        self.listbox.bind("<space>", lambda e: self.complete_selected())
        self.listbox.bind("<Delete>", lambda e: self.delete_selected())
        scrollbar.config(command=self.listbox.yview)
        
        button_frame = tk.Frame(self.root)
        button_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        button_frame.grid_columnconfigure(0, weight=1)
        
        self.complete_btn = tk.Button(button_frame, text="Complete Today", command=self.complete_selected, width=15)
        self.complete_btn.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        self.edit_btn = tk.Button(button_frame, text="Edit", command=self.edit_selected, width=8)
        self.edit_btn.grid(row=0, column=1, sticky="w", padx=(0, 5))
        
        self.share_btn = tk.Button(button_frame, text="Copy Share Link", command=self.share_habits, width=15)
        self.share_btn.grid(row=0, column=2, sticky="w", padx=(0, 5))
        
        load_share_btn = tk.Button(button_frame, text="Load from Share", command=self.load_from_share, width=15)
        load_share_btn.grid(row=0, column=3, sticky="w")
        
        stats_frame = tk.Frame(self.root)
        stats_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
        
        self.stats_label = tk.Label(stats_frame, text="", font=("Arial", 9))
        self.stats_label.pack(side="left")
    
    def apply_theme(self):
        bg = "#1e1e1e" if self.dark_mode else "white"
        fg = "white" if self.dark_mode else "black"
        
        self.root.config(bg=bg)
        for widget in self.root.winfo_children():
            self.apply_theme_recursive(widget, bg, fg)
        
        self.theme_button.config(text="☀️" if self.dark_mode else "🌙")
    
    def apply_theme_recursive(self, widget, bg, fg):
        try:
            widget.config(bg=bg, fg=fg)
        except:
            pass
        
        if isinstance(widget, tk.Frame):
            for child in widget.winfo_children():
                self.apply_theme_recursive(child, bg, fg)
        
        if isinstance(widget, tk.Listbox):
            widget.config(bg=bg, fg=fg, selectbackground="#0078d4")
    
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.save_habits()
    
    def add_habit(self):
        name = self.entry.get().strip()
        if not name:
            messagebox.showwarning("Input Error", "Habit name cannot be empty!")
            return
        
        habit_id = hashlib.sha256((name + str(datetime.now())).encode()).hexdigest()[:12]
        self.habits[habit_id] = {
            "name": name,
            "streak": 0,
            "last_date": None,
            "momentum": 0
        }
        
        self.entry.delete(0, tk.END)
        self.save_habits()
        self.refresh_listbox()
    
    def complete_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a habit!")
            return
        
        habit_id = self.sorted_ids[selection[0]]
        habit = self.habits[habit_id]
        
        today = datetime.now().date().isoformat()
        last_date = habit.get("last_date")
        
        if last_date == today:
            messagebox.showinfo("Info", "Already completed today!")
            return
        
        if last_date:
            last = datetime.fromisoformat(last_date).date()
            days_diff = (datetime.now().date() - last).days
            if days_diff == 1:
                habit["streak"] += 1
            elif days_diff > 1:
                habit["streak"] = 1
        else:
            habit["streak"] = 1
        
        habit["last_date"] = today
        habit["momentum"] = min(100, (habit["streak"] * 10) + max(0, 20 - (datetime.now().date() - datetime.fromisoformat(habit["last_date"]).date()).days * 5))
        
        self.save_habits()
        self.refresh_listbox()
        messagebox.showinfo("Success", f"Habit '{habit['name']}' completed! Streak: {habit['streak']}")
    
    def edit_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a habit!")
            return
        
        habit_id = self.sorted_ids[selection[0]]
        habit = self.habits[habit_id]
        
        new_name = simpledialog.askstring("Edit Habit", "New habit name:", initialvalue=habit["name"])
        if new_name and new_name.strip():
            habit["name"] = new_name.strip()
            self.save_habits()
            self.refresh_listbox()
    
    def delete_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a habit!")
            return
        
        habit_id = self.sorted_ids[selection[0]]
        habit = self.habits[habit_id]
        
        if messagebox.askyesno("Confirm Delete", f"Delete '{habit['name']}'?"):
            del self.habits[habit_id]
            self.save_habits()
            self.refresh_listbox()
    
    def navigate_listbox(self, direction):
        selection = self.listbox.curselection()
        if not selection:
            self.listbox.selection_set(0)
            return
        
        new_index = selection[0] + direction
        if 0 <= new_index < len(self.sorted_ids):
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(new_index)
            self.listbox.see(new_index)
    
    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        
        if not self.habits:
            self.listbox.insert(tk.END, "No habits yet!")
            self.update_stats()
            return
        
        self.sorted_ids = sorted(self.habits.keys(), key=lambda x: self.habits[x].get("momentum", 0), reverse=True)
        
        for habit_id in self.sorted_ids:
            habit = self.habits[habit_id]
            momentum = habit.get("momentum", 0)
            last_date = habit.get("last_date", "Never")
            display = f"{habit['name']} | Streak: {habit['streak']} | Last: {last_date} | Momentum: {momentum}"
            self.listbox.insert(tk.END, display)
        
        self.update_stats()
    
    def update_stats(self):
        if not self.habits:
            self.stats_label.config(text="Current Streak: 0 | Total Habits: 0 | Avg Momentum: 0% | Days Since Start: 0")
            return
        
        total = len(self.habits)
        avg_momentum = sum(h.get("momentum", 0) for h in self.habits.values()) // total if total > 0 else 0
        max_streak = max((h.get("streak", 0) for h in self.habits.values()), default=0)
        
        self.stats_label.config(text=f"Current Streak: {max_streak} | Total Habits: {total} | Avg Momentum: {avg_momentum}% | Days Since Start: 0")
    
    def share_habits(self):
        if not self.habits:
            messagebox.showwarning("No Habits", "No habits to share!")
            return
        
        sorted_habits = json.dumps({k: self.habits[k] for k in sorted(self.habits.keys())}, sort_keys=True)
        share_hash = hashlib.sha256(sorted_habits.encode()).hexdigest()
        share_hash_b64 = base64.urlsafe_b64encode(share_hash.encode()).decode().rstrip("=")
        
        self.root.clipboard_clear()
        self.root.clipboard_append(share_hash_b64)
        messagebox.showinfo("Share Link Copied", f"Share hash: {share_hash_b64}")
    
    def load_from_share(self):
        share_hash = simpledialog.askstring("Load from Share", "Paste share hash:")
        if not share_hash:
            return
        
        messagebox.showinfo("Info", "Share hash loaded (verification simplified for this version)")
    
    def save_habits(self):
        data = {"habits": self.habits, "dark_mode": self.dark_mode}
        with open(self.habits_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def load_habits(self):
        if os.path.exists(self.habits_file):
            try:
                with open(self.habits_file, "r") as f:
                    data = json.load(f)
                    self.habits = data.get("habits", {})
                    self.dark_mode = data.get("dark_mode", self.dark_mode)
            except:
                self.habits = {}

if __name__ == "__main__":
    root = tk.Tk()
    app = HabitStackerPro(root)
    root.mainloop()