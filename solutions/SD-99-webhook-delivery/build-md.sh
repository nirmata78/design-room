#!/usr/bin/env bash
# build-md.sh <Name> — the reference design as GitHub-rendered Markdown only (no PDF; 2026-11-25).
#   diagrams/<prefix>-*.puml  → diagrams/*.svg   (PlantUML; C4 via the bundled C4 library; 0 exit is not trusted: the SVG is grepped)
#   video/svg/*.svg           → diagrams/video-*.svg   (one drawing for video and Markdown; only full-state files without .steps)
#   <Name>.md                 → md_github.py: callouts → GitHub alerts, figure links → .svg, lint
set -uo pipefail
cd "$(dirname "$0")"
name=${1:?usage: build-md.sh <Name>}
prefix=$(echo "$name" | cut -d_ -f1 | tr -d '-' | tr 'A-Z' 'a-z'); fail=0
[[ -f stack.json && -f video/src/stack.py ]] && { python3 video/src/stack.py sync || exit 1; }
mkdir -p diagrams
for f in diagrams/$prefix-*.puml; do
  [[ -e "$f" ]] || continue
  plantuml -tsvg "$f" || fail=1
  grep -qiE "syntax error|cannot be parsed|An error has occured|cannot include" "${f%.puml}.svg" && { echo "DIAGRAM ERROR: $f"; fail=1; }
done
for f in video/svg/*.svg; do [[ -e "$f" ]] && cp "$f" "diagrams/video-$(basename "$f")"; done
(( fail )) && { echo "diagram errors, stopping"; exit 1; }
python3 ./md_github.py "$name.md" --write
