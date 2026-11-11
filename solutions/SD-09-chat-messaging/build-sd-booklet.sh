#!/usr/bin/env bash
# build-sd-booklet.sh <Name> [--no-diagrams]
#   Renders diagrams/<prefix>-*.puml -> .svg -> .pdf (prefix = lower-cased "SD-09" -> "sd09"),
#   converts the video's video/svg/*.svg -> diagrams/video-*.pdf so booklet and video share one drawing,
#   then builds <Name>.md -> <Name>.pdf with sd-preamble.tex + sd-callouts.lua.
# PlantUML exits 0 on most errors and draws an error image instead, so the SVG is grepped.
set -uo pipefail
cd "$(dirname "$0")"
name=${1:?usage: build-sd-booklet.sh <Name> [--no-diagrams]}
prefix=$(echo "$name" | cut -d_ -f1 | tr -d '-' | tr 'A-Z' 'a-z')
fail=0
if [[ "${2:-}" != "--no-diagrams" ]]; then
  for f in diagrams/$prefix-*.puml; do
    [[ -e "$f" ]] || continue
    b=${f%.puml}
    plantuml -tsvg "$f" || fail=1
    if grep -qiE "syntax error|cannot be parsed|An error has occured|cannot include|Please use CSS style|deprecated" "$b.svg"; then
      echo "DIAGRAM ERROR: $b"; fail=1; continue
    fi
    rsvg-convert -f pdf -o "$b.pdf" "$b.svg" || { echo "RSVG FAILED: $b"; fail=1; continue; }
    w=$(grep -o 'width="[0-9]*' "$b.svg" | head -1 | tr -dc 0-9)
    if [[ -n "$w" ]] && (( w > 1100 )); then echo "WIDE ($w px): $b"; fi
  done
  for f in video/svg/*.svg; do
    [[ -e "$f" ]] || continue
    rsvg-convert -f pdf -o "diagrams/video-$(basename "${f%.svg}").pdf" "$f" || fail=1
  done
fi
(( fail )) && { echo "diagram errors, stopping"; exit 1; }
# every referenced figure must exist
missing=0
while read -r p; do
  [[ -f "$p" ]] || { echo "MISSING FIGURE: $p"; missing=1; }
done < <(grep -o 'diagrams/[a-z0-9-]*\.pdf' "$name.md" | sort -u)
(( missing )) && exit 1
# unbalanced ::: fences swallow the rest of the document and still build
n=$(grep -c '^:::' "$name.md"); (( n % 2 )) && { echo "UNBALANCED ::: fences ($n)"; exit 1; }
# keep pandoc's warnings visible: a glyph the font lacks vanishes from the PDF with only a warning
# build to a fresh file so a failed build can never be mistaken for a stale PDF
rm -f "$name.pdf"
log=$(mktemp)
pandoc "$name.md" -o "$name.pdf" --pdf-engine=xelatex -H sd-preamble.tex \
  --lua-filter sd-callouts.lua --syntax-highlighting=tango >"$log" 2>&1; rc=$?
grep -vE "Underfull|Overfull|hbox|vbox" "$log" | sort | uniq -c; rm -f "$log"
(( rc == 0 )) && [[ -f "$name.pdf" ]] || { echo "PANDOC FAILED (exit $rc)"; exit 1; }
pdfinfo "$name.pdf" | awk '/^Pages:/{print "pages", $2}'
