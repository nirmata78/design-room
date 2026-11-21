---
name: reference-solution
description: Build or rebuild, end to end, the design-room reference solution for one question-bank ID — outline, written reference design (booklet PDF), diagrams, slides, script, the 60–90 minute video and the YouTube/LinkedIn publish kit — in one run, with no stages and no stop. Invoke as "/reference-solution SD-96" (new) or "/reference-solution SD-08" (reworks an existing solution or older-format video); a title fragment ("/reference-solution url-shortener") also works. All output stays inside the repository (never ~/Movies); a rework retires the old version. Use whenever the author asks to create, regenerate, re-cut, re-render or publish a solution or its video for a bank question. Replaces the former /solution command.
---

# /reference-solution SD-NN — one question, from the prompt to the publish kit

**One invocation runs everything, in order, to the end: outline → reference design → diagrams → slides and script → video → QA →
publish kit → bank links → acceptance report.** There are no stages to choose and no planned stop. Stop only if a check fails twice
in a row or a tool is missing, and then say exactly what is missing.

This is **authoring work, not an interview session**. The repository's `CLAUDE.md` interviewer rules (do not name technologies, do not
teach, ask before writing files) do **not** apply. Its confidentiality rules do: the repository is public, so write generic content
only and never copy anything from `profile.md`, `private/`, `sessions/` or `Progress-Log.md` into a tracked file.

The standard is `.claude/skills/reference-solution-video/GUIDELINES.md`. **Read it in full first** and follow it exactly. The picture,
sound, caption and QA rules are `~/.claude/skills/slide-video-kit/STANDARD.md`; the booklet rules are
`~/.claude/skills/slide-video-kit/REFERENCE-DESIGN.md`.

## Paths

```
Q    = solutions/SD-NN-<slug>/                 slug: the bank title in lower case with hyphens, 2–3 words
V    = $Q/video/
KIT  = ~/.claude/skills/slide-video-kit        scripts/, templates/, STANDARD.md, REFERENCE-DESIGN.md
PY   = pdf-kit/.venv/bin/python                (Playwright venv, renders slides)
TTS  = ~/.cache/kokoro-tts/.venv/bin/python    (runs theory/video/build_cached.py)
MODEL= solutions/SD-94-denylist-system/        the worked example of the current format: copy its patterns
```

If `$KIT` is missing, write the outline, booklet and script only, and say that rendering needs the kit.

## 0 · Resolve and prepare

1. Resolve the ID: `grep -n -i '<text>' Question-Bank.md`. Several rows match → list them and ask which. Not in the bank → write a
   cue sheet (`Cue-Sheet-Template.md`, next free ID from the bank footer) and add the bank row, then continue.
2. **Rework or new.** If `$V` holds an older-format video (a `*.script.md` and no `src/`), copy its script, `video-slides.html`,
   `diagrams.py`, `video.css` and `README.md` into `$V/.vN-<format>-<YYYY-MM-DD>/`. If `$V` already holds the current format, copy
   `src/`, `diagrams.py`, `README.md` and `publish/` into `$V/.vN-<date>/`. The copy is a working reference for this run
   only: **only the current version is kept** (author's decision, 2026-11-21), so step 7 removes it (see there). Material from an
   older series elsewhere in the repo (a merged course folder) is mapped into the outline the same way and retired at the end.
3. Read: the cue sheet section (offset into the file, ~170 lines), `levels.md`, GUIDELINES, `references/video-examples/README.md`
   and the three `ANALYSIS.md`, the existing `solutions/SD-NN-*.md`, `$MODEL/video/OUTLINE.md`, the matching `theory/` chapters, and
   for the canon check any book extract under `private/books/` (summarise in our own words, quote nothing, copy no figure).

## 1 · Outline

`$V/OUTLINE.md` from `.claude/skills/reference-solution-video/templates/outline.template.md`, every section filled (GUIDELINES §3–§9):
thesis and definition; what this question grades; six clarifying answers; FRs and NFRs with numbers; estimates with arithmetic and a
label; the theory chapter (six parts, 4–7 mechanisms, an options matrix of 3–6 rows with a pick and its cost); API and entities;
V1/V2/V3 with the objection each answers; one numbered flow per FR; 6–8 challenges with all nine beats (last = observability); build
cost (AUX); recap; canon check; budget (minutes, words, slides per chapter, 60–90 min at ≈ 0.49 s a word with the pacing beats).
Recut: a "From the old version" table (reused · new · dropped). Check: 6–8 `### Challenge` headings; no `TBD`, no empty cells.
**Recompute every number.** If an `OUTLINE.md` already exists and the author did not ask for changes, use it as it is.

## 2 · Reference design (booklet)

Follow `$KIT/REFERENCE-DESIGN.md`. Output `$Q/SD-NN_<Title>_Reference_Design.md` (about 12–20 thousand words) and its PDF, built with
the files copied from `$KIT/templates/reference-design/` (`build-sd-booklet.sh`, `sd-preamble.tex`, `sd-callouts.lua`) as in `$MODEL`.
Same numbers, mechanisms and challenge order as the outline. Check: the PDF builds; read three pages spread across it as images.
Rework: update the existing booklet to the outline instead of starting again.

## 3 · Diagrams

`$V/diagrams.py` → `$V/svg/`, as `$MODEL/video/diagrams.py`:
- the **carried baseline** with `basesvg.Baseline` (start from `$KIT/templates/reference-solution/baseline.example.py`): every box and
  arrow declared once with `since=1|2|3` and `tag=` for challenge-only boxes; `base-v1/v2/v3`, one `flow-frN` per FR, `chK-attack` and
  `chK-fix` per challenge; layout: fixed left-to-right spine, ≥ 150 px between joined boxes, requests on the upper part of a side,
  responses on the lower;
- C4 context and container views, one sequence per core flow and per challenge fix, Chen and physical data models (`c4svg`, `seqsvg`,
  `erdsvg`); `basesvg.budget_bar` for the latency budget. Existing SVGs from an older version may be reused when they meet the rules.
- Check: run clean; `rsvg-convert -w 1200 -b white` every SVG; tile them and **read every sheet**. Fix overlaps, labels on boxes,
  text too small (a row of small boxes becomes a table slide instead). Repeat until clean.

## 4 · Slides and script, from one source

Copy `$MODEL/video/src/` (`dsl.py`, `gen.py`, chapter files) and `$MODEL/video/build-video.sh`, plus the current `$KIT/templates/video.css`
and `deck.css` (re-copy; older folders hold old CSS; then append `$MODEL/video/video.css`'s 2026-11-20 additions: `table.tl`, code sizes,
`.th.card`). Write the chapter files: each `S()` call is one slide and its narration, so every frame has a cue by construction.
- Chapters 0–9 in GUIDELINES order with ribbon cards; theory slides with class `theory`; build cost `aux`; every sub-chapter
  (each challenge) opens with `subchapter(label, title, ["N: one-sentence intro"])`.
- Voices (approved; never change without asking): `C` candidate ≈ 80 %, `I` interviewer < 10 %, `V` key lines < 5 % (every challenge
  ends "If asked, I'd say"), `N` coach < 5 %. Speech without symbols; spell acronyms (`theory/video/say.py`; add respellings there).
- Readability rules (author feedback 2026-11-17): tables or diagrams rather than monospace blocks; traces as `timeline()` tables;
  highlighted code with a language flag, short enough to read at 1080p; LaTeX for arithmetic where it helps.
- Check: `python3 $V/src/gen.py` prints slides and words per voice: total 8,000–12,000, candidate ≈ 80 %; then
  `build-video.sh --frames`, tile **all** frames eight to a sheet and **read every sheet**; fix overflow, clipped tables, shrunken
  diagrams; repeat until clean. Report slides and words per chapter against the outline budget.

## 5 · Video

Run `$V/build-video.sh` **in the background** (build_cached.py, `--dissolve 0.3 --chapter-gap 0`; a 90-minute video takes roughly an
hour on a cold TTS cache). Output `$V/<slug>-reference.mp4`, local only. QA per `$KIT/STANDARD.md` §4:
- `ffprobe`: H.264 + AAC, 1920×1080, chapters present, no subtitle stream; duration 60–90 min (hard limit 180);
- `theory/video/check_audio.py` on 20+ excerpts; fix real mispronunciations in `say.py` and rebuild (the cache re-voices only changed
  lines); one sync probe late in the video; eight frames sampled across the length, read as images; the chapter list.
- Everything stays inside the repository: the MP4 in `$V`, the booklet PDF in `$Q` (both gitignored). Never write to `~/Movies`,
  Google Drive, any cloud folder or anywhere outside the repository (author's decisions, 2026-11-13 and 2026-11-21).

## 6 · Publish kit and links

1. `$V/README.md`: length, chapters with times, the challenge list, rebuild command, QA done, the canon check table.
2. `$V/publish/meta.json` as in `$MODEL/video/publish/` (YouTube title ≤ 100 characters, description, tags, thumbnail text, LinkedIn post
   with a hook under ~140 characters), then `$KIT/scripts/publish_kit.py`. **Look at the thumbnail.** Labels: synthetic voices, built
   with Claude Code, numbers illustrative, not reviewed by a person.
3. Update `solutions/VIDEOS.md`, the bank row in `Question-Bank.md` (link `solutions/SD-NN-<slug>/`), `solutions/README.md`.
4. Never upload, post, commit or push. The author does those.

## 7 · Acceptance and report

Go through GUIDELINES §10 line by line: pass or fail with evidence; fix what fails. **Retire the old version** once the new
MP4 has passed QA: delete `$V/.v*/`, the older MP4 and its `*.script.md` (`git rm` if tracked), and any old SVG the new
`diagrams.py` no longer writes; fix every link that pointed at them (`grep -rn` the old names). Never before QA passes. Then report: files written; length, slides and words;
checks run and their results; anything skipped or failed; "not watched end to end"; the paths of the MP4, the booklet PDF and the
publish kit.

## Running several questions at once

Parallel runs are fine. Each run owns only its `$Q` folder. Shared files (`Question-Bank.md`, `solutions/VIDEOS.md`,
`solutions/README.md`, `theory/video/say.py`) are edited with a short read-modify-write script at the moment of the change, never from a
stale copy; or reported back for the coordinating session to apply. Render at most three videos at the same time.
