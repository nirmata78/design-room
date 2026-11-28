# Plan 03 · Containerized Structurizr C4 Skill & Progressive Video Bake-Off

**Shared rules:** [`00-shared-rules-and-sources.md`](00-shared-rules-and-sources.md). Read it first in every session.  
**Visual standard:** [`.claude/skills/reference-solution/DESIGN-TOKENS.md`](../.claude/skills/reference-solution/DESIGN-TOKENS.md) and `~/.claude/skills/slide-video-kit/STANDARD.md` (`1920×1080` frames, `>= 22 px` slide text, `>= 18 px` diagram labels, Google palette & offline OFL fonts).  
**Skill location (current):** `.claude/skills/c4-structurizr/` inside `design-room` (structured for zero-rewrite promotion to `nirmata78/dev-standards`).  
**Status file:** `plans/STATUS-03.md` (create in Subtask Card 1 from the table in §6.1).  
**Target AI Agents:** Claude (Claude Code), Gemini (Antigravity / Gemini CLI), and Grok (xAI Function Calling / CLI).

---

## 1 · Title & Overview

### 1.1 Objective
Design, containerize, validate, and package a **local-first, zero-host-dependency C4 architecture diagramming skill (`c4-structurizr`)** centered on **Structurizr DSL**, paired with a deterministic **Viewport & Progressive SVG Normalizer**, to produce publication-grade raw `.svg` and `.png` artifacts and human-like progressive video sequences (`1920×1080` MP4).

### 1.2 Architectural Decisions & Critical Review Summary
Before writing code, this plan incorporates five critical engineering adjustments uncovered by reviewing Docker Hub (`hub.docker.com/u/structurizr`), `/Users/neo.bsuir/Projects/structurizr`, `DESIGN-TOKENS.md`, and `nirmata78/dev-standards`:

1. **Commit 100% to the Hybrid Two-Stage Structurizr Pipeline (Reject D2 Fallback):**
   Maintaining a secondary D2 backend violates YAGNI, splits prompt token budgets, doubles golden-test surface area, and weakens LLM adherence. Structurizr DSL is the sole modeling language.
2. **Docker Hub Tag Trap (`latest` vs. `-playwright` & Deprecated Repos):**
   - `structurizr/cli` and `structurizr/lite` on Docker Hub are **deprecated / EOL** and must not be used.
   - `structurizr/structurizr:latest` is built from `eclipse-temurin-alpine` **without Playwright**; calling `export -format svg|png` on `latest` fails with `"Exporting to PNG/SVG is not supported in this build"`.
   - Browser-rendered SVG/PNG export requires `structurizr/structurizr:<version>-playwright` (or `preview`), **plus** offline `Inter` / `Plus Jakarta Sans` / `Roboto Mono` fonts baked into `/usr/local/share/fonts` inside the container so Chromium's JointJS text bounding boxes match the video renderer's font metrics (`<1%` glyph drift).
3. **Warm Reusable Container Over Cold `docker run --rm` Loops:**
   Cold-starting a container + Spring Boot `.war` + Chromium per diagram adds `4–7s` latency. Deploying **one long-lived warm container** (`structurizr-c4-daemon`) and invoking exports via `docker exec` (with batch `workspace.dsl` views) keeps the host 100% clean while cutting 10-view exports to `~3s`.
4. **Strict `DESIGN-TOKENS.md` Compliance in SVG Post-Processing:**
   JointJS hardcodes `font-family="Tahoma, Verdana, Helvetica, Arial"` (which violates `DESIGN-TOKENS.md` §4's `grep` gate) and renders `[Container]` type lines at `0.5×` title size. Furthermore, `DESIGN-TOKENS.md` §1 forbids purple, orange, and teal. Both the DSL theme and the AST normalizer enforce the exact Google C4 ramp and rewrite all SVG font declarations to `Inter, Roboto, sans-serif`.
5. **Empirical Bake-Off Gate Before Locking Progressive Video Mode:**
   Rather than guessing which progressive-reveal animation looks most natural in motion, Subtask Card 3 renders short (`10–15s`) `1080p` sample MP4s for **4 C4 diagram types** (`System Context`, `Container`, `Component`, `Version Delta`) across **Techniques A, B, and C**, then **halts at a human review gate** for author selection before finalizing the skill.

### 1.3 Goals, Non-Goals & System Invariants (SLOs)

| Dimension | Specification |
| :--- | :--- |
| **Goals** | Deterministic local `.dsl` → normalized `.svg` / `.png` + progressive reveal metadata; containerized runtime; `1080p` legibility gate; cross-LLM skill portability; `dev-standards`-ready layout. |
| **Non-Goals** | Cloud Structurizr SaaS push/pull; D2/Mermaid/PlantUML C4 fallbacks; migrating full 90-minute `SD-*` reference videos inside this plan; automated YouTube uploads. |
| **Invariant I1 (Host Purity)** | Zero Java, Maven, or Playwright installations required on the host OS; everything executes inside Docker + project Python `.venv`. |
| **Invariant I2 (Spatial Permanence)** | Across all progressive reveal steps `1..K` of a view, every revealed element's `(x, y, width, height)` in `1920×1080` frame space shifts by **`0.0 px`**. |
| **Invariant I3 (Legibility Gate)** | Every visible `<text>` node in a rendered `1920×1080` slide frame resolves to **`>= 18.0 px`** (`check_layout.py` rule); box labels never overflow box widths. |
| **Invariant I4 (Token Hygiene)** | `grep -Ei "Charter|Georgia|Helvetica|Arial|DejaVu|Tahoma|STIX"` across normalized `.svg` outputs returns **0 matches**; zero hex codes outside `DESIGN-TOKENS.md`. |
| **Performance SLO** | Warm-container batch export + normalization of a 5-view `workspace.dsl` completes in **`<= 5.0 seconds`** on Apple Silicon / modern x86_64. |

---

## 2 · Tool Landscape & Architectural Decision Record (ADR)

### 2.1 Evaluation of Docker Hub `structurizr/*` Repositories

| Docker Hub Image | Status | Role & Verdict |
| :--- | :--- | :--- |
| **`structurizr/structurizr`** | **Active (v6 Unified)** | **ADOPT (Playwright variant).** Consolidates CLI, Lite (`local`), Server, and Export. *Caveat:* Only `<version>-playwright` and `preview` tags contain Chromium/Playwright needed for `export -f svg\|png`. |
| **`structurizr/mcp`** | **Active** | **OPTIONAL COMPANION.** Exposes Structurizr DSL validation/inspection tools over MCP (`stdio`/SSE). Useful for interactive IDE exploration, but **not** a replacement for deterministic CLI batch export (`render_c4.py` wraps validation + export + SVG normalization atomically in one call). |
| **`structurizr/cli`** | **Deprecated / EOL** | **REJECT.** Frozen pre-v6 CLI; lacks Playwright JointJS SVG export (only exported PlantUML/Mermaid/DOT text). |
| **`structurizr/lite`** | **Deprecated / EOL** | **REJECT.** Replaced by `structurizr/structurizr local`. |

### 2.2 Evaluation of Rejected Alternatives
- **PlantUML + C4-PlantUML (Legacy):** Offline and fast, but Graphviz spline routing creates ultra-wide `5:1` strips, embeds rasterized PNG person sprites, splits labels word-by-word across `<text>` nodes, and looks visually dated. **Rejected.**
- **LikeC4:** Modern visual cards, but exports static SVGs with embedded HTML `<foreignObject>` subtrees that break non-browser SVG consumers (`rsvg-convert`, `resvg`, lxml XPath gates) and complicate per-element progressive CSS/stroke animations. **Rejected.**
- **D2 (`--layout=elk`):** Fast single binary and clean pure SVG, but lacks native C4 hierarchical model inheritance (`System → Container → Component`). **Rejected** per single-DSL focus.
- **Mermaid C4 (`mmdc`):** Fixed grid layout ignores graph topology and produces severe arrow crossings on real architectures. **Rejected.**

---

## 3 · Recommended Local Stack

### 3.1 Stage 1: Containerized Structurizr Engine (Option B — Zero Host Dependencies)

#### Image Resolution Strategy ("Pull-Verify or Build-Once, Then Reuse")
Provide an idempotent management script `.claude/skills/c4-structurizr/scripts/c4_runtime.sh` with subcommands `ensure`, `start`, `stop`, `status`, and `exec`:

1. **Check Local Image Cache:** If `local/structurizr-c4:playwright` already exists locally and passes `c4_runtime.sh healthcheck`, reuse it immediately (`0s` build).
2. **Pull Official Playwright Base (or Local Source Build):**
   - Attempt to pull the pinned Playwright-capable `structurizr/structurizr` tag (e.g., `structurizr/structurizr:preview` or `<YYYY.MM.DD>-playwright`) matching host architecture (`linux/arm64` on Apple Silicon, `linux/amd64` on x86_64).
   - If the upstream tag lacks native `linux/arm64` support or is unreachable offline, automatically fall back to building from `/Users/neo.bsuir/Projects/structurizr` via a multi-stage `Dockerfile` (`maven:3.9-eclipse-temurin-21` builder stage → `mcr.microsoft.com/playwright/java:v1.64.0-noble` runtime stage).
3. **Font-Hermetic Thin Layer (`Dockerfile.c4`):**
   Wrap the base image in a tiny cached layer that copies `pdf-kit/fonts/google/static/*.ttf` (`Inter`, `Plus Jakarta Sans`, `Roboto Mono`) into `/usr/local/share/fonts/google/` and runs `fc-cache -f -v`. Tag the resulting image `local/structurizr-c4:playwright`.

```dockerfile
# .claude/skills/c4-structurizr/docker/Dockerfile.c4
ARG BASE_IMAGE=structurizr/structurizr:preview
FROM ${BASE_IMAGE}

USER root
COPY fonts/*.ttf /usr/local/share/fonts/google/
RUN fc-cache -f && mkdir -p /workspace && chmod 777 /workspace

WORKDIR /workspace
```

4. **Warm Daemon Deployment (`structurizr-c4-daemon`):**
   Launch a single detached background container mounting the active repository at `/workspace`:
   ```bash
   docker run -d \
     --name structurizr-c4-daemon \
     --restart unless-stopped \
     --shm-size=1gb \
     -v "/Users/neo.bsuir/Projects/design-room:/workspace" \
     --entrypoint tail \
     local/structurizr-c4:playwright -f /dev/null
   ```
   *Why `--shm-size=1gb` and warm container?* Headless Chromium crashes on complex SVGs with Docker's default `64MB` `/dev/shm`. Keeping the container warm lets `render_c4.py` run `docker exec structurizr-c4-daemon /usr/local/structurizr.sh validate ...` and `export ...` with zero container creation overhead. (An `--ephemeral` flag remains available for stateless CI.)

### 3.2 Stage 2: Viewport & Progressive Normalizer Stack

| Component | Choice | Engineering Rationale |
| :--- | :--- | :--- |
| **Language & Env** | **Python 3.12** (`pdf-kit/.venv` in `design-room`, declared via `pyproject.toml` inside the skill for portability) | Already powers `design-room`'s `check_layout.py` and `render_slides.py`; zero new language runtimes. |
| **SVG AST Engine** | **`lxml.etree`** | Real XML parser + XPath 1.0 support; cleanly traverses JointJS `<g id="j_*">` layers, parses `transform="translate(x,y)"` / `matrix(...)`, strips footers, and serializes deterministic XML in `<15ms` without brittle regexes. |
| **Config & Metadata Contracts** | **`pydantic` v2** | Enforces strict JSON schemas on `views.json` inputs and `.meta.json` / `.steps.json` outputs; auto-generates JSON Schema for LLM tool definitions. |
| **SVG → PNG & Video Frame Renderer** | **Playwright Chromium** (already in `pdf-kit/.venv`) + **`ffmpeg`** | Renders both static `@2x.png` artifacts and 30fps `1920×1080` progressive MP4 frames (needed especially for Technique C CSS/SVG stroke animations) with 100% identical `@font-face` rendering to `render_slides.py`. |
| **Test Framework** | **`pytest`** | Unit tests for AST bounding-box math, `DESIGN-TOKENS.md` lint compliance, `18px @ 1080p` legibility gates, and spatial-permanence invariants. |

### 3.3 `DESIGN-TOKENS.md` Structurizr Theme (`c4-google-tokens.dsl`)
Every generated workspace `!include`s a locked theme matching `.claude/skills/reference-solution/DESIGN-TOKENS.md` (no purple, orange, or teal):

- **`Person`:** `#174EA6` fill, `#174EA6` stroke, `#FFFFFF` text (`shape Person`, `360×290`, `fontSize 34`)
- **`Software System`:** `#4285F4` fill, `#1967D2` stroke, `#FFFFFF` text (`shape RoundedBox`, `420×240`, `fontSize 34`)
- **`Container`:** `#8AB4F8` fill, `#1967D2` stroke, `#202124` text (`shape RoundedBox`, `420×240`, `fontSize 34`)
- **`Database` (`store`):** `#34A853` fill (or `#188038` high-contrast fill with `#FFFFFF` text), `#188038` stroke (`shape Cylinder`)
- **`Queue` (`queue`):** `#F8F9FA` fill, `#202124` stroke, `#202124` text (`shape Pipe`)
- **`Component`:** `#E8F0FE` fill, `#4285F4` stroke, `#202124` text (`shape RoundedBox`)
- **`External`:** `#5F6368` fill, `#3C4043` stroke, `#FFFFFF` text (`shape RoundedBox`)
- **`New` (delta highlight):** `#4285F4` or `#FBBC05` stroke, `strokeWidth 6` + normalizer-injected crisp `NEW` badge above top-right corner
- **`Breaks` / `Fix` (challenge overlays):** `#EA4335` (`#C5221F` stroke) for failures only; `#34A853` (`#188038` stroke) for fixes only
- **`Boundary`:** `#F8F9FA` fill, `#9AA0A6` dashed stroke, `#202124` text
- **`Relationship`:** `routing Orthogonal`, `jump true`, `fontSize 28`, `width 240`:
  - `HTTPS` / `Sync`: solid `#202124`, `thickness 3`
  - `Event` / `Async`: dashed `#1967D2`, `thickness 3`
  - `File` / `Batch`: dashed `#5F6368`, `thickness 3`
  - `Response` / `Match`: dashed `#188038`, `thickness 3`

### 3.4 Normalizer Pipeline (`svg_normalizer.py`)
For each raw Structurizr `<view>.svg`:
1. **Discard** auto-generated `<view>-key.svg` files unless `--include-legend` is requested; instead inject a compact inline 1-line protocol legend pill bar when relationships use multiple styles.
2. **Strip** JointJS metadata footer `<g>` elements (`System Context View:...`, `Container View:...`, date/timestamp `<text>` nodes).
3. **Rewrite Typography:** Replace all `Tahoma, Verdana, Helvetica, Arial` declarations with `Inter, Roboto, sans-serif`; scale up JointJS `[Container: ...]` type-line `<text>` nodes (`font-size < 24px`) by `1.4×` and adjust vertical `dy` spacing so subtitles clear `18px @ 1080p` without colliding with descriptions.
4. **Tight-Crop & Slot-Pad `viewBox`:** Compute exact union bounding box `(x0, y0, x1, y1)` across all remaining shapes and text labels, add `28px` breathing room, remove fixed `width`/`height` attributes, and set `preserveAspectRatio="xMidYMid meet"`.
5. **Enforce Slot Legibility Gate:** Given target slot dimensions (`full`: `1704×780`, `composite`: `1704×480`, `split`: `820×740`), compute `scale = min(slot_w / vb_w, slot_h / vb_h)` and `min_rendered_px = min_font_size * scale`. Fail with actionable layout diagnostics if `min_rendered_px < 18.0`.
6. **Tag Semantic Cells:** Map each JointJS element `<g id="j_*">` to its DSL alias (`data-k="e:<alias>"`, `data-role="node"`) and each connector `<g id="j_*">` to `data-k="l:<src>-><dst>"` (`data-role="edge"`), writing `<view>.steps.json` and `<view>.meta.json`.

---

## 4 · Progressive / Human-like Drawing Approach & Bake-Off Design

To make architecture explanations feel authored by a Staff engineer at a whiteboard—without shaky novelty clipart or layout jitter—we implement **three candidate progressive rendering modes** behind a single `--mode=A|B|C` switch and evaluate them empirically on real `10–15s` videos before locking the skill default.

### 4.1 The Three Candidate Techniques

| Mode | Name | Visual Mechanics | Pros | Trade-offs |
| :--- | :--- | :--- | :--- | :--- |
| **Technique A** | **Master SVG + Step Cross-Dissolve (Ghost Context Optional)** | Full layout locked in one `.svg`. Unrevealed steps have `visibility: hidden` (or `opacity: 0.10` ghosted blueprint). Each narration beat renders one static PNG; FFmpeg cross-dissolves (`0.35s`) between beats. | Fastest render (`N` PNGs per view, not `30×15` frames); integrates directly with `design-room`'s existing `build_cached.py` `--reveal-fade`. | Boxes and arrows fade in simultaneously rather than "drawing" directionally. |
| **Technique B** | **Structurizr Native `-animation true` Sequence** | Uses Structurizr DSL's built-in `animation { step1; step2; ... }` block exported natively via `export -f svg -animation true` into `view-001.svg … view-00K.svg`, normalized to the final frame's `viewBox`, and crossfaded in FFmpeg. | 100% official Structurizr semantics; Structurizr automatically validates that every relationship appears with its endpoints. | Coarse step granularity; requires exporting `K` separate pages inside Playwright (`~2×` slower export). |
| **Technique C** | **Directional Vector "Live Draw" (Stroke-Dashoffset + Card Pop)** | Uses the single normalized `.svg` inside a `1920×1080` HTML stage driven at `30fps`: when step `k` triggers, new node outlines trace in (`220ms` `stroke-dashoffset`), card fills fade in (`160ms` cubic-bezier ease-out), and edges **draw directionally from caller to callee** (`380ms` `stroke-dashoffset: L → 0`) before arrowheads and label pills snap in (`120ms`). | Most human-like, engaging "live architecture sketch" feel; visually guides the viewer's eye along request/event flow direction. | Renders `~20–30` transition frames per reveal beat (~`1.5s` extra Chromium capture per diagram). |

### 4.2 Bake-Off Matrix (Subtask Card 3 — Human Review Gate)
Generate **12 short `1920×1080 @ 30fps` MP4 clips** (`10–15 seconds` each, silent or subtle tick markers, with clean slide header + caption bar) covering **4 C4 view types × 3 Techniques**, plus **4 side-by-side `2×2` comparison MP4s** (A vs. B vs. C + static reference in the 4th quadrant):

1. **`01-system-context` (~12s, 4 beats):** `Customer` & `Merchant` → `Loan Servicing` → `Card Processor` (`HTTPS`) → `Bank` (`Batch File`).
2. **`02-container-view` (~15s, 5 beats):** `Servicing API` → `Schedule Service` → `Servicing DB` (`Cylinder`) → `Dispatcher` (`Outbox Event`) → External Rails.
3. **`03-component-view` (~12s, 4 beats):** Zoom inside `Dispatcher`: `Outbox Poller` + `Day Plan` → `Token Bucket` → `Card Client` & `File Builder`.
4. **`04-version-delta` (~12s, 3 beats):** `V1` baseline carried at step 0 → `V2` `Servicing DB [NEW]` + `Dispatcher [NEW]` highlighted with `#FBBC05` / `NEW` badge.

> **Mandatory Review Gate:** After Subtask Card 3 produces `artifacts/c4-bakeoff/*.mp4`, the runner **stops** and presents the 4 comparison reels to the author. Subtask Card 4 (finalizing the skill default and `SKILL.md`) executes **only after** the author selects A, B, C, or a hybrid (e.g., Mode A for static slide decks + Mode C for hero architecture walkthroughs).

---

## 5 · Reusable Skill Design

### 5.1 Repository Placement & `nirmata78/dev-standards` Promotion Path
Store the skill during development and daily use at:
`/Users/neo.bsuir/Projects/design-room/.claude/skills/c4-structurizr/`

To make future publication into `/Users/neo.bsuir/Projects/nirmata78/dev-standards` frictionless (satisfying `dev-standards/scripts/check_repo.py`'s three CI laws: *atomic docs near code*, *doc-as-a-constraint*, and *self-contained plugin skills*):
- Zero hardcoded `/Users/neo.bsuir/...` paths inside scripts; workspace root is resolved from `--workspace-root` or `$PWD`.
- Fonts default to `$SKILL_DIR/resources/fonts/` (copied once from `pdf-kit/fonts/google/static/`, OFL-licensed) so the skill is 100% self-contained when copied out of `design-room`.
- Include an atomic `README.md` beside `SKILL.md` documenting inputs, outputs, SLOs, and troubleshooting.
- When promoting to `dev-standards`, the folder moves directly to `plugins/c4-architecture/skills/c4-structurizr/` alongside a 10-line `.claude-plugin/plugin.json` and an entry in `docs/nav.json`.

### 5.2 Multi-Agent Compatibility Surface (Claude, Gemini, Grok)

| Agent Platform | Discovery & Invocation Mechanism |
| :--- | :--- |
| **Claude Code** | Native discovery via `.claude/skills/c4-structurizr/SKILL.md` (YAML frontmatter `name`, `description`). Invocable explicitly as `/c4-structurizr` or automatically on C4 tasks. |
| **Gemini (Antigravity / Gemini CLI)** | Symlink `.gemini/skills/c4-structurizr` → `.claude/skills/c4-structurizr` (identical `SKILL.md` frontmatter + `scripts/` convention). |
| **Grok (xAI API / CLI Agent)** | `schemas/tool-definition.json` exports the OpenAI/xAI-compatible JSON Schema generated from `pydantic` (`render_c4_workspace`), paired with `SKILL.md` injected as developer instructions. |

### 5.3 Skill Contract (`render_c4.py`)

**Inputs:**
- `--dsl <path/to/workspace.dsl>`: Single Structurizr DSL file modeling the domain across C4 levels.
- `--spec <path/to/views.json>`: Declarative per-view rendering specification:
  ```json
  {
    "views": {
      "c4-context": {
        "slot": "full",
        "reveal_mode": "auto",
        "steps": [
          ["cus", "mer", "ls"],
          ["proc"],
          ["bank", "fin"]
        ]
      },
      "m-queue": {
        "slot": "composite",
        "steps": [["claimer", "db"], ["intentWriter", "outboxRow"], ["sweeper"]]
      }
    }
  }
  ```
- `--out <dir>`: Output directory for `.svg`, `.steps.json`, `.meta.json`, optional `--png`, and optional `--preview-mp4`.

**Outputs & Exit Codes:**
- `0`: All views validated, exported, normalized, token-clean, and `>= 18.0 px` at `1080p`.
- `2`: Structurizr DSL syntax/model error (returns exact line number + DSL grammar hint).
- `3`: Layout/legibility gate failure (returns offending view key, `min_rendered_px`, `vb_w × vb_h`, and concrete remediation advice: *"Switch `autoLayout lr` → `tb` or split >10 nodes"*).

### 5.4 Prompting Strategy for Dynamic & Incremental C4 Modeling
`SKILL.md` enforces four rules so any LLM drives Structurizr deterministically:
1. **Strict C4 Hierarchy:** `person` and `softwareSystem` live ONLY at top-level `model { ... }`; `container` ONLY inside `softwareSystem`; `component` ONLY inside `container`. Use `!identifiers hierarchical` always.
2. **Slot-Driven Topology Budgets:**
   - `composite` (`1704×480` strip on mechanism/option slides): `3–6` elements max, `autoLayout lr 200 100`, max 2 parallel vertical branches.
   - `full` (`1704×780` full diagram slide): `5–11` elements max; prefer `lr` for pipelines (`<= 4` ranks) and `tb` for hub-and-spoke/fan-out graphs.
3. **Incremental Caching by View Hash:** `render_c4.py` hashes `(resolved_view_json + view_spec + theme_hash)` into `<key>.meta.json`. Re-running after adding a single component view skips unchanged views' post-processing and video frame renders.
4. **Closed-Loop Self-Repair:** Run `render_c4.py` → inspect structured JSON summary → if exit code `2` or `3`, apply the suggested fix → visually inspect rendered `.png` on dense views (`>= 8` elements) before finishing.

---

## 6 · Implementation Plan (Session Subtask Cards)

Following `00-shared-rules-and-sources.md` §2, work is divided into **five self-contained ~30–45 minute subtask cards** tracked in `plans/STATUS-03.md`.

### 6.1 Status File Template (`plans/STATUS-03.md`)
Create `plans/STATUS-03.md` at the start of Card 1:

| Card | Unit | State | Duration / Perf | Notes & Open Questions |
| :--- | :--- | :--- | :--- | :--- |
| **C3-01** | Containerized Structurizr runtime (`Dockerfile.c4` + `c4_runtime.sh`) | `todo` | — | Verify `arm64` Playwright image & font metrics |
| **C3-02** | `lxml` Viewport & Progressive Normalizer + `pytest` suite | `todo` | — | Enforce `DESIGN-TOKENS.md` & `18px` gate |
| **C3-03** | Progressive Bake-Off: 4 C4 types × Techniques A, B, C (`10–15s` MP4s) | `todo` | — | **STOP FOR AUTHOR REVIEW AFTER THIS CARD** |
| **C3-04** | Finalize `c4-structurizr` skill (`SKILL.md`, `README.md`, Grok schema) | `blocked on C3-03 review` | — | Lock winning progressive mode from author feedback |
| **C3-05** | Smoke-test skill via cold agent invocation across 3 system archetypes | `blocked on C3-04` | — | Microservices, Kafka streaming, Geo-distributed |

### 6.2 Directory Layout Inside `design-room`
```text
.claude/skills/c4-structurizr/
├── SKILL.md                          # Cross-agent instructions (Claude / Gemini / Grok)
├── README.md                         # Atomic component doc (dev-standards compliant)
├── pyproject.toml                    # Standalone deps: lxml, pydantic, pytest
├── docker/
│   └── Dockerfile.c4                 # Structurizr Playwright + offline Google OFL fonts
├── resources/
│   ├── c4-google-tokens.dsl          # Locked DESIGN-TOKENS.md Structurizr styles
│   └── fonts/                        # Inter, PlusJakartaSans, RobotoMono static .ttf
├── schemas/
│   └── tool-definition.json          # Auto-generated JSON Schema for Grok / API tool use
├── scripts/
│   ├── c4_runtime.sh                 # ensure | start | stop | status | healthcheck
│   ├── svg_normalizer.py             # lxml AST cropper, font rewriter, data-k & steps tagger
│   ├── progressive_video.py          # Renders 1080p MP4s using Mode A, B, or C
│   └── render_c4.py                  # Main CLI entry point + 18px @ 1080p gate
├── examples/
│   └── bakeoff/                      # 4 canonical C4 views (Context, Container, Component, Delta)
│       ├── workspace.dsl
│       └── views.json
└── tests/
    ├── test_normalizer.py            # Font-token grep, viewBox crop, 18px gate, 0px jitter
    └── fixtures/
```

### 6.3 Subtask Card Specifications

#### Card C3-01 · Containerized Structurizr Runtime (`~30 min`)
- **Build:**
  1. Copy offline `.ttf` fonts from `pdf-kit/fonts/google/static/` (`Inter`, `PlusJakartaSans`, `RobotoMono`) into `.claude/skills/c4-structurizr/resources/fonts/`.
  2. Write `docker/Dockerfile.c4` and `scripts/c4_runtime.sh`:
     - Inspect/pull `structurizr/structurizr:preview` (or `<version>-playwright`); if unavailable or wrong arch, build `.war` inside multi-stage Docker from `/Users/neo.bsuir/Projects/structurizr` onto `mcr.microsoft.com/playwright/java:v1.64.0-noble`.
     - Bake in the Google OFL fonts (`fc-cache -f`), tag `local/structurizr-c4:playwright`, and start `structurizr-c4-daemon` (`--shm-size=1gb`).
- **Verify:**
  ```bash
  .claude/skills/c4-structurizr/scripts/c4_runtime.sh ensure
  .claude/skills/c4-structurizr/scripts/c4_runtime.sh healthcheck
  ```
- **Done when:** `healthcheck` validates a minimal `.dsl` and exports a raw `.svg` via `docker exec` in `< 4s` with zero host Java usage.

#### Card C3-02 · Viewport & Progressive Normalizer + Unit Tests (`~45 min`)
- **Build:**
  1. Author `resources/c4-google-tokens.dsl` adhering strictly to `DESIGN-TOKENS.md` §1–§2.
  2. Implement `scripts/svg_normalizer.py` (`lxml` + `pydantic`) and `scripts/render_c4.py`:
     - Batch-validate and export `.dsl` via `c4_runtime.sh`.
     - Strip JointJS footers and `-key.svg` sidecars, rewrite fonts to `Inter, Roboto, sans-serif`, boost `[Container]` metadata subtitles, tight-crop `viewBox` with `28px` border padding, inject `NEW` pills on `"New"` elements, tag `data-k` attributes, and write `.steps.json` + `.meta.json`.
     - Enforce `min_rendered_px >= 18.0` against slot dimensions and `0` forbidden font/color tokens.
  3. Write `tests/test_normalizer.py` covering footer removal, font hygiene, legibility gate failure diagnostics, and coordinate invariance.
- **Verify:**
  ```bash
  pdf-kit/.venv/bin/pytest .claude/skills/c4-structurizr/tests/ -q
  ```
- **Done when:** All `pytest` checks pass and `grep -Ei "Tahoma|Helvetica|Arial|DejaVu"` on normalized test SVGs returns nothing.

#### Card C3-03 · Progressive Drawing Bake-Off Videos — A vs. B vs. C (`~45 min`)
- **Build:**
  1. Create `examples/bakeoff/workspace.dsl` + `views.json` defining four compact, realistic C4 views (`01-system-context`, `02-container-view`, `03-component-view`, `04-version-delta`).
  2. Implement `scripts/progressive_video.py` supporting:
     - `--mode A`: Master `.svg` + step `visibility:hidden` (plus optional `--ghost 0.12` blueprint preview) + `0.35s` FFmpeg `xfade`.
     - `--mode B`: Structurizr `-animation true` discrete SVG export normalized to final-frame `viewBox` + `0.35s` FFmpeg `xfade`.
     - `--mode C`: `30fps` HTML/Playwright capture animating card border `stroke-dashoffset` (`220ms`), card fill fade (`160ms`), and directional edge `stroke-dashoffset` (`380ms`) from source to target.
  3. Render `10–15s` `1920×1080` MP4s (`H.264`, `yuv420p`) for all `4 views × 3 modes` (`12` clips) plus **4 `2×2` side-by-side comparison grid MP4s** (`ffmpeg` `xstack`) into `.claude/skills/c4-structurizr/examples/bakeoff/out/` (gitignored).
  4. Tile sample frames with `~/.claude/skills/slide-video-kit/scripts/tile_frames.sh` and visually inspect every sheet.
- **Done when:** All 12 individual MP4s (`10–15s` each) + 4 `2×2` comparison MP4s play cleanly (`ffprobe` verified `1920×1080`, `10–15s`), `STATUS-03.md` is updated, and **execution stops to present the videos for author review**.

#### Card C3-04 · Finalize Skill After Author Review (`~30 min`, *runs after author picks winning mode*)
- **Build:**
  1. Set the author's chosen progressive technique (A, B, C, or hybrid) as the default in `render_c4.py` / `progressive_video.py` and prune rejected experimental branches if unneeded.
  2. Write `.claude/skills/c4-structurizr/SKILL.md`, `README.md` (matching `dev-standards` atomic doc rules), and `schemas/tool-definition.json` (for Grok / function-calling agents).
  3. Symlink `.gemini/skills/c4-structurizr` (if `.gemini/skills` is used locally) so Claude and Gemini share one source.
- **Done when:** `SKILL.md`, `README.md`, and `tool-definition.json` pass schema/markdown lint and match the approved animation mode.

#### Card C3-05 · Multi-Domain Smoke Verification (`~30 min`)
- **Build & Verify:**
  Test `render_c4.py` + `progressive_video.py` on three distinct system-design domains (`10–15s` preview video + SVG/PNG artifacts each):
  1. **Transactional Microservices:** Idempotent API + relational ledger + outbox worker.
  2. **Event/Data Platform:** Ingestion gateway + Kafka pipe (`shape Pipe`) + stream processor + OLAP store (`shape Cylinder`).
  3. **Edge / Caching Architecture:** Client + CDN/Edge + stateless service + cache (`#FEF7E0` / `#FBBC05` tint) + primary DB.
- **Done when:** All 3 domains pass `render_c4.py` (`exit 0`, `>= 18px @ 1080p`, `0` token violations) on the first run.

---

## 7 · Gotchas & Engineering Best Practices

1. **Docker `/dev/shm` Starvation Crashes Chromium Silently:**
   Playwright Chromium inside Docker defaults to `64MB` shared memory and hangs or crashes when exporting large `2800×2000` JointJS SVGs. Always pass `--shm-size=1gb` in `c4_runtime.sh start`.
2. **File Ownership on Bind Mounts (Linux vs. macOS Docker Desktop/OrbStack):**
   Pass `--user "$(id -u):$(id -g)"` (or chmod output directories cleanly) on `docker exec` so root-owned `.svg` artifacts are never stranded in the workspace.
3. **Structurizr Strict Hierarchy Law:**
   Never place `person` or external `softwareSystem` declarations inside another `softwareSystem { ... }` block—Structurizr DSL immediately fails parsing. Declare all actors and systems at top-level `model`, and use `views { container sys "key" { include ... } }` to scope each diagram.
4. **JointJS `0.5×` Type-Line Trap & Text-on-Tint Contrast:**
   - Light container fills (`#8AB4F8`) and component fills (`#E8F0FE`) require dark text (`#202124`), whereas saturated fills (`#174EA6`, `#4285F4`, `#5F6368`, `#188038`) require `#FFFFFF` text.
   - Because JointJS renders `[Container: Go]` at `0.5×` the element `fontSize`, always pair DSL `fontSize 34` with AST subtitle scaling (`>= 24px` in SVG coordinates) so `1080p` frames never drop below `18px`.
5. **Normalize Multi-Frame `viewBox` to the Final Step (`Mode B`):**
   If exporting Structurizr native `animation` frames (`view-001.svg … view-00K.svg`), never crop each frame independently—cropping frame 1 to just 2 boxes makes those 2 boxes huge on frame 1 and shrinks them on frame 2! Always compute `viewBox` once from the **final** frame (`view-00K.svg`) and apply that exact `viewBox` to frames `001..00K`.
6. **Directional Stroke Reveal Path Orientation (`Mode C`):**
   JointJS draws `<path joint-selector="line" d="M x0 y0 ...">` from source element to target element. Animating `stroke-dashoffset` from `+pathLength` down to `0` naturally draws the line in causal flow order; verify `getTotalLength()` in Chromium rather than approximating Euclidean distance on orthogonal multi-segment paths.

---

## 8 · Next Actions (Prioritized Checklist for Implementation Sessions)

- [ ] **1. Initialize tracking & skill scaffold (`Card C3-01`):** Create `plans/STATUS-03.md` and scaffold `.claude/skills/c4-structurizr/` inside `design-room` with self-contained layout ready for future promotion to `nirmata78/dev-standards`.
- [ ] **2. Build & deploy warm containerized Structurizr (`Card C3-01`):** Implement `c4_runtime.sh` + `Dockerfile.c4` (verifying `structurizr/structurizr` Playwright support or building locally once, baking in offline `Inter`/`Plus Jakarta Sans`/`Roboto Mono` fonts, and starting `structurizr-c4-daemon` with `--shm-size=1gb`).
- [ ] **3. Implement `lxml` Viewport & Progressive Normalizer (`Card C3-02`):** Build `c4-google-tokens.dsl`, `svg_normalizer.py`, `render_c4.py`, and `pytest` unit tests enforcing `DESIGN-TOKENS.md` palette/font rules, tight `viewBox` cropping, `data-k` / `.steps.json` tagging, and the `>= 18px @ 1080p` legibility gate.
- [ ] **4. Render `10–15s` Progressive Drawing Bake-Off Videos (`Card C3-03`):** Generate `1920×1080` sample MP4s (`10–15 seconds` max each) across **4 C4 diagram types** (`System Context`, `Container View`, `Component View`, and `Version Delta`) using **Techniques A, B, and C**, plus `2×2` side-by-side comparison reels; inspect contact sheets and `ffprobe` metadata.
- [ ] **5. Pause for Author Review Gate:** Present the sample `10–15s` bake-off videos to the author, collect feedback on visual pacing and progressive reveal feel, and record the winning mode in `plans/STATUS-03.md`.
- [ ] **6. Finalize multi-agent skill & run 3-domain smoke tests (`Cards C3-04 & C3-05`):** Lock the chosen progressive mode into `render_c4.py`, author `SKILL.md` + `README.md` + `schemas/tool-definition.json` (for Claude, Gemini, and Grok), and verify end-to-end `10–15s` sample renders across microservices, streaming data, and edge-caching scenarios.
