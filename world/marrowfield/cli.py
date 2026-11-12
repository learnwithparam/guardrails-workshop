"""Commands: `uv run world`, `uv run desk ...`, `uv run models`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import db, desk, gatehouse, mail, paths, score, sets


def _pct(x: float) -> str:
    return f"{round(x * 100)}%"


def _write(path: str | None, data: dict) -> None:
    if not path:
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {p}")


# ------------------------------------------------------------------ world


def world_main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="world", description="Marrowfield Kitchens' system of record.")
    ap.add_argument("action", nargs="?", default="status", choices=["status", "reset"])
    a = ap.parse_args(argv)
    if a.action == "reset":
        p = db.reset()
        print(f"World reset: {p.relative_to(paths.ROOT) if p.is_relative_to(paths.ROOT) else p} rebuilt from world/seed, run logs cleared.")
    con = db.connect()
    n = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
         for t in ("sites", "suppliers", "orders", "deliveries", "invoices", "guests", "payments", "credit_notes", "outbox", "held")}
    print(f"Marrowfield Kitchens: {n['sites']} sites, {n['suppliers']} suppliers, {n['orders']} open orders, "
          f"{n['deliveries']} delivery notes, {n['invoices']} invoices, {n['guests']} private dining bookings.")
    print(f"Since the last reset: {n['payments']} payments, {n['credit_notes']} credit notes, {n['outbox']} messages sent, "
          f"{n['held']} emails held.")
    return 0


# ------------------------------------------------------------------ desk


def _guards(a):
    return desk.load_guards(getattr(a, "guards", None), reference=getattr(a, "reference", False))


def _desk_args(p: argparse.ArgumentParser) -> None:
    g = p.add_mutually_exclusive_group()
    g.add_argument("--open", action="store_true", help="the desk as shipped: one prompt rule, no guards (default)")
    g.add_argument("--reference", action="store_true", help="the finished, guarded desk")
    g.add_argument("--guards", help="your guards: a .py file or the URL of a guard service")
    p.add_argument("--approve", default="person", choices=["person", "auto-approve", "auto-deny"])


def _set_path(name_or_path: str | None, fallback: str) -> Path:
    if name_or_path and Path(name_or_path).exists():
        return Path(name_or_path)
    name = name_or_path or fallback
    local = Path("sets") / f"{name}.jsonl"
    if local.exists():
        return local
    p = paths.SETS / f"{name}.jsonl"
    if not p.exists():
        raise SystemExit(f"There is no set called '{name}'. Use benign, attacks, heldout or a path to a .jsonl file.")
    return p


def cmd_inbox(a) -> int:
    print(f"{'id':6}  {'from':38}  subject")
    for mid, raw in mail.inbox():
        m = mail.parse(raw)
        print(f"{mid:6}  {m['from'][:38]:38}  {m['subject']}")
    print("Show one with: uv run desk show MK-07")
    return 0


def cmd_show(a) -> int:
    raw = mail.find(a.email_id)
    if raw is None:
        print(f'There is no email called "{a.email_id}". Run uv run desk inbox to list them.')
        return 1
    print(mail.model_view(raw))
    print("\n--- what it touches in the system of record ---")
    con = db.connect()
    import re  # noqa: PLC0415

    text = mail.model_view(raw)
    for po in dict.fromkeys(re.findall(r"PO-[A-Z]{2}-[A-Z]{3}", text)):
        lines = con.execute("SELECT item, qty, unit FROM order_lines WHERE order_id=?", (po,)).fetchall()
        print(f"{po}: " + ", ".join(f"{q:g} {u} {i}" for i, q, u in lines))
    for d in dict.fromkeys(re.findall(r"DN-\d{4}", text)):
        r = con.execute("SELECT * FROM deliveries WHERE id=?", (d,)).fetchone()
        if r:
            print(f"{d}: {r['qty_short']:g} {r['unit']} of {r['item']} short, worth £{r['shortfall_value']:.2f}")
    for inv in dict.fromkeys(re.findall(r"INV-\d{4}", text)):
        r = con.execute("SELECT * FROM invoices WHERE id=?", (inv,)).fetchone()
        if r:
            print(f"{inv}: £{r['amount']:.2f}, {r['status']}")
    sup = desk.sender_supplier(con, mail.parse(raw)["from"])
    if sup:
        r = con.execute("SELECT * FROM suppliers WHERE id=?", (sup,)).fetchone()
        print(f"Sender: {r['name']} ({sup}), verified account {r['sort_code']} {r['account']}, phone {r['verified_phone']}")
    else:
        print(f"Sender: {mail.parse(raw)['from']} is not a supplier on record.")
    return 0


def cmd_handle(a) -> int:
    raw = mail.find(a.email_id)
    if raw is None:
        print(f'There is no email called "{a.email_id}". Run uv run desk inbox to list them.')
        return 1
    log = desk.new_run("handle")
    con = db.seed_copy()
    r = desk.handle(raw, a.email_id, _guards(a), con, log, approve=a.approve)
    for act in r["actions"]:
        print(f"  {act['verdict']:7} {act['tool']} {json.dumps(act['args'], ensure_ascii=False)[:110]}")
    for c in r["changes"]:
        print(f"  change: {c['kind']} " + " ".join(f"{k}={v}" for k, v in c.items() if k != "kind"))
    for f in r["forbidden"]:
        print(f"  FORBIDDEN: {f['kind']}")
    print(f"Held for a person: {'; '.join(r['held_reasons'])}" if r["held"] else "Not held.")
    print(f"Run log: {log.dir}")
    return 0


def cmd_run(a) -> int:
    path = _set_path(a.set, "benign")
    rows = sets.load(path)
    guards = _guards(a)
    log = desk.new_run("run")
    results = score.run_rows(rows, guards, log, approve=a.approve)
    is_benign = all("category" not in r for r in rows)
    emails = []
    if is_benign:
        judged = score.judge_benign(rows, results)
        for j, r in zip(judged, results):
            emails.append({"id": j["id"], "ok": j["ok"], "why": j["why"], "held": r["held"], "changes": r["changes"]})
        ok = sum(e["ok"] for e in emails)
        print(f"Utility: {ok} of {len(emails)} benign emails reached the expected end state ({_pct(ok / len(emails))}).")
        for e in emails:
            if not e["ok"]:
                print(f"  missed {e['id']}: {e['why']}")
        summary = {"utility": {"rate": round(ok / len(emails), 4), "passed": ok, "n": len(emails)}}
    else:
        judged = score.judge_attacks(rows, results)
        for j, r in zip(judged, results):
            emails.append({"id": j["id"], "category": j["category"], "stopped": j["stopped"], "forbidden": j["forbidden"],
                           "held": r["held"], "changes": r["changes"]})
        st = sum(e["stopped"] for e in emails)
        print(f"Security: {st} of {len(emails)} attacks caused no forbidden change ({_pct(st / len(emails))}).")
        summary = {"security": {"rate": round(st / len(emails), 4), "stopped": st, "n": len(emails)}}
    _write(a.out, {"desk": getattr(guards, "name", "guards"), "set": str(path), "set_sha256": sets.sha256(path),
                   "run_id": log.run_id, **summary, "emails": emails})
    print(f"Run log: {log.dir}")
    return 0


def print_score(s: dict) -> None:
    sec, ut = s["security"], s["utility"]
    if sec["n"]:
        print(f"{'attack category':22} stopped")
        for c, v in sec["by_category"].items():
            print(f"  {c:20} {v['stopped']:>2} of {v['n']:<2} {_pct(v['rate']):>5}")
        print(f"Security: {sec['stopped']} of {sec['n']} attacks stopped ({_pct(sec['rate'])}).")
    if ut["n"]:
        print(f"Utility: {ut['passed']} of {ut['n']} benign emails handled ({_pct(ut['rate'])}); "
              f"hard negatives {_pct(ut['hard_negatives']['rate'])}.")
    print(f"Runs: {s['runs']} (median shown), seed {s['seed']}, cost USD {s['cost_usd']:.4f}.")


def cmd_score(a) -> int:
    att = None if a.attacks == "none" else _set_path(a.attacks, "heldout" if a.heldout else "attacks")
    ben = None if a.benign == "none" else _set_path(a.benign, "benign")
    print(f"Scoring with attacks from {att} and benign mail from {ben}.")
    s = score.score(_guards(a), att, ben, runs=a.runs, seed=a.seed, approve=a.approve, label="score")
    print_score(s)
    _write(a.out, s)
    return 0


def cmd_gatehouse(a) -> int:
    folder = Path(a.dir)
    if not folder.exists():
        print(f"There is no folder {folder}. Run this from the step's problem/ folder, or pass --dir.")
        return 1
    r = gatehouse.play(folder, _guards(a), a.approve)
    for lv in r["levels"]:
        mark = "CAPTURED" if lv["captured"] else "        "
        what = ", ".join(lv["forbidden"]) or ("no file" if lv["file"] is None else "no forbidden change")
        print(f"  {mark} level {lv['level']} {lv['title']:26} {what}")
    print(f"Flags captured: {r['captured']} of {len(r['levels'])}.")
    _write(a.out, r)
    return 0


def cmd_serve(a) -> int:
    from . import server  # noqa: PLC0415

    server.serve(_guards(a), a.port, a.approve)
    return 0


def desk_main(argv: list[str] | None = None) -> int:
    paths.load_env()
    ap = argparse.ArgumentParser(prog="desk", description="Marrowfield's purchasing desk.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("inbox", help="list the supplier inbox")
    p = sub.add_parser("show", help="show one email beside the records it touches")
    p.add_argument("email_id")
    p = sub.add_parser("handle", help="run the desk on one email, on a fresh copy of the records")
    p.add_argument("email_id")
    _desk_args(p)
    p = sub.add_parser("run", help="run the desk on a whole set and write each email's end state")
    p.add_argument("--set", help="benign, attacks, heldout or a .jsonl path (default benign)")
    p.add_argument("--out")
    _desk_args(p)
    p = sub.add_parser("score", help="utility and security on an attack set and a benign set")
    p.add_argument("--attacks", help="a .jsonl path, a set name, or none (default: sets/attacks.jsonl here, else the world's)")
    p.add_argument("--benign", help="a .jsonl path, a set name, or none")
    p.add_argument("--heldout", action="store_true", help="use the held-out attack set")
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--out")
    _desk_args(p)
    p = sub.add_parser("gatehouse", help="play the five capture-the-flag levels with your level-N.eml files")
    p.add_argument("--dir", default="gatehouse")
    p.add_argument("--out")
    _desk_args(p)
    p = sub.add_parser("serve", help="open the desk page and the guard contract on http://127.0.0.1:8300")
    p.add_argument("--port", type=int, default=8300)
    _desk_args(p)
    a = ap.parse_args(argv)
    return {"inbox": cmd_inbox, "show": cmd_show, "handle": cmd_handle, "run": cmd_run, "score": cmd_score,
            "gatehouse": cmd_gatehouse, "serve": cmd_serve}[a.cmd](a)


# ------------------------------------------------------------------ models


def models_main(argv: list[str] | None = None) -> int:
    paths.load_env()
    from config import models  # noqa: PLC0415

    from . import llm  # noqa: PLC0415

    try:
        prov = models.provider()
    except ValueError as e:
        print(f"FAIL  {e}")
        return 1
    if prov in models.KEYS and not __import__("os").environ.get(models.KEYS[prov]):
        print(f"FAIL  LLM_PROVIDER is {prov} but {models.KEYS[prov]} is empty in .env.")
        return 1
    bad = 0
    for role in models.ROLES:
        try:
            r = llm.complete(role, [{"role": "user", "content": "Reply with the word ok."}])
            ok = bool((r.get("content") or "").strip())
            print(f"{'PASS' if ok else 'FAIL'}  role {role:5}  provider {prov:10}  cost USD {r.get('cost', 0):.5f}")
            bad += not ok
        except Exception as e:  # noqa: BLE001 - print the reason, never the key
            msg = str(e).splitlines()[0][:160] if str(e) else ""
            for k in models.KEYS.values():
                if __import__("os").environ.get(k):
                    msg = msg.replace(__import__("os").environ[k], "<key>")
            print(f"FAIL  role {role:5}  provider {prov:10}  {type(e).__name__}: {msg}")
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(desk_main())
