
---

## Quick start (MUSE-GM package)
```
pip install -e .            # engine only (needs numpy)
pip install -e ".[app]"     # plus the chat app (needs the anthropic package)

muse-gm variables --values
muse-gm run --top 5
muse-gm run --effect pivot --distinct node,era,economy
muse-gm run --select node=Harlem --select era=3 --out runs/001
muse-gm sensitivity

export ANTHROPIC_API_KEY=...      # your key, billed to you, never written to disk
muse-gm-app                       # http://127.0.0.1:8484  (--port, --model, env MUSE_MODEL, MUSE_RUNS)
```
Without installing: `python -m muse_gm ...` and `python -m muse_gm.app` from the repo root.

## Layout
```
muse_gm/
  engine.py            scoring engine + CLI (validation, enumeration, ranking, export)
  app.py               chat server, Claude tool loop, gates
  data/variables.json  Variable View: names, labels, value labels
  data/rubric.json     lookup tables, component formulas, weight profiles
  prompts/chatbot_system_prompt.md
  static/index.html    chat UI
tests/                 26 tests (python -m unittest discover -v tests)
docs/                  ARCHITECTURE.md, ROADMAP.md, source/ (original Master Prompt export), results/ (baseline run)
.github/workflows/     CI on Python 3.10-3.12
```

## Safety and honesty rules built in
- Fail closed: non-finite or out-of-range table values, wrong shapes, weights that do not sum to 1, unknown keys, and spaces over 10^9 stop the run.
- The approval gate is a UI button. The model cannot approve, and typing "approved" does nothing.
- `save_artifact` refuses a script until the spine, audit, characters and tonal sheet are saved.
- The app binds to 127.0.0.1, checks Host, requires a custom header on POSTs, and never echoes your key.

## Known limits
- The Claude API path has not been run against the live API; the tool loop is tested with a fake client.
- Model chat text is not filtered. Gates stop files, not words.
- The guilt, forgiveness, one-year-gap and containment ideas are in the bot's checks but are not scored by the engine yet (see `docs/ROADMAP.md`).
- The engine is standalone. It does not call the Brute Genius MCP server; it reproduces the exhaustive-enumeration idea in numpy.
- No license is included. Choose one before publishing (see `docs/ROADMAP.md`).
