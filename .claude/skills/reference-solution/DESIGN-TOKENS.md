# Design tokens · Google colours and Google Fonts (2026-11-22)

One visual system for every slide, diagram, video frame, Markdown figure and thumbnail this skill produces. It replaces the earlier
"scientific" serif style (Charter, muted blue/purple/amber). **Do not restyle per question.** Sources of truth, kept in step:

| File | Used by |
|---|---|
| `pdf-kit/google-theme.css` | HTML slides → frames, HTML booklets (load **last**, after `style.css`, `deck.css`, `video.css`) |
| `.claude/skills/reference-solution/kit/gtheme.py` | `seqsvg`, `erdsvg`, `statesvg`, `figsvg`, `build_video`, `publish_kit` (non-C4 diagrams, chips, thumbnail) |
| `.claude/skills/c4-structurizr/resources/c4-google-tokens.dsl` | every C4 view (context, containers, components, versions, zooms), rendered by c4-structurizr |
| `pdf-kit/fonts/google/` (variable `.ttf`, OFL) and `fonts/google/static/` (static instances) | Chromium (`@font-face`, offline), XeLaTeX (static), `rsvg-convert` (`fonts/fonts.conf`) |

## 1 · Colour

| Token | Hex | Use |
|---|---|---|
| Google Blue | `#4285F4` | primary accent, "new in this step", active state, primary series, client/edge/service outlines |
| Google Red | `#EA4335` | **failure only**: the BREAKS marks, negative deltas, the "Q" badge of a challenge |
| Google Yellow | `#FBBC05` | warning, hedge, cost, cache, interviewer question rule, secondary highlight |
| Google Green | `#34A853` | **fix only**: the FIX marks, positive metrics, data stores, secondary series |
| Canvas / card | `#FFFFFF` | every slide, every diagram background |
| Soft surface | `#F8F9FA` | statement slides, code blocks, alternate cards, external boxes |
| Text | `#202124` (`#141413` for display on a statement slide if more contrast is wanted) | everything |
| Muted text | `#5F6368` | captions, kickers' companions, slide number, axis labels |
| Hairlines (borders only) | `#DADCE0`, `#E8EAED` | rules, table lines |

**Text-on-light shades.** The brand hex fails 4.5:1 as *small text* on white or on its own tint (blue 3.6, red 3.6, green 3.0, yellow 1.7).
Coloured **text** therefore uses the Google 700/800 shade, while fills, rules and strokes keep the brand hex:
blue `#1967D2`, red `#C5221F`, green `#188038`, yellow `#B06000`. In CSS: `var(--g-blue-ink)` …; in Python: `gtheme.ink(colour)`.
Tints for panels: blue `#E8F0FE`, red `#FCE8E6`, green `#E6F4EA`, yellow `#FEF7E0`.

**C4 diagrams** (c4-structurizr native renderer, 2026-11-28; the c4model.com look): white box, 3 px outline, 14 px corners. In scope
(system, containers, components): outline `#1A73E8`, title `#174EA6` 25 px bold, `[Type: technology]` `#1967D2` 18 px, description
`#3C4043` 19 px. Person: outline `#174EA6` on `#E8F0FE`, a head and a body. External: outline `#80868B` on `#F1F3F4`, text `#3C4043`.
Boundary: dashed `#1A73E8` on `#F8FAFF`, its name bottom-left 22 px bold. Edges: dashed `#5F6368`, a filled arrowhead, the label 18 px
`#3C4043` on a white plate, `[technology]` 18 px italic `#5F6368`. Overlays: BREAKS `#EA4335` on `#FCE8E6`, FIX `#34A853` on
`#E6F4EA`, NEW `#F9AB00` on `#FEF7E0`, IN FOCUS `#1A73E8` on `#E8F0FE`, ALTERNATE dashed `#F9AB00`; pills 18 px, 800 weight; a flow
is a `#1A73E8` highlight under the arrow with a numbered `#1967D2` disc.

**Roles in diagrams** (the same in every video): in C4 views the role is the **shape** (person, cylinder for a store, log icon for a
queue, bucket, `>_` for a server-side app, the component icon), the colour says in scope (blue) or external (grey), and red / green /
yellow are reserved for BREAKS / FIX / NEW. Non-C4 figures (sequences, ERDs, state machines) keep their own role colours from
`gtheme.py`. There is no purple, orange or teal.

**Restraint.** White or `#F8F9FA` surfaces only inside the card. No gradients (the four-colour stripe on the thumbnail is hard-stopped, not a gradient).

**Frame and card** (2026-11-28, learned from two of the author's decks — a white card floating on a frame of colour bands, three
diagonal stripes in the corners of a title card, a large light title — and recoloured to Google): every video slide is a white card
inset 12 CSS px (18 frame px) in a `#202124` frame with a Google Yellow `#FBBC04` wedge bottom-left and a `#DADCE0` wedge on the
right, a soft shadow under the card. Chapter and challenge cards use a 28 px four-colour frame — Blue `#4285F4` top-left, `#202124`
top-right, Green `#34A853` bottom-left, Yellow `#FBBC04` bottom-right, hard stops — with three diagonal stripes in each corner and the
title centred at 52 pt, weight 500. Slide titles carry a 42 pt × 3 pt Google Blue bar instead of a full-width rule (red on a
question title). All of it is `video.css` (inline SVG backgrounds, no image files); the frame sits inside the slide padding, so no
layout moves.

## 2 · Type

| Role | Face | Weight | Where |
|---|---|---|---|
| Display (title, H1, H2, big numbers, statements) | **Plus Jakarta Sans** (fallback `Google Sans`, `Roboto`) | 700 / 600 | `--display` |
| Body, tables, labels, captions, diagram labels | **Inter** (fallback `Roboto`) | 400 / 500, labels 650 | `--body` |
| Code, keys, wire formats | **Roboto Mono** | 400 / 700 | `--mono` |
| *Editorial pairing* (narrative decks, optional) | **DM Sans** 700/500 titles + **Source Sans 3** 400/500 body (or Space Grotesk + IBM Plex Sans) | | `<body class="editorial">` |

Never fall back to Charter, Georgia, Helvetica, Arial, DejaVu or a system face. A glyph the face lacks (`⁵ ⁶ ≥ ✓`) vanishes: read the build output.

**Sizes** (HTML slide 13.333 × 7.5 in → 1920 × 1080 frame; 1 pt = 2 frame px):

| Element | Size | Weight | Face |
|---|---|---|---|
| Chapter card / title | 54 pt (108 px) | 700 | display |
| Statement (thesis, key line, question) | 38–40 pt | 600 | display |
| H1 (slide title) | 31 pt (62 px) | 700 | display |
| H2 / card label | 13 pt caps, +1.3 pt tracking | 650 | body |
| Body, table cells, cards | 19–21 pt (38–42 px) | 400 / 500 | body |
| Caption, figure note, slide number | 11–14 pt (22–28 px) | 400 / 600 | body |
| Lower third / on-screen label (if a scene needs one) | 28–32 px, 600, `#202124` on white at 92 %, 4 px blue rule, max 7 words | | body |
| Code | 16.5 pt | 400 | mono |

Minimum on-screen text at 1080p: 22 px. One idea per frame; no paragraph longer than three lines. Diagram labels: 18 px on the frame (GUIDELINES §7.6); both are measured by `check_layout.py`, not eyeballed.

## 3 · How each renderer loads the fonts

| Renderer | How |
|---|---|
| HTML → Chromium (slides, frames) | `<link rel="stylesheet" href="google-theme.css">` last; `build.py` / `render_slides.py` rewrite the relative `url()`s to file URIs, so it is **offline**. On a web page: `<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700&family=Inter:wght@400;500;600&family=Roboto+Mono:wght@400;700&display=swap" rel="stylesheet">` |
| SVG generators (`seqsvg`, `erdsvg`, `statesvg`, `figsvg`; c4-structurizr normalizes its exports to the same family) | `font-family="Inter, Roboto, sans-serif"` for every label, Plus Jakarta Sans for diagram titles; inlined into the HTML, so Chromium resolves them through `google-theme.css` |
| `rsvg-convert` (letterboxed images, chips) | `PANGOCAIRO_BACKEND=fc FONTCONFIG_FILE=pdf-kit/fonts/fonts.conf` (the kit scripts set both) |
| Remotion / React video (if a project uses it) | `npm i @remotion/google-fonts`; `import {loadFont} from "@remotion/google-fonts/PlusJakartaSans"` (weights `600`, `700`) and `…/Inter` (`400`, `500`, `600`); `await` the load with `delayRender` before the first frame; colours from the table above |
| Google Slides / Slides API | font names `Plus Jakarta Sans`, `Inter`, `Roboto Mono` (all in the Slides font menu); `Google Sans` is not offered by Slides, so use Plus Jakarta Sans for display; colours as RGB floats of the hex above |
| PPTX | the three families embedded or installed; fall back to Roboto, never Calibri or Arial |
| ffmpeg `drawtext` | `fontfile=…/fonts/google/static/PlusJakartaSans-Bold.ttf` |

## 4 · Checklist before a render is accepted

- [ ] `grep -rEi "Charter|Georgia|Helvetica|Arial|DejaVu|STIX" video.css deck.css diagrams.py` finds nothing; no hex outside the tables above.
- [ ] Frames read at a glance: tile a sample (`tile_frames.sh`) and look; small coloured text is a `*-ink` shade; no purple or orange anywhere.
- [ ] `pdffonts <booklet>.pdf` lists only Inter, PlusJakartaSans, RobotoMono (plus LatinModern for maths).
- [ ] Red appears only on failures, green only on fixes.
