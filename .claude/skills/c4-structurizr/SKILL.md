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

## `views.json`: every version, flow, zoom and overlay from one layout (2026-11-28)

Export each Structurizr view once; derive everything else in `views.json`, so boxes keep their pixel positions across a whole
video. A view key that names an exported view normalizes it; any other key needs `"from"`.

| Field | Effect |
|---|---|
| `from` | the exported view this one is cut from; its viewBox is locked to that view unless `crop` (0 px shift between versions) |
| `hide: ["alias", "a->b"]` | remove boxes (and every edge touching them) or single edges: how V1 … Vn are cut from one master view |
| `new: [...]` | Google Yellow border + NEW pill; carried boxes are visible on frame 0, each new box reveals with its edges |
| `breaks` · `fix` · `focus` · `alternate` | red BREAKS · green FIX · blue IN FOCUS · dashed yellow ALTERNATE border and pill; each pill is a reveal step |
| `badges: {"alias": "M1 · Dedup"}` | a white pill above the box's top-left corner, one reveal step each |
| `keep: [...]` + `crop: true` | a zoom: only the kept boxes and the edges between them, viewBox cropped to them (without `crop`: the rest dims to 0.25) |
| `flow: ["a->b", ...]` | a numbered disc and a highlighted copy of each edge (either direction), one reveal step per arrow |
| `steps: [[...], ...]` | explicit reveal order for a first drawing (aliases; edges follow when both ends are shown) |
| `slot` | `stage` (1800 × 860, a diagram-only slide) · `full` (1704 × 780) · `composite` · `split` |
| `min_px` (18) · `video: false` | the 1080p gate threshold; `false` marks a Markdown-only view (no gate) |
| `lock_viewbox_to` | lock to another view than `from` |

Unknown aliases fail the render (exit 3) with the list. Aliases are the last segment of the DSL identifier (`ac.stream.dedup` → `dedup`).
Worked example: `solutions/SD-03-ad-click-aggregation/workspace.dsl` + `views.json`.

**Layout rules that pass the 1080p gate:** `!impliedRelationships false`; arrows in C4 "uses" direction (reader → what it reads),
which keeps rank depth low; relationship technology empty; `routing Direct`; a master container view of ≤ 11 elements with
`autoLayout tb`; component chains shown on video only as `keep`+`crop` zooms of 2–4 adjacent components; raise `fontSize` (and the
`Boundary` label) in the workspace's own `styles` block when a view lands just under 18 px.

## Slot Topology Budgets

| Slot | Target `1080p` Box | Node Budget | Recommended `autoLayout` |
| :--- | :--- | :--- | :--- |
| `composite` | `1704 × 480` (above/below prose) | `3–6` nodes | `autoLayout lr 180 100` (max 2 parallel vertical rows) |
| `stage` | `1800 × 860` (diagram-only slide) | `5–11` nodes | `autoLayout tb 80 30` with uses-direction arrows |
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
   For full narrated decks in `design-room`, simply drop the normalized `.svg`, `.steps.json`, and `.meta.json` into `video/svg/` — the reference-solution kit (`.claude/skills/reference-solution/kit/dsl.py`) reads each `.steps.json` as reveal units, and `scripts/ref_solution.py diagrams` runs this renderer for a whole solution.
