# Auto-generated via Perplexity on 2026-01-30T02:51:11.671552Z
#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import json
import hashlib
import base64
import threading
from pathlib import Path
import argparse
import webbrowser

class AccessibilityAuditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Accessibility Auditor Pro")
        self.root.geometry("1200x800")
        
        # Data
        self.paths = []
        self.scan_results = []
        self.scan_data_file = Path(__file__).parent / "scan_data.json"
        
        # UI Setup
        self.setup_ui()
        self.bind_hotkeys()
        self.load_initial_paths()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0,5))
        
        ttk.Button(toolbar, text="New (Ctrl+N)", command=self.new_scan).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Scan (F5)", command=self.run_scan).pack(side=tk.LEFT, padx=(5,0))
        ttk.Button(toolbar, text="Open (Ctrl+O)", command=self.add_paths_dialog).pack(side=tk.LEFT, padx=(5,0))
        ttk.Button(toolbar, text="Save (Ctrl+S)", command=self.save_scan).pack(side=tk.LEFT, padx=(5,0))
        ttk.Button(toolbar, text="Load (Ctrl+L)", command=self.load_scan).pack(side=tk.LEFT, padx=(5,0))
        ttk.Button(toolbar, text="Share (Ctrl+H)", command=self.share_hash).pack(side=tk.LEFT, padx=(5,0))
        
        self.status_label = ttk.Label(toolbar, text="Ready")
        self.status_label.pack(side=tk.RIGHT)
        
        # Panes
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left: File list
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="Files & Folders", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.file_listbox = tk.Listbox(left_frame, height=20)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, pady=(0,5))
        self.file_listbox.bind('<Double-1>', self.show_details)
        self.file_listbox.bind('<Return>', self.show_details)
        self.file_listbox.bind('<Up>', lambda e: 'break')
        self.file_listbox.bind('<Down>', lambda e: 'break')
        
        # Right: Details
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        ttk.Label(right_frame, text="Details", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.details_text = tk.Text(right_frame, height=20, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=scrollbar.set)
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bottom: Progress
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(5,0))
        
        # Accessibility labels
        self.root.wm_attributes('-topmost', False)
        self.file_listbox.focus_set()
        
    def bind_hotkeys(self):
        self.root.bind('<Control-n>', lambda e: self.new_scan())
        self.root.bind('<F5>', lambda e: self.run_scan())
        self.root.bind('<Control-o>', lambda e: self.add_paths_dialog())
        self.root.bind('<Control-s>', lambda e: self.save_scan())
        self.root.bind('<Control-l>', lambda e: self.load_scan())
        self.root.bind('<Control-h>', lambda e: self.share_hash())
        self.root.bind('<Escape>', lambda e: self.root.quit())
        self.root.bind('<Control-c>', lambda e: self.copy_share_hash())
        
    def load_initial_paths(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('paths', nargs='*')
        args = parser.parse_args(sys.argv[1:])
        for path in args.paths:
            self.paths.append(Path(path))
        self.update_file_list()
        
    def new_scan(self):
        self.paths.clear()
        self.scan_results.clear()
        self.file_listbox.delete(0, tk.END)
        self.details_text.delete(1.0, tk.END)
        self.status_label.config(text="New scan started")
        
    def add_paths_dialog(self):
        paths = filedialog.askopenfilenames(title="Select files/folders")
        for path in paths:
            self.paths.append(Path(path))
        self.update_file_list()
        
    def update_file_list(self):
        self.file_listbox.delete(0, tk.END)
        for path in self.paths:
            self.file_listbox.insert(tk.END, str(path))
            
    def run_scan(self):
        if not self.paths:
            messagebox.showwarning("No paths", "Add files/folders first")
            return
            
        self.progress.start()
        self.status_label.config(text="Scanning...")
        self.root.update()
        
        def scan_thread():
            self.scan_results.clear()
            for path in self.paths:
                try:
                    result = self.audit_path(path)
                    self.scan_results.append(result)
                except Exception as e:
                    self.scan_results.append({
                        'path': str(path),
                        'issues': [f"Error: {str(e)}"],
                        'score': 0
                    })
            
            self.root.after(0, self.scan_complete)
            
        threading.Thread(target=scan_thread, daemon=True).start()
        
    def audit_path(self, path):
        issues = []
        score = 100
        
        try:
            stat = path.stat()
            
            # File permissions
            if path.is_file():
                mode = oct(stat.st_mode)[-3:]
                if mode != '644':
                    issues.append(f"File permission should be 644 (is {mode})")
                    score -= 20
                if not os.access(path, os.R_OK):
                    issues.append("File not readable")
                    score -= 30
            else:
                mode = oct(stat.st_mode)[-3:]
                if mode != '755':
                    issues.append(f"Dir permission should be 755 (is {mode})")
                    score -= 15
                    
            # Naming conventions
            name = path.name
            if ' ' in name:
                issues.append("Filename contains spaces")
                score -= 10
            if name != name.lower():
                issues.append("Filename contains uppercase")
                score -= 10
            if path.suffix not in ['.jpg', '.png', '.gif', '.pdf', '.html', '.txt']:
                issues.append("Non-standard extension")
                score -= 5
                
            # Size check
            if path.is_file() and stat.st_size > 50 * 1024 * 1024:
                issues.append(f"File too large: {stat.st_size/1024/1024:.1f}MB")
                score -= 25
                
            # Hash for duplicates
            if path.is_file():
                h = hashlib.sha256()
                with open(path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        h.update(chunk)
                issues.append(f"SHA256: {h.hexdigest()[:16]}...")
                
        except Exception as e:
            issues.append(f"Access error: {str(e)}")
            score = 0
            
        score = max(0, score)
        return {'path': str(path), 'issues': issues, 'score': score}
        
    def scan_complete(self):
        self.progress.stop()
        self.file_listbox.delete(0, tk.END)
        for result in self.scan_results:
            score_color = "green" if result['score'] >= 80 else "orange" if result['score'] >= 50 else "red"
            display = f"{result['path']} [{result['score']}]"
            self.file_listbox.insert(tk.END, display)
            self.file_listbox.itemconfig(tk.END, {'fg': score_color})
            
        avg_score = sum(r['score'] for r in self.scan_results) / len(self.scan_results) if self.scan_results else 0
        self.status_label.config(text=f"Scan complete: {len(self.scan_results)} items, avg score {avg_score:.1f}")
        self.auto_save()
        
    def show_details(self, event=None):
        selection = self.file_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        result = self.scan_results[idx]
        
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, f"Path: {result['path']}\n")
        self.details_text.insert(tk.END, f"Score: {result['score']}/100\n\n")
        self.details_text.insert(tk.END, "Issues:\n")
        for issue in result['issues']:
            self.details_text.insert(tk.END, f"• {issue}\n")
            
    def save_scan(self):
        self.auto_save()
        messagebox.showinfo("Saved", "Scan saved to scan_data.json")
        
    def auto_save(self):
        data = {
            'paths': [str(p) for p in self.paths],
            'results': self.scan_results
        }
        try:
            with open(self.scan_data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
            
    def load_scan(self):
        try:
            with open(self.scan_data_file, 'r') as f:
                data = json.load(f)
            self.paths = [Path(p) for p in data.get('paths', [])]
            self.scan_results = data.get('results', [])
            self.update_file_list()
            self.scan_complete()
            messagebox.showinfo("Loaded", "Scan loaded successfully")
        except Exception as e:
            messagebox.showerror("Load failed", str(e))
            
    def share_hash(self):
        if not self.scan_results:
            messagebox.showwarning("No data", "Run a scan first")
            return
            
        summary = {
            'count': len(self.scan_results),
            'avg_score': sum(r['score'] for r in self.scan_results) / len(self.scan_results),
            'issues': len([i for r in self.scan_results for i in r['issues'] if 'Error' not in i])
        }
        
        hash_str = base64.urlsafe_b64encode(json.dumps(summary).encode()).decode()[:32]
        self.root.clipboard_clear()
        self.root.clipboard_append(hash_str)
        self.status_label.config(text=f"Share hash copied: {hash_str}")
        messagebox.showinfo("Share ready", f"Hash copied to clipboard:\n{hash_str}")
        
    def copy_share_hash(self):
        self.share_hash()

if __name__ == "__main__":
    root = tk.Tk()
    app = AccessibilityAuditor(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.auto_save(), root.quit()))
    root.mainloop()