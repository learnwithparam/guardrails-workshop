"""The desk page and the guard contract, on http://127.0.0.1:8300.

GET  /                  the desk page: inbox, the agent's run with each guard verdict,
                        the ledger and the scoreboard
GET  /api/state         the desk's name and the inbox
GET  /api/email/<id>    one email as the model reads it
GET  /api/score         the scoreboard (computed once, then cached in world/state/)
POST /desk/handle       {"email_id": "MK-07", "approve": "person"}
                        returns the run on a fresh copy of the records
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
    guards_name = getattr(guards, "name", "guards")
    safe_name = "".join(letter if letter.isalnum() else "-" for letter in guards_name)[:40]
    cache_file = paths.state_dir() / f"scoreboard-{safe_name}.json"
    attacks_file = paths.SETS / "attacks.jsonl"
    benign_file = paths.SETS / "benign.jsonl"
    # The cache is stale when the prompt or either set changes.
    key = f"{db.PROMPT_MARKER}|{sets.sha256(attacks_file)}|{sets.sha256(benign_file)}"
    if cache_file.exists():
        cached = json.loads(cache_file.read_text())
        if cached.get("key") == key:
            return cached
    rows = []
    if getattr(guards, "name", "") == "reference_guards":
        rows = score.by_layer(guards, attacks_file, benign_file, runs=1)
    full_score = score.score(guards, attacks_file, benign_file, runs=1, label="scoreboard")
    scoreboard = {
        "key": key,
        "desk": guards_name,
        "by_layer": rows,
        "security": full_score["security"],
        "utility": full_score["utility"],
    }
    cache_file.write_text(json.dumps(scoreboard, indent=2))
    return scoreboard


def label(guards) -> str:
    guards_name = getattr(guards, "name", "")
    known_labels = {"open": "Open desk", "reference_guards": "Reference guarded desk"}
    return known_labels.get(guards_name, f"Your desk ({guards_name})")


def make_handler(guards, approve: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *message_parts):
            # Keep the terminal quiet: no line for every request.
            pass

        def _send(self, code: int, body, content_type="application/json"):
            if isinstance(body, bytes):
                data = body
            else:
                data = json.dumps(body, ensure_ascii=False, default=str).encode()
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _body(self) -> dict:
            length = int(self.headers.get("Content-Length") or 0)
            try:
                return json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return {}

        def do_GET(self):
            self.path = self.path.split("?", 1)[0]
            if self.path in ("/", "/index.html"):
                return self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            if self.path == "/api/state":
                box = []
                for email_id, raw in mail.inbox():
                    message = mail.parse(raw)
                    box.append(
                        {
                            "id": email_id,
                            "from": message["from"],
                            "name": message["from_name"],
                            "subject": message["subject"],
                        }
                    )
                return self._send(200, {"desk": label(guards), "inbox": box})
            if self.path.startswith("/api/email/"):
                raw = mail.find(self.path.rsplit("/", 1)[-1])
                if not raw:
                    return self._send(404, {"error": "no such email"})
                return self._send(200, {"view": mail.model_view(raw)})
            if self.path == "/api/score":
                return self._send(200, _score_cache(guards))
            return self._send(404, {"error": "not found"})

        def do_POST(self):
            body = self._body()
            if self.path == "/desk/handle":
                return self._handle_email(body)
            route = {
                "/guard/input": guards.input,
                "/guard/tool": guards.tool,
                "/guard/output": guards.output,
            }
            if self.path in route:
                return self._send(200, route[self.path](body))
            if self.path == "/guard/result":
                return self._send(200, {"result": guards.result(body)})
            return self._send(404, {"error": "not found"})

        def _handle_email(self, body: dict):
            raw = mail.find(str(body.get("email_id", "")))
            if raw is None:
                return self._send(404, {"error": "no such email"})
            log = desk.new_run("page")
            con = db.seed_copy()
            run_approve = body.get("approve", approve)
            result = desk.handle(raw, body["email_id"], guards, con, log, approve=run_approve)
            con.close()
            decisions = []
            decisions_file = log.dir / "decisions.jsonl"
            if decisions_file.exists():
                lines = decisions_file.read_text().splitlines()
                decisions = [json.loads(line) for line in lines if line.strip()]
            return self._send(200, {**result, "decisions": decisions})

    return Handler


def serve(guards, port: int = 8300, approve: str = "person") -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(guards, approve))
    print(f"{label(guards)} on http://127.0.0.1:{port}  (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
