---
name: solution
description: Generate or re-generate a full design-room reference solution for one question — outline, written reference design, diagrams, slides, script and the 60–90 minute video — in stages with a stop for the author's approval. Invoke as "/solution SD-24", "/solution distributed-lock", "/solution SD-09 recut", or "/solution SD-24 <stage>" where stage is one of status, outline, design, diagrams, slides, script, video, publish. Use whenever the author asks to create, regenerate, re-cut or continue a solution or its video for a bank question.
---

# /solution — one question, from the prompt to the video

This is **authoring work, not an interview session**. The repository's `CLAUDE.md` describes how to run a mock
interview; its interviewer rules (do not name technologies, do not teach, ask before writing files) do **not**
apply here. Its confidentiality rules do: this is a public repository, so write generic content only and never
copy anything from `profile.md`, `private/`, `sessions/` or `Progress-Log.md` into a tracked file.

The standard is `.claude/skills/reference-solution-video/GUIDELINES.md`. **Read it in full before any stage.**
Follow it exactly; when unsure, re-read the section instead of guessing.

## Arguments

`/solution <question> [recut] [stage]`

- `<question>`: a bank ID (`SD-24`) or part of a title (`distributed-lock`, `chat`).
  Resolve it with `grep -n -i '<text>' Question-Bank.md`. If more than one row matches, list them and ask which.
- `recut`: the question already has a solution or video in the older format; rebuild it in the new one.
  Assume `recut` whenever `solutions/SD-NN-*/video/` already holds a script and no `OUTLINE.md`.
- `[stage]`: run only that stage. With no stage, run `status`, then continue from the first unfinished stage.

## Rules for every stage

1. **One stage at a time.** Finish it, run its check, tick it in the progress list at the top of
   `video/OUTLINE.md`, report, then continue to the next. Never skip a check.
2. **Stop after the outline** and wait for the author to approve or change it. This is the only planned stop.
   Do not stop elsewhere to ask permission; do stop if a check fails twice or a tool is missing.
3. **Never invent a measurement.** Every number is arithmetic from stated inputs and carries a label:
   illustrative, initial target, or measured.
4. **Own words and own drawings.** The material in `references/video-examples/` and any book extract is for
   structure and for the canon check. Quote nothing from it and copy no figure.
5. **Look at what you render.** Frames are checked on contact sheets by reading the image, not assumed.
6. **Report honestly**: what was built, what was checked and how, what failed, what was skipped.
   Say "not watched end to end" for any video.
7. Do not commit, push, upload or post. The author does those.

## Paths

```
Q    = solutions/SD-NN-<slug>/                 e.g. solutions/SD-24-distributed-lock/
V    = $Q/video/
KIT  = ~/.claude/skills/slide-video-kit        scripts/, templates/, STANDARD.md, REFERENCE-DESIGN.md
PY   = pdf-kit/.venv/bin/python                (the Playwright venv, needed to render slides)
```

`<slug>` is the question title in lower case with hyphens, two to three words. If `$KIT` does not exist, do
stages `outline`, `design` and `script` only, and say that rendering needs the kit.

## Stage `status`

Print one table: for each stage below, the file that proves it is done and whether it exists.
Also print the bank row, the cue-sheet location (`grep -n '^### SD-NN' questions/*.md`), and whether this is a
new solution or a recut.

## Stage `outline`  (ends with a STOP)

1. Read: the cue sheet section for the question (offset into the file; about 170 lines), `levels.md`,
   `GUIDELINES.md`, `references/video-examples/README.md` and the three `ANALYSIS.md` files,
   the existing `solutions/SD-NN-*.md` and reference design if they exist, the matching `theory/` chapters
   (`grep -ril '<topic words>' theory/*.md`), and any source the author named in the request.
2. **Recut only:** read the old script and slide list. Copy the old sources into `$V/.vN-<format>-<date>/`
   (script, `video-slides.html`, `diagrams.py`, `video.css`) so nothing is lost. Do not delete the old MP4.
3. Copy `.claude/skills/reference-solution-video/templates/outline.template.md` to `$V/OUTLINE.md`.
   Put this progress list at the very top:
   `- [ ] outline approved  - [ ] design  - [ ] diagrams  - [ ] slides  - [ ] script  - [ ] video  - [ ] publish`
4. Fill **every** section of the outline. No empty cell, no "TBD". In particular:
   - the theory chapter: all six parts, 4–7 mechanisms, an options matrix of 3–6 rows with a pick and its cost;
   - V1, V2, V3, each with the objection it answers;
   - one numbered flow per functional requirement;
   - 6–8 challenges with all nine beats, one line per beat; the last challenge is observability;
   - the canon check table;
   - the budget table: minutes, words (minutes × 133) and slides per chapter, totalling 60–90 minutes.
   - **Recut only:** add a section "From the old version": a three-column table of reused, new and dropped material.
5. Check: `grep -c '^### Challenge' $V/OUTLINE.md` is 6–8; no line contains `TBD` or an empty table cell `| |`.
6. **STOP.** Show the author: thesis, the options matrix, V1/V2/V3, the challenge list (question and fix for
   each), the budget total, and for a recut the reused/new/dropped table. Ask for approval or changes.

## Stage `design`  (the written reference design)

Follow `$KIT/REFERENCE-DESIGN.md` exactly. Output: `$Q/SD-NN_<Title>_Reference_Design.md`, about 15–22 thousand
words, in the structure of `solutions/SD-09-chat-messaging/SD-09_Chat_Messaging_Reference_Design.md`, plus the
build files copied from `$KIT/templates/reference-design/`. It carries the same numbers, mechanisms and
challenge order as the outline, and adds a theory part matching outline §3. Build the PDF with the copied
`build-sd-booklet.sh`. Check: the PDF exists and opens; read three pages spread across it as images.
Recut: update the existing reference design to the outline instead of writing a new one; list what changed.

## Stage `diagrams`

Write `$V/diagrams.py` → `$V/svg/`.

1. The **carried baseline**, from `$KIT/templates/reference-solution/baseline.example.py`: declare every box
   and arrow once with `since=1|2|3` (and `tag=` for boxes that appear only in a challenge). Save
   `base-v1/v2/v3.svg`, one `flow-frN.svg` per functional requirement, and `chK-attack.svg` and `chK-fix.svg`
   for every challenge. Layout: fixed left-to-right spine; at least 150 px between boxes joined by a labelled
   arrow; requests on the upper part of a box side, responses on the lower part.
2. C4 context and container views, one sequence per core flow and per challenge fix, the conceptual (Chen) and
   physical data models, with `c4svg`, `seqsvg`, `erdsvg` as in `solutions/SD-09-chat-messaging/video/diagrams.py`.
3. `basesvg.budget_bar` for the latency or capacity budget.
4. Check: `python3 $V/diagrams.py` runs clean. Convert every SVG to PNG
   (`rsvg-convert -w 1200 -b white`), tile them 2×3 with ffmpeg, and read each sheet. Fix any overlap, any
   label on top of a box, any text too small to read. Repeat until clean.

## Stage `slides`

1. `cp $KIT/templates/video.css $KIT/templates/deck.css $V/` (always re-copy; older folders hold old CSS).
2. Write `$V/video-slides.html` from the outline, one idea per slide, using the slide types shown in
   `$KIT/templates/reference-solution/slides.example.html` and the existing types in
   `$KIT/templates/slides.example.html`. Put an HTML comment `<!-- v-NN name -->` before each slide.
   Expect 150–220 slides. Every chapter opens with a ribbon card. Every theory slide has class `theory`.
   The build-cost chapter has class `aux`.
3. Render: `$PY $KIT/scripts/render_slides.py --html $V/video-slides.html --prefix v --svg-dir $V/svg --css-dir $V --out $V/frames`
4. Check: tile **all** frames eight to a sheet (`$KIT/scripts/tile_frames.sh`) and read every sheet. Fix text
   overflow, clipped tables, diagrams that shrank too small (split the slide). Re-render until clean.
   Report the slide count per chapter against the budget.

## Stage `script`

1. Write `$V/<slug>-reference.script.md` following
   `.claude/skills/reference-solution-video/templates/script-grammar.md`, one `[slide: v-NN]` cue per slide, in order.
2. Voices per GUIDELINES §6. At least 40–70 spoken words on every diagram slide, walking each box and each
   numbered arrow. Spell acronyms the voice mangles (`A-P-I`); see `$KIT/STANDARD.md` §2.
3. Check, and print the results:
   - every frame has a cue: compare `ls $V/frames | wc -l` with `grep -c '^\[slide:' script`;
   - words per speaker: `grep -E '^C: ' script | wc -w` and the same for `I`, `V`, `N`; candidate about 80%;
   - total words between 8,000 and 12,000 (× 0.45 s ≈ minutes); words per chapter against the outline budget;
   - every challenge has an `I:` question, a second `I:` push and a `V:` line starting "If asked, I'd say".

## Stage `video`

1. Copy `solutions/SD-09-chat-messaging/video/build-video.sh` to `$V/`, change the script name and set
   `--max-minutes 180`. Run it **in the background**; a 90-minute video takes roughly 45 minutes to build.
2. QA, all of `$KIT/STANDARD.md` §4: streams (video, audio, chapters, no subtitle stream, 1920×1080); the audio
   check script; a sync probe late in the video; eight sampled frames read as images; the chapter list.
3. Leave the MP4 in its local output folder and name the path in the report (`$KIT/STANDARD.md` §5). Never copy
   it to Google Drive or any other cloud folder (author's decision, 2026-11-13).

## Stage `publish`

1. `$V/README.md`: length, chapters with times, the challenge list, the rebuild command, the QA done, and the
   canon check table from the outline.
2. Publish kit as in the `system-design-video` skill, step 9 (`$KIT/scripts/publish_kit.py`). Look at the thumbnail.
3. Add or update the row in `solutions/VIDEOS.md`; link the solution in `Question-Bank.md` and
   `solutions/README.md` if it is new.
4. Go through GUIDELINES §10 line by line. Print each line with pass or fail and the evidence. Fix what fails.

## Final report (after any run)

Stages done this run · files written · length and word count if a video was built · checks run and their
results · anything skipped or failed · the next stage and the command to run it.
