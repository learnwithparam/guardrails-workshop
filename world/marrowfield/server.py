"""The desk page and the guard contract, on http://127.0.0.1:8300.

GET  /                  the desk page: inbox, the agent's run with each guard verdict, ledger and scoreboard
GET  /api/state         the desk's name and the inbox
GET  /api/email/<id>    one email as the model reads it
GET  /api/score         the scoreboard (computed once, then cached in world/state/)
POST /desk/handle       {"email_id": "MK-07", "approve": "person"} -> the run on a fresh copy of the records
POST /guard/input       the contract: the same answers the desk gets from its guards
POST /guard/tool
POST /guard/output
POST /guard/result
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import db, desk, mail, paths, score, sets

PAGE = Path(__file__).with_name("page") / "index.html"


def _score_cache(guards) -> dict:
    name = "".join(ch if ch.isalnum() else "-" for ch in getattr(guards, "name", "guards"))[:40]
    p = paths.state_dir() / f"scoreboard-{name}.json"
    att, ben = paths.SETS / "attacks.jsonl", paths.SETS / "benign.jsonl"
    key = f"{db.PROMPT_MARKER}|{sets.sha256(att)}|{sets.sha256(ben)}"
    if p.exists():
        cached = json.loads(p.read_text())
        if cached.get("key") == key:
            return cached
    rows = (
        score.by_layer(guards, att, ben, runs=1)
        if getattr(guards, "name", "") == "reference_guards"
        else []
    )
    s = score.score(guards, att, ben, runs=1, label="scoreboard")
    out = {
        "key": key,
        "desk": getattr(guards, "name", "guards"),
        "by_layer": rows,
        "security": s["security"],
        "utility": s["utility"],
    }
    p.write_text(json.dumps(out, indent=2))
    return out


def label(guards) -> str:
    n = getattr(guards, "name", "")
    return {"open": "Open desk", "reference_guards": "Reference guarded desk"}.get(
        n, f"Your desk ({n})"
    )


def make_handler(guards, approve: str):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):  # quiet
            pass

        def _send(self, code: int, body, ctype="application/json"):
            data = (
                body
                if isinstance(body, bytes)
                else json.dumps(body, ensure_ascii=False, default=str).encode()
            )
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            try:
                return json.loads(self.rfile.read(n) or b"{}")
            except json.JSONDecodeError:
                return {}

        def do_GET(self):
            self.path = self.path.split("?", 1)[0]
            if self.path in ("/", "/index.html"):
                return self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            if self.path == "/api/state":
                box = []
                for mid, raw in mail.inbox():
                    m = mail.parse(raw)
                    box.append(
                        {
                            "id": mid,
                            "from": m["from"],
                            "name": m["from_name"],
                            "subject": m["subject"],
                        }
                    )
                return self._send(200, {"desk": label(guards), "inbox": box})
            if self.path.startswith("/api/email/"):
                raw = mail.find(self.path.rsplit("/", 1)[-1])
                return (
                    self._send(200, {"view": mail.model_view(raw)})
                    if raw
                    else self._send(404, {"error": "no such email"})
                )
            if self.path == "/api/score":
                return self._send(200, _score_cache(guards))
            return self._send(404, {"error": "not found"})

        def do_POST(self):
            b = self._body()
            if self.path == "/desk/handle":
                raw = mail.find(str(b.get("email_id", "")))
                if raw is None:
                    return self._send(404, {"error": "no such email"})
                log = desk.new_run("page")
                con = db.seed_copy()
                r = desk.handle(
                    raw, b["email_id"], guards, con, log, approve=b.get("approve", approve)
                )
                con.close()
                dec = []
                f = log.dir / "decisions.jsonl"
                if f.exists():
                    dec = [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
                return self._send(200, {**r, "decisions": dec})
            route = {
                "/guard/input": guards.input,
                "/guard/tool": guards.tool,
                "/guard/output": guards.output,
            }
            if self.path in route:
                return self._send(200, route[self.path](b))
            if self.path == "/guard/result":
                return self._send(200, {"result": guards.result(b)})
            return self._send(404, {"error": "not found"})

    return H


def serve(guards, port: int = 8300, approve: str = "person") -> None:
    srv = ThreadingHTTPServer(("127.0.0.1", port), make_handler(guards, approve))
    print(f"{label(guards)} on http://127.0.0.1:{port}  (Ctrl+C to stop)", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
