#!/usr/bin/env bash
# Usage: ./merge_into_bang.sh /path/to/muse-gm-repo /path/to/your/clone/of/bang
# Non-destructive: uses git mv (history kept), keeps your README, LICENSE and "Terrible 3" untouched.
set -euo pipefail
SRC="$(cd "$1" && pwd)"; DST="$(cd "$2" && pwd)"
[ -d "$DST/.git" ] || { echo "error: $DST is not a git clone"; exit 1; }
[ -f "$SRC/pyproject.toml" ] || { echo "error: $SRC does not look like the muse-gm repo"; exit 1; }
cd "$DST"
[ -z "$(git status --porcelain)" ] || { echo "error: commit or stash your changes first"; exit 1; }
mkdir -p archive/vintage-harness-audit prototype
# 1. unrelated Vintage-harness audit files out of the root
for f in failures.jsonl run.log.jsonl summary.json; do
  [ -f "$f" ] && git mv "$f" archive/vintage-harness-audit/ || true
done
# 2. first-draft scripts out of the way (a root muse_gm.py would sit next to the muse_gm/ package)
[ -f muse_gm.py ]      && git mv muse_gm.py prototype/muse_gm_v0.py || true
[ -f muse_surface.py ] && git mv muse_surface.py prototype/muse_surface_v0.py || true
[ -f surface.json ]    && git mv surface.json prototype/surface_v0.json || true
# 3. add the package (never overwrite README.md or LICENSE)
for item in muse_gm tests docs .github pyproject.toml CHANGELOG.md .gitignore; do
  if [ -e "$item" ] && [ "$item" != docs ] && [ "$item" != .github ] && [ "$item" != tests ]; then
    echo "skip existing: $item"; continue; fi
  mkdir -p "$(dirname "$item")"; cp -R "$SRC/$item" "$(dirname "$item")/" 2>/dev/null || cp -R "$SRC/$item" .
done
[ -f pyproject.toml ] || cp "$SRC/pyproject.toml" .
[ -f CHANGELOG.md ]   || cp "$SRC/CHANGELOG.md" .
[ -f .gitignore ]     || cp "$SRC/.gitignore" .
[ -d muse_gm ]        || cp -R "$SRC/muse_gm" .
# 4. append the quick start once
if ! grep -q "Quick start (MUSE-GM package)" README.md 2>/dev/null; then cat "$SRC/docs/QUICKSTART.md" >> README.md; fi
find . -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
git add -A
git status --short
echo; echo "Review above, then: python -m unittest discover tests && git commit -m 'Restructure MUSE-GM as a package' && git push"
