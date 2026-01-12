# Auto-generated via Perplexity on 2026-01-12T01:44:48.473341Z
#!/usr/bin/env python3
import argparse
import configparser
import csv
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, date
from pathlib import Path

STAGES = ["Lead", "Qualified", "Proposal", "Negotiation", "Won", "Lost"]
DATE_FMT = "%Y-%m-%d"
DATETIME_FMT = "%Y-%m-%dT%H:%M:%S"
DEFAULT_DATA_FILE = "deals.json"
CONFIG_FILE = ".dealsrc"
ENV_DATA_FILE = "DEALS_DATA_FILE"


def load_config():
    cfg = {}
    home = Path.home()
    cfg_path = home / CONFIG_FILE
    if cfg_path.is_file():
        parser = configparser.ConfigParser()
        try:
            parser.read(cfg_path)
            if "defaults" in parser:
                d = parser["defaults"]
                if "owner" in d:
                    cfg["owner"] = d["owner"]
                if "data_file" in d:
                    cfg["data_file"] = d["data_file"]
        except Exception:
            pass
    return cfg


def parse_date(s, field_name):
    try:
        return datetime.strptime(s, DATE_FMT).date()
    except ValueError:
        print(f"Invalid date for {field_name}, expected YYYY-MM-DD: {s}", file=sys.stderr)
        sys.exit(1)


def parse_stage(s, field_name="stage"):
    if s not in STAGES:
        print(f"Invalid {field_name}: {s}. Must be one of: {', '.join(STAGES)}", file=sys.stderr)
        sys.exit(1)
    return s


def get_data_file(args, config):
    if getattr(args, "data_file", None):
        return Path(args.data_file)
    if ENV_DATA_FILE in os.environ:
        return Path(os.environ[ENV_DATA_FILE])
    if "data_file" in config:
        return Path(config["data_file"])
    return Path(DEFAULT_DATA_FILE)


def atomic_save(path, data):
    tmp_fd, tmp_name = tempfile.mkstemp(prefix="deals_tmp_", dir=str(path.parent))
    os.close(tmp_fd)
    try:
        with open(tmp_name, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        shutil.move(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass


def load_deals(path):
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        backup = path.with_suffix(path.suffix + ".bak")
        try:
            shutil.copy2(path, backup)
        except OSError:
            pass
        print(f"Warning: Malformed JSON in {path}. Backed up to {backup}. Starting with empty list.", file=sys.stderr)
        return []
    except FileNotFoundError:
        return []


def save_deals(path, deals, no_save):
    if no_save:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_save(path, deals)


def next_id(deals):
    return max((d.get("id", 0) for d in deals), default=0) + 1


def truncate(text, width):
    if text is None:
        text = ""
    s = str(text)
    return s if len(s) <= width else s[: width - 1] + "…"


def format_value(v):
    try:
        return f"{float(v):.2f}"
    except (TypeError, ValueError):
        return ""


def is_overdue(next_action_str):
    if not next_action_str:
        return False
    try:
        d = datetime.strptime(next_action_str, DATE_FMT).date()
    except ValueError:
        return False
    return d < date.today()


def parse_next_action_arg(val):
    if val is None:
        return None
    if val == "":
        return None
    _ = parse_date(val, "next_action")
    return val


def filter_deals(deals, args):
    res = deals
    if args.stage:
        res = [d for d in res if d.get("stage") == args.stage]
    if args.owner:
        res = [d for d in res if d.get("owner") == args.owner]
    if args.min_value is not None:
        res = [d for d in res if isinstance(d.get("value"), (int, float)) and d.get("value", 0) >= args.min_value]
    if args.max_value is not None:
        res = [d for d in res if isinstance(d.get("value"), (int, float)) and d.get("value", 0) <= args.max_value]
    if args.search:
        q = args.search.lower()
        res = [
            d
            for d in res
            if q in str(d.get("title", "")).lower()
            or q in str(d.get("client", "")).lower()
            or q in str(d.get("notes", "")).lower()
        ]
    key = None
    if args.sort == "value":
        key = lambda d: d.get("value", 0.0)
    elif args.sort == "stage":
        key = lambda d: d.get("stage", "")
    elif args.sort == "client":
        key = lambda d: d.get("client", "")
    elif args.sort == "owner":
        key = lambda d: d.get("owner", "")
    elif args.sort == "next_action":
        key = lambda d: d.get("next_action") or ""
    elif args.sort == "created_at":
        key = lambda d: d.get("created_at") or ""
    if key:
        res = sorted(res, key=key, reverse=args.reverse)
    return res


def print_table(deals, compact, plain):
    if compact:
        widths = {
            "id": 4,
            "title": 18,
            "client": 14,
            "value": 10,
            "stage": 10,
            "owner": 10,
            "next": 10,
        }
    else:
        widths = {
            "id": 5,
            "title": 30,
            "client": 20,
            "value": 12,
            "stage": 12,
            "owner": 16,
            "next": 12,
        }
    header = [
        "ID".ljust(widths["id"]),
        "Title".ljust(widths["title"]),
        "Client".ljust(widths["client"]),
        "Value".rjust(widths["value"]),
        "Stage".ljust(widths["stage"]),
        "Owner".ljust(widths["owner"]),
        "Next".ljust(widths["next"]),
        "!",
    ]
    print(" ".join(header))
    print("-" * (sum(widths.values()) + 7))
    for d in deals:
        overdue = is_overdue(d.get("next_action"))
        mark = "!" if overdue else ""
        row = [
            str(d.get("id")).ljust(widths["id"]),
            truncate(d.get("title", ""), widths["title"]).ljust(widths["title"]),
            truncate(d.get("client", ""), widths["client"]).ljust(widths["client"]),
            format_value(d.get("value")).rjust(widths["value"]),
            truncate(d.get("stage", ""), widths["stage"]).ljust(widths["stage"]),
            truncate(d.get("owner", ""), widths["owner"]).ljust(widths["owner"]),
            truncate(d.get("next_action", ""), widths["next"]).ljust(widths["next"]),
            mark,
        ]
        print(" ".join(row))


def cmd_add(args, deals, config):
    title = args.title or input("Title: ").strip()
    while not title:
        title = input("Title (required): ").strip()
    client = args.client or input("Client: ").strip()
    while not client:
        client = input("Client (required): ").strip()
    value = args.value
    while value is None:
        raw = input("Value: ").strip()
        try:
            value = float(raw)
        except ValueError:
            print("Please enter a numeric value.")
            continue
    stage = parse_stage(args.stage or "Lead")
    owner = args.owner or config.get("owner") or input("Owner: ").strip()
    while not owner:
        owner = input("Owner (required): ").strip()
    next_action = parse_next_action_arg(args.next_action) if args.next_action else None
    if next_action is None and args.next_action:
        next_action = None
    if next_action is None and not args.next_action:
        na = input("Next action date (YYYY-MM-DD, optional): ").strip()
        if na:
            next_action = parse_next_action_arg(na)
    notes = args.notes or input("Notes (optional): ")
    now = datetime.now().strftime(DATETIME_FMT)
    new_id = next_id(deals)
    deal = {
        "id": new_id,
        "title": title,
        "client": client,
        "value": float(value),
        "stage": stage,
        "owner": owner,
        "created_at": now,
        "updated_at": now,
        "next_action": next_action,
        "notes": notes,
    }
    deals.append(deal)
    print(f"Added deal #{new_id}: {title} for {client} [{stage}] value {value:.2f}")
    return deals, "add"


def find_deal(deals, deal_id):
    for d in deals:
        if d.get("id") == deal_id:
            return d
    print(f"Deal with id {deal_id} not found.", file=sys.stderr)
    sys.exit(1)


def cmd_list(args, deals, config):
    filtered = filter_deals(deals, args)
    if not filtered:
        print("No deals found.")
        return deals
    print_table(filtered, args.compact, args.plain)
    return deals


def cmd_move(args, deals, config):
    deal_id = args.id
    new_stage = parse_stage(args.stage)
    deal = find_deal(deals, deal_id)
    old_stage = deal.get("stage")
    deal["stage"] = new_stage
    deal["updated_at"] = datetime.now().strftime(DATETIME_FMT)
    print(f"Deal #{deal_id}: stage {old_stage} -> {new_stage}")
    return deals, "move"


def cmd_edit(args, deals, config):
    deal_id = args.id
    deal = find_deal(deals, deal_id)
    changed = []
    if args.title is not None:
        deal["title"] = args.title
        changed.append("title")
    if args.client is not None:
        deal["client"] = args.client
        changed.append("client")
    if args.value is not None:
        deal["value"] = float(args.value)
        changed.append("value")
    if args.stage is not None:
        deal["stage"] = parse_stage(args.stage)
        changed.append("stage")
    if args.owner is not None:
        deal["owner"] = args.owner
        changed.append("owner")
    if args.next_action is not None:
        if args.next_action == "":
            deal["next_action"] = None
        else:
            deal["next_action"] = parse_next_action_arg(args.next_action)
        changed.append("next_action")
    if args.notes is not None:
        deal["notes"] = args.notes
        changed.append("notes")
    if changed:
        deal["updated_at"] = datetime.now().strftime(DATETIME_FMT)
        print(f"Edited deal #{deal_id}. Fields changed: {', '.join(changed)}")
    else:
        print(f"No changes for deal #{deal_id}.")
    return deals, "edit"


def cmd_delete(args, deals, config):
    deal_id = args.id
    deal = find_deal(deals, deal_id)
    if not args.force:
        confirm = input('Type DELETE to confirm deletion: ').strip()
        if confirm != "DELETE":
            print("Deletion cancelled.")
            return deals, "delete-cancelled"
    deals = [d for d in deals if d.get("id") != deal_id]
    print(f"Deleted deal #{deal_id}: {deal.get('title', '')}")
    return deals, "delete"


def cmd_stats(args, deals, config):
    subset = filter_deals(deals, args)
    if not subset:
        print("No deals to show stats for.")
        return deals
    per_stage = {}
    for d in subset:
        st = d.get("stage", "Unknown")
        per_stage.setdefault(st, {"count": 0, "total": 0.0})
        per_stage[st]["count"] += 1
        try:
            per_stage[st]["total"] += float(d.get("value", 0.0))
        except (TypeError, ValueError):
            pass
    print("Stage statistics:")
    print("{:<15} {:>6} {:>15} {:>15}".format("Stage", "Count", "Total", "Average"))
    print("-" * 55)
    for st in STAGES:
        if st not in per_stage:
            continue
        c = per_stage[st]["count"]
        t = per_stage[st]["total"]
        avg = t / c if c else 0.0
        print("{:<15} {:>6} {:>15.2f} {:>15.2f}".format(st, c, t, avg))
    open_total = sum(
        float(d.get("value", 0.0))
        for d in subset
        if d.get("stage") not in ("Won", "Lost")
    )
    print()
    print(f"Sum of open deals (not Won/Lost): {open_total:.2f}")
    return deals


def cmd_export(args, deals, config):
    data = deals
    if args.format == "json":
        out = json.dumps(data, indent=2, sort_keys=True)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(out)
        else:
            print(out)
    elif args.format == "csv":
        fieldnames = ["id", "title", "client", "value", "stage", "owner", "created_at", "updated_at", "next_action", "notes"]
        if args.output:
            f = open(args.output, "w", encoding="utf-8", newline="")
            close = True
        else:
            f = sys.stdout
            close = False
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for d in data:
            row = {k: d.get(k, "") for k in fieldnames}
            writer.writerow(row)
        if close:
            f.close()
    return deals


def cmd_undo(args, deals, history, redo_stack):
    if not history:
        print("Nothing to undo.")
        return deals, history, redo_stack
    prev_state, desc = history.pop()
    redo_stack.append((json.loads(json.dumps(deals)), desc))
    print("Undid last operation.")
    return prev_state, history, redo_stack


def cmd_redo(args, deals, history, redo_stack):
    if not redo_stack:
        print("Nothing to redo.")
        return deals, history, redo_stack
    next_state, desc = redo_stack.pop()
    history.append((json.loads(json.dumps(deals)), desc))
    print("Redid last operation.")
    return next_state, history, redo_stack


def main_usage(parser):
    print("Client Deal Pipeline CLI")
    print()
    print("Usage: python deals.py <command> [options]")
    print()
    print("Common commands:")
    print("  add       Add a new deal")
    print("  list      List deals with filters and sorting")
    print("  move      Move a deal to another stage")
    print("  edit      Edit deal fields")
    print("  delete    Delete a deal")
    print("  stats     Show pipeline statistics")
    print("  export    Export deals as JSON or CSV")
    print("  undo      Undo last change (current session)")
    print("  redo      Redo last undone change (current session)")
    print()
    print("Run 'python deals.py <command> --help' for details on a command.")
    parser.print_help()


def build_parser(config):
    parser = argparse.ArgumentParser(add_help=True, description="Client Deal Pipeline CLI")
    parser.add_argument("--data-file", help="Path to deals JSON file")
    parser.add_argument("--compact", action="store_true", help="Use more compact tabular output")
    parser.add_argument("--plain", action="store_true", help="Disable any styling (placeholder)")
    parser.add_argument("--no-save", action="store_true", help="Do not write any changes to disk (in-memory only)")
    subparsers = parser.add_subparsers(dest="command")

    p_add = subparsers.add_parser("add", help="Add a new deal (e.g. python deals.py add --title ...)")
    p_add.add_argument("--title", help="Deal title")
    p_add.add_argument("--client", help="Client name")
    p_add.add_argument("--value", type=float, help="Deal value")
    p_add.add_argument("--stage", choices=STAGES, default="Lead", help="Stage (default: Lead)")
    p_add.add_argument("--owner", help="Owner (default from config if set)")
    p_add.add_argument("--next-action", help="Next action date (YYYY-MM-DD)")
    p_add.add_argument("--notes", help="Notes")
    p_add.set_defaults(func="add")

    p_list = subparsers.add_parser("list", help="List deals (e.g. python deals.py list --stage Lead)")
    p_list.add_argument("--stage", choices=STAGES, help="Filter by stage")
    p_list.add_argument("--owner", help="Filter by owner")
    p_list.add_argument("--min-value", type=float, help="Minimum deal value")
    p_list.add_argument("--max-value", type=float, help="Maximum deal value")
    p_list.add_argument("--search", help="Search in title, client, notes")
    p_list.add_argument(
        "--sort",
        choices=["value", "stage", "client", "owner", "next_action", "created_at"],
        help="Sort by field",
    )
    p_list.add_argument("--reverse", action="store_true", help="Reverse sort order")
    p_list.set_defaults(func="list")

    p_move = subparsers.add_parser("move", help="Move a deal to a new stage (e.g. python deals.py move 3 --stage Won)")
    p_move.add_argument("id", type=int, help="Deal id")
    p_move.add_argument("--stage", required=True, choices=STAGES, help="New stage")
    p_move.set_defaults(func="move")

    p_edit = subparsers.add_parser("edit", help="Edit deal fields (e.g. python deals.py edit 2 --value 1000)")
    p_edit.add_argument("id", type=int, help="Deal id")
    p_edit.add_argument("--title", help="New title")
    p_edit.add_argument("--client", help="New client")
    p_edit.add_argument("--value", type=float, help="New value")
    p_edit.add_argument("--stage", choices=STAGES, help="New stage")
    p_edit.add_argument("--owner", help="New owner")
    p_edit.add_argument("--next-action", help="New next action date (YYYY-MM-DD, empty string to clear)")
    p_edit.add_argument("--notes", help="New notes")
    p_edit.set_defaults(func="edit")

    p_del = subparsers.add_parser("delete", help="Delete a deal (e.g. python deals.py delete 4)")
    p_del.add_argument("id", type=int, help="Deal id")
    p_del.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    p_del.set_defaults(func="delete")

    p_stats = subparsers.add_parser("stats", help="Show statistics (e.g. python deals.py stats --stage Lead)")
    p_stats.add_argument("--stage", choices=STAGES, help="Filter by stage")
    p_stats.add_argument("--owner", help="Filter by owner")
    p_stats.set_defaults(func="stats")

    p_export = subparsers.add_parser("export", help="Export data (e.g. python deals.py export --format csv)")
    p_export.add_argument("--format", choices=["json", "csv"], required=True, help="Export format")
    p_export.add_argument("--output", help="Output file path (default: stdout)")
    p_export.set_defaults(func="export")

    p_undo = subparsers.add_parser("undo", help="Undo last change in current session")
    p_undo.set_defaults(func="undo")

    p_redo = subparsers.add_parser("redo", help="Redo last undone change in current session")
    p_redo.set_defaults(func="redo")

    return parser


def main():
    config = load_config()
    parser = build_parser(config)
    if len(sys.argv) == 1:
        main_usage(parser)
        sys.exit(0)
    args = parser.parse_args()
    data_file = get_data_file(args, config)
    deals = load_deals(data_file)
    history = []
    redo_stack = []
    command = getattr(args, "command", None)

    if command in ("add", "move", "edit", "delete"):
        history.append((json.loads(json.dumps(deals)), command))
        redo_stack.clear()

    if command == "add":
        deals, _ = cmd_add(args, deals, config)
        save_deals(data_file, deals, args.no_save)
    elif command == "list":
        cmd_list(args, deals, config)
    elif command == "move":
        deals, _ = cmd_move(args, deals, config)
        save_deals(data_file, deals, args.no_save)
    elif command == "edit":
        deals, _ = cmd_edit(args, deals, config)
        save_deals(data_file, deals, args.no_save)
    elif command == "delete":
        deals, desc = cmd_delete(args, deals, config)
        if desc != "delete-cancelled":
            save_deals(data_file, deals, args.no_save)
    elif command == "stats":
        cmd_stats(args, deals, config)
    elif command == "export":
        cmd_export(args, deals, config)
    elif command == "undo":
        deals, history, redo_stack = cmd_undo(args, deals, history, redo_stack)
        save_deals(data_file, deals, args.no_save)
    elif command == "redo":
        deals, history, redo_stack = cmd_redo(args, deals, history, redo_stack)
        save_deals(data_file, deals, args.no_save)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()