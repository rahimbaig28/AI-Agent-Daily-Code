# Auto-generated via Perplexity on 2026-01-18T18:42:45.813152Z
#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import hashlib
import urllib.request
import urllib.parse
import tempfile
import shutil
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

# ANSI color codes
COLORS = {
    'RESET': '\033[0m',
    'RED': '\033[91m',
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'MAGENTA': '\033[95m',
    'CYAN': '\033[96m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m'
}

HISTORY_FILE = Path.home() / '.audit_history.json'
SHARE_CODES = {}

def load_history() -> List[Dict]:
    """Load audit history from persistent storage."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return []

def save_history(history: List[Dict]):
    """Save audit history with backup."""
    backup = HISTORY_FILE.with_suffix('.backup')
    try:
        shutil.copy2(HISTORY_FILE, backup)
    except:
        pass
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def parse_color(color_str: str) -> Tuple[float, float, float]:
    """Parse hex or rgb color to RGB tuple (0-1)."""
    color_str = color_str.lstrip('#').lower()
    if len(color_str) == 6:
        return tuple(int(color_str[i:i+2], 16)/255 for i in (0,2,4))
    elif len(color_str) == 3:
        return tuple(int(c*2, 16)/255 for c in color_str)
    return 0, 0, 0

def relative_luminance(r: float, g: float, b: float) -> float:
    """Calculate relative luminance per WCAG."""
    def srgb_to_linear(c: float) -> float:
        return c/12.92 if c <= 0.03928 else ((c+0.055)/1.055)**2.4
    return 0.2126 * srgb_to_linear(r) + 0.7152 * srgb_to_linear(g) + 0.0722 * srgb_to_linear(b)

def contrast_ratio(color1: Tuple[float,float,float], color2: Tuple[float,float,float]) -> float:
    """Calculate contrast ratio between two colors."""
    l1, l2 = relative_luminance(*color1), relative_luminance(*color2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

def audit_html(content: str, filepath: str = "unknown") -> Dict[str, Any]:
    """Core HTML accessibility audit."""
    issues = []
    total_checks = 0
    passed_checks = 0
    
    # 1. Missing alt text on images
    imgs = re.findall(r'<img[^>]*>', content, re.IGNORECASE)
    total_checks += len(imgs)
    for img in imgs:
        if not re.search(r'\balt\s*=\s*["\'][^"\']*["\']', img, re.IGNORECASE):
            issues.append({"type": "missing_alt", "fix": "Add descriptive alt attribute to img"})
        else:
            passed_checks += 1
    
    # 2. Heading structure (h1-h6 sequential)
    headings = re.findall(r'<h([1-6])[^>]*>([^<]+)</h[1-6]>', content, re.IGNORECASE)
    total_checks += len(headings)
    prev_level = 0
    for level, text in headings:
        level = int(level)
        if level < prev_level - 1:
            issues.append({"type": "heading_skip", "fix": f"Heading level {level} skips from {prev_level}"})
        elif abs(level - prev_level) <= 1:
            passed_checks += 1
        prev_level = level
    
    # 3. Color contrast (basic inline styles)
    styles = re.findall(r'style\s*=\s*["\']([^"\']*)["\']', content, re.IGNORECASE)
    total_checks += len(styles)
    for style in styles:
        color_pairs = re.findall(r'(color|background-color)\s*:\s*([^;,\'"!]+)', style, re.IGNORECASE)
        for prop1, val1 in color_pairs:
            for prop2, val2 in color_pairs:
                if prop1 != prop2:
                    try:
                        c1 = parse_color(val1.strip())
                        c2 = parse_color(val2.strip())
                        if contrast_ratio(c1, c2) < 4.5:
                            issues.append({"type": "low_contrast", "fix": f"Contrast {contrast_ratio(c1,c2):.1f}:1 < 4.5:1 between {val1} and {val2}"})
                        else:
                            passed_checks += 1
                    except:
                        pass
    
    # 4. Empty links
    links = re.findall(r'<a[^>]*href\s*=[^>]*>([^<]*)</a>', content, re.IGNORECASE)
    total_checks += len(links)
    for link_text in links:
        if not link_text or link_text.isspace():
            issues.append({"type": "empty_link", "fix": "Add descriptive link text"})
        else:
            passed_checks += 1
    
    # 5. Form labels
    inputs = re.findall(r'<input[^>]*>', content, re.IGNORECASE)
    total_checks += len(inputs)
    labeled_inputs = re.findall(r'<label[^>]*for\s*=\s*["\']([^"\']+)["\'][^>]*>.*?</label>', content, re.IGNORECASE | re.DOTALL)
    labeled = set(labeled_inputs)
    for inp in inputs:
        inp_id = re.search(r'id\s*=\s*["\']([^"\']+)["\']', inp)
        if inp_id and inp_id.group(1) not in labeled:
            issues.append({"type": "unlabeled_input", "fix": "Add <label for='input-id'>"})
        elif inp_id:
            passed_checks += 1
    
    score = max(0, min(100, int((passed_checks / max(total_checks, 1)) * 100)))
    
    return {
        "filepath": filepath,
        "score": score,
        "issues_count": len(issues),
        "total_checks": total_checks,
        "issues": issues[:10],  # Top 10 issues
        "timestamp": datetime.now().isoformat()
    }

def fetch_url(url: str, timeout: int = 10) -> str:
    """Fetch URL content with timeout."""
    req = urllib.request.Request(url, headers={'User-Agent': 'AccessibilityAuditPro/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        raise Exception(f"Failed to fetch {url}: {e}")

def process_file(filepath: str) -> Dict[str, Any]:
    """Process single file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    return audit_html(content, str(path))

def process_directory(directory: str) -> List[Dict[str, Any]]:
    """Process all HTML files in directory."""
    path = Path(directory)
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    results = []
    for file in path.rglob("*.html"):
        try:
            results.append(process_file(str(file)))
        except Exception as e:
            print(f"{COLORS['YELLOW']}Skipped {file}: {e}{COLORS['RESET']}", file=sys.stderr)
    return results

def generate_report_hash(results: List[Dict]) -> str:
    """Generate unique hash for report."""
    data = json.dumps(results, sort_keys=True)
    return hashlib.md5(data.encode()).hexdigest()[:8]

def print_table(results: List[Dict]):
    """Print color-coded console table."""
    if not results:
        print(f"{COLORS['YELLOW']}No files audited{COLORS['RESET']}")
        return
    
    print(f"{COLORS['BOLD']}{'File':<40} {'Score':>5} {'Issues':>7} {'Top Fixes'}{COLORS['RESET']}")
    print("-" * 100)
    
    for result in results:
        score_color = COLORS['GREEN'] if result['score'] >= 80 else COLORS['YELLOW'] if result['score'] >= 60 else COLORS['RED']
        fixes = [issue['fix'][:30] + '...' for issue in result['issues'][:3]]
        fixes_str = '; '.join(fixes) if fixes else 'None'
        
        print(f"{result['filepath']:<40} "
              f"{score_color}{result['score']:>3}%{COLORS['RESET']:>2} "
              f"{result['issues_count']:>7} "
              f"{fixes_str}")

def interactive_mode():
    """Interactive file watcher mode."""
    print(f"{COLORS['CYAN']}{COLORS['BOLD']}Accessibility Audit Pro - Interactive Mode{COLORS['RESET']}")
    print("Commands: 'file <path>', 'dir <path>', 'url <url>', 'history', 'quit'")
    print("Keyboard shortcuts: Ctrl+C to quit")
    
    history = load_history()
    while True:
        try:
            cmd = input("\n> ").strip()
            if cmd.lower() == 'quit':
                break
            elif cmd.startswith('history'):
                print_table([h for h in history[-10:]])
                continue
            elif cmd.startswith('file '):
                try:
                    result = process_file(cmd[5:])
                    print_table([result])
                    history.append(result)
                except Exception as e:
                    print(f"{COLORS['RED']}Error: {e}{COLORS['RESET']}")
            elif cmd.startswith('dir '):
                try:
                    results = process_directory(cmd[4:])
                    print_table(results)
                    history.extend(results)
                except Exception as e:
                    print(f"{COLORS['RED']}Error: {e}{COLORS['RESET']}")
            elif cmd.startswith('url '):
                try:
                    content = fetch_url(cmd[4:])
                    result = audit_html(content, cmd[4:])
                    print_table([result])
                    history.append(result)
                except Exception as e:
                    print(f"{COLORS['RED']}Error: {e}{COLORS['RESET']}")
            else:
                print("Unknown command")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
    
    save_history(history)

def main():
    parser = argparse.ArgumentParser(description="Accessibility Audit Pro - CLI")
    parser.add_argument('--file', help="Audit single HTML file")
    parser.add_argument('--dir', help="Audit HTML files in directory")
    parser.add_argument('--url', help="Audit remote URL")
    parser.add_argument('--interactive', action='store_true', help="Interactive mode")
    parser.add_argument('--share', action='store_true', help="Generate shareable hash")
    parser.add_argument('--load', help="Load audit by hash ID")
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
        return
    
    if args.load and args.load in SHARE_CODES:
        with open(f"audit_{args.load}.json", 'r') as f:
            results = json.load(f)
        print_table(results)
        return
    
    results = []
    
    if args.file:
        results.append(process_file(args.file))
    elif args.dir:
        results = process_directory(args.dir)
    elif args.url:
        content = fetch_url(args.url)
        results.append(audit_html(content, args.url))
    else:
        print("Error: Specify --file, --dir, --url, or --interactive")
        parser.print_help()
        return
    
    # Generate report
    report_id = generate_report_hash(results)
    report_file = f"audit_{report_id}.json"
    
    report = {
        "audit_id": report_id,
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "summary": {
            "total_files": len(results),
            "avg_score": sum(r['score'] for r in results) / max(len(results), 1),
            "total_issues": sum(r['issues_count'] for r in results)
        }
    }
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print_table(results)
    print(f"\n{COLORS['GREEN']}✓ Report saved: {report_file}{COLORS['RESET']}")
    
    if args.share:
        print(f"{COLORS['CYAN']}Share command: python audit_pro.py --load {report_id}{COLORS['RESET']}")
        SHARE_CODES[report_id] = report
    
    # Update history
    history = load_history()
    history.extend([r for r in results if len(history) < 100])  # Keep last 100
    save_history(history)

if __name__ == "__main__":
    main()