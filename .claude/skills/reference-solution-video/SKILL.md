---
name: reference-solution-video
description: Plan, script and build a design-room reference solution video for a system-design question (SD-NN) — a 60–90 minute candidate-led walkthrough with a theory chapter, a V1→V2→V3 baseline carried through 6–8 interviewer challenges, numbered flows, an options matrix, "what is graded" and build cost. Use whenever the author asks for a reference solution video, a re-cut or re-render of an existing solution video (SD-08, SD-09 …) in the reference style, an outline or script for one, or to analyse a new reference video or book chapter for the format.
---

# Reference-solution video

**Read `GUIDELINES.md` in this folder first.** It is the standard: the purpose, the fixed chapter order, the
theory chapter, the nine-beat challenge grammar, voices, picture and language rules, the canon check and the
acceptance checklist. This file is the workflow.

Rendering is done by the author's shared kit, which is not in this repository:
`~/.claude/skills/slide-video-kit/` (scripts, templates, `STANDARD.md` for picture, sound, captions and QA) and
the `system-design-video` skill (reference design booklet, publish kit, delivery). If the kit is missing, stop
at the outline and script and say so.

This repository is public. Generic content only: no profile data, no employer detail, nothing from `private/`.

## Workflow

1. **Sources.** Read the question's cue sheet (`Question-Bank.md` → `questions/*.md`), `solutions/SD-NN-*` if
   one exists, and `levels.md` for the target level (default `staff`, manager layer marked AUX). Read
   `references/video-examples/README.md` for the reference analyses.
2. **Canon check** (GUIDELINES §9). List what the standard treatments of this question cover. A private book
   extract may be read for this if the author has one under `private/books/`; summarise in our own words, quote
   nothing, copy no figure.
3. **Outline.** Copy `templates/outline.template.md` to `solutions/SD-NN-<name>/video/OUTLINE.md` and fill it:
   thesis, graded axes, theory parts, the options matrix, V1/V2/V3 with objections, the flows, the 6–8
   challenges with all nine beats in one line each, minutes and word budget per chapter.
   **Show the outline to the author before writing slides.** It is the cheapest place to change direction.
4. **Reference design booklet** before the script, as `system-design-video` step 1b requires. Same numbers in both.
5. **Diagrams.** In `video/diagrams.py`:
   - the carried baseline with `basesvg.Baseline` (start from
     `~/.claude/skills/slide-video-kit/templates/reference-solution/baseline.example.py`): version views,
     one flow view per functional requirement, attack and fix views per challenge, the latency budget bar;
   - C4 context and container views, sequences, Chen and physical data models with the kit's existing
     generators, as before.
6. **Slides.** `video/video-slides.html`. Copy the current `video.css` from the kit templates (it holds the
   slide types for this format) and use `templates/reference-solution/slides.example.html` there as the
   pattern for: ribbon, graded table, scope pair, theory properties, options matrix, version build, numbered
   flow, challenge question, break, trace, fix, "if asked", budget, symptom pairs.
   Render the frames and **look at every one** on contact sheets before writing the script.
7. **Script.** Follow `templates/script-grammar.md`. Count the words per chapter against the outline before
   building (about 0.45 s per spoken word).
8. **Build, QA, document, publish kit** as in `system-design-video` steps 5–9, with
   `--max-minutes 180` and the target of 60–90 minutes. Keep the previous version of a re-cut video in
   `video/.vN-*/`.
9. **Acceptance.** Go through GUIDELINES §10 line by line and report each failed line, not a summary.

## Re-cutting an existing video (SD-08, SD-09, …)

Do not start from the old script. Write the outline first (step 3) and map old material into it: the old deep
dives and follow-ups become challenges; the old C4 walk follows the V1 → V2 → V3 build; vocabulary slides move
into the theory chapter. List what is new (theory parts, matrix, graded table, build cost), what is reused, and
what is dropped, and get the author's go-ahead before rendering.

## Adding a reference

A new video or chapter the author wants to learn from goes in `references/video-examples/NN-<slug>/` with an
`ANALYSIS.md` in the shape of the existing ones (agenda with times, script architecture, diagramming approach,
gaps, reusable devices). Media, transcripts and book text stay untracked. Then add one row to GUIDELINES §2 and
change a rule only if the reference shows something the three existing ones do not.
