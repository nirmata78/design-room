#!/usr/bin/env bash
# build-sd-booklet.sh <Name> [--no-diagrams]
#   Renders diagrams/<prefix>-*.puml -> .svg -> .pdf (prefix = lower-cased "SD-47" -> "sd47"),
#   then builds <Name>.md -> <Name>.pdf with sd-preamble.tex + sd-callouts.lua.
# PlantUML exits 0 on most errors and draws an error image instead, so the SVG is grepped.
set -uo pipefail
cd "$(dirname "$0")"
name=${1:?usage: build-sd-booklet.sh <Name> [--no-diagrams]}
prefix=$(echo "$name" | cut -d_ -f1 | tr -d '-' | tr 'A-Z' 'a-z')
fail=0
if [[ "${2:-}" != "--no-diagrams" ]]; then
  for f in diagrams/$prefix-*.puml; do
    b=${f%.puml}
    plantuml -tsvg "$f" || fail=1
    if grep -qiE "syntax error|cannot be parsed|An error has occured|cannot include|Please use CSS style|deprecated" "$b.svg"; then
      echo "DIAGRAM ERROR: $b"; fail=1; continue
    fi
    rsvg-convert -f pdf -o "$b.pdf" "$b.svg"
    w=$(grep -o 'width="[0-9]*' "$b.svg" | head -1 | tr -dc 0-9)
    (( w > 1100 )) && echo "WIDE ($w px): $b"
  done
fi
(( fail )) && { echo "diagram errors, stopping"; exit 1; }
# every referenced figure must exist
grep -o 'diagrams/[a-z0-9-]*\.pdf' "$name.md" | sort -u | while read -r p; do
  [[ -f "$p" ]] || echo "MISSING FIGURE: $p"
done
# unbalanced ::: fences swallow the rest of the document and still build
n=$(grep -c '^:::' "$name.md"); (( n % 2 )) && { echo "UNBALANCED ::: fences ($n)"; exit 1; }
pandoc "$name.md" -o "$name.pdf" --pdf-engine=xelatex -H sd-preamble.tex \
  --lua-filter sd-callouts.lua --syntax-highlighting=tango 2>&1 \
  | grep -vE "Underfull|Overfull|hbox|vbox" | sort | uniq -c
pdfinfo "$name.pdf" | awk '/^Pages:/{print "pages", $2}'
