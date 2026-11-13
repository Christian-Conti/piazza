#!/bin/sh
# Regenerate patches/0001-piazza.patch from the working tree of the nchat submodule.
# Run after editing files under nchat/ (new files are picked up too).
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/nchat"
# the patch is a diff against the pinned upstream commit; build output and the marker are ignored by git
git add -N . >/dev/null 2>&1 || true
git diff --binary > "$ROOT/patches/0001-piazza.patch"
echo "wrote patches/0001-piazza.patch ($(grep -c '^diff --git' "$ROOT/patches/0001-piazza.patch") files)"
