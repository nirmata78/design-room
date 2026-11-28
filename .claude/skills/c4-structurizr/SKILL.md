---
name: c4-structurizr
description: Local-first, containerized C4 architecture diagramming skill using Structurizr DSL, Google DESIGN-TOKENS.md styling, 1080p viewport normalization, and Mode A progressive cross-dissolve video generation. Use whenever designing, drawing, updating, or animating C4 System Context, Container, Component, or Version-Delta architecture diagrams for Markdown docs or 1080p video slides. Compatible with Claude CLI, Antigravity (Gemini), and Grok.
---

# `c4-structurizr` — Containerized Structurizr C4 Renderer & Progressive Video Skill

Produce crisp, `1920×1080`-ready C4 vector diagrams (`.svg` + optional `@2x.png`) and progressive-reveal video clips (`.mp4`) from **one** Structurizr `.dsl` workspace—with **zero host Java/Playwright dependencies** (runs inside a reusable local Docker container `local/structurizr-c4:playwright`).

## Multi-Agent Compatibility
- **Claude CLI:** Discovered natively at `.claude/skills/c4-structurizr/SKILL.md`.
- **Antigravity (Gemini) / Gemini CLI:** Discovered via `.agents/skills/c4-structurizr` symlink pointing to `.claude/skills/c4-structurizr`.
- **Grok (xAI API / CLI):** Load `SKILL.md` as developer/system instructions and pass `schemas/tool-definition.json` as OpenAI/xAI-compatible `tools`.

## Core Invariants (Non-Negotiable)

1. **Single DSL, Batch Export:** Put all views for a system in **one** `workspace.dsl` and always `!include` `resources/c4-google-tokens.dsl`. Never invoke Structurizr in a per-view loop.
2. **Strict C4 Hierarchy:** `person` and `softwareSystem` live ONLY at top-level `model { ... }`; `container` ONLY inside `softwareSystem`; `component` ONLY inside `container`. Always set `!identifiers hierarchical`.
3. **1080p Legibility & Organic Sizing:** Keep box descriptions `<= 40` chars. `c4-google-tokens.dsl` sets `metadata false` so JointJS wraps titles and descriptions cleanly with zero post-hoc text inflation or overflow.
4. **Google Design Token Hygiene:** Zero `Tahoma`, `Helvetica`, `Arial`, `DejaVu`, or purple/orange/teal hex codes. Use only semantic tags from `c4-google-tokens.dsl`:
   - Elements: `Person`, `Software System`, `Container`, `Database`, `Queue`, `Cache`, `Component`, `External`, `New`, `Breaks`, `Fix`.
   - Relationships: `HTTPS`/`Sync` (solid `#202124`), `Event`/`Async` (dashed `#1967D2`), `File`/`Batch` (dashed `#5F6368`), `Response` (dashed `#188038`), `Internal` (solid `#5F6368`).
5. **Mode A Progressive Reveal (`0.0 px` jitter):** Export **one** master `.svg` per view with `data-k` attributes and a `.steps.json` reveal plan. Unrevealed elements stay `visibility: hidden` (or `--ghost 0.10` if faint upcoming silhouettes are desired) and cross-dissolve (`0.35s`) in video rendering.

## Slot Topology Budgets

| Slot | Target `1080p` Box | Node Budget | Recommended `autoLayout` |
| :--- | :--- | :--- | :--- |
| `composite` | `1704 × 480` (above/below prose) | `3–6` nodes | `autoLayout lr 180 100` (max 2 parallel vertical rows) |
| `full` | `1704 × 780` (full diagram slide) | `5–11` nodes | `autoLayout lr 180 110` for pipelines; `tb 160 110` for wide fan-out |
| `split` | `820 × 740` (half-slide) | `3–6` nodes | `autoLayout tb 150 110` |

## 4-Step Closed-Loop Agent Workflow

1. **Ensure Warm Container:**
   ```bash
   scripts/c4_runtime.sh ensure
   ```
2. **Author `workspace.dsl` + optional `views.json`:**
   - Keep box descriptions crisp (`<= 40` chars).
   - Define ordered `steps` in `views.json` matching your narration beats (can be edited later with zero Docker re-export).
3. **Validate, Export, and Normalize (Single Command):**
   ```bash
   python3 scripts/render_c4.py --dsl path/to/workspace.dsl --spec path/to/views.json --out path/to/svg --png
   ```
   - Exit `0`: All views passed DSL validation, font hygiene, and `1080p` legibility gate.
   - Exit `2`: DSL syntax error — fix the reported line and re-run.
   - Exit `3`: Legibility/token gate failed — follow the returned `remedy` (flip `lr ↔ tb`, shorten descriptions, or split >10 nodes).
4. **Render Progressive Video (Mode A — Optional Standalone Preview):**
   ```bash
   python3 scripts/progressive_video.py --svg out/02-container-view.svg --title "L2 · Container Architecture" --out out/02-container-view.mp4 [--ghost 0.10]
   ```
   For full narrated decks in `design-room`, simply drop the normalized `.svg`, `.steps.json`, and `.meta.json` into `video/svg/` — `render_slides.py` and `build_cached.py` consume Mode A natively.
