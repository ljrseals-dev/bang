# Logs

Run records kept for audit. None of these are measurements of audio or story quality.

## `vintage-harness/`
Dry-run records from the Vintage Compressor Reference harness audit (a separate project that shares the Brute Genius tooling).
- `run.log.jsonl`: events from the dry-run stage (config hash, plan, limits, run end).
- `failures.jsonl`: the refused run manifest (`MISSING_REFERENCE_EVIDENCE`) and the cost-ceiling policy blocker (`POLICY_COST_CEILING_CONFLICT`).
- `summary.json`: status `dry_run_only_no_measurements`, `submission_status: none`, known coverage gaps, and the order of work needed for a real submission.

Read them as an honest record that nothing was submitted, not as results.

## MUSE-GM runs
Run manifests and ranked results live in `../results/` (`baseline/` and `prototype/`).
