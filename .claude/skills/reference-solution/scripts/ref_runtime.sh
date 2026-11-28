#!/usr/bin/env bash
# ref_runtime.sh — one place that resolves every tool the reference-solution pipeline needs (issue #5, Workstream 1).
# Source it (`. ref_runtime.sh`) to get the variables, or run `ref_runtime.sh doctor` for a JSON readiness report.
#   REPO   repository root                         KIT   .claude/skills/reference-solution/kit
#   PY     pdf-kit venv python (Playwright, lxml)  TTS   Kokoro venv python ($KOKORO_PYTHON, default ~/.cache/kokoro-tts/.venv/bin/python)
#   C4     .claude/skills/c4-structurizr           AUDIO the audio-version skill's scripts ($AUDIO_SKILL_DIR)
# kit/paths.py resolves the same values for Python callers; keep the two in step.
_here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export REPO="${REPO:-$(cd "$_here/../../../.." && pwd)}"
export KIT="$REPO/.claude/skills/reference-solution/kit"
export C4="$REPO/.claude/skills/c4-structurizr"
export PY="${REF_PYTHON:-$REPO/pdf-kit/.venv/bin/python}"
export TTS="${KOKORO_PYTHON:-$HOME/.cache/kokoro-tts/.venv/bin/python}"
if [[ -n "${AUDIO_SKILL_DIR:-}" ]]; then export AUDIO="$AUDIO_SKILL_DIR"
elif [[ -d "$REPO/.claude/skills/audio-version/scripts" ]]; then export AUDIO="$REPO/.claude/skills/audio-version/scripts"
else export AUDIO="$HOME/.claude/skills/audio-version/scripts"; fi

doctor() {
  ok() { [[ -e "$1" ]] && echo true || echo false; }
  have() { command -v "$1" >/dev/null 2>&1 && echo true || echo false; }
  docker_ok=false; docker info >/dev/null 2>&1 && docker_ok=true
  cat <<JSON
{"repo": "$REPO", "kit": $(ok "$KIT/dsl.py"), "pdf_kit_python": $(ok "$PY"), "kokoro_python": $(ok "$TTS"),
 "audio_skill": $(ok "$AUDIO/build_audio.py"), "c4_structurizr": $(ok "$C4/scripts/render_c4.py"), "docker": $docker_ok,
 "ffmpeg": $(have ffmpeg), "node": $(have node),
 "needs": {"diagrams": ["pdf_kit_python", "c4_structurizr", "docker"], "deck": ["pdf_kit_python", "node"],
           "markdown": ["node"], "video": ["pdf_kit_python", "kokoro_python", "audio_skill", "ffmpeg"], "publish": ["pdf_kit_python"]}}
JSON
}
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  case "${1:-doctor}" in
    doctor) doctor ;;
    env) echo "REPO=$REPO"; echo "KIT=$KIT"; echo "C4=$C4"; echo "PY=$PY"; echo "TTS=$TTS"; echo "AUDIO=$AUDIO" ;;
    *) echo "usage: ref_runtime.sh [doctor|env]  (or source it)" >&2; exit 2 ;;
  esac
fi
