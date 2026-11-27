# `c4-structurizr`

Containerized, local-first C4 architecture diagramming skill for AI agents (Claude Code, Gemini Antigravity / CLI, and Grok). Converts **Structurizr DSL** workspaces into `1920×1080`-ready normalized SVGs, `@2x` PNGs, and zero-jitter progressive MP4 videos.

## Quickstart

```bash
# 1. Pull/build font-hermetic Playwright image once and start warm local daemon
.claude/skills/c4-structurizr/scripts/c4_runtime.sh ensure
.claude/skills/c4-structurizr/scripts/c4_runtime.sh healthcheck

# 2. Validate, export, normalize, and gate-check a workspace
pdf-kit/.venv/bin/python .claude/skills/c4-structurizr/scripts/render_c4.py \
  --dsl .claude/skills/c4-structurizr/examples/bakeoff/workspace.dsl \
  --spec .claude/skills/c4-structurizr/examples/bakeoff/views.json \
  --out .claude/skills/c4-structurizr/examples/bakeoff/out/svg \
  --png --animation
```

## Components

| Path | Responsibility |
| :--- | :--- |
| `SKILL.md` | Agent instructions, C4 hierarchy rules, slot budgets, and 4-step workflow |
| `docker/Dockerfile.c4` | Thin layer baking offline Google OFL fonts (`Inter`, `Plus Jakarta Sans`, `Roboto Mono`) onto `structurizr/structurizr:preview` |
| `resources/c4-google-tokens.dsl` | Shared Structurizr `styles` block adhering to `DESIGN-TOKENS.md` |
| `scripts/c4_runtime.sh` | Manages `local/structurizr-c4:playwright` image and warm `structurizr-c4-daemon` (`--shm-size=1gb`) |
| `scripts/svg_normalizer.py` | `lxml` AST normalizer: strips footers, rewrites fonts, tight-crops `viewBox`, enforces `>= 18px @ 1080p`, injects `data-k` & `NEW` pills |
| `scripts/render_c4.py` | End-to-end CLI orchestrator (`validate` → `export` → `normalize` → `@2x.png`) |
| `scripts/progressive_video.py` | Renders `10–15s` `1920×1080 @ 30fps` MP4s in Mode A (Cross-Dissolve), Mode B (Native Animation), Mode C (Directional Live-Draw), plus `2×2` comparison grids |
| `schemas/tool-definition.json` | JSON Schema for xAI Grok / OpenAI / Anthropic function-calling integration |

## Tests

```bash
pdf-kit/.venv/bin/pytest .claude/skills/c4-structurizr/tests/ -v
```
