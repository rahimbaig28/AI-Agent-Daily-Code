# Auto-generated via Perplexity on 2025-12-01T13:32:53.390934Z
#!/usr/bin/env python3
"""
Accessibility Helper CLI
A keyboard-first terminal application for accessibility actions.
Features: theme toggle, print view, shortcuts, system info, and help.
"""

import os
import sys
import json
import platform
import shutil
from enum import Enum
from typing import Dict, Any, List, Tuple

# Configuration file path
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".accessibility_helper.json")

# ANSI color codes
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "underline": "\033[4m",
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "bg_black": "\033[40m",
    "bg_red": "\033[41m",
    "bg_green": "\033[42m",
    "bg_yellow": "\033[43m",
    "bg_blue": "\033[44m",
    "bg_magenta": "\033[45m",
    "bg_cyan": "\033[46m",
    "bg_white": "\033[47m",
}

# Theme modes
class ThemeMode(Enum):
    AUTO = "auto"
    DARK = "dark"
    LIGHT = "light"

# App sections
class Section(Enum):
    MAIN = "main"
    THEME = "theme"
    PRINT = "print"
    SHORTCUTS = "shortcuts"
    SYSTEM = "system"
    HELP = "help"

# Default configuration
DEFAULT_CONFIG = {
    "theme": ThemeMode.AUTO.value,
    "last_section": Section.MAIN.value,
}

# Load configuration
def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Validate and set defaults
                if "theme" not in data:
                    data["theme"] = DEFAULT_CONFIG["theme"]
                if "last_section" not in data:
                    data["last_section"] = DEFAULT_CONFIG["last_section"]
                return data
        except (json.JSONDecodeError, PermissionError):
            pass
    return DEFAULT_CONFIG.copy()

# Save configuration
def save_config(config: Dict[str, Any]) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except PermissionError:
        print("Warning: Could not save configuration (permission denied).")

# Detect system theme preference
def detect_system_theme() -> ThemeMode:
    # Heuristic: check environment variables
    if "DARKMODE" in os.environ and os.environ["DARKMODE"].lower() == "1":
        return ThemeMode.DARK
    if "LIGHTMODE" in os.environ and os.environ["LIGHTMODE"].lower() == "1":
        return ThemeMode.LIGHT
    # Check for common dark mode indicators
    if "COLORFGBG" in os.environ:
        fg, bg = os.environ["COLORFGBG"].split(";")
        if int(bg) > 7:
            return ThemeMode.DARK
    # Default to light for terminals
    return ThemeMode.LIGHT

# Get current theme
def get_current_theme(config: Dict[str, Any]) -> ThemeMode:
    if config["theme"] == ThemeMode.AUTO.value:
        return detect_system_theme()
    return ThemeMode(config["theme"])

# Get color for theme
def get_color(config: Dict[str, Any], color_name: str) -> str:
    theme = get_current_theme(config)
    if theme == ThemeMode.DARK:
        # Dark theme: use lighter colors
        color_map = {
            "title": COLORS["yellow"],
            "option": COLORS["cyan"],
            "selected": COLORS["white"] + COLORS["bg_blue"],
            "help": COLORS["green"],
            "info": COLORS["magenta"],
            "reset": COLORS["reset"],
        }
    else:
        # Light theme: use darker colors
        color_map = {
            "title": COLORS["blue"],
            "option": COLORS["magenta"],
            "selected": COLORS["black"] + COLORS["bg_yellow"],
            "help": COLORS["green"],
            "info": COLORS["red"],
            "reset": COLORS["reset"],
        }
    return color_map.get(color_name, COLORS["reset"])

# Clear screen
def clear_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')

# Print accessible title
def print_title(config: Dict[str, Any], text: str) -> None:
    color = get_color(config, "title")
    print(f"{color}{COLORS['bold']}{text}{COLORS['reset']}\n")

# Print accessible option
def print_option(config: Dict[str, Any], text: str, selected: bool = False) -> None:
    if selected:
        color = get_color(config, "selected")
        print(f" > {color}{text}{COLORS['reset']}")
    else:
        color = get_color(config, "option")
        print(f"   {color}{text}{COLORS['reset']}")

# Print help text
def print_help(config: Dict[str, Any], text: str) -> None:
    color = get_color(config, "help")
    print(f"{color}{text}{COLORS['reset']}")

# Print info text
def print_info(config: Dict[str, Any], text: str) -> None:
    color = get_color(config, "info")
    print(f"{color}{text}{COLORS['reset']}")

# Print plain text (no colors)
def print_plain(text: str) -> None:
    print(text)

# Get terminal size
def get_terminal_size() -> Tuple[int, int]:
    try:
        size = shutil.get_terminal_size()
        return size.columns, size.lines
    except:
        return 80, 24

# Main menu options
MAIN_OPTIONS = [
    "Toggle Dark/Light Theme",
    "Print-Friendly View",
    "Keyboard Shortcuts",
    "System Information",
    "Help",
    "Exit",
]

# Theme options
THEME_OPTIONS = [
    "Auto (detect system)",
    "Dark Theme",
    "Light Theme",
    "Back to Main Menu",
]

# Print-friendly view
def show_print_friendly() -> None:
    clear_screen()
    print_plain("Accessibility Helper CLI - Print-Friendly View")
    print_plain("")
    print_plain("Features:")
    print_plain("  - Toggle Dark/Light Theme: Switch between themes for better visibility.")
    print_plain("  - Print-Friendly View: This view uses plain text for printing or screen readers.")
    print_plain("  - Keyboard Shortcuts: List of accessible shortcuts for this app.")
    print_plain("  - System Information: Show basic system details.")
    print_plain("  - Help: Instructions for keyboard navigation and accessibility features.")
    print_plain("")
    print_plain("Keyboard Navigation:")
    print_plain("  - Use arrow keys to move between options.")
    print_plain("  - Press Enter to select an option.")
    print_plain("  - Press Escape or Q to exit.")
    print_plain("")
    print_plain("Press Enter to return to main menu.")

# Keyboard shortcuts
def show_shortcuts() -> None:
    clear_screen()
    print_plain("Keyboard Shortcuts")
    print_plain("")
    print_plain("Navigation:")
    print_plain("  - Up/Down Arrow: Move between options.")
    print_plain("  - Enter: Select current option.")
    print_plain("  - Escape or Q: Exit the application.")
    print_plain("")
    print_plain("Theme:")
    print_plain("  - T: Toggle theme (dark/light).")
    print_plain("")
    print_plain("Other:")
    print_plain("  - H: Show help.")
    print_plain("  - P: Print-friendly view.")
    print_plain("  - S: System information.")
    print_plain("  - K: Keyboard shortcuts.")
    print_plain("")
    print_plain("Press Enter to return to main menu.")

# System info
def show_system_info() -> None:
    clear_screen()
    print_plain("System Information")
    print_plain("")
    print_plain(f"Operating System: {platform.system()} {platform.release()}")
    print_plain(f"Python Version: {platform.python_version()}")
    print_plain(f"Terminal Size: {get_terminal_size()[0]} x {get_terminal_size()[1]}")
    print_plain(f"Platform: {platform.platform()}")
    print_plain(f"Machine: {platform.machine()}")
    print_plain(f"Processor: {platform.processor()}")
    print_plain("")
    print_plain("Press Enter to return to main menu.")

# Help screen
def show_help(config: Dict[str, Any]) -> None:
    clear_screen()
    print_title(config, "Help")
    print_help(config, "Keyboard Navigation:")
    print_help(config, "  - Use arrow keys to move between options.")
    print_help(config, "  - Press Enter to select an option.")
    print_help(config, "  - Press Escape or Q to exit.")
    print_help(config, "")
    print_help(config, "Accessibility Features:")
    print_help(config, "  - This app is designed for keyboard-first navigation.")
    print_help(config, "  - All output is accessible and screen reader friendly.")
    print_help(config, "  - Themes can be toggled for better visibility.")
    print_help(config, "  - Print-friendly view removes colors and formatting.")
    print_help(config, "")
    print_help(config, "Shortcuts:")
    print_help(config, "  - T: Toggle theme (dark/light).")
    print_help(config, "  - H: Show help.")
    print_help(config, "  - P: Print-friendly view.")
    print_help(config, "  - S: System information.")
    print_help(config, "  - K: Keyboard shortcuts.")
    print_help(config, "")
    print_help(config, "Press Enter to return to main menu.")

# Main menu
def show_main_menu(config: Dict[str, Any], selected: int) -> None:
    clear_screen()
    print_title(config, "Accessibility Helper CLI")
    for i, option in enumerate(MAIN_OPTIONS):
        print_option(config, option, i == selected)
    print_help(config, "\nUse arrow keys to navigate, Enter to select, Q to quit.")

# Theme menu
def show_theme_menu(config: Dict[str, Any], selected: int) -> None:
    clear_screen()
    print_title(config, "Theme Settings")
    for i, option in enumerate(THEME_OPTIONS):
        print_option(config, option, i == selected)
    print_help(config, "\nUse arrow keys to navigate, Enter to select, Escape to go back.")

# Handle main menu selection
def handle_main_selection(config: Dict[str, Any], selection: int) -> Section:
    if selection == 0:  # Toggle theme
        return Section.THEME
    elif selection == 1:  # Print-friendly view
        show_print_friendly()
        input()
        return Section.MAIN
    elif selection == 2:  # Keyboard shortcuts
        show_shortcuts()
        input()
        return Section.MAIN
    elif selection == 3:  # System info
        show_system_info()
        input()
        return Section.MAIN
    elif selection == 4:  # Help
        show_help(config)
        input()
        return Section.MAIN
    elif selection == 5:  # Exit
        return Section.MAIN  # Will exit in main loop
    return Section.MAIN

# Handle theme menu selection
def handle_theme_selection(config: Dict[str, Any], selection: int) -> Section:
    if selection == 0:  # Auto
        config["theme"] = ThemeMode.AUTO.value
    elif selection == 1:  # Dark
        config["theme"] = ThemeMode.DARK.value
    elif selection == 2:  # Light
        config["theme"] = ThemeMode.LIGHT.value
    elif selection == 3:  # Back
        return Section.MAIN
    save_config(config)
    return Section.MAIN

# Read single key (cross-platform)
def read_key() -> str:
    if os.name == 'nt':  # Windows
        import msvcrt
        return msvcrt.getch().decode('utf-8', errors='ignore')
    else:  # Unix/Linux/Mac
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

# Main application loop
def main() -> None:
    config = load_config()
    section = Section(config.get("last_section", Section.MAIN.value))
    main_selected = 0
    theme_selected = 0

    # Set terminal to raw mode for single key input
    if os.name != 'nt':
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setraw(fd)

    try:
        while True:
            if section == Section.MAIN:
                show_main_menu(config, main_selected)
                key = read_key().lower()
                if key == '\x1b':  # Escape
                    break
                elif key in ['q', '\x03']:  # Q or Ctrl+C
                    break
                elif key == '\x08' or key == '\x7f':  # Backspace
                    pass
                elif key == '\n' or key == '\r':  # Enter
                    section = handle_main_selection(config, main_selected)
                    if section == Section.MAIN and main_selected == 5:  # Exit
                        break
                    config["last_section"] = section.value
                    save_config(config)
                elif key == 't':  # Toggle theme
                    theme = get_current_theme(config)
                    if theme == ThemeMode.DARK:
                        config["theme"] = ThemeMode.LIGHT.value
                    elif theme == ThemeMode.LIGHT:
                        config["theme"] = ThemeMode.AUTO.value
                    else:
                        config["theme"] = ThemeMode.DARK.value
                    save_config(config)
                elif key == 'h':  # Help
                    show_help(config)
                    input()
                elif key == 'p':  # Print-friendly
                    show_print_friendly()
                    input()
                elif key == 's':  # System info
                    show_system_info()
                    input()
                elif key == 'k':  # Shortcuts
                    show_shortcuts()
                    input()
                elif key == '\x1b[A' or key == 'k':  # Up arrow
                    main_selected = (main_selected - 1) % len(MAIN_OPTIONS)
                elif key == '\x1b[B' or key == 'j':  # Down arrow
                    main_selected = (main_selected + 1) % len(MAIN_OPTIONS)
                elif key.isdigit():
                    num = int(key)
                    if 1 <= num <= len(MAIN_OPTIONS):
                        main_selected = num - 1
                        section = handle_main_selection(config, main_selected)
                        if section == Section.MAIN and main_selected == 5:
                            break
                        config["last_section"] = section.value
                        save_config(config)

            elif section == Section.THEME:
                show_theme_menu(config, theme_selected)
                key = read_key().lower()
                if key == '\x1b':  # Escape
                    section = Section.MAIN
                elif key in ['q']:
                    break
                elif key == '\n' or key == '\r':  # Enter
                    section = handle_theme_selection(config, theme_selected)
                    config["last_section"] = section.value
                    save_config(config)
                elif key == '\x1b[A' or key == 'k':  # Up arrow
                    theme_selected = (theme_selected - 1) % len(THEME_OPTIONS)
                elif key == '\x1b[B' or key == 'j':  # Down arrow
                    theme_selected = (theme_selected + 1) % len(THEME_OPTIONS)

    except KeyboardInterrupt:
        pass
    finally:
        # Restore terminal settings
        if os.name != 'nt':
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        clear_screen()
        print("Goodbye!")

if __name__ == "__main__":
    main()