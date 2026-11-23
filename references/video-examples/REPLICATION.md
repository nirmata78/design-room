# How to replicate the reference style with our own video kit

> **Superseded as the source of rules (2026-11-12).** The decisions taken from this analysis now live in
> `.claude/skills/reference-solution/GUIDELINES.md`. Build-plan tasks 1–3 are done (slide types in the kit's
> `video.css`, `scripts/basesvg.py`). The whiteboard skin (§4) was not chosen: house slides with a carried baseline instead.
> This file stays as the working notes behind those decisions.

Two third-party references (see [README](README.md)) decomposed into a build spec for our kit
(`~/.claude/skills/slide-video-kit` + `system-design-video`, house rules in `STANDARD.md`).
**We already exceed both on content** (full round, estimates, wire formats, C4, sequences, EM layer, follow-ups).
What they do better is **format**: a single visible canvas that *grows*, deep-dive slides that read as questions,
and a repeatable grammar. This file lists what to borrow, what to leave, and how to build it.

## 1 · The two references side by side

| | 01 Batch inference | 02 URL shortener | Our kit (SD-08/09) |
|---|---|---|---|
| Length | 66:34 | 38:42 | 35–45 min, hard limit 45 |
| Voices / pace | 1 · ~130 wpm | 1 · ~150 wpm | 4 (interviewer, candidate, key-line, coach) |
| Visual medium | hand-drawn whiteboard, ink colours as annotations | hand-drawn frames with colour-filled boxes | light HTML slides + generated SVG (C4, sequence, Chen ERD) |
| Slide density | very low, grows live | low–medium, 3–4 builds per frame | one idea per slide, ~85 slides |
| Baseline | V1 → V2 → V3 (3 versions) | 1 flow per FR (3 workflows + analytics) | C4 → rule → sequence → code per path |
| Deep dives | 7 "challenges" (45 of 66 min) | 3 (≈ 12 of 38 min) | 4 + 5 follow-ups |
| Numbers | batch arithmetic, latency budget | alias-space capacity table | estimates as arithmetic with consequences |
| Failure/ops | strong (lease, fencing, outbox, idempotency, fairness, cancel, observability) | light | strong, with SLOs and cost |
| Captions | none | none | burned in |
| Estimated bar | staff-ish | senior | staff L6/L7 + AUX EM layer |

## 2 · What to adopt (ranked by value)

1. **Challenge-slide template ("DD-N") — from 01.** A deep-dive slide is a *question*, not a topic:
   `Q:` title → chip strip → the baseline diagram, the attacked component outlined (dashed red) → case/state trace → green fix →
   red "what if the fix fails?" → second fix. Add a `.dd` slide type to `templates/video.css` and a generator in `diagrams.py`
   that takes the *same* baseline SVG and a list of `(component, state)` highlights, so DD slides are produced from one source.
2. **Carry one baseline diagram through all deep dives — from 01.** Today each deep dive draws its own picture. Add
   `baseline.svg` (the container view with a fixed left→right spine and a return lane) and overlay per-dive annotations
   (outline, ghost node, green replacement) with `scripts/overlay.py` (new, see §5).
3. **Versioned baseline V1 → V2 → V3 — from 01.** In the HLD, build the design in three slides, each answering the previous
   one's objection (`V1 sync` → `V2 batch` → `V3 queue + lease`), *before* the C4 container view. Keep our C4 views afterwards.
4. **Chip strip under every title — from 01.** One line previewing the slide content (`10K RPS · P95 < 2 s · 100/batch`).
   Cheap to add (`<p class="chips">`); lets a viewer re-orient in 2 s. We already number slides; add this.
5. **Section progress ribbon — from 02.** Five chevrons (Requirements › APIs & Entities › HLD › Deep dives › Recap), current one
   highlighted, shown on each section-opening slide. Add `.ribbon` with `data-step="3"`.
6. **FR → API → entity traceability tags — from 02.** Every API slide shows `serves FR1, FR3 · writes UrlMapping`. One line.
7. **IN / OUT scope pair + "core is N things" bar — from 02.** Use for the requirements slide; we have scope but not as a side-by-side artifact.
8. **Numbered-arrow workflow figure — from 02.** For each FR, one component diagram with arrows numbered 1…N and dashed returns.
   Our sequence diagrams carry the same content; use the numbered component version as the *first* picture of a path and the
   sequence as the *second*. Same numbers on both.
9. **Latency-budget bar — from 01.** One horizontal stacked bar whose segments sum to the SLO with an explicit spare segment.
   Add to `diagrams.py` (`budget_bar(stages, total, spare)`).
10. **Symptom-pair diagnosis table — from 01.** `queue age ↑ + GPU util high → overload`. Use in every operations section.
11. **"Every solution creates the next question" bridge and "different flows need different guarantees" thesis — from 02.**
    Put the bridge sentence in the coach's repertoire and the thesis in the closing key line (`V:`).
12. **Final clean recap diagram (icon-based) — from 01.** After the build-up, show one polished full-system picture.
    Our C4 container view can be re-skinned for this (rounded, colour families by role, icons).

13. **"If asked, I'd say…" closer on every deep dive — from 01.** A 2–4 sentence model answer, spoken by the candidate (`V:` key-line voice)
    as the last beat of each deep dive. We have key lines at the thesis and follow-ups; make it a fixed slot per deep dive.
14. **Precision statements and hedges — from 01.** Name the guarantee exactly ("one authoritative client-visible result per logical
    request, *not* exactly-once execution") and label every number `illustrative / initial target / measured`. Add a line to the
    candidate's style guide and to the coach's "tells".
15. **Interviewer-voice bridge into each deep dive — from 01.** Our `I:` voice already exists; use the pattern *naive answer → case with
    numbers → break it* so the interviewer's question is answered by a failing example before the fix.

## 3 · What to leave

- Sponsor/CTA blocks, product screenshots, "book a session" outros.
- Single-voice lecturing with long unbroken takes (our interviewer/candidate/coach split is the stronger teaching device).
- Missing estimation and cost (02) and no captions (both).
- Asserted technology (02: "Redis enters here") — keep our rule: every store against its rejected alternatives.

## 4 · Visual spec — "whiteboard" skin (optional variant)

To produce a video in the reference look rather than the house light-slide look, add a second CSS skin and a rough-stroke renderer.

| Element | Spec (measured from reference frames) |
|---|---|
| Canvas | white, 16:9, thin light-grey frame border, tiny grey frame label top-left (`10 · Complete the synchronous return path`) |
| Title | hand-drawn font (e.g. Excalifont / Virgil via Google Fonts), ~34 px at 1080p, top-left; **number prefix** (`DD3`, `09`) |
| Chips | 11–12 px blue monospace-ish line under the title, separated by `·` |
| Boxes | rounded rectangle, 2 px stroke, roughness ≈ 1 (rough.js `roughness:1`, `bowing:1`), ≤ 3 words, centre-aligned |
| Fill (02 style) | pastel: client blue `#a5d8ff`, service purple `#d0bfff`, data mint `#96f2d7`, decision yellow `#ffec99`, good green `#b2f2bb`, bad red `#ffc9c9` |
| Ink (01 style) | black baseline; blue = step being added; red = question/failure; green = fix/defense; dashed outline = under attack/replacement |
| Arrows | solid black = request, dashed teal/green = response, dashed purple = async; numbered labels `1. POST /…` 11–12 px |
| Text blocks | handwritten, 12–14 px, left-aligned beneath diagrams; problem/solution pair as red box beside green box |
| Takeaway | one yellow rounded box per frame |
| Builds | author-order reveal: a slide is rendered as N cumulative frames; each frame adds one element (`data-step`). Hold each build 2–6 s |
| Safe-area | ≥ 6 % margin; a diagram never exceeds ~60 % of frame height so text blocks fit beneath |

Implementation route: generate SVG with **rough.js** server-side (Node) or `roughpy`; render with the existing slide renderer
(`render_slides.py`). Use cumulative `data-step` layers to emit the build frames, then let `build_video.py` hold each for its
share of the narration. Keep the default light-slide skin for the main series; use the whiteboard skin for "article" style videos.

## 5 · Build plan (ordered)

| # | Task | Output | Effort |
|---|---|---|---|
| 1 | Add `.dd`, `.chips`, `.ribbon`, `.scope2`, `.trace` CSS to `slide-video-kit/templates/video.css` | new slide types | S |
| 2 | `diagrams.py`: `budget_bar`, `baseline_overlay`, `symptom_table` helpers | SVG generators | M |
| 3 | `scripts/overlay.py`: take `baseline.svg` + `[(node, style)]` → annotated SVG per deep dive | reusable overlays | M |
| 4 | Rewrite the SD-09 HLD section as V1→V2→V3 then C4 (pilot) | one video re-cut | M |
| 5 | Convert two SD-09 deep dives to the challenge template with the carried baseline | pilot DD slides | M |
| 6 | Whiteboard skin (§4) + rough.js renderer; build one **article-style** video (e.g. SD-25 rate limiter) in it | `video/` variant | L |
| 7 | Update `STANDARD.md` §1c "Reference-derived rules" with items 1–15 | house rules | S |
| 8 | Add a `reference-analysis` checklist to `system-design-video` so new reference videos are decomposed the same way | skill doc | S |

## 6 · Script grammar to reuse (copy into the coach/candidate scripts)

```
HOOK        "<problem> looks too simple. It isn't testing <the obvious thing>; it tests <3–5 real challenges>."
FRAMEWORK   "I'll go scenarios → FR/NFR → entities → APIs → HLD → challenge-driven deep dives."
RULE        "Don't go too deep too early. Simple version first; say what is intentionally simple and where I'll fix it."
SCOPE       IN/OUT pair → "the core is three things: …"
NFR         quantified (<number> per month, P95 <ms>), CAP split per workflow
HLD         one workflow per FR; arrows numbered; "this proves it works; it does not solve scale"
BRIDGE      "It works. The next question isn't whether it works — it's where it breaks first."
DEEP DIVE   weakness → (pause: viewer answers) → naive options + why each annoys → improvement
            → "every solution creates the next question" → next weakness → one-line recommendation
RECAP       one bar per path, one sentence each; thesis: "different flows need different guarantees"
```

## 7 · Re-running the analysis

```
yt-dlp --no-playlist -f "bv*[height<=1080]+ba/b" --merge-output-format mp4 -o original.%(ext)s <url>
yt-dlp --no-playlist --skip-download --write-auto-subs --sub-langs en --sub-format vtt -o subs <url>   # 429 → retry later or transcribe locally
ffmpeg -i original.mp4 -vf "fps=1/20,scale=960:-1" -q:v 4 frames/t%04d.jpg
ffmpeg -framerate 1 -i frames/t%04d.jpg -vf "select='not(mod(n,6))',scale=480:-1,tile=4x4" -fps_mode vfr sheet_%02d.jpg
```
