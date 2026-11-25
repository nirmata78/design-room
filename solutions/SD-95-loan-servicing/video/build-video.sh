#!/usr/bin/env bash
# Rebuild the reference-solution video (1080p). THEORY FIRST (2026-11-25): the theory chapter is generated, layout-gated and rendered
# before anything else, so a defect in the vocabulary slides fails in minutes, not after the design chapters.
#   build-video.sh --theory   theory chapter only: gate + frames (+ a theory MP4 when --theory-video)
#   build-video.sh --frames   everything up to the frames
#   build-video.sh            sources -> slides -> frames -> <stem>.mp4 (+ .srt and .vtt beside it)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; kit="$HOME/.claude/skills/slide-video-kit/scripts"; root="$HOME/Projects/design-room"
PY="$root/pdf-kit/.venv/bin/python"; TTS="$HOME/.cache/kokoro-tts/.venv/bin/python"
stem="$(python3 -c "import re,sys;print(re.search(r\"stem=['\\\"]([^'\\\"]+)\", open(sys.argv[1]).read()).group(1))" "$here/src/gen.py")"
[[ -f "$here/src/stack.py" ]] && python3 "$here/src/stack.py" sync
python3 "$here/diagrams.py" >/dev/null
gate() {   # $1 html  $2 report
  lc=0; "$PY" "$kit/check_layout.py" --html "$1" --svg-dir "$here/svg" --css-dir "$here" > "$2" || lc=$?
  tail -1 "$2"; [[ $lc == 0 || ${LAYOUT_CHECK:-} == warn ]] || { echo "layout check failed: see $2"; exit 1; }
}
# 1 · theory pass
ONLY_CHAPTER=3 python3 "$here/src/gen.py" >/dev/null
gate "$here/video-theory.html" "$here/layout-report-theory.txt"
rm -rf "$here/frames-theory"
"$PY" "$kit/render_slides.py" --html "$here/video-theory.html" --prefix v --svg-dir "$here/svg" --css-dir "$here" --out "$here/frames-theory" >/dev/null 2>&1
if [[ ${1:-} == --theory ]]; then
  [[ ${2:-} == --theory-video ]] && "$TTS" "$root/theory/video/build_cached.py" "$here/$stem-theory.script.md" --frames "$here/frames-theory" \
    --out "$here/$stem-theory.mp4" --dissolve 0.3 --chapter-gap 0 --captions sidecar --reveal-fade 0.4 --max-minutes 60
  exit 0
fi
# 2 · the whole deck
python3 "$here/src/gen.py"
gate "$here/video-slides.html" "$here/layout-report.txt"
rm -rf "$here/frames"
"$PY" "$kit/render_slides.py" --html "$here/video-slides.html" --prefix v --svg-dir "$here/svg" --css-dir "$here" --out "$here/frames" >/dev/null 2>&1
[[ ${1:-} == --frames ]] && exit 0
"$TTS" "$root/theory/video/build_cached.py" "$here/$stem.script.md" --frames "$here/frames" --out "$here/$stem.mp4" \
  --dissolve 0.3 --chapter-gap 0 --captions sidecar --reveal-fade 0.4 --max-minutes 180
