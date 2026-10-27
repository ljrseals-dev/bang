# Changelog

## 0.1.0
- Engine: exhaustive enumeration of 4,445,280 combinations (8 variables), six scored components, `master` and `equal` profiles.
- Config-driven variables (value labels) and rubric tables, with fail-closed validation.
- CLI: `variables`, `check`, `run` (`--select`, `--distinct`, `--out`), `sensitivity`; CSV, JSONL, manifest and SPSS syntax export.
- Chat app: local web UI, Claude tool loop, human-click approval gate, artifact gate.
- 26 tests (engine and app, fake Claude client).
