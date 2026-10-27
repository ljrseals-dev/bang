"""python -m unittest discover -v tests  (fake Claude client; no network, no API key)"""
import json, tempfile, threading, unittest, urllib.request, urllib.error
from types import SimpleNamespace as NS
import muse_gm.app as app_mod


def text(t): return NS(type="text", text=t)
def tool(i, name, inp): return NS(type="tool_use", id=i, name=name, input=inp)


class FakeClient:
    """Plays a scripted list of responses; records each request."""
    def __init__(self, script): self.script, self.calls = list(script), []
    @property
    def messages(self): return self
    def create(self, **kw):
        self.calls.append(kw)
        return NS(content=self.script.pop(0), stop_reason="end_turn")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = app_mod.Engine()
        self.sess = app_mod.Session("testsession1", self.tmp.name)
    def tearDown(self): self.tmp.cleanup()


class Gates(Base):
    def test_save_blocked_without_approval(self):
        res, err = app_mod.run_tool(self.sess, self.engine, "save_artifact", {"kind": "causal_spine", "content": "x"})
        self.assertTrue(err); self.assertIn("GATE", res["error"])

    def run_surface(self):
        c = FakeClient([[tool("t1", "run_surface", {"effect": "pivot", "top": 3, "select": ["node=Harlem", "era=3"]})], [text("Ranked.")]])
        app_mod.chat_turn(self.sess, self.engine, c, "m", "rank pivot for Harlem")
        return c

    def test_surface_rows_are_real_engine_output(self):
        self.run_surface()
        rec = self.sess.surfaces["S1-P1"]
        self.assertEqual(rec["config"]["node"], "Harlem")
        self.assertEqual(len(rec["rubric_sha256"]), 64)
        self.assertEqual(sum(1 for k in self.sess.surfaces if k.startswith("S1-P")), 3)

    def test_full_gate_sequence(self):
        self.run_surface()
        self.assertTrue(self.sess.stage().startswith("S2"))
        app_mod.approve(self.sess, "S1-P1")
        self.assertTrue(self.sess.stage().startswith("S3"))
        for kind in ("script",):
            res, err = app_mod.run_tool(self.sess, self.engine, "save_artifact", {"kind": kind, "content": "pages"})
            self.assertTrue(err); self.assertIn("causal_spine", res["error"])
        for kind in app_mod.SCRIPT_PREREQS:
            res, err = app_mod.run_tool(self.sess, self.engine, "save_artifact", {"kind": kind, "content": f"{kind} body"})
            self.assertFalse(err, res)
        res, err = app_mod.run_tool(self.sess, self.engine, "save_artifact", {"kind": "script", "content": "pages"})
        self.assertFalse(err); self.assertEqual(res["version"], 1)
        res, _ = app_mod.run_tool(self.sess, self.engine, "save_artifact", {"kind": "script", "content": "pages v2"})
        self.assertEqual(res["version"], 2)
        self.assertTrue((self.sess.dir / "session.json").is_file())

    def test_model_has_no_approve_tool(self):
        self.assertNotIn("approve", " ".join(t["name"] for t in app_mod.TOOLS))
        res, err = app_mod.run_tool(self.sess, self.engine, "approve_configuration", {"row_id": "S1-P1"})
        self.assertTrue(err)

    def test_approve_unknown_row(self):
        with self.assertRaises(KeyError): app_mod.approve(self.sess, "S9-X9")

    def test_bad_inputs_become_tool_errors_not_crashes(self):
        res, err = app_mod.run_tool(self.sess, self.engine, "run_surface", {"select": ["node=Atlantis"]})
        self.assertTrue(err)
        res, err = app_mod.run_tool(self.sess, self.engine, "run_surface", {"profile": "nope"})
        self.assertTrue(err)

    def test_state_block_reflects_truth_not_chat(self):
        c = FakeClient([[text("Great, approved!")]])
        app_mod.chat_turn(self.sess, self.engine, c, "m", "approved")
        self.assertIn("approved configuration: NONE", c.calls[0]["system"])


class Http(Base):
    def setUp(self):
        super().setUp()
        self.fake = FakeClient([[tool("t1", "run_surface", {"effect": "humanized", "top": 2, "select": ["node=Harlem"]})], [text("Here you go.")]])
        self.app = app_mod.App(lambda: self.fake, "m", self.tmp.name)
        self.srv = app_mod.serve(self.app, "127.0.0.1", 0)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"
    def tearDown(self): self.srv.shutdown(); self.srv.server_close(); super().tearDown()

    def post(self, path, body, headers=None, host=None):
        h = {"Content-Type": "application/json", "X-MUSE": "1"} if headers is None else headers
        if host: h = {**h, "Host": host}
        req = urllib.request.Request(self.base + path, json.dumps(body).encode(), h)
        try:
            with urllib.request.urlopen(req) as r: return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e: return e.code, json.loads(e.read())

    def test_chat_approve_flow_over_http(self):
        sid = "abcdefgh12345678"
        code, st = self.post("/api/chat", {"session": sid, "message": "rank humanized Harlem"})
        self.assertEqual(code, 200); self.assertTrue(st["stage"].startswith("S2"))
        row = next(i for i in st["ui"] if i["type"] == "surface")["rows"][0]["row_id"]
        code, st = self.post("/api/approve", {"session": sid, "row_id": row})
        self.assertEqual(code, 200); self.assertEqual(st["approved"]["row_id"], row)

    def test_security_checks(self):
        self.assertEqual(self.post("/api/chat", {"session": "abcdefgh12345678", "message": "hi"}, headers={"Content-Type": "application/json"})[0], 403)
        self.assertEqual(self.post("/api/chat", {"session": "abcdefgh12345678", "message": "hi"}, host="evil.example")[0], 403)
        self.assertEqual(self.post("/api/chat", {"session": "../etc/passwd", "message": "hi"})[0], 400)
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(self.base + "/api/artifact?session=abcdefgh12345678&name=../../x.md")
        self.assertEqual(cm.exception.code, 400)

    def test_api_failure_is_reported_not_leaked(self):
        import os
        os.environ["ANTHROPIC_API_KEY"] = "sk-secret-123"
        def boom(): raise RuntimeError("auth failed for sk-secret-123")
        self.app._client = None; self.app.client_factory = boom
        try:
            code, body = self.post("/api/chat", {"session": "zzzzzzzz12345678", "message": "hi"})
        finally: del os.environ["ANTHROPIC_API_KEY"]
        self.assertEqual(code, 500); self.assertNotIn("sk-secret-123", json.dumps(body))


if __name__ == "__main__":
    unittest.main()
