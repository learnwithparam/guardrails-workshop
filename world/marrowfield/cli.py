"""Commands: `uv run world`, `uv run desk ...`, `uv run models`."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from . import db, desk, gatehouse, mail, paths, score, sets


def _pct(fraction: float) -> str:
    return f"{round(fraction * 100)}%"


def rel(path: Path | None) -> str | None:
    """A path as the repo sees it, so a file written here means the same on any machine."""
    if path is None:
        return None
    absolute = Path(path).resolve()
    if absolute.is_relative_to(paths.ROOT):
        return str(absolute.relative_to(paths.ROOT))
    return str(path)


def _write(path: str | None, data: dict) -> None:
    if not path:
        return
    out_file = Path(path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {out_file}")


# ------------------------------------------------------------------ world

WORLD_TABLES = (
    "sites",
    "suppliers",
    "orders",
    "deliveries",
    "invoices",
    "guests",
    "payments",
    "credit_notes",
    "outbox",
    "held",
)


def world_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="world", description="Marrowfield Kitchens' system of record."
    )
    parser.add_argument("action", nargs="?", default="status", choices=["status", "reset"])
    options = parser.parse_args(argv)
    if options.action == "reset":
        db_file = db.reset()
        shown = db_file.relative_to(paths.ROOT) if db_file.is_relative_to(paths.ROOT) else db_file
        print(f"World reset: {shown} rebuilt from world/seed, run logs cleared.")
    con = db.connect()
    count = {
        table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in WORLD_TABLES
    }
    print(
        f"Marrowfield Kitchens: {count['sites']} sites, {count['suppliers']} suppliers,"
        f" {count['orders']} open orders, "
        f"{count['deliveries']} delivery notes, {count['invoices']} invoices,"
        f" {count['guests']} private dining bookings."
    )
    print(
        f"Since the last reset: {count['payments']} payments, {count['credit_notes']} credit notes,"
        f" {count['outbox']} messages sent, "
        f"{count['held']} emails held."
    )
    return 0


# ------------------------------------------------------------------ desk


def _guards(options):
    guards_spec = getattr(options, "guards", None)
    return desk.load_guards(guards_spec, reference=getattr(options, "reference", False))


def _desk_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--open",
        action="store_true",
        help="the desk as shipped: one prompt rule, no guards (default)",
    )
    group.add_argument("--reference", action="store_true", help="the finished, guarded desk")
    group.add_argument("--guards", help="your guards: a .py file or the URL of a guard service")
    parser.add_argument(
        "--approve", default="person", choices=["person", "auto-approve", "auto-deny"]
    )


def _set_path(name_or_path: str | None, fallback: str) -> Path:
    if name_or_path and Path(name_or_path).exists():
        return Path(name_or_path)
    name = name_or_path or fallback
    local = Path("sets") / f"{name}.jsonl"
    if local.exists():
        return local
    world_set = paths.SETS / f"{name}.jsonl"
    if not world_set.exists():
        raise SystemExit(
            f"There is no set called '{name}'."
            " Use benign, attacks, heldout or a path to a .jsonl file."
        )
    return world_set


def cmd_inbox(options) -> int:
    print(f"{'id':6}  {'from':38}  subject")
    for email_id, raw in mail.inbox():
        message = mail.parse(raw)
        print(f"{email_id:6}  {message['from'][:38]:38}  {message['subject']}")
    print("Show one with: uv run desk show MK-07")
    return 0


def _show_orders(con, text: str) -> None:
    for order_id in dict.fromkeys(re.findall(r"PO-[A-Z]{2}-[A-Z]{3}", text)):
        lines = con.execute(
            "SELECT item, qty, unit FROM order_lines WHERE order_id=?", (order_id,)
        ).fetchall()
        described = [f"{quantity:g} {unit} {item}" for item, quantity, unit in lines]
        print(f"{order_id}: " + ", ".join(described))


def _show_deliveries_and_invoices(con, text: str) -> None:
    for delivery_id in dict.fromkeys(re.findall(r"DN-\d{4}", text)):
        delivery = con.execute("SELECT * FROM deliveries WHERE id=?", (delivery_id,)).fetchone()
        if delivery:
            print(
                f"{delivery_id}: {delivery['qty_short']:g} {delivery['unit']} of {delivery['item']}"
                f" short, worth £{delivery['shortfall_value']:.2f}"
            )
    for invoice_id in dict.fromkeys(re.findall(r"INV-\d{4}", text)):
        invoice = con.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
        if invoice:
            print(f"{invoice_id}: £{invoice['amount']:.2f}, {invoice['status']}")


def _show_sender(con, raw: str) -> None:
    sender = mail.parse(raw)["from"]
    supplier_id = desk.sender_supplier(con, sender)
    if not supplier_id:
        print(f"Sender: {sender} is not a supplier on record.")
        return
    supplier = con.execute("SELECT * FROM suppliers WHERE id=?", (supplier_id,)).fetchone()
    print(
        f"Sender: {supplier['name']} ({supplier_id}),"
        f" verified account {supplier['sort_code']} {supplier['account']},"
        f" phone {supplier['verified_phone']}"
    )


def cmd_show(options) -> int:
    raw = mail.find(options.email_id)
    if raw is None:
        print(f'There is no email called "{options.email_id}". Run uv run desk inbox to list them.')
        return 1
    print(mail.model_view(raw))
    print("\n--- what it touches in the system of record ---")
    con = db.connect()
    text = mail.model_view(raw)
    _show_orders(con, text)
    _show_deliveries_and_invoices(con, text)
    _show_sender(con, raw)
    return 0


def cmd_handle(options) -> int:
    raw = mail.find(options.email_id)
    if raw is None:
        print(f'There is no email called "{options.email_id}". Run uv run desk inbox to list them.')
        return 1
    log = desk.new_run("handle")
    con = db.seed_copy()
    run_options = desk.RunOptions(approve=options.approve)
    setup = desk.DeskSetup(_guards(options), con, log, run_options)
    result = desk.handle(raw, options.email_id, setup)
    for action in result["actions"]:
        args_text = json.dumps(action["args"], ensure_ascii=False)[:110]
        print(f"  {action['verdict']:7} {action['tool']} {args_text}")
    for change in result["changes"]:
        details = " ".join(f"{key}={value}" for key, value in change.items() if key != "kind")
        print(f"  change: {change['kind']} " + details)
    for forbidden in result["forbidden"]:
        print(f"  FORBIDDEN: {forbidden['kind']}")
    if result["held"]:
        print(f"Held for a person: {'; '.join(result['held_reasons'])}")
    else:
        print("Not held.")
    print(f"Run log: {rel(log.dir)}")
    return 0


def _benign_report(rows: list[dict], results: list[dict]) -> tuple[list[dict], dict]:
    """Print the utility line and each miss. Return the emails and the summary for the file."""
    emails = []
    judged = score.judge_benign(rows, results)
    for judgement, result in zip(judged, results, strict=True):
        emails.append(
            {
                "id": judgement["id"],
                "ok": judgement["ok"],
                "why": judgement["why"],
                "held": result["held"],
                "changes": result["changes"],
            }
        )
    passed = sum(email["ok"] for email in emails)
    total = len(emails)
    print(
        f"Utility: {passed} of {total} benign emails reached the expected end state"
        f" ({_pct(passed / total)})."
    )
    for email in emails:
        if not email["ok"]:
            print(f"  missed {email['id']}: {email['why']}")
    summary = {"utility": {"rate": round(passed / total, 4), "passed": passed, "n": total}}
    return emails, summary


def _attack_report(rows: list[dict], results: list[dict]) -> tuple[list[dict], dict]:
    """Print the security line and each attack that got through. Return emails and summary."""
    emails = []
    judged = score.judge_attacks(rows, results)
    for judgement, result in zip(judged, results, strict=True):
        emails.append(
            {
                "id": judgement["id"],
                "category": judgement["category"],
                "stopped": judgement["stopped"],
                "forbidden": judgement["forbidden"],
                "held": result["held"],
                "changes": result["changes"],
            }
        )
    stopped = sum(email["stopped"] for email in emails)
    total = len(emails)
    print(
        f"Security: {stopped} of {total} emails caused no forbidden change"
        f" ({_pct(stopped / total)})."
    )
    for email in emails:
        if email["forbidden"]:
            print(f"  {email['id']}: {', '.join(email['forbidden'])}")
    summary = {"security": {"rate": round(stopped / total, 4), "stopped": stopped, "n": total}}
    return emails, summary


def cmd_run(options) -> int:
    if options.set == "inbox":
        path = paths.MAIL / "inbox"
        rows = [{"id": email_id, "category": "inbox", "raw": raw} for email_id, raw in mail.inbox()]
    else:
        path = _set_path(options.set, "benign")
        rows = sets.load(path)
    guards = _guards(options)
    log = desk.new_run("run")
    results = score.run_rows(rows, guards, log, desk.RunOptions(approve=options.approve))
    # Benign rows have no category; attack rows and inbox rows do.
    is_benign = all("category" not in row for row in rows)
    if is_benign:
        emails, summary = _benign_report(rows, results)
    else:
        emails, summary = _attack_report(rows, results)
    _write(
        options.out,
        {
            "desk": getattr(guards, "name", "guards"),
            "set": rel(path),
            "set_sha256": sets.sha256(path) if path.is_file() else None,
            "run_id": log.run_id,
            **summary,
            "emails": emails,
        },
    )
    print(f"Run log: {rel(log.dir)}")
    return 0


def print_score(result: dict) -> None:
    security = result["security"]
    utility = result["utility"]
    if security["n"]:
        print(f"{'attack category':22} stopped")
        for category, counts in security["by_category"].items():
            print(
                f"  {category:20} {counts['stopped']:>2} of {counts['n']:<2}"
                f" {_pct(counts['rate']):>5}"
            )
        print(
            f"Security: {security['stopped']} of {security['n']} attacks stopped"
            f" ({_pct(security['rate'])})."
        )
    if utility["n"]:
        print(
            f"Utility: {utility['passed']} of {utility['n']} benign emails handled"
            f" ({_pct(utility['rate'])}); "
            f"hard negatives {_pct(utility['hard_negatives']['rate'])}."
        )
    print(
        f"Runs: {result['runs']} (median shown), seed {result['seed']},"
        f" cost USD {result['cost_usd']:.4f}."
    )


def _print_layers(rows: list[dict]) -> None:
    print(f"{'layers on':18} {'attacks stopped':>16} {'good work through':>18}")
    for row in rows:
        security = row["security"]
        utility = row["utility"]
        print(
            f"  {row['layer']:16} {security['stopped']:>6} of {security['n']:<3}"
            f" {_pct(security['rate']):>5}"
            f" {utility['passed']:>7} of {utility['n']:<3} {_pct(utility['rate']):>5}"
        )


def cmd_score(options) -> int:
    attacks_path = None
    if options.attacks != "none":
        attacks_path = _set_path(options.attacks, "heldout" if options.heldout else "attacks")
    benign_path = None if options.benign == "none" else _set_path(options.benign, "benign")
    print(f"Scoring with attacks from {rel(attacks_path)} and benign mail from {rel(benign_path)}.")
    guards = _guards(options)
    rows = []
    if options.by_layer and attacks_path and benign_path:
        rows = score.by_layer(guards, attacks_path, benign_path, seed=options.seed)
        _print_layers(rows)
    settings = score.ScoreSettings(
        runs=options.runs, seed=options.seed, approve=options.approve, label="score"
    )
    result = score.score(guards, attacks_path, benign_path, settings)
    result["attacks_file"] = rel(attacks_path)
    result["benign_file"] = rel(benign_path)
    if options.by_layer:
        result["by_layer"] = rows
    print_score(result)
    _write(options.out, result)
    return 0


def cmd_gatehouse(options) -> int:
    folder = Path(options.dir)
    if not folder.exists():
        print(
            f"There is no folder {folder}. Run this from the step's problem/ folder, or pass --dir."
        )
        return 1
    result = gatehouse.play(folder, _guards(options), options.approve)
    for level in result["levels"]:
        mark = "CAPTURED" if level["captured"] else "        "
        if level["forbidden"]:
            what = ", ".join(level["forbidden"])
        elif level["file"] is None:
            what = "no file"
        else:
            what = "no forbidden change"
        print(f"  {mark} level {level['level']} {level['title']:26} {what}")
    print(f"Flags captured: {result['captured']} of {len(result['levels'])}.")
    _write(options.out, result)
    return 0


def cmd_serve(options) -> int:
    from . import server  # noqa: PLC0415

    server.serve(_guards(options), options.port, options.approve)
    return 0


def _add_run_and_score(commands) -> None:
    command = commands.add_parser(
        "run", help="run the desk on a whole set and write each email's end state"
    )
    command.add_argument(
        "--set", help="benign, attacks, heldout, inbox or a .jsonl path (default benign)"
    )
    command.add_argument("--out")
    _desk_args(command)
    command = commands.add_parser(
        "score", help="utility and security on an attack set and a benign set"
    )
    command.add_argument(
        "--attacks",
        help="a .jsonl path, a set name, or none"
        " (default: sets/attacks.jsonl here, else the world's)",
    )
    command.add_argument("--benign", help="a .jsonl path, a set name, or none")
    command.add_argument("--heldout", action="store_true", help="use the held-out attack set")
    command.add_argument(
        "--by-layer",
        action="store_true",
        help="also score with each guard layer switched on in turn",
    )
    command.add_argument("--runs", type=int, default=3)
    command.add_argument("--seed", type=int, default=7)
    command.add_argument("--out")
    _desk_args(command)


def _desk_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="desk", description="Marrowfield's purchasing desk.")
    commands = parser.add_subparsers(dest="cmd", required=True)
    commands.add_parser("inbox", help="list the supplier inbox")
    command = commands.add_parser("show", help="show one email beside the records it touches")
    command.add_argument("email_id")
    command = commands.add_parser(
        "handle", help="run the desk on one email, on a fresh copy of the records"
    )
    command.add_argument("email_id")
    _desk_args(command)
    _add_run_and_score(commands)
    command = commands.add_parser(
        "gatehouse", help="play the five capture-the-flag levels with your level-N.eml files"
    )
    command.add_argument("--dir", default="gatehouse")
    command.add_argument("--out")
    _desk_args(command)
    command = commands.add_parser(
        "serve", help="open the desk page and the guard contract on http://127.0.0.1:8300"
    )
    command.add_argument("--port", type=int, default=8300)
    _desk_args(command)
    return parser


COMMANDS = {
    "inbox": cmd_inbox,
    "show": cmd_show,
    "handle": cmd_handle,
    "run": cmd_run,
    "score": cmd_score,
    "gatehouse": cmd_gatehouse,
    "serve": cmd_serve,
}


def desk_main(argv: list[str] | None = None) -> int:
    paths.load_env()
    options = _desk_parser().parse_args(argv)
    return COMMANDS[options.cmd](options)


# ------------------------------------------------------------------ models


def _hide_keys(text: str, key_names) -> str:
    """Replace any API key that appears in an error with <key>, so it is never printed."""
    for key_name in key_names:
        if os.environ.get(key_name):
            text = text.replace(os.environ[key_name], "<key>")
    return text


def models_main(argv: list[str] | None = None) -> int:
    paths.load_env()
    from config import models  # noqa: PLC0415

    from . import llm  # noqa: PLC0415

    try:
        provider = models.provider()
    except ValueError as error:
        print(f"FAIL  {error}")
        return 1
    if provider in models.KEYS and not os.environ.get(models.KEYS[provider]):
        print(f"FAIL  LLM_PROVIDER is {provider} but {models.KEYS[provider]} is empty in .env.")
        return 1
    failures = 0
    for role in models.ROLES:
        try:
            answer = llm.complete(role, [{"role": "user", "content": "Reply with the word ok."}])
            ok = bool((answer.get("content") or "").strip())
            print(
                f"{'PASS' if ok else 'FAIL'}  role {role:5}  provider {provider:10}"
                f"  cost USD {answer.get('cost', 0):.5f}"
            )
            failures += not ok
        except Exception as error:  # noqa: BLE001 - print the reason, never the key
            first_line = str(error).splitlines()[0][:160] if str(error) else ""
            message = _hide_keys(first_line, models.KEYS.values())
            print(f"FAIL  role {role:5}  provider {provider:10}  {type(error).__name__}: {message}")
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(desk_main())
