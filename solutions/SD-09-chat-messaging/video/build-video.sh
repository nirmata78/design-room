#!/usr/bin/env bash
# Rebuild the SD-09 chat mock-round video (L6 EM framing, 1080p) with the system-design-video skill.
#   video/build-video.sh            diagrams → slides → frames → chat-mock.mp4
#   video/build-video.sh --frames   stop after the frames
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; kit="$HOME/.claude/skills/slide-video-kit/scripts"
python3 "$here/diagrams.py"
"$HOME/Projects/design-room/pdf-kit/.venv/bin/python" "$kit/render_slides.py" --html "$here/video-slides.html" --prefix v \
  --svg-dir "$here/svg" --css-dir "$here" --out "$here/frames" >/dev/null 2>&1
if [[ ${1:-} == --frames ]]; then exit 0; fi
"$kit/build_video.py" "$here/chat-mock.script.md" --frames "$here/frames" --gap-scale 1.3 --max-minutes 30
