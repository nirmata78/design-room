---
name: reference-solution
description: Build, rebuild, re-cut or plan the design-room reference solution for one question-bank ID — outline, written reference design (GitHub Markdown, no PDF), diagrams, slides, script, the 60–90 minute candidate-led video (scale line, theory chapter, V1→V2→V3 carried baseline drawn once as the C4 container view then shown as deltas, an alternate simpler path, 6–10 interviewer challenges that reach the mechanism one level down and carry the design on to V4, V5 …, numbered flows, options matrix, build cost; a measured layout gate before any frame is rendered) and the YouTube/LinkedIn publish kit — in one run, with no stages and no stop. Invoke as "/reference-solution SD-96" (new) or "/reference-solution SD-08" (reworks an existing solution or older-format video); a title fragment ("/reference-solution url-shortener") also works. Use whenever the author asks to create, regenerate, re-cut, re-render or publish a solution or its video for a bank question, for an outline or script only, or to analyse a new reference video or book chapter for the format. All output stays inside the repository (never ~/Movies); a rework retires the old version. Replaces the former /solution command and the former reference-solution-video skill.
---

# /reference-solution SD-NN — one question, from the prompt to the publish kit

**One invocation runs everything, in order, to the end: outline → reference design → diagrams → slides and script → video → QA →
publish kit → bank links → acceptance report.** There are no stages to choose and no planned stop. Stop only if a check fails twice
in a row or a tool is missing, and then say exactly what is missing. (If the author asks for an outline or a script only, stop
there — see *Partial runs* at the end.)

This is **authoring work, not an interview session**. The repository's `CLAUDE.md` interviewer rules (do not name technologies, do not
teach, ask before writing files) do **not** apply. Its confidentiality rules do: the repository is public, so write generic content
only and never copy anything from `profile.md`, `private/`, `sessions/` or `Progress-Log.md` into a tracked file.

The standard is **`GUIDELINES.md` in this folder. Read it in full first** and follow it exactly: the purpose, the fixed chapter
order, the theory chapter, the nine-beat challenge grammar, voices, picture and language rules, the canon check and the acceptance
checklist. The picture, sound, caption and QA rules are `~/.claude/skills/slide-video-kit/STANDARD.md`; the Markdown design rules are
`~/.claude/skills/slide-video-kit/REFERENCE-DESIGN.md`. Where GUIDELINES and STANDARD disagree on shape or length, GUIDELINES wins.

## Files in this skill

```
SKILL.md                         this workflow
GUIDELINES.md                    the standard (what a reference solution must contain and look like)
DESIGN-TOKENS.md                 Google colours, Google Fonts, sizes and weights, how each renderer loads them (apply to every visual)
templates/outline.template.md    the outline to fill first
templates/script-grammar.md      the spoken grammar of every chapter and challenge
RETROFIT.md                      temporary: bring an older-format solution to the current standard by delta (delete when all are done);
                                 its "Layout and fit checklist" is how to rework an old video against the layout gate
                                 Cheap path used on 2026-11-22: `dsl.META["automark"]=True` (markers placed automatically), `stack.json` + kit `ch5_1.py`
                                 (5.1 slides, stack, drill and fix-slide Rejected lines generated from one file), `c4svg.Diagram.OVERRIDE` (tech container view)
```

## Paths

```
Q    = solutions/SD-NN-<slug>/                 slug: the bank title in lower case with hyphens, 2–3 words
V    = $Q/video/
SK   = .claude/skills/reference-solution/      this skill
KIT  = ~/.claude/skills/slide-video-kit        scripts/, templates/, STANDARD.md, REFERENCE-DESIGN.md
PY   = pdf-kit/.venv/bin/python                (Playwright venv, renders slides)
TTS  = ~/.cache/kokoro-tts/.venv/bin/python    (runs theory/video/build_cached.py)
MODEL= solutions/SD-96-url-shortener/          the worked example of the 2026-11-21 format: copy its patterns, but not where
                                               GUIDELINES §3.1–3.3 and §7.5–7.7 (2026-11-22) differ; its next edition is planned in RETROFIT.md
```

If `$KIT` is missing, write the outline, booklet and script only, and say that rendering needs the kit.

## 0 · Resolve and prepare

1. Resolve the ID: `grep -n -i '<text>' Question-Bank.md`. Several rows match → list them and ask which. Not in the bank → write a
   cue sheet (`Cue-Sheet-Template.md`, next free ID from the bank footer) and add the bank row, then continue.
2. **Rework or new.** A solution whose `video/src/` exists but predates the current standard (no `$Q/stack.json`, burned-in
   captions, no reveal markers) is upgraded with `RETROFIT.md`, by delta, not rebuilt from the outline. If `$V` holds an older-format video (a `*.script.md` and no `src/`), copy its script, `video-slides.html`,
   `diagrams.py`, `video.css` and `README.md` into `$V/.vN-<format>-<YYYY-MM-DD>/`. If `$V` already holds the current format, copy
   `src/`, `diagrams.py`, `README.md` and `publish/` into `$V/.vN-<date>/`. The copy is a working reference for this run
   only: **only the current version is kept** (author's decision, 2026-11-21), so step 7 removes it. Material from an
   older series elsewhere in the repo (a merged course folder) is mapped into the outline the same way and retired at the end.
3. Read: the cue sheet section (offset into the file, ~170 lines), `levels.md` (default target `staff`, manager layer AUX),
   GUIDELINES, `references/video-examples/README.md` and the three `ANALYSIS.md`, the existing `solutions/SD-NN-*.md`,
   `$MODEL/video/OUTLINE.md`, the matching `theory/` chapters, and for the canon check any book extract under `private/books/`
   (summarise in our own words, quote nothing, copy no figure).

## 1 · Outline

`$V/OUTLINE.md` from `$SK/templates/outline.template.md`, every section filled (GUIDELINES §3–§9):
thesis and definition; **the scale line** (GUIDELINES §3.1: monthly volume, total, peak and its cause); what this question
grades; six clarifying answers; FRs and NFRs with numbers; estimates with arithmetic **from the scale line** and a label; the theory chapter (five parts, theory rendered first, 4–7 mechanisms each with its diagram type and its own infographic, one infographic per option, the mechanisms-at-work pictures, an options matrix of 3–6 rows with a pick
and its cost); API and entities; V1/V2/V3 with the objection each answers; **the canonical diagram plan** (one per level, and the delta each later slide shows,
GUIDELINES §7.5); one numbered flow and one sequence per FR; **the alternate path** (§3.2: the simpler design, what it gives
up, the crossover number); **components
and technologies** (per in-scope container: the pick, how it is built, ≥ 2 rejected alternatives and why, the theory part it
rests on; the same data goes into `$Q/stack.json`, step 2a); 6–10 challenges with all nine beats (last = observability), each fix one level down (§3.3: what is written or appended, which
failure it covers and which it does not, why this tool and not the one under it, when the simpler option is fine) and the
version it produces (V4, V5 … or "no change"); build cost (AUX); recap; canon check; budget (minutes,
words, slides per chapter; 75–100 min at ≈ 0.49 s a word plus ≈ 0.45 s per reveal step).
**Compact cut** (GUIDELINES §3.4) when the author asks for 60–80 minutes: 6 challenges, no drill interlude, no build-cost chapter, 7,800–8,800 words; worked example `solutions/SD-03-ad-click-aggregation/`. Check: 6–10 `### Challenge` headings; a scale line; an alternate path; no `TBD`, no empty cells. **Recompute every number.** If an `OUTLINE.md` already exists and
the author did not ask for changes, use it as it is.

**Re-cutting an existing video** (SD-08, SD-09, …): do not start from the old script. Write the outline first and map old material
into it: the old deep dives and follow-ups become challenges; the old C4 walk follows the V1 → V2 → V3 build; vocabulary slides move
into the theory chapter. Add a "From the old version" table to the outline (reused · new · dropped).

## 2a · Technology choices, one file

`$Q/stack.json` (shape: `$KIT/templates/reference-solution/stack.example.json`; worked: `$MODEL/stack.json`) holds, per in-scope
container: heading, kicker and title, the pick and why, how it is built (+ booklet-only `detail`), the rejected alternatives with
reasons, the summary row, the theory parts, an optional booklet `figure`, and for 4–5 of them a `drill` (probe, booklet answer,
short slide form); plus `c4` (the type and description lines of the container view with technologies) and `challenges` (per
challenge, the tool an interviewer will name and the property that rules it out). Copy `$KIT/templates/reference-solution/stack.py`
to `$V/src/`. It feeds `tech(**TECH(id))`, `SUMMARY()`, `DRILL()`, `rejl(*REJ(n))` and `diagrams.py` (`stack.C4`), and
`python3 $V/src/stack.py sync` rewrites the booklet's `<!-- stack:sections -->` and `<!-- stack:summary -->` regions and the
outline's `<!-- stack:outline -->` region (both build scripts run it). **A technology is edited in `stack.json` only**; the
narration stays hand-written, and the reveal check catches a slide whose row count changed under it.

## 2 · Reference design (Markdown only; no PDF since 2026-11-25)

Follow `$KIT/REFERENCE-DESIGN.md`. Output `$Q/SD-NN_<Title>_Reference_Design.md` (about 12–20 thousand words) built with
`$KIT/templates/reference-solution/build-md.sh` and `md_github.py` (copied into `$Q`; diagrams from PlantUML `.puml` or the video's SVGs; callouts as GitHub alerts, `> [!NOTE]`; **no pandoc, no LaTeX, no PDF**). Older solutions keep their `build-sd-booklet.sh` only until reworked (the build script passes the Google Fonts to pandoc and sets the font path for `rsvg-convert`).
Same numbers, mechanisms, **technologies** and challenge order as the outline: the booklet carries the component views and a
"technology choices" stage generated from `$Q/stack.json` (step 2a): put the two marker pairs where the sections and the stack
table go, and write only the stage's introduction and figures by hand. Check: `md_github.py` prints `GitHub-ready` (figures exist, no bare property codes, fences balanced); open three figures as images.
Rework: update the existing booklet to the outline instead of starting again.

## 3 · Diagrams

> **Deprecated 2026-11-28 — do not use PlantUML (`pumlsvg.py`, `plantuml -tsvg`) for new or reworked solutions.** Its Graphviz layout renders poorly on video; `.claude/skills/c4-structurizr` supersedes it for every C4 view, and issue #5 removes `pumlsvg.py`, `c4svg.py` and `basesvg.py` from the kit. The paragraph below documents how SD-59, SD-95 and SD-99 were built (they rebuild as-is until issue #5 re-cuts them).

**PlantUML and C4 (2026-11-25).** `$KIT/scripts/pumlsvg.py` (mirrored in the repo at `.claude/skills/reference-solution/kit/`) renders PlantUML (including the bundled C4 library, offline) to a themed SVG with a reveal plan and meta sidecar: `render(src, "svg/x.svg", kind="c4"|"seq"|"state"|"erd", level=…, order=…)`. Use it for sequences of the failing case behind each version objection, state machines, and any C4 view the native `c4svg` cannot lay out; the same SVG is copied into the Markdown design. Event versus HTTPS: `c4svg` edges take `proto="event"|"https"`, PlantUML has `ev()` / `https()`. **Pick the diagram type per mechanism**: state machine (lifecycle), sequence (protocol, race), C4 (placement), ERD (keys).

`$V/diagrams.py` → `$V/svg/`, as `$MODEL/video/diagrams.py`:
- **one canonical diagram per level** (GUIDELINES §7.5): the container view is the carried baseline, declared once in `c4svg`
  with `since=1|2|3|4…` and `tag=` per box and edge (`basesvg.Baseline` for older solutions); save views of it, never a redraw:
  `upto=1` for V1, `new=N` for every later version (V4, V5 … from the challenges), `flow=` per FR, `badges=` for mechanisms and
  products, `keep=` + `attack=`/`fix=`/`focus=` for a challenge (cropped to the boxes in focus). Each challenge's break and fix
  are drawn on the **component view** of the container involved (`c4svg`, `focus=`, `attack=`, `fix=`), not on an ad-hoc sketch; layout: fixed left-to-right spine, ≥ 150 px between joined boxes, requests on the upper part of a side,
  responses on the lower; the latency budget with `basesvg.budget_bar`;
- C4 context, container and **component** views (one per in-scope service), the container view a second time with technologies,
  a container view labelled by mechanism for the theory chapter; **one sequence per functional requirement** (every core read and
  write path), one or two theory sequences showing a mechanism at protocol level, one per challenge fix; Chen and physical data
  models (`c4svg`, `seqsvg`, `erdsvg`; both ERD kinds write a build-up plan: one entity or one relationship per step, `order=`).
  Lay every diagram out for the 16:9 figure area (wider than tall, box titles `size=` 24–28, the legend in a free column): the
  layout gate fails any label under 18 px on the frame. Existing SVGs from an older version may be reused when they meet the rules.
- **Reveal plans.** Every generator writes `<name>.steps.json` beside the SVG: the order in which the picture is drawn. Defaults:
  a sequence adds one message per step; a numbered flow adds one arrow per step; an overlay adds the marks then the note; a build
  adds boxes left to right. Where left to right is not the request flow, pass `order=` (`b.save(…, order=[…])`,
  `d.save(…, order=[…])`, tuples for boxes drawn together) or override with a `restep()` helper as in `$MODEL/video/diagrams.py`.
- Check: run clean; `rsvg-convert -w 1200 -b white` every SVG; tile them and **read every sheet**. Fix overlaps, labels on boxes,
  text too small (a row of small boxes becomes a table slide instead). Repeat until clean. The measured check comes in step 4.

## 4 · Slides and script, from one source

**Theory first (2026-11-25).** Write `ch3.py` first, run `ONLY_CHAPTER=3 python3 src/gen.py` and the layout gate on `video-theory.html`, read its frames, and only then write the other chapters (`build-video.sh` does this pass before the whole deck; `--theory` stops after it). New dsl helpers: `props()`/`pid()`/`ps()` (descriptive property slugs; bare `S1` fails the build), `mech_slide()`, `option_slide()`, `objection()`, `followups()`, `wire()`. Copy `dsl.py`, `video.css`, `build-video.sh`, `build-md.sh`, `md_github.py` from `$KIT/templates/reference-solution/`. Chapter 3 has no failure-catalogue slide; chapter 9 ends with `followups()`.

Copy `$MODEL/video/src/` (`dsl.py`, `gen.py`, chapter files), `$MODEL/video/build-video.sh`, `$MODEL/video/video.css` (the
Google theme, GUIDELINES §7.1 and `DESIGN-TOKENS.md`; do not restyle per question) and `deck.css`; the generated HTML links
`google-theme.css` last (it lives in `pdf-kit/`, which `render_slides.py` resolves), and the diagrams come from the kit generators, which
already use the theme. Write the chapter files following
`$SK/templates/script-grammar.md`: each `S()` call is one logical slide and its narration, so every frame has a cue by construction.
- **Progressive disclosure** (GUIDELINES §7.2): `dsl.write()` finds the reveal units of every slide (table rows, trace events,
  cards, tiles, strips, lines, grading notes, interviewer answers, and the figure's `steps.json` units) and renders one frame per
  step. The narration places them: `"[+]"` the next unit, `"[+N]"` the next N, `"[+*]"` the rest; lines before the first marker
  are spoken with nothing revealed. `gen.py` **fails** on a slide that leaves units unrevealed or reveals too many: fix the
  markers, never switch the check off. Statement slides use `steps=False` (`key`, `say_slide`, `qs`, chapter cards).
- Helpers: `trace(kicker, title, [(time, event)], hedge=…)` for state traces; `cards((cls, title, text), …, cols=)`;
  `tech(**TECH(id))` for a technology slide (from `stack.json`); `table(..., "bt xs")` for dense tables; `rejl(*REJ(n))` as the
  last element of every challenge's fix slide (after the mechanism and property strips: `strip(...) + rejl(*REJ(n))`, or
  `extra=rejl(...)`), with one candidate line naming the rejected tool and why.
- **Drill interlude** at the end of 5.1, after the stack slide (~2 min): a `qs()` slide where the coach hands the viewer the
  interviewer's seat ("which box would you drill, and what is your one question?", 3 s pause), then a table from `DRILL()`
  (box · probe · what a strong answer names), each row read as `I:` probe then `N:` the answer, and a grading note.
- Chapters 0–9 in GUIDELINES order with ribbon cards; theory slides with class `theory`; build cost `aux`; every sub-chapter
  (5.1 components and technologies, each challenge) opens with `subchapter(label, title, ["N or C: one-sentence intro"])`.
- Voices (approved; never change without asking): `C` candidate ≈ 80 %, `I` interviewer < 10 %, `V` key lines < 5 % (every challenge
  ends "If asked, I'd say"), `N` coach < 5 %. Speech without symbols; spell acronyms (`theory/video/say.py`; add respellings there).
- Readability rules (author feedback 2026-11-17, 2026-11-22): tables or diagrams rather than monospace blocks; traces as
  `timeline()` tables; **code as `pseudo(src, hl=(…))` by default**, `code(src, "go", hl=…)` only when the idiom is the lesson
  (≤ 56 characters × 12 lines, refused otherwise; key lines marked); LaTeX for arithmetic where it helps; the caps of GUIDELINES
  §7.6 (≈ 95 words, 7 rows, one strip under a challenge figure).
- Check: `python3 $V/src/gen.py` prints logical slides, frames and words per voice and per chapter: total 10,000–12,500 (compact cut 7,800–8,800),
  candidate ≈ 80–88 %. Then **the layout gate**:
  `$PY $KIT/scripts/check_layout.py --html $V/video-slides.html` must print **0 failures** (overflow, overlap, label wider than its
  box, text under 22 px or diagram labels under 18 px at 1080p, code past 56 × 12). Read the warnings (`dense`, `redraw`) and act
  on them. `--only 4,48 --shots DIR` writes 1920 × 1080 PNGs of chosen slides (last step) without rendering frames: use it to
  look at what you fixed. `build-video.sh` runs the gate before the frames and `render_slides.py` runs it again, so a failing
  deck never becomes a video (`LAYOUT_CHECK=warn` only for an old video being retrofitted). Then `build-video.sh --frames`, tile the **last step of every slide** (the fullest state) sixteen to a
  sheet and **read every sheet**, plus the full step sequence of at least three diagrams and three tables; fix overflow (the
  `.cite` line and the last table row are the first casualties), clipped tables, shrunken diagrams; repeat until clean. Report
  slides, frames and words per chapter against the outline budget.

## 5 · Video

Run `$V/build-video.sh` **in the background** (build_cached.py, `--dissolve 0.3 --chapter-gap 0 --captions sidecar
--reveal-fade 0.6 --max-minutes 180`; a 100-minute video takes roughly an hour on a cold TTS cache). Output
`$V/<slug>-reference.mp4` with `<slug>-reference.srt` and `.vtt` beside it, local only. QA per `$KIT/STANDARD.md` §4:
- `ffprobe`: H.264 + AAC, 1920×1080, chapters present, **no subtitle stream**; duration 75–100 min (hard limit 180);
- the `.srt` and `.vtt` exist, start at 00:00, end within a second of the video, cues ≤ 2 lines of ≤ 42 characters (SRT
  including the `Name: ` prefix on a speaker change); every VTT cue opens with a `<v Name>` voice span;
- a frame grab from the middle of a reveal (a crossfade) and one after it: nothing drawn over the slide;
- `~/.claude/skills/audio-version/scripts/check_audio.py` on 20+ excerpts (6 inside 5.1, where the new vocabulary is); fix real mispronunciations in `say.py` and rebuild (the cache re-voices only changed
  lines); one sync probe late in the video; eight frames sampled across the length, read as images; the chapter list.
- Everything stays inside the repository: the MP4 in `$V`, the Markdown design and its `diagrams/` in `$Q`. Never write to `~/Movies`,
  Google Drive, any cloud folder or anywhere outside the repository (author's decisions, 2026-11-13 and 2026-11-21).

## 6 · Publish kit and links

1. `$V/README.md`: length, chapters with times, the challenge list, rebuild command, QA done, the canon check table.
2. `$V/publish/meta.json` as in `$MODEL/video/publish/` (YouTube title ≤ 100 characters, description, tags, thumbnail text, LinkedIn post
   with a hook under ~140 characters), then `$KIT/scripts/publish_kit.py`. **Look at the thumbnail.** Labels: synthetic voices, built
   with Claude Code, numbers illustrative, not reviewed by a person. The upload steps include the caption file: YouTube Studio →
   Subtitles → Add language English → Upload file → `<slug>-reference.srt` (with timing).
3. Update `solutions/VIDEOS.md`, the bank row in `Question-Bank.md` (link `solutions/SD-NN-<slug>/`), `solutions/README.md`.
4. Never upload, post, commit or push. The author does those.

## 7 · Acceptance and report

Go through GUIDELINES §10 line by line: pass or fail with evidence; fix what fails; report each failed line, not a summary.
**Retire the old version** once the new MP4 has passed QA: delete `$V/.v*/`, the older MP4 and its `*.script.md` (`git rm` if
tracked), and any old SVG the new `diagrams.py` no longer writes; fix every link that pointed at them (`grep -rn` the old names).
Never before QA passes. Then report: files written; length, slides and words; checks run and their results; anything skipped or
failed; "not watched end to end"; the paths of the MP4, the Markdown design and the publish kit.

## Partial runs

- **Outline only / script only**: on request, stop after step 1 (show the outline: it is the cheapest place to change direction) or
  after step 4 with `--frames`.
- **Adding a reference.** A new video or chapter the author wants to learn from goes in `references/video-examples/NN-<slug>/` with an
  `ANALYSIS.md` in the shape of the existing ones (agenda with times, script architecture, diagramming approach, gaps, reusable
  devices). Media, transcripts and book text stay untracked. Then add one row to GUIDELINES §2 and change a rule only if the
  reference shows something the existing ones do not.

## Running several questions at once

Parallel runs are fine. Each run owns only its `$Q` folder. Shared files (`Question-Bank.md`, `solutions/VIDEOS.md`,
`solutions/README.md`, `theory/video/say.py`) are edited with a short read-modify-write script at the moment of the change, never from a
stale copy; or reported back for the coordinating session to apply. Render at most three videos at the same time.
