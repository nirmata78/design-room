---
name: reference-solution
description: Build, rebuild, re-cut or plan the design-room reference solution for one question-bank ID — outline, written reference design (booklet PDF), diagrams, slides, script, the 60–90 minute candidate-led video (theory chapter, V1→V2→V3 carried baseline, 6–8 interviewer challenges, numbered flows, options matrix, build cost) and the YouTube/LinkedIn publish kit — in one run, with no stages and no stop. Invoke as "/reference-solution SD-96" (new) or "/reference-solution SD-08" (reworks an existing solution or older-format video); a title fragment ("/reference-solution url-shortener") also works. Use whenever the author asks to create, regenerate, re-cut, re-render or publish a solution or its video for a bank question, for an outline or script only, or to analyse a new reference video or book chapter for the format. All output stays inside the repository (never ~/Movies); a rework retires the old version. Replaces the former /solution command and the former reference-solution-video skill.
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
checklist. The picture, sound, caption and QA rules are `~/.claude/skills/slide-video-kit/STANDARD.md`; the booklet rules are
`~/.claude/skills/slide-video-kit/REFERENCE-DESIGN.md`. Where GUIDELINES and STANDARD disagree on shape or length, GUIDELINES wins.

## Files in this skill

```
SKILL.md                         this workflow
GUIDELINES.md                    the standard (what a reference solution must contain and look like)
templates/outline.template.md    the outline to fill first
templates/script-grammar.md      the spoken grammar of every chapter and challenge
```

## Paths

```
Q    = solutions/SD-NN-<slug>/                 slug: the bank title in lower case with hyphens, 2–3 words
V    = $Q/video/
SK   = .claude/skills/reference-solution/      this skill
KIT  = ~/.claude/skills/slide-video-kit        scripts/, templates/, STANDARD.md, REFERENCE-DESIGN.md
PY   = pdf-kit/.venv/bin/python                (Playwright venv, renders slides)
TTS  = ~/.cache/kokoro-tts/.venv/bin/python    (runs theory/video/build_cached.py)
MODEL= solutions/SD-96-url-shortener/          the worked example of the current format (2026-11-21): copy its patterns
```

If `$KIT` is missing, write the outline, booklet and script only, and say that rendering needs the kit.

## 0 · Resolve and prepare

1. Resolve the ID: `grep -n -i '<text>' Question-Bank.md`. Several rows match → list them and ask which. Not in the bank → write a
   cue sheet (`Cue-Sheet-Template.md`, next free ID from the bank footer) and add the bank row, then continue.
2. **Rework or new.** If `$V` holds an older-format video (a `*.script.md` and no `src/`), copy its script, `video-slides.html`,
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
thesis and definition; what this question grades; six clarifying answers; FRs and NFRs with numbers; estimates with arithmetic and a
label; the theory chapter (six parts, 4–7 mechanisms, the mechanisms-at-work pictures, an options matrix of 3–6 rows with a pick
and its cost); API and entities; V1/V2/V3 with the objection each answers; one numbered flow and one sequence per FR; **components
and technologies** (per in-scope container: the pick, how it is built, ≥ 2 rejected alternatives and why, the theory part it
rests on); 6–8 challenges with all nine beats (last = observability); build cost (AUX); recap; canon check; budget (minutes,
words, slides per chapter; 75–100 min at ≈ 0.49 s a word plus ≈ 0.45 s per reveal step).
Check: 6–8 `### Challenge` headings; no `TBD`, no empty cells. **Recompute every number.** If an `OUTLINE.md` already exists and
the author did not ask for changes, use it as it is.

**Re-cutting an existing video** (SD-08, SD-09, …): do not start from the old script. Write the outline first and map old material
into it: the old deep dives and follow-ups become challenges; the old C4 walk follows the V1 → V2 → V3 build; vocabulary slides move
into the theory chapter. Add a "From the old version" table to the outline (reused · new · dropped).

## 2 · Reference design (booklet)

Follow `$KIT/REFERENCE-DESIGN.md`. Output `$Q/SD-NN_<Title>_Reference_Design.md` (about 12–20 thousand words) and its PDF, built with
the files copied from `$KIT/templates/reference-design/` (`build-sd-booklet.sh`, `sd-preamble.tex`, `sd-callouts.lua`) as in `$MODEL`.
Same numbers, mechanisms, **technologies** and challenge order as the outline: the booklet carries the component views and a
"technology choices" stage with the same picks and rejected alternatives as sub-chapter 5.1. Check: the PDF builds; read three
pages spread across it as images.
Rework: update the existing booklet to the outline instead of starting again.

## 3 · Diagrams

`$V/diagrams.py` → `$V/svg/`, as `$MODEL/video/diagrams.py`:
- the **carried baseline** with `basesvg.Baseline` (start from `$KIT/templates/reference-solution/baseline.example.py`): every box and
  arrow declared once with `since=1|2|3` and `tag=` for challenge-only boxes; `base-v1/v2/v3`, one `flow-frN` per FR, `chK-attack` and
  `chK-fix` per challenge; layout: fixed left-to-right spine, ≥ 150 px between joined boxes, requests on the upper part of a side,
  responses on the lower; the latency budget with `basesvg.budget_bar`;
- C4 context, container and **component** views (one per in-scope service), the container view a second time with technologies,
  a container view labelled by mechanism for the theory chapter; **one sequence per functional requirement** (every core read and
  write path), one or two theory sequences showing a mechanism at protocol level, one per challenge fix; Chen and physical data
  models (`c4svg`, `seqsvg`, `erdsvg`). Existing SVGs from an older version may be reused when they meet the rules.
- **Reveal plans.** Every generator writes `<name>.steps.json` beside the SVG: the order in which the picture is drawn. Defaults:
  a sequence adds one message per step; a numbered flow adds one arrow per step; an overlay adds the marks then the note; a build
  adds boxes left to right. Where left to right is not the request flow, pass `order=` (`b.save(…, order=[…])`,
  `d.save(…, order=[…])`, tuples for boxes drawn together) or override with a `restep()` helper as in `$MODEL/video/diagrams.py`.
- Check: run clean; `rsvg-convert -w 1200 -b white` every SVG; tile them and **read every sheet**. Fix overlaps, labels on boxes,
  text too small (a row of small boxes becomes a table slide instead). Repeat until clean.

## 4 · Slides and script, from one source

Copy `$MODEL/video/src/` (`dsl.py`, `gen.py`, chapter files), `$MODEL/video/build-video.sh`, `$MODEL/video/video.css` (the
scientific style, GUIDELINES §7.1; do not restyle per question) and `deck.css`. Write the chapter files following
`$SK/templates/script-grammar.md`: each `S()` call is one logical slide and its narration, so every frame has a cue by construction.
- **Progressive disclosure** (GUIDELINES §7.2): `dsl.write()` finds the reveal units of every slide (table rows, trace events,
  cards, tiles, strips, lines, grading notes, interviewer answers, and the figure's `steps.json` units) and renders one frame per
  step. The narration places them: `"[+]"` the next unit, `"[+N]"` the next N, `"[+*]"` the rest; lines before the first marker
  are spoken with nothing revealed. `gen.py` **fails** on a slide that leaves units unrevealed or reveals too many: fix the
  markers, never switch the check off. Statement slides use `steps=False` (`key`, `say_slide`, `qs`, chapter cards).
- Helpers: `trace(kicker, title, [(time, event)], hedge=…)` for state traces; `cards((cls, title, text), …, cols=)`;
  `tech(kicker, title, pick, how, rejected, cite=)` for a technology slide; `table(..., "bt xs")` for dense tables.
- Chapters 0–9 in GUIDELINES order with ribbon cards; theory slides with class `theory`; build cost `aux`; every sub-chapter
  (5.1 components and technologies, each challenge) opens with `subchapter(label, title, ["N or C: one-sentence intro"])`.
- Voices (approved; never change without asking): `C` candidate ≈ 80 %, `I` interviewer < 10 %, `V` key lines < 5 % (every challenge
  ends "If asked, I'd say"), `N` coach < 5 %. Speech without symbols; spell acronyms (`theory/video/say.py`; add respellings there).
- Readability rules (author feedback 2026-11-17): tables or diagrams rather than monospace blocks; traces as `timeline()` tables;
  highlighted code with a language flag, short enough to read at 1080p; LaTeX for arithmetic where it helps.
- Check: `python3 $V/src/gen.py` prints logical slides, frames and words per voice and per chapter: total 10,000–12,500,
  candidate ≈ 80–88 %; then `build-video.sh --frames`, tile the **last step of every slide** (the fullest state) sixteen to a
  sheet and **read every sheet**, plus the full step sequence of at least three diagrams and three tables; fix overflow (the
  `.cite` line and the last table row are the first casualties), clipped tables, shrunken diagrams; repeat until clean. Report
  slides, frames and words per chapter against the outline budget.

## 5 · Video

Run `$V/build-video.sh` **in the background** (build_cached.py, `--dissolve 0.3 --chapter-gap 0 --captions sidecar
--reveal-fade 0.6 --max-minutes 180`; a 100-minute video takes roughly an hour on a cold TTS cache). Output
`$V/<slug>-reference.mp4` with `<slug>-reference.srt` and `.vtt` beside it, local only. QA per `$KIT/STANDARD.md` §4:
- `ffprobe`: H.264 + AAC, 1920×1080, chapters present, **no subtitle stream**; duration 75–100 min (hard limit 180);
- the `.srt` and `.vtt` exist, start at 00:00, end within a second of the video, cues ≤ 2 lines of ≤ ~45 characters;
- a frame grab from the middle of a reveal (a crossfade) and one after it: nothing drawn over the slide;
- `~/.claude/skills/audio-version/scripts/check_audio.py` on 20+ excerpts (6 inside 5.1, where the new vocabulary is); fix real mispronunciations in `say.py` and rebuild (the cache re-voices only changed
  lines); one sync probe late in the video; eight frames sampled across the length, read as images; the chapter list.
- Everything stays inside the repository: the MP4 in `$V`, the booklet PDF in `$Q` (both gitignored). Never write to `~/Movies`,
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
failed; "not watched end to end"; the paths of the MP4, the booklet PDF and the publish kit.

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
