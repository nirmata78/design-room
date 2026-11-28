# `c4-structurizr`

Containerized, local-first C4 architecture diagramming skill for **Claude CLI**, **Antigravity (Gemini)**, and **Grok**. Converts **Structurizr DSL** workspaces into `1920×1080`-ready normalized SVGs, `@2x` PNGs, and **Mode A** progressive cross-dissolve MP4 videos (`visibility: hidden` + `0.35s` fade, optional `--ghost 0.0..1.0`).

## Multi-Agent Discovery
- **Claude CLI:** `.claude/skills/c4-structurizr/SKILL.md`
- **Antigravity (Gemini) / Gemini CLI:** `.agents/skills/c4-structurizr` (symlinked to `.claude/skills/c4-structurizr`)
- **Grok (xAI API / CLI):** `schemas/tool-definition.json` (OpenAI/xAI `tools` JSON array) + `SKILL.md`

## Quickstart

```bash
# 1. Pull/build font-hermetic Playwright image once and start warm local daemon
.claude/skills/c4-structurizr/scripts/c4_runtime.sh ensure
.claude/skills/c4-structurizr/scripts/c4_runtime.sh healthcheck

# 2. Validate, export, normalize, and gate-check a workspace
pdf-kit/.venv/bin/python .claude/skills/c4-structurizr/scripts/render_c4.py \
  --dsl path/to/workspace.dsl \
  --spec path/to/views.json \
  --out path/to/svg \
  --png

# 3. Render a standalone Mode A progressive video (optional --ghost 0.10)
pdf-kit/.venv/bin/python .claude/skills/c4-structurizr/scripts/progressive_video.py \
  --svg path/to/svg/c4-context.svg \
  --title "L1 · System Context" \
  --out path/to/c4-context.mp4
```

## Components

| Path | Responsibility |
| :--- | :--- |
| `SKILL.md` | Agent instructions, C4 hierarchy rules, slot budgets, and 4-step workflow |
| `docker/Dockerfile.c4` | Thin layer baking offline Google OFL fonts (`Inter`, `Plus Jakarta Sans`, `Roboto Mono`) onto `structurizr/structurizr:preview` |
| `resources/c4-google-tokens.dsl` | Shared Structurizr `styles` block adhering to `DESIGN-TOKENS.md` |
| `scripts/c4_runtime.sh` | Manages `local/structurizr-c4:playwright` image and warm `structurizr-c4-daemon` (`--shm-size=1gb`) |
| `scripts/svg_normalizer.py` | `lxml` AST normalizer: strips footers, rewrites fonts, tight-crops `viewBox`, enforces legibility, injects `data-k` & `NEW` pills |
| `scripts/render_c4.py` | End-to-end CLI orchestrator (`validate` → `export` → `normalize` → `@2x.png`) |
| `scripts/progressive_video.py` | Mode A `1920×1080 @ 30fps` progressive cross-dissolve MP4 renderer (optional `--ghost`, default `0.0`) |
| `schemas/tool-definition.json` | OpenAI / xAI Grok function-calling tool definitions |

## Tests

```bash
pdf-kit/.venv/bin/pytest .claude/skills/c4-structurizr/tests/ -v
```
