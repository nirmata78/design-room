---
name: c4-structurizr
description: Local-first, containerized C4 architecture diagramming skill using Structurizr DSL, Google DESIGN-TOKENS.md styling, 1080p viewport normalization, and progressive video generation. Use whenever designing, drawing, updating, or animating C4 System Context, Container, Component, or Version-Delta architecture diagrams for Markdown docs or 1080p video slides. Compatible with Claude Code, Gemini (Antigravity / Gemini CLI), and Grok.
---

# `c4-structurizr` — Containerized Structurizr C4 Renderer & Progressive Video Skill

Produce crisp, `1920×1080`-ready C4 vector diagrams (`.svg` + optional `@2x.png`) and progressive-reveal video clips (`.mp4`) from **one** Structurizr `.dsl` workspace—with **zero host Java/Playwright dependencies** (runs inside a reusable local Docker container `local/structurizr-c4:playwright`).

## Core Invariants (Non-Negotiable)

1. **Single DSL, Batch Export:** Put all views for a system in **one** `workspace.dsl` and always `!include` `resources/c4-google-tokens.dsl`. Never invoke Structurizr in a per-view loop.
2. **Strict C4 Hierarchy:** `person` and `softwareSystem` live ONLY at top-level `model { ... }`; `container` ONLY inside `softwareSystem`; `component` ONLY inside `container`. Always set `!identifiers hierarchical`.
3. **1080p Legibility (`>= 18 px`):** Every visible `<text>` element must resolve to `>= 18.0 px` when fitted to its video slot (`full`: `1704×780`, `composite`: `1704×480`, `split`: `820×740`).
4. **Google Design Token Hygiene:** Zero `Tahoma`, `Helvetica`, `Arial`, `DejaVu`, or purple/orange/teal hex codes. Use only semantic tags from `c4-google-tokens.dsl`:
   - Elements: `Person`, `Software System`, `Container`, `Database`, `Queue`, `Cache`, `Component`, `External`, `New`, `Breaks`, `Fix`.
   - Relationships: `HTTPS`/`Sync` (solid `#202124`), `Event`/`Async` (dashed `#1967D2`), `File`/`Batch` (dashed `#5F6368`), `Response` (dashed `#188038`), `Internal` (solid `#5F6368`).
5. **Spatial Permanence (`0.0 px` jitter):** Progressive narration videos never re-layout between steps; all steps lock to the master `viewBox`.

## Slot Topology Budgets

| Slot | Target `1080p` Box | Node Budget | Recommended `autoLayout` |
| :--- | :--- | :--- | :--- |
| `composite` | `1704 × 480` (above/below prose) | `3–6` nodes | `autoLayout lr 200 100` (max 2 parallel vertical rows) |
| `full` | `1704 × 780` (full diagram slide) | `5–11` nodes | `autoLayout lr 200 110` for pipelines; `tb 180 130` for wide fan-out |
| `split` | `820 × 740` (half-slide) | `3–6` nodes | `autoLayout tb 160 120` |

## 4-Step Closed-Loop Agent Workflow

1. **Ensure Warm Container:**
   ```bash
   scripts/c4_runtime.sh ensure
   ```
2. **Author `workspace.dsl` + `views.json`:**
   - Keep box descriptions crisp (`<= 45` chars).
   - Define `steps` in `views.json` (and matching `animation { ... }` blocks in `.dsl` when using Mode B) ordered by narration beat.
3. **Validate, Export, and Normalize (Single Command):**
   ```bash
   python3 scripts/render_c4.py --dsl path/to/workspace.dsl --spec path/to/views.json --out path/to/svg --png
   ```
   - Exit `0`: All views passed DSL validation, font hygiene, and `18px @ 1080p` legibility gate.
   - Exit `2`: DSL syntax error — fix the reported line and re-run.
   - Exit `3`: Legibility/token gate failed — follow the returned `remedy` (flip `lr ↔ tb`, shorten descriptions, or split >10 nodes).
4. **Render Progressive Video (Optional):**
   ```bash
   python3 scripts/progressive_video.py --svg out/02-container-view.svg --mode C --title "L2 · Container Architecture" --out out/02-container-view.mp4
   ```
   *(Default mode is provisional `C` [Live Draw] pending Author Review of the C3-03 bake-off; modes `A` [Cross-Dissolve] and `B` [Native Animation] are also supported.)*
