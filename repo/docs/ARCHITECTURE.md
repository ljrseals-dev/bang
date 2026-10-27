# Architecture

## Engine (`muse_gm/engine.py`)
- **Variables** (`data/variables.json`): eight nominal variables with codes `1..n` and labels, like an SPSS Variable View. Their order defines the axes of the surface array.
- **Tables** (`data/rubric.json`): named 0-1 lookup tables whose axes are variables (for example `node_era`). Each is a judgment encoded by the author.
- **Components**: six scores built from tables. `linear` is a weighted sum; `geomean` is a weighted product, used for causal integrity so one implausible anchor drags the whole chain down.
- **Profiles**: weight sets over components. `master` is Module 2 of the Master Prompt (.30/.20/.15/.15/.10/.10); `equal` is for sensitivity checks.
- **Enumeration**: tables are broadcast onto an 8-D float array (no row-per-case table), scored once, ranked with a deterministic tie-break. `--select` restricts the space before scoring (exhaustive within it). `--distinct` keeps the best configuration per core.
- **Manifest**: command, SHA-256 of both config files, weights, selection, versions, `evidence_status`.

## App (`muse_gm/app.py`)
- Tools exposed to the model: `list_variables`, `run_surface`, `save_artifact`. There is deliberately no approve tool.
- Session state (stage, approved configuration, saved artifacts) is injected into the system prompt every turn, so the model sees the true status, not what the chat claims.
- Approval is `POST /api/approve` from the UI button. Artifacts are versioned and hashed under `runs/<session>/`.
- Transport: stdlib `http.server`, 127.0.0.1 only, Host check, `X-MUSE` header required on POST (blocks cross-site form posts).

## Why gates live in code
Prompt rules are probabilistic; harness rules are not. The approval and script gates are enforced by the server, in line with the Playbook's principle that a contract without enforcement is a suggestion.
