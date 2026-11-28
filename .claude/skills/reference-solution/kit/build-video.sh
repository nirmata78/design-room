#!/usr/bin/env bash
# build-video.sh — copy into solutions/SD-NN-<slug>/video/. The one entry point for a solution's build; every stage is the
# kit's ref_solution.py (issue #5), so the build is the same for Claude CLI, Gemini/Antigravity, Grok and a human.
#   build-video.sh                 diagrams → deck (layout gate) → markdown (lint) → video → publish → clean
#   build-video.sh --no-video      stop after the Markdown
#   build-video.sh <stage>         one stage: diagrams | deck | markdown | video | publish | clean
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; sol="$(dirname "$here")"
runner="$(cd "$here/../../.." && pwd)/.claude/skills/reference-solution/scripts/ref_solution.py"
case "${1:-all}" in
  --no-video) exec python3 "$runner" all "$sol" --no-video ;;
  all|"")     exec python3 "$runner" all "$sol" ;;
  *)          exec python3 "$runner" "$1" "$sol" "${@:2}" ;;
esac
