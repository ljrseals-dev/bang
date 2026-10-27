#!/usr/bin/env bash
# Usage: ./merge_into_bang.sh /path/to/this/zip/repo /path/to/your/clone/of/bang
# Keeps everything you have: files are moved with git mv (history kept), nothing is overwritten,
# your LICENSE and the "Terrible 3" folder are never touched.
set -euo pipefail
SRC="$(cd "$1" && pwd)"; DST="$(cd "$2" && pwd)"
[ -d "$DST/.git" ]        || { echo "error: $DST is not a git clone"; exit 1; }
[ -f "$SRC/pyproject.toml" ] || { echo "error: $SRC is not the MUSE-GM repo folder"; exit 1; }
cd "$DST"
[ -z "$(git status --porcelain)" ] || { echo "error: commit or stash your changes first"; exit 1; }
mv_keep() {  # mv_keep <from> <to>: git mv if the source exists and the target does not
  if [ -e "$1" ] && [ ! -e "$2" ]; then mkdir -p "$(dirname "$2")"; git mv "$1" "$2"; echo "moved  $1 -> $2"; fi
}
# 1. your files go to their new homes (history preserved)
mv_keep failures.jsonl   logs/vintage-harness/failures.jsonl
mv_keep run.log.jsonl    logs/vintage-harness/run.log.jsonl
mv_keep summary.json     logs/vintage-harness/summary.json
mv_keep muse_gm.py       prototype/muse_gm_v0.py
mv_keep muse_surface.py  prototype/muse_surface_v0.py
mv_keep surface.json     results/prototype/surface_v0.json
mv_keep README.md        docs/source/README_original.md      # your teaser + paper as it was
# 2. add the new tree without overwriting anything that already exists
( cd "$SRC" && find . -type f -not -path "./.git/*" -not -name "*.pyc" ) | while IFS= read -r rel; do
  if [ -e "$DST/$rel" ]; then echo "kept   $rel (already exists)"; else mkdir -p "$DST/$(dirname "$rel")"; cp "$SRC/$rel" "$DST/$rel"; fi
done
find . -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
git add -A
echo; git status --short | head -80
echo; echo "Next: python -m unittest discover tests && git commit -m 'MUSE-GM package, paper, maths, logs' && git push"
