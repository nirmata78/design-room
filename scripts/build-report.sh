#!/usr/bin/env bash
# Render a session's report.md to report.pdf.
#
#   scripts/build-report.sh sessions/2026-10-21-SD-08-news-feed
#   scripts/build-report.sh --all          # every session that has report.md but no up-to-date PDF
#   scripts/build-report.sh path/to/any-report.md   # render a single file next to itself
#
# Needs pandoc. Prints to PDF with the first engine it finds:
#   1. a Chromium-family browser, headless (Chrome · Chromium · Edge · Brave)   ← best output
#   2. weasyprint
#   3. pandoc's LaTeX path (xelatex / lualatex)                                ← plainer output
# Force one with REPORT_ENGINE=browser|weasyprint|latex.
# The PDF lands next to report.md. Both are under sessions/, which is gitignored.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CSS="$ROOT/templates/report.css"

die() { echo "build-report: $*" >&2; exit 1; }
command -v pandoc >/dev/null || die "pandoc is required (https://pandoc.org/installing.html)"

find_browser() {
  local c
  for c in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
    google-chrome google-chrome-stable chromium chromium-browser microsoft-edge brave-browser; do
    if [[ -x "$c" ]]; then echo "$c"; return; fi
    if command -v "$c" >/dev/null 2>&1; then command -v "$c"; return; fi
  done
}

build_one() {
  local dir md html pdf browser base
  if [[ -f "$1" && "$1" == *.md ]]; then
    dir="$(dirname "$1")"; base="$(basename "$1" .md)"; md="$1"
  else
    dir="${1%/}"; base="report"; md="$dir/report.md"
  fi
  html="$dir/.$base.html"; pdf="$dir/$base.pdf"
  [[ -f "$md" ]] || die "no report.md in $dir"

  local want="${REPORT_ENGINE:-auto}" ws=""
  browser=""; [[ "$want" == auto || "$want" == browser ]] && browser="$(find_browser || true)"
  [[ "$want" == auto || "$want" == weasyprint ]] && command -v weasyprint >/dev/null && ws=1
  [[ "$want" == browser && -z "$browser" ]] && die "REPORT_ENGINE=browser but no Chromium-family browser found"
  if [[ -n "$browser" || -n "$ws" ]]; then
    pandoc "$md" --standalone --embed-resources --css "$CSS" \
      --metadata pagetitle="design-room report" --from markdown+pipe_tables+smart \
      -o "$html"
    if [[ -n "$browser" ]]; then
      "$browser" --headless=new --disable-gpu --no-pdf-header-footer \
        --print-to-pdf="$pdf" "file://$(cd "$dir" && pwd)/.$base.html" >/dev/null 2>&1 \
        || "$browser" --headless --disable-gpu --print-to-pdf-no-header \
        --print-to-pdf="$pdf" "file://$(cd "$dir" && pwd)/.$base.html" >/dev/null 2>&1
      engine="headless browser"
    else
      weasyprint "$html" "$pdf"; engine="weasyprint"
    fi
    rm -f "$html"
  else
    local tex=""
    for e in xelatex lualatex; do command -v "$e" >/dev/null && { tex="$e"; break; }; done
    [[ -n "$tex" ]] || die "no PDF engine found — install Chrome/Chromium, weasyprint, or a TeX distribution"
    # Pick a system font with wide Unicode coverage (★ → ≈ ·); Latin Modern lacks several.
    local font=""
    if [[ -f "/Library/Fonts/Arial Unicode.ttf" || -f "/System/Library/Fonts/Supplemental/Arial Unicode.ttf" ]]; then
      font="Arial Unicode MS"
    elif command -v fc-list >/dev/null; then
      for f in "DejaVu Sans" "Noto Sans" "Liberation Sans"; do
        fc-list | grep -q "$f" && { font="$f"; break; }
      done
    fi
    pandoc "$md" -o "$pdf" --pdf-engine="$tex" -V geometry:margin=0.8in -V fontsize=10pt \
      -V colorlinks=true ${font:+-V mainfont="$font"} 2>&1 \
      | grep -vE "Missing character|Underfull|Overfull|^\[WARNING\]" || true
    engine="$tex"
  fi

  [[ -s "$pdf" ]] || die "PDF was not produced for $dir"
  echo "✓ $pdf  ($engine)"
}

[[ $# -ge 1 ]] || die "usage: $0 <session-dir> | --all"
if [[ "$1" == "--all" ]]; then
  shopt -s nullglob
  for d in "$ROOT"/sessions/*/; do
    [[ -f "$d/report.md" ]] || continue
    [[ -f "$d/report.pdf" && "$d/report.pdf" -nt "$d/report.md" ]] && continue
    build_one "$d"
  done
else
  build_one "$1"
fi
