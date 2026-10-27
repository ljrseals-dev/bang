# MUSE-GM Decision Surface

Exhaustive enumeration of a factorial story space. Every combination is scored; nothing is sampled.
Requires Python 3.9+ and numpy.

## Files
- `muse_gm.py` - the program
- `config/variables.json` - the "Variable View": 8 nominal variables with value labels (codes 1..n)
- `config/rubric.json` - lookup tables (0-1), component formulas, weight profiles (`master`, `equal`)
- `test_muse_gm.py` - 16 tests (`python -m unittest -v test_muse_gm`)

## Commands
```
python muse_gm.py variables --values          # Variable View with value labels
python muse_gm.py check                       # validate config, size, hashes
python muse_gm.py run --top 5                 # all 4,445,280 cases, top 5 per effect target
python muse_gm.py run --effect pivot --distinct node,era,economy --top 5
python muse_gm.py run --out runs/001          # + results.jsonl, manifest.json, CSVs, SPSS syntax
python muse_gm.py run --select node=Harlem --select era=3 --select economy=policy --effect pivot
python muse_gm.py sensitivity                 # master vs equal weights, +/-0.05 one-at-a-time shifts
```
`--select VAR=VAL|VAL` is SPSS SELECT IF: restrict to a subspace (code number or unique label text),
still exhaustive inside it. `--distinct` collapses near-duplicates to the best config per core.

## What the numbers are
The tables in `rubric.json` are encoded judgments (historical plausibility, drawability, etc.), not measurements.
Every manifest records `evidence_status: rubric_encoded_judgments_not_measured_data`, the SHA-256 of both
config files, the profile and weights, and the selection. Change a table, and the hash and ranking change.

## SPSS
`--out` writes `surface_top.csv` (numeric codes), `surface_top_labeled.csv`, and `surface_top.sps`
(GET DATA + VARIABLE LABELS + VALUE LABELS). The .sps has not been run in SPSS; check the file path inside it.

## Fail-closed behavior
Non-finite or out-of-range table values, wrong shapes, weights that do not sum to 1, unknown keys/tables,
and spaces above 10^9 combinations stop the run with `CONFIG ERROR` (exit code 2).

## Extending
Add a variable in `variables.json`, add tables whose axes include it, and reference them in a component's
`terms`. Components are `linear` (weighted sum) or `geomean` (weighted product); term weights sum to 1.
Penalty terms (negative weights) are not supported yet; the current objective is a convex combination.
Memory is ~64 bytes per combination; stage large spaces with `--select` rather than enumerating them flat.
