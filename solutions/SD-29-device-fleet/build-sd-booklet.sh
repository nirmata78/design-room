#!/usr/bin/env bash
# build-sd-booklet.sh <Name> [--no-diagrams]
#   Renders diagrams/<prefix>-*.puml -> .svg -> .pdf (prefix = lower-cased "SD-09" -> "sd09"),
#   converts the video's video/svg/*.svg -> diagrams/video-*.pdf so booklet and video share one drawing,
#   then builds <Name>.md -> <Name>.pdf with sd-preamble.tex + sd-callouts.lua.
# PlantUML exits 0 on most errors and draws an error image instead, so the SVG is grepped.
set -uo pipefail
cd "$(dirname "$0")"
export PANGOCAIRO_BACKEND=fc FONTCONFIG_FILE="$HOME/Projects/design-room/pdf-kit/fonts/fonts.conf"   # rsvg-convert finds Inter / Plus Jakarta Sans / Roboto Mono here
name=${1:?usage: build-sd-booklet.sh <Name> [--no-diagrams]}
prefix=$(echo "$name" | cut -d_ -f1 | tr -d '-' | tr 'A-Z' 'a-z')
fail=0
# technology choices come from stack.json (one source with the video): regenerate the marked Stage 5 regions
[[ -f stack.json && -f video/src/stack.py ]] && { python3 video/src/stack.py sync || exit 1; }
if [[ "${2:-}" != "--no-diagrams" ]]; then
  for f in diagrams/$prefix-*.puml; do
    [[ -e "$f" ]] || continue
    b=${f%.puml}
    plantuml -tsvg "$f" || fail=1
    if grep -qiE "syntax error|cannot be parsed|An error has occured|cannot include|Please use CSS style|deprecated" "$b.svg"; then
      echo "DIAGRAM ERROR: $b"; fail=1; continue
    fi
    rsvg-convert -f pdf -o "$b.pdf" "$b.svg"
    w=$(grep -o 'width="[0-9]*' "$b.svg" | head -1 | tr -dc 0-9)
    (( w > 1100 )) && echo "WIDE ($w px): $b"
  done
  for f in video/svg/*.svg; do
    [[ -e "$f" ]] || continue
    rsvg-convert -f pdf -o "diagrams/video-$(basename "${f%.svg}").pdf" "$f" || fail=1
  done
fi
(( fail )) && { echo "diagram errors, stopping"; exit 1; }
# every referenced figure must exist
grep -o 'diagrams/[a-z0-9-]*\.pdf' "$name.md" | sort -u | while read -r p; do
  [[ -f "$p" ]] || echo "MISSING FIGURE: $p"
done
# unbalanced ::: fences swallow the rest of the document and still build
n=$(grep -c '^:::' "$name.md"); (( n % 2 )) && { echo "UNBALANCED ::: fences ($n)"; exit 1; }
# keep pandoc's warnings visible: a glyph the font lacks vanishes from the PDF with only a warning
# Google theme: Inter body, Plus Jakarta Sans headings and labels, Roboto Mono code; static files from pdf-kit/fonts (XeTeX cannot use variable fonts)
FONTS="$HOME/Projects/design-room/pdf-kit/fonts"
pandoc "$name.md" -o "$name.pdf" --pdf-engine=xelatex -H sd-preamble.tex \
  -V mainfont=Inter-Regular.otf -V "mainfontoptions=Path=$FONTS/,BoldFont=Inter-Bold.otf,ItalicFont=Inter-Italic.otf,BoldItalicFont=Inter-BoldItalic.otf" \
  -V sansfont=PlusJakartaSans-SemiBold.ttf -V "sansfontoptions=Path=$FONTS/google/static/,BoldFont=PlusJakartaSans-Bold.ttf" \
  -V monofont=RobotoMono-Regular.ttf -V "monofontoptions=Path=$FONTS/google/static/,BoldFont=RobotoMono-Bold.ttf,ItalicFont=RobotoMono-Italic.ttf,Scale=0.88" \
  -V linkcolor=gblueink -V urlcolor=gblueink -V toccolor=gink \
  --lua-filter sd-callouts.lua --syntax-highlighting="$HOME/Projects/design-room/pdf-kit/google.theme" 2>&1 \
  | grep -vE "Underfull|Overfull|hbox|vbox" | sort | uniq -c
pdfinfo "$name.pdf" | awk '/^Pages:/{print "pages", $2}'
