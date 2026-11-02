#!/usr/bin/env bash
# Template: copy into <example>/video/ and set NAME. Rebuilds diagrams → frames → 1080p MP4.
set -euo pipefail
NAME=notification-mock
here="$(cd "$(dirname "$0")" && pwd)"; kit="$HOME/.claude/skills/slide-video-kit/scripts"
python3 "$here/diagrams.py"
"$HOME/Projects/design-room/pdf-kit/.venv/bin/python" "$kit/render_slides.py" --html "$here/video-slides.html" --prefix v \
  --svg-dir "$here/../svg" --css-dir "$here" --out "$here/frames" >/dev/null 2>&1
[[ ${1:-} == --frames ]] && exit 0
"$kit/build_video.py" "$here/$NAME.script.md" --frames "$here/frames" --gap-scale 1.3 --max-minutes 30
