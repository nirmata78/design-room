---
name: c4-structurizr
description: Local-first C4 architecture diagramming from one Structurizr DSL workspace, drawn in the c4model.com style with Google colours and fonts (person = head + body, cylinders for stores, the component icon, dashed labelled arrows), laid out on an explicit grid sized to a 1080p slot, with every version, flow, zoom and overlay derived from one layout so nothing moves between frames. Also renders Mode A progressive cross-dissolve clips. Use whenever designing, drawing, updating, or animating C4 System Context, Container, Component, or Version-Delta architecture diagrams for Markdown docs or 1080p video slides. Compatible with Claude CLI, Antigravity (Gemini), and Grok.
---

# `c4-structurizr` — Structurizr model, c4model.com drawing, 1080p-ready

One Structurizr `workspace.dsl` is the model: elements, technologies, descriptions, tags and the include set of every view. The
Structurizr CLI (in a warm Docker container, `local/structurizr-c4:playwright`, no host Java) validates it and exports it as JSON —
no browser. `scripts/c4draw.py` then draws every view itself (the **native** renderer, the default since 2026-11-28):

- **Look**: [c4model.com](https://c4model.com/diagrams) — white boxes with a coloured outline, `[Type: technology]` under the name,
  a person as a head and a body, cylinders for stores, the component icon, dashed arrows with the description on a white plate and
  the technology in `[brackets]`; a dashed rounded boundary with its name and `[type]` bottom-left. Google palette and Inter
  (`DESIGN-TOKENS.md` of the reference-solution skill).
- **Layout**: a `grid` per view in `views.json`, sized to the slot the view is shown in. Every gap is as wide as the labels that
  cross it, boxes shrink to fit, and the drawing is centred. Derived views inherit the grid **and the canvas**: 0 px of movement from
  V1 to the recap.
- **Why not Structurizr's own SVG export**: dagre/JointJS output at 1080p gave cramped boxes, text outside shapes, crossing routes
  and holes in derived views (the 2026-11-28 review of SD-03). That path is kept as `"renderer": "structurizr"` (top level of
  `views.json`) and `svg_normalizer.py`, for old workspaces only.

## Multi-Agent Compatibility
- **Claude CLI:** `.claude/skills/c4-structurizr/SKILL.md`.
- **Antigravity (Gemini) / Gemini CLI:** the `.agents/skills/c4-structurizr` symlink.
- **Grok (xAI) / any OpenAI-style agent:** load this file as instructions and pass `schemas/tool-definition.json` as `tools`.

## Core invariants

1. **One DSL.** All views of a system in one `workspace.dsl`, `!identifiers hierarchical`, `!impliedRelationships false`.
   `person` and `softwareSystem` at the top of `model`, `container` inside a system, `component` inside a container.
2. **Uses direction.** An arrow points from the reader to what it reads (C4's "uses"); the relationship's **technology** is the
   third string (`a -> b "Reads hour H" "Kafka"`) and is drawn as `[Kafka]` under the label. A fourth string is tags.
3. **Shape by tag** (c4model.com): `Database` cylinder · `Queue` box with a log icon · `Bucket` · `Folder` · `Browser` window ·
   `App` box with `>_` (a server-side application) · components always carry the component icon · `External` = grey.
   Colour is semantic: blue outline = in scope, grey = external, person = blue tint. Red, green and yellow appear **only** as
   overlays (BREAKS, FIX, NEW/ALTERNATE).
4. **1080p legibility, measured.** The canvas is the slot in frame px (`stage` 1800 × 860 …), so 1 svg px = 1 px on a 1080p
   frame. Title 25 px bold, `[Type]` 18, description 19, edge label and `[technology]` 18, pills 18. A view fails (exit 3) if any
   text is under `min_px` (18) or does not fit its box. Keep a description to one short line (≈ 20 characters in a dense view) and
   a technology to one or two words (`Flink`, `Iceberg`, `Go`): detail belongs in the narration.
5. **Mode A progressive reveal.** Every view writes `<key>.svg` (groups tagged `data-k`: `e:<alias>`, `l:<a>-<b>`,
   `p:<kind>:<alias>`, `f:<n>`, `b:<scope>`), `<key>.steps.json` (the reveal plan) and `<key>.meta.json` (`ViewMeta` +
   `overflow` + `renderer`). Unrevealed groups stay `visibility: hidden`; nothing moves when they appear.

## `views.json`

```json
{"views": {
  "c4-context": {"slot": "stage", "box": [380, 170], "grid": [
      " .    adv    .  ",
      "cli   ac   fraud",
      " .    invo   .  "]},
  "containers": {"slot": "stage", "box": [236, 176], "grid": [
      "cli    .       fraud   .      adv",
      "col    lake    batch   bill   api",
      "log    stream  .       live   .  "]},
  "v1":       {"from": "containers", "hide": ["stream", "live", "fraud"], "steps": ["cli", "col", "log"]},
  "v2":       {"from": "containers", "hide": ["fraud"], "new": ["stream", "live"]},
  "flow-v1":  {"from": "containers", "hide": ["stream", "live", "fraud"], "flow": ["cli->col", "col->log"]},
  "dd-break": {"from": "comp-stream", "keep": ["src", "time", "dedup"], "breaks": ["dedup"]}
}}
```

| Field | Effect |
|---|---|
| `grid` | rows of DSL identifiers (last segment), `.` for an empty cell. Only on an exported view; derived views inherit it. Put the containers of the system in scope (or the components of the container in scope) in a rectangular block and everything external **outside** it: the boundary is drawn around that block. Without a grid, a layered layout is computed (fine for a first look, never for a video) |
| `box: [w, h]` | the box size to aim for (shrunk to fit the slot; persons get 30 px for the head) |
| `from` | the exported view this one is cut from: same grid, same canvas, same routes |
| `hide: ["alias", "a->b"]` | leave boxes (and their edges) or single edges out: how V1 … Vn are cut from one master view. The hole stays; design the grid so the first version sits in the middle |
| `new` | yellow outline + NEW pill; carried boxes show on frame 0, each new box reveals with its edges |
| `breaks` · `fix` · `focus` · `alternate` | red BREAKS · green FIX · blue IN FOCUS · dashed yellow ALTERNATE, outline + tint + pill; each pill is a reveal step |
| `badges: {"alias": "M1 M2"}` | a white pill on the top-left of the box, one reveal step each |
| `keep` | a zoom: everything else dims to 28 %, nothing moves. Prefer it to `crop` — the viewer keeps the whole pipeline in sight |
| `crop: true` | with `keep`: the viewBox shrinks to the kept boxes and scales them up (for a composite slot only) |
| `flow: ["a->b", …]` | a numbered disc (placed clear of labels and boxes) and a blue highlight under each arrow, one step per arrow |
| `steps: [[…], …]` | reveal order of a first drawing; group aliases to keep the step count near the narration's beats |
| `slot` | `stage` 1800 × 860 (a diagram-only slide) · `full` 1704 × 780 · `composite` 1704 × 480 · `split` 820 × 740 |
| `min_px` (18) · `video: false` | the gate; `false` exempts a Markdown-only view from the size gate (not from the fit check) |
| `legend: true` | a small legend bottom-left (person · external · in scope) |

Unknown aliases fail the render (exit 3) with the list; so does an element of the view that the grid leaves out.

**Grids that read well** (from SD-03): the context view as a cross, the system in the middle. The container view in 3 rows ×
5 columns at most, externals on the top row, the main data path along one row and the second path along the row under it (the
batch row and the live row of SD-03). A component view of 7–9 components in 3 rows × 4 columns, or 4 × 5 with one-line
descriptions; that is legible at 1080p, so a challenge first shows the **whole** component view, then dims to the 2–3 boxes in
play. Neighbours that talk should be adjacent (a straight arrow); an arrow that must skip a box is routed around it through the
gaps.

## Workflow

1. `scripts/c4_runtime.sh ensure` (once; builds the image and starts the warm container).
2. Write `workspace.dsl` (include `resources/c4-google-tokens.dsl`; its styles only matter to Structurizr's own tools now) and
   `views.json` with a `grid` per exported view.
3. Render and gate:
   ```bash
   python3 scripts/render_c4.py --dsl path/to/workspace.dsl --spec path/to/views.json --out path/to/svg [--png]
   ```
   Exit `0` all views pass · `2` DSL error (fix the line) · `3` a gate failed: each failure has a `remedy` (shorten the
   description or technology, give the grid fewer columns, set `box`, or fix an alias).
4. Look at the PNGs of the master view and one zoom (`--png`, or `rsvg-convert -w 1800 x.svg -o x.png`) before anything else uses them.
5. Optional standalone clip: `python3 scripts/progressive_video.py --svg out/v2.svg --title "V2" --out out/v2.mp4 [--ghost 0.10]`.
   In design-room, `scripts/ref_solution.py diagrams SD-NN` (reference-solution skill) runs steps 3–4 for a whole solution and the
   deck reads each `.steps.json` as reveal units.

Worked example: `solutions/SD-03-ad-click-aggregation/workspace.dsl` + `views.json` (5 exported views, 18 derived ones).

## Style lock

The SD-03 drawings are the approved look (2026-11-28) for every solution that follows. `tests/test_golden_sd03.py` re-draws 11 of
them from a frozen JSON export (`tests/golden/sd03/`, no Docker) and requires identical SVG bytes, so a change to `c4draw.py` that
moves a pixel fails the tests. Change the look only on purpose: look at the new PNGs, then refresh the golden files as that test's
docstring says (`C4_SAVE_JSON=<path>` makes `render_c4.py` keep the export). Run `python3 -m pytest tests` before every commit.
