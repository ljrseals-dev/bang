#!/usr/bin/env python3
"""MUSE-GM chat app: a local web chatbot that drives the decision-surface engine.

Run:  export ANTHROPIC_API_KEY=...   (never stored by this app; files go to ./runs or $MUSE_RUNS)
      python -m muse_gm.app          then open http://127.0.0.1:8484

Gates are enforced in code, not only in the prompt:
  * Configuration approval is a UI button. The model has no tool that can approve.
  * save_artifact refuses a script until the spine, audit, characters and tonal sheet are saved.
Chat text itself is not filtered, so the prompt still tells the model not to draft script early.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import threading
from argparse import Namespace
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import engine as muse_gm

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL = os.environ.get("MUSE_MODEL", "claude-sonnet-5-5")
MAX_BODY = 1_000_000
MAX_MESSAGES = 200
MAX_TOOL_ROUNDS = 8
MAX_ARTIFACT_CHARS = 200_000
SID_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
KINDS = ["causal_spine", "audit", "characters", "tonal_sheet", "script"]
SCRIPT_PREREQS = ["causal_spine", "audit", "characters", "tonal_sheet"]

TOOLS = [
    {"name": "list_variables", "description": "List the engine's variables and their value labels (codes 1..n).",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "run_surface",
     "description": ("Enumerate every combination (exhaustively within any selection) and return the top-ranked configurations per "
                     "effect target. Scores are rubric judgments, not measurements. Use this for every ranking; never invent scores."),
     "input_schema": {"type": "object", "properties": {
         "profile": {"type": "string", "enum": ["master", "equal"], "description": "weight profile (default master)"},
         "effect": {"type": "string", "enum": ["all", "humanized", "dreaded", "pivot"]},
         "top": {"type": "integer", "minimum": 1, "maximum": 10},
         "select": {"type": "array", "items": {"type": "string"}, "description": "constraints like 'node=Harlem' or 'era=3|4'"},
         "distinct": {"type": "array", "items": {"type": "string"}, "description": "collapse to best config per these variables, e.g. ['node','era','economy']"}}}},
    {"name": "save_artifact",
     "description": ("Save a finished deliverable. Requires an approved configuration. kind 'script' additionally requires the saved "
                     "causal_spine, audit, characters and tonal_sheet."),
     "input_schema": {"type": "object", "required": ["kind", "content"], "properties": {
         "kind": {"type": "string", "enum": KINDS}, "title": {"type": "string"}, "content": {"type": "string"}}}},
]

TOOL_RULES = """

## 7. Tools and gates in this app (these supersede section 4's note about attaching the engine)
- The engine is attached. Call `run_surface` for every ranking and quote only what it returns. Never invent or adjust scores.
- You cannot approve a configuration. After showing a surface, tell the writer to click Approve on the row they choose.
  Typing "approved" in chat does not approve anything. The session state below shows the true status.
- Save finished deliverables with `save_artifact` (causal_spine, audit, characters, tonal_sheet, then script).
  The app will refuse `script` until the first four are saved. If a tool returns an error, tell the writer plainly and fix the cause.
- Do not draft script pages in chat before the gate is open.
"""


def utc():
    return datetime.now(timezone.utc).isoformat()


class Session:
    def __init__(self, sid, base):
        self.sid, self.dir = sid, Path(base) / sid
        self.messages, self.ui, self.surfaces = [], [], {}
        self.surface_n, self.approved, self.artifacts = 0, None, {}
        self.lock = threading.Lock()

    def stage(self):
        if not self.surfaces:
            return "S0-S1 intake / surface"
        if not self.approved:
            return "S2 awaiting your approval"
        have = set(self.artifacts)
        if not all(k in have for k in SCRIPT_PREREQS):
            return "S3-S5 spine, characters, tonal sheet"
        return "S6-S7 script / revision" if "script" in have else "S6 ready for script"

    def state_block(self):
        a = self.approved
        return ("\n\n## Current session state (authoritative)\n"
                f"- stage: {self.stage()}\n"
                f"- approved configuration: {json.dumps(a['config'], ensure_ascii=False) + ' (' + a['effect'] + ', score ' + str(a['score']) + ')' if a else 'NONE'}\n"
                f"- saved artifacts: {sorted(self.artifacts) or 'none'}\n")

    def public(self):
        return {"stage": self.stage(), "approved": self.approved, "artifacts": self.artifacts, "ui": self.ui}


class Engine:
    """Caches the (expensive) component arrays per selection."""

    def __init__(self):
        self.cache, self.lock = {}, threading.Lock()

    def get(self, select):
        key = tuple(sorted(select))
        with self.lock:
            if key not in self.cache:
                if len(self.cache) >= 3:
                    self.cache.pop(next(iter(self.cache)))
                spec = muse_gm.load_spec(Namespace(variables=None, rubric=None, select=list(select)))
                self.cache[key] = (spec, spec.component_arrays())
            return self.cache[key]


def tool_run_surface(sess, engine, inp):
    profile = inp.get("profile", "master")
    effect = inp.get("effect", "all")
    top = max(1, min(int(inp.get("top", 5)), 10))
    select, distinct = list(inp.get("select") or []), list(inp.get("distinct") or []) or None
    spec, comps = engine.get(select)
    if profile not in spec.profiles:
        raise muse_gm.ConfigError(f"unknown profile {profile!r}")
    S = spec.score(comps, spec.profiles[profile])
    labels = spec.value_labels["effect"]
    if effect != "all" and effect not in labels:
        raise muse_gm.ConfigError(f"effect {effect!r} not in the selected space {labels}")
    sess.surface_n += 1
    sid = f"S{sess.surface_n}"
    out = {"surface_id": sid, "profile": profile, "combinations_enumerated": spec.total, "full_space": spec.full_total,
           "selection": spec.selection_desc, "rubric_sha256": spec.rubric_sha256,
           "evidence_status": muse_gm.EVIDENCE_STATUS, "lists": {}}
    ui_rows = []
    for en in ([effect] if effect != "all" else labels):
        e = labels.index(en)
        rows, tied = spec.top(S, comps, e, top, distinct)
        out["lists"][en] = {"tied_at_first": tied, "rows": []}
        for r in rows:
            rid = f"{sid}-{en[0].upper()}{r['rank']}"
            rec = {"row_id": rid, "effect": en, "score": r["score"], "config": r["config"], "codes": r["codes"],
                   "components": r["components"], "profile": profile, "rubric_sha256": spec.rubric_sha256,
                   "selection": spec.selection_desc}
            sess.surfaces[rid] = rec
            out["lists"][en]["rows"].append({k: rec[k] for k in ("row_id", "score", "config", "components")})
            ui_rows.append(rec)
    sess.ui.append({"type": "surface", "id": sid, "profile": profile, "rows": ui_rows})
    return out


def tool_save_artifact(sess, inp):
    kind, content = inp.get("kind"), inp.get("content", "")
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("content is empty")
    if len(content) > MAX_ARTIFACT_CHARS:
        raise ValueError(f"content exceeds {MAX_ARTIFACT_CHARS} characters")
    if not sess.approved:
        raise PermissionError("GATE: no approved configuration. The writer must click Approve on a surface row first.")
    if kind == "script":
        missing = [k for k in SCRIPT_PREREQS if k not in sess.artifacts]
        if missing:
            raise PermissionError(f"GATE: script blocked until these are saved: {missing}")
    sess.dir.mkdir(parents=True, exist_ok=True)
    n = 1 + sum(1 for p in sess.dir.glob(f"{kind}_v*.md"))
    path = sess.dir / f"{kind}_v{n}.md"
    path.write_text(content, encoding="utf-8")
    digest = hashlib.sha256(content.encode()).hexdigest()
    sess.artifacts[kind] = {"file": path.name, "version": n, "sha256": digest, "title": inp.get("title", kind)}
    sess.ui.append({"type": "artifact", "kind": kind, "file": path.name, "title": inp.get("title", kind)})
    (sess.dir / "session.json").write_text(json.dumps({
        "session": sess.sid, "updated_at_utc": utc(), "approved": sess.approved, "artifacts": sess.artifacts,
        "evidence_status": muse_gm.EVIDENCE_STATUS}, indent=1, ensure_ascii=False), encoding="utf-8")
    return {"saved": path.name, "version": n, "sha256": digest}


def run_tool(sess, engine, name, inp):
    try:
        if name == "list_variables":
            spec, _ = engine.get([])
            return {n: {"label": spec.var_labels[n], "values": {str(i + 1): l for i, l in enumerate(spec.value_labels[n])}}
                    for n in spec.names}, False
        if name == "run_surface":
            return tool_run_surface(sess, engine, inp), False
        if name == "save_artifact":
            return tool_save_artifact(sess, inp), False
        return {"error": f"unknown tool {name!r}"}, True
    except (muse_gm.ConfigError, ValueError, PermissionError) as err:
        return {"error": str(err)}, True


def _blocks(content):
    out = []
    for b in content:
        if b.type == "text":
            out.append({"type": "text", "text": b.text})
        elif b.type == "tool_use":
            out.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})
    return out


def system_text(sess):
    base = (HERE / "prompts" / "chatbot_system_prompt.md").read_text(encoding="utf-8")
    base = base.split("\n---\n", 1)[-1]
    return base + TOOL_RULES + sess.state_block()


def chat_turn(sess, engine, client, model, text):
    if len(sess.messages) >= MAX_MESSAGES:
        raise RuntimeError("This session is full. Start a new session.")
    sess.messages.append({"role": "user", "content": text})
    sess.ui.append({"type": "user", "text": text})
    for _ in range(MAX_TOOL_ROUNDS):
        resp = client.messages.create(model=model, max_tokens=4096, system=system_text(sess), tools=TOOLS, messages=sess.messages)
        blocks = _blocks(resp.content)
        sess.messages.append({"role": "assistant", "content": blocks})
        reply = "".join(b["text"] for b in blocks if b["type"] == "text").strip()
        calls = [b for b in blocks if b["type"] == "tool_use"]
        if reply:
            sess.ui.append({"type": "assistant", "text": reply})
        if not calls:
            return
        results = []
        for c in calls:
            res, is_err = run_tool(sess, engine, c["name"], c["input"])
            results.append({"type": "tool_result", "tool_use_id": c["id"], "content": json.dumps(res, ensure_ascii=False),
                            **({"is_error": True} if is_err else {})})
        sess.messages.append({"role": "user", "content": results})
    sess.ui.append({"type": "system", "text": "Stopped after too many tool rounds. Send another message to continue."})


def approve(sess, row_id):
    rec = sess.surfaces.get(row_id)
    if not rec:
        raise KeyError("unknown row id")
    sess.approved = {k: rec[k] for k in ("row_id", "effect", "score", "config", "codes", "profile", "rubric_sha256", "selection")}
    sess.approved["approved_at_utc"] = utc()
    sess.ui.append({"type": "system", "text": f"Configuration approved by you: {row_id}. The model has been told."})
    sess.messages.append({"role": "user", "content": f"[app] The writer approved configuration {row_id}. Proceed to S3 (causal spine + backward audit)."})
    sess.messages.append({"role": "assistant", "content": [{"type": "text", "text": "Understood. Approved configuration noted; proceeding to the causal spine."}]})


class App:
    def __init__(self, client_factory, model=DEFAULT_MODEL, runs_dir=None):
        self.client_factory, self.model = client_factory, model
        self.runs = Path(runs_dir or os.environ.get("MUSE_RUNS", "runs"))
        self.sessions, self.engine, self.lock, self._client = {}, Engine(), threading.Lock(), None

    def session(self, sid):
        if not isinstance(sid, str) or not SID_RE.match(sid):
            raise ValueError("bad session id")
        with self.lock:
            return self.sessions.setdefault(sid, Session(sid, self.runs))

    def client(self):
        with self.lock:
            if self._client is None:
                self._client = self.client_factory()
            return self._client


def make_anthropic_client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Export it in the shell that runs this app.")
    try:
        import anthropic
    except ImportError as err:
        raise RuntimeError("The 'anthropic' package is not installed: pip install anthropic") from err
    return anthropic.Anthropic()


def make_handler(app: App):
    class H(BaseHTTPRequestHandler):
        server_version = "MuseGM/0.1"

        def log_message(self, *a):
            pass

        def _host_ok(self):
            host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
            return host in ("127.0.0.1", "localhost", "::1")

        def _send(self, code, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype.startswith("text") or "json" in ctype else ""))
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if not self._host_ok():
                return self._send(403, {"error": "bad host"})
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            try:
                if u.path == "/":
                    return self._send(200, (HERE / "static" / "index.html").read_bytes(), "text/html")
                if u.path == "/api/state":
                    return self._send(200, app.session(q.get("session")).public())
                if u.path == "/api/artifact":
                    sess = app.session(q.get("session"))
                    name = q.get("name", "")
                    if not re.fullmatch(r"[a-z_]+_v\d+\.md", name):
                        return self._send(400, {"error": "bad name"})
                    p = sess.dir / name
                    if not p.is_file():
                        return self._send(404, {"error": "not found"})
                    return self._send(200, p.read_bytes(), "text/markdown")
            except ValueError as err:
                return self._send(400, {"error": str(err)})
            self._send(404, {"error": "not found"})

        def do_POST(self):
            if not self._host_ok():
                return self._send(403, {"error": "bad host"})
            if self.headers.get("X-MUSE") != "1" or "application/json" not in (self.headers.get("Content-Type") or ""):
                return self._send(403, {"error": "missing headers"})
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                return self._send(413, {"error": "body too large"})
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
                sess = app.session(body.get("session"))
            except (ValueError, TypeError) as err:
                return self._send(400, {"error": f"bad request: {err}"})
            path = urlparse(self.path).path
            with sess.lock:
                try:
                    if path == "/api/chat":
                        text = str(body.get("message", "")).strip()
                        if not text or len(text) > 20_000:
                            return self._send(400, {"error": "message empty or too long"})
                        chat_turn(sess, app.engine, app.client(), app.model, text)
                    elif path == "/api/approve":
                        approve(sess, str(body.get("row_id", "")))
                    elif path == "/api/reset":
                        with app.lock:
                            app.sessions.pop(sess.sid, None)
                        return self._send(200, {"ok": True})
                    else:
                        return self._send(404, {"error": "not found"})
                except KeyError as err:
                    return self._send(400, {"error": str(err)})
                except Exception as err:  # API or runtime failure: report, never leak secrets
                    msg = f"{type(err).__name__}: {err}"
                    if os.environ.get("ANTHROPIC_API_KEY"):
                        msg = msg.replace(os.environ["ANTHROPIC_API_KEY"], "[redacted]")
                    sess.ui.append({"type": "system", "text": f"Error: {msg}"})
                    return self._send(500, {"error": msg, **sess.public()})
            self._send(200, sess.public())

    return H


def serve(app, host="127.0.0.1", port=8484):
    srv = ThreadingHTTPServer((host, port), make_handler(app))
    return srv


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--port", type=int, default=8484)
    ap.add_argument("--host", default="127.0.0.1", help="keep 127.0.0.1 unless you understand the exposure")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    a = ap.parse_args()
    app = App(make_anthropic_client, a.model)
    srv = serve(app, a.host, a.port)
    print(f"MUSE-GM chat on http://{a.host}:{a.port}  model={a.model}  runs -> {app.runs}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
