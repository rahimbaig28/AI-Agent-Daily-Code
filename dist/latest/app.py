# Auto-generated via Perplexity on 2026-01-10T04:33:20.188925Z
#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
import random
from datetime import datetime, timedelta

# Allowed stdlib: json, sqlite3, random, datetime, argparse (sqlite3 unused but allowed)
import sqlite3  # noqa: F401  # kept for requirement consistency

APP_NAME = "vocab_srs"
CONFIG_FILE = os.path.join(os.path.expanduser("~"), f".{APP_NAME}_config.json")
DEFAULT_STUDY_DIR = os.path.join(os.path.expanduser("~"), f".{APP_NAME}_decks")


def load_config():
    cfg = {
        "study_dir": DEFAULT_STUDY_DIR,
        "theme": "auto",  # auto, light, dark
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                cfg.update(data)
        except Exception:
            pass
    return cfg


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def ensure_study_dir(study_dir):
    os.makedirs(study_dir, exist_ok=True)


def deck_path(study_dir, name):
    return os.path.join(study_dir, f"{name}.json")


def now_iso():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def parse_iso(dt_str):
    try:
        if dt_str.endswith("Z"):
            dt_str = dt_str[:-1]
        return datetime.fromisoformat(dt_str)
    except Exception:
        return None


def colored(text, color_code, theme):
    if theme == "none":
        return text
    if theme == "auto":
        # simple auto-detect: if TERM supports colors by convention
        term = os.environ.get("TERM", "")
        if not sys.stdout.isatty() or term in ("dumb", ""):
            return text
    return f"\033[{color_code}m{text}\033[0m"


def apply_theme(config, theme_arg):
    theme = config.get("theme", "auto")
    if theme_arg:
        if theme_arg in ("auto", "light", "dark", "none"):
            theme = theme_arg
            config["theme"] = theme
            save_config(config)
        else:
            print("Invalid theme. Use: auto, light, dark, none", file=sys.stderr)
    # map logical theme to color usage; for simplicity we only toggle on/off
    if theme == "none":
        return "none"
    return "auto"


def init_deck(name):
    ts = now_iso()
    return {
        "name": name,
        "created_at": ts,
        "last_reviewed_at": None,
        "total_time_seconds": 0,
        "review_sessions": 0,
        "cards": [],
    }


def validate_card(card):
    if not isinstance(card, dict):
        return False
    if "question" not in card or "answer" not in card:
        return False
    # metadata defaults
    card.setdefault("created_at", now_iso())
    card.setdefault("last_reviewed_at", None)
    card.setdefault("review_count", 0)
    card.setdefault("confidence_history", [])
    card.setdefault("avg_confidence", None)
    card.setdefault("easiness", 2.5)
    card.setdefault("interval_days", 0)
    card.setdefault("repetitions", 0)
    card.setdefault("due_at", now_iso())
    return True


def validate_deck(obj):
    if not isinstance(obj, dict):
        return False
    if "name" not in obj or "cards" not in obj:
        return False
    obj.setdefault("created_at", now_iso())
    obj.setdefault("last_reviewed_at", None)
    obj.setdefault("total_time_seconds", 0)
    obj.setdefault("review_sessions", 0)
    if not isinstance(obj["cards"], list):
        return False
    for c in obj["cards"]:
        if not validate_card(c):
            return False
    return True


def load_deck(path):
    if not os.path.exists(path):
        print(f"Deck file not found: {path}", file=sys.stderr)
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Deck JSON is corrupt: {path}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error reading deck: {e}", file=sys.stderr)
        return None
    if not validate_deck(data):
        print(f"Error: Deck file invalid format: {path}", file=sys.stderr)
        return None
    return data


def save_deck(path, deck):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(deck, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving deck: {e}", file=sys.stderr)


def list_decks_cmd(args, config, theme):
    study_dir = config["study_dir"]
    ensure_study_dir(study_dir)
    files = [f for f in os.listdir(study_dir) if f.endswith(".json")]
    if not files:
        print("No decks found.")
        return
    print("Available decks:")
    for f in sorted(files):
        deck_name = f[:-5]
        path = os.path.join(study_dir, f)
        deck = load_deck(path)
        if deck is None:
            continue
        count = len(deck["cards"])
        print(f" - {deck_name} ({count} cards)")


def add_deck_cmd(args, config, theme):
    study_dir = config["study_dir"]
    ensure_study_dir(study_dir)
    name = args.name
    path = deck_path(study_dir, name)
    if os.path.exists(path) and not args.force:
        print(f"Deck '{name}' already exists. Use --force to overwrite.", file=sys.stderr)
        return
    deck = init_deck(name)
    save_deck(path, deck)
    print(f"Deck '{name}' created at {path}")


def add_card_cmd(args, config, theme):
    study_dir = config["study_dir"]
    ensure_study_dir(study_dir)
    path = deck_path(study_dir, args.deck)
    deck = load_deck(path)
    if deck is None:
        return
    q = args.question
    a = args.answer
    if q is None:
        print("Enter question (end with empty line):")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line == "":
                break
            lines.append(line)
        q = "\n".join(lines).strip()
    if a is None:
        print("Enter answer (end with empty line):")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line == "":
                break
            lines.append(line)
        a = "\n".join(lines).strip()
    if not q or not a:
        print("Question and answer cannot be empty.", file=sys.stderr)
        return
    card = {
        "question": q,
        "answer": a,
    }
    if not validate_card(card):
        print("Internal error: card validation failed.", file=sys.stderr)
        return
    deck["cards"].append(card)
    save_deck(path, deck)
    print(f"Added card to deck '{deck['name']}' (total {len(deck['cards'])}).")


def delete_deck_cmd(args, config, theme):
    study_dir = config["study_dir"]
    ensure_study_dir(study_dir)
    path = deck_path(study_dir, args.deck)
    if not os.path.exists(path):
        print(f"Deck '{args.deck}' not found.", file=sys.stderr)
        return
    if not args.yes:
        ans = input(f"Delete deck '{args.deck}'? This cannot be undone. [y/N]: ").strip().lower()
        if ans != "y":
            print("Aborted.")
            return
    try:
        os.remove(path)
        print(f"Deck '{args.deck}' deleted.")
    except Exception as e:
        print(f"Error deleting deck: {e}", file=sys.stderr)


def export_deck_cmd(args, config, theme):
    study_dir = config["study_dir"]
    ensure_study_dir(study_dir)
    path = deck_path(study_dir, args.deck)
    deck = load_deck(path)
    if deck is None:
        return
    out = args.output or f"{deck['name']}_export.json"
    try:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(deck, f, indent=2, ensure_ascii=False)
        print(f"Exported deck '{deck['name']}' to {out}")
    except Exception as e:
        print(f"Error exporting deck: {e}", file=sys.stderr)


def import_deck_cmd(args, config, theme):
    study_dir = config["study_dir"]
    ensure_study_dir(study_dir)
    src = args.file
    if not os.path.exists(src):
        print(f"Import file not found: {src}", file=sys.stderr)
        return
    try:
        with open(src, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Import JSON is corrupt: {src}", file=sys.stderr)
        return
    except Exception as e:
        print(f"Error reading import file: {e}", file=sys.stderr)
        return
    if not validate_deck(data):
        print("Error: Imported file is not a valid deck format.", file=sys.stderr)
        return
    name = args.name or data.get("name") or "imported_deck"
    data["name"] = name
    path = deck_path(study_dir, name)
    if os.path.exists(path) and not args.force:
        print(f"Deck '{name}' already exists. Use --force to overwrite.", file=sys.stderr)
        return
    save_deck(path, data)
    print(f"Imported deck as '{name}' with {len(data['cards'])} cards.")


def print_deck_cmd(args, config, theme):
    study_dir = config["study_dir"]
    ensure_study_dir(study_dir)
    path = deck_path(study_dir, args.deck)
    deck = load_deck(path)
    if deck is None:
        return
    print(f"# Deck: {deck['name']}")
    print()
    for idx, card in enumerate(deck["cards"], 1):
        print(f"Card {idx}")
        print("Q:")
        print(card["question"])
        print()
        print("A:")
        print(card["answer"])
        print("-" * 40)


def sm2_update(card, quality):
    """
    Simple SM-2-like update.
    quality: 0-5, we'll map 1-5 input to 0-5.
    """
    q = max(0, min(5, quality))
    easiness = card.get("easiness", 2.5)
    interval = card.get("interval_days", 0)
    repetitions = card.get("repetitions", 0)

    if q < 3:
        repetitions = 0
        interval = 1
    else:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = int(round(interval * easiness))
        repetitions += 1

    easiness = easiness + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    if easiness < 1.3:
        easiness = 1.3

    card["easiness"] = easiness
    card["interval_days"] = interval
    card["repetitions"] = repetitions

    next_due = datetime.utcnow() + timedelta(days=interval)
    card["due_at"] = next_due.isoformat(timespec="seconds") + "Z"


def card_priority(card):
    """Lower score means higher priority."""
    due_at = parse_iso(card.get("due_at") or now_iso())
    if due_at is None:
        due_at = datetime.utcnow()
    days_overdue = (datetime.utcnow() - due_at).total_seconds() / 86400.0
    if days_overdue < 0:
        days_overdue = 0
    avg_conf = card.get("avg_confidence")
    if avg_conf is None:
        avg_conf = 0
    # score: base on -days_overdue (more overdue => lower score), and (5-avg_conf)
    score = -days_overdue + (5 - avg_conf) * 0.2
    return score


def choose_cards_for_study(deck, limit):
    cards = deck["cards"]
    if not cards:
        return []
    sorted_cards = sorted(cards, key=card_priority)
    if limit is None or limit <= 0 or limit > len(sorted_cards):
        return sorted_cards
    return sorted_cards[:limit]


def study_cmd(args, config, theme):
    study_dir = config["study_dir"]
    ensure_study_dir(study_dir)
    path = deck_path(study_dir, args.deck)
    deck = load_deck(path)
    if deck is None:
        return
    if not deck["cards"]:
        print("Deck has no cards.")
        return

    session_start = time.time()
    to_study = choose_cards_for_study(deck, args.limit)
    if not to_study:
        print("No cards to study.")
        return

    print(colored(f"Studying deck '{deck['name']}' ({len(to_study)} cards)...", "36", theme))
    print("Controls: [Enter]=reveal, [1-5]=rate, [n]=next, [s]=skip, [q]=quit")

    for idx, card in enumerate(to_study, 1):
        print()
        print(colored(f"Card {idx}/{len(to_study)}", "33", theme))
        print(colored("Q:", "32", theme))
        print(card["question"])
        revealed = False
        while True:
            try:
                cmd = input("> ").strip()
            except EOFError:
                cmd = "q"
            if cmd == "" and not revealed:
                print(colored("A:", "31", theme))
                print(card["answer"])
                revealed = True
                print("Rate [1-5], [n]=next, [s]=skip, [q]=quit")
                continue
            if cmd.lower() == "q":
                print("Ending session.")
                deck["last_reviewed_at"] = now_iso()
                deck["review_sessions"] = deck.get("review_sessions", 0) + 1
                deck["total_time_seconds"] = deck.get("total_time_seconds", 0) + int(
                    time.time() - session_start
                )
                save_deck(path, deck)
                return
            if cmd.lower() == "s":
                break
            if cmd.lower() == "n":
                break
            if cmd in ("1", "2", "3", "4", "5"):
                quality = int(cmd)
                # map 1-5 to 0-5 (simply take same, but cap)
                sm2_update(card, quality)
                card["review_count"] = card.get("review_count", 0) + 1
                ch = card.get("confidence_history") or []
                ch.append(
                    {
                        "timestamp": now_iso(),
                        "confidence": quality,
                    }
                )
                # keep last 50 entries
                if len(ch) > 50:
                    ch = ch[-50:]
                card["confidence_history"] = ch
                card["avg_confidence"] = round(
                    sum(e["confidence"] for e in ch) / len(ch), 2
                )
                card["last_reviewed_at"] = now_iso()
                print(f"Recorded confidence {quality}.")
                break
            if not revealed and cmd == "":
                continue
            print("Invalid input. Use [Enter], [1-5], [n], [s], [q].")

    deck["last_reviewed_at"] = now_iso()
    deck["review_sessions"] = deck.get("review_sessions", 0) + 1
    deck["total_time_seconds"] = deck.get("total_time_seconds", 0) + int(time.time() - session_start)
    save_deck(path, deck)
    print("Session complete.")


def stats_cmd(args, config, theme):
    study_dir = config["study_dir"]
    ensure_study_dir(study_dir)
    path = deck_path(study_dir, args.deck)
    deck = load_deck(path)
    if deck is None:
        return
    cards = deck["cards"]
    total = len(cards)
    mastered = 0
    confs = []
    streak = 0

    for c in cards:
        avg = c.get("avg_confidence")
        if avg is not None:
            confs.append(avg)
        if avg is not None and avg >= 4.0 and c.get("review_count", 0) >= 3:
            mastered += 1
        # simple streak: count cards due today or earlier with avg_conf >=3.5
        due_at = parse_iso(c.get("due_at") or now_iso())
        if due_at and due_at <= datetime.utcnow() and (avg or 0) >= 3.5:
            streak += 1

    avg_conf = round(sum(confs) / len(confs), 2) if confs else None
    total_time = int(deck.get("total_time_seconds", 0))
    sessions = deck.get("review_sessions", 0)
    last_reviewed = deck.get("last_reviewed_at")

    print(f"Deck: {deck['name']}")
    print(f"Total cards: {total}")
    print(f"Cards mastered: {mastered}")
    if avg_conf is not None:
        print(f"Average confidence: {avg_conf:.2f}")
    else:
        print("Average confidence: N/A")
    print(f"Review streak (high-confidence due cards): {streak}")
    print(f"Time spent studying: {total_time} seconds")
    print(f"Review sessions: {sessions}")
    print(f"Last reviewed: {last_reviewed or 'never'}")


def main():
    config = load_config()

    parser = argparse.ArgumentParser(description="Vocabulary Flashcard Study System")
    parser.add_argument(
        "--theme",
        choices=["auto", "light", "dark", "none"],
        help="Color theme (stored in config)",
    )
    sub = parser.add_subparsers(dest="command")

    p_add_deck = sub.add_parser("add-deck", help="Create a new deck")
    p_add_deck.add_argument("name", help="Deck name")
    p_add_deck.add_argument("--force", action="store_true", help="Overwrite if exists")

    p_add_card = sub.add_parser("add-card", help="Add card to a deck")
    p_add_card.add_argument("deck", help="Deck name")
    p_add_card.add_argument("--question", "-q", help="Question text")
    p_add_card.add_argument("--answer", "-a", help="Answer text")

    p_study = sub.add_parser("study", help="Study a deck")
    p_study.add_argument("deck", help="Deck name")
    p_study.add_argument(
        "--limit", type=int, help="Max number of cards this session"
    )

    p_list = sub.add_parser("list-decks", help="List available decks")

    p_export = sub.add_parser("export-deck", help="Export deck to JSON")
    p_export.add_argument("deck", help="Deck name")
    p_export.add_argument("--output", "-o", help="Output file path")

    p_import = sub.add_parser("import-deck", help="Import deck from JSON")
    p_import.add_argument("file", help="JSON file to import")
    p_import.add_argument("--name", help="Name for the imported deck")
    p_import.add_argument("--force", action="store_true", help="Overwrite if exists")

    p_delete = sub.add_parser("delete-deck", help="Delete a deck")
    p_delete.add_argument("deck", help="Deck name")
    p_delete.add_argument("--yes", "-y", action="store_true", help="Confirm deletion")

    p_stats = sub.add_parser("stats", help="Show deck statistics")
    p_stats.add_argument("deck", help="Deck name")

    p_print = sub.add_parser("print-deck", help="Print deck as text")
    p_print.add_argument("deck", help="Deck name")

    args = parser.parse_args()
    theme = apply_theme(config, args.theme)

    if args.command == "add-deck":
        add_deck_cmd(args, config, theme)
    elif args.command == "add-card":
        add_card_cmd(args, config, theme)
    elif args.command == "study":
        study_cmd(args, config, theme)
    elif args.command == "list-decks":
        list_decks_cmd(args, config, theme)
    elif args.command == "export-deck":
        export_deck_cmd(args, config, theme)
    elif args.command == "import-deck":
        import_deck_cmd(args, config, theme)
    elif args.command == "delete-deck":
        delete_deck_cmd(args, config, theme)
    elif args.command == "stats":
        stats_cmd(args, config, theme)
    elif args.command == "print-deck":
        print_deck_cmd(args, config, theme)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()