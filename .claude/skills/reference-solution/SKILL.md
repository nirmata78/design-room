---
name: reference-solution
description: Build, rebuild, re-cut or plan the design-room reference solution for one question-bank ID — a 40–55 minute candidate-led video in six chapters (prompt + clarifying Q&A + C4 context, back-of-the-envelope, API + data model, the design as a C4 container view V1 that evolves V2 → V3 … through 5–6 interviewer challenges with mechanisms, C4 component zooms and technology cards introduced just in time, the alternate simpler path, recap with trade-offs and follow-ups), the Markdown reference design generated from the same source (GitHub Pages ready), every C4 picture from one Structurizr workspace via c4-structurizr, and the YouTube/LinkedIn publish kit. Staged and deterministic (scripts/ref_solution.py, JSON status with remedies), so Claude CLI, Antigravity/Gemini and Grok run it the same way. Invoke as "/reference-solution SD-96" (new) or "/reference-solution SD-08" (re-cut an older solution); a title fragment also works. Use whenever the author asks to create, regenerate, re-cut, re-render or publish a solution or its video, for an outline or script only, or to analyse a new reference video for the format. All output stays inside the repository.
---

# /reference-solution SD-NN — one question, from the prompt to the publish kit

The standard is **`GUIDELINES.md` in this folder: read it in full first** (the six chapters, the challenge grammar, C4 rules,
voices, picture and language rules, the deliverables and the acceptance checklist). This file is the workflow. The worked
example is **`solutions/SD-03-ad-click-aggregation/`**: copy its patterns.

This is **authoring work, not an interview session**: the repository's `CLAUDE.md` interviewer rules do not apply. Its
confidentiality rules do: the repository is public, so write generic content only and never copy anything from `profile.md`,
`private/`, `sessions/` or `Progress-Log.md` into a tracked file.

## Multi-agent use

- **Claude CLI**: discovered at `.claude/skills/reference-solution/SKILL.md`.
- **Antigravity (Gemini) / Gemini CLI**: discovered through the `.agents/skills/reference-solution` symlink.
- **Grok (xAI) or any OpenAI-style function-calling agent**: load this file as instructions and pass
  `schemas/tool-definition.json` as `tools`; each tool maps to one `ref_solution.py` stage.

Every stage prints **one JSON object** (`status`, and on failure `remedy` plus the failing tool's `log`) and exits 0 only on `ok`.
Act on the `remedy`, re-run the stage, and stop only if the same stage fails twice with the same status.

## Files in this skill

```
SKILL.md · GUIDELINES.md · DESIGN-TOKENS.md      the workflow, the standard, the visual tokens
templates/outline.template.md                    the outline to fill first
templates/script-grammar.md                      the spoken grammar of every chapter and challenge
schemas/tool-definition.json                     the five stages as function-calling tools
scripts/ref_solution.py                          the staged runner: doctor · outline · diagrams · deck · markdown · video · publish · clean · all
scripts/ref_runtime.sh                           resolves REPO, KIT, PY (pdf-kit venv), TTS ($KOKORO_PYTHON), C4, AUDIO; `doctor` reports readiness
kit/                                             everything the build imports — nothing outside the repo except the Kokoro venv:
  dsl.py           slides + narration + the generated Markdown (write(), write_reference_markdown(), stage(), challenge(), push() …)
  stack.py         reads <solution>/stack.json: tech cards, their narration, the summary table, challenge rejections
  seqsvg.py erdsvg.py statesvg.py figsvg.py gtheme.py      non-C4 diagrams in the Google theme (C4 comes from c4-structurizr)
  check_layout.py render_slides.py build_video.py tts_cached.py publish_kit.py md_github.py paths.py
  video.css deck.css build-video.sh                        the theme; the per-solution entry point to copy into video/
```

## The run

`R = python3 .claude/skills/reference-solution/scripts/ref_solution.py` · `Q = solutions/SD-NN-<slug>/` · `V = $Q/video/`

### 0 · Resolve and prepare

1. `$R doctor` — fix anything `false` that the stages you need list.
2. Resolve the ID: `grep -n -i '<text>' Question-Bank.md`. Several rows match → ask which. Not in the bank → write a cue sheet
   (`Cue-Sheet-Template.md`, next free ID) and add the bank row.
3. Read the cue sheet section (offset into the file, ~170 lines), `levels.md` (default target `staff`), GUIDELINES,
   `references/video-examples/README.md`, the existing `solutions/SD-NN-*.md` if any, the SD-03 example (`workspace.dsl`,
   `views.json`, `video/src/`), and the matching `theory/` chapters.
4. **Re-cut** of an older-format solution (ten chapters, `diagrams/`, booklet scripts, PlantUML, a per-solution `dsl.py` or
   `stack.py`): do not start from the old script. Write the outline in the new shape and map old material into it (deep dives and
   follow-ups → challenges; the theory chapter's mechanisms → the challenges that need them; 5.1 tech slides → tech cards inside the
   challenges; the build-cost chapter → dropped or one recap row). Git keeps the old version: no `.v*` snapshot folders.

### 1 · Outline

`$R outline SD-NN` creates `$V/OUTLINE.md` from the template if missing. Fill every section (GUIDELINES §3–§5): the thesis; the
scale line; what this question grades; 4–6 clarifying answers; FRs, NFRs with numbers, properties with slugs; estimates with
arithmetic **from the scale line**, each with the constraint it forces; API and data; **V1 and the 5–6 challenges**, each with its
break, mechanism, fix (C4 delta or zoom), technology card, push and second fix, and the version it produces; the alternate path
with its crossover number; recap and follow-ups; the canon check; the budget (minutes and words per chapter). Recompute every
number. `$R outline SD-NN` must then print `ok`.

### 2 · Technologies → `$Q/stack.json`

Per in-scope container: `id`, `heading`, `kicker`, `title`, `pick`, `why`, `how` (2–3 sentences), `detail`, `rejected` (≥ 2, each
with the property that rules it out), `summary` (container · choice · rejected · reason), `course` citation; plus `challenges`
(per challenge number: the tool an interviewer will name and why not). Shape: SD-03's `stack.json`. Write "layer-4", never "L4".

### 3 · Diagrams → `$Q/workspace.dsl`, `$Q/views.json`, `$V/diagrams.py`

- **`workspace.dsl`** (GUIDELINES §7.4): one Structurizr workspace with the system context view, **one master container view**
  holding every container that will ever appear (≤ 11 elements, `autoLayout tb`), the component views of the containers the
  challenges open, and any alternate view; `!include ../../.claude/skills/c4-structurizr/resources/c4-google-tokens.dsl`; a
  `styles` block may raise `fontSize`, box sizes and the boundary label until the gate passes.
- **`views.json`**: V1 … Vn as `from` + `hide` + `new`, flows as `flow`, challenge breaks and fixes as `breaks`/`fix` on the
  container view or `keep` + `crop` zooms of 2–4 adjacent components, recap `badges`, the alternate's `alternate`; full component
  views `"video": false`; C4 views shown full-frame `"slot": "stage"`.
- **`diagrams.py`**: sequences (`seqsvg`), the physical model (`erdsvg`), a lifecycle (`statesvg`), the budget bar
  (`figsvg.budget_bar`) and any figure. It imports from `.claude/skills/reference-solution/kit`, never clears `svg/`.
- `$R diagrams SD-NN` renders all of it into `$V/svg/` and must print `ok`. On `diagram_gate_failed`, follow each failure's
  `remedy` (raise the workspace font, flip the layout, crop fewer boxes); on `unknown_aliases`, use the DSL identifier's last segment.
  Look at the rendered PNGs of the master view and two zooms (`render_c4.py … --png` into a scratch folder).

### 4 · Slides and narration → `$V/src/`

`gen.py` (copy SD-03's: it sets `dsl.META` — title, stem, the pronunciation map `say`, and `md` front matter — declares
`dsl.props(...)`, imports the chapter files, then calls `dsl.write()` and `dsl.write_reference_markdown()`), and the chapter files
`ch1.py ch2.py ch3.py ch4.py ch5_6.py`, following `templates/script-grammar.md`. Each `S()` call is one logical slide with its
narration; helpers: `chapter()`, `qs()`, `key()`, `say_slide()`, `plain()`, `dia()`, `stage()`, `table()`, `cards()`, `strip()`,
`trace()`, `tech(**ST.tech(id))`, `mech_slide()`, `challenge()`, `push()`, `rejl(*ST.rej(n))`, `code()`/`pseudo()`, `followups()`.
Reveal markers `[+]`, `[+N]`, `[+*]` place every unit; `REVEAL_REPORT=1 python3 $V/src/gen.py` lists every mismatch at once.

`$R deck SD-NN` regenerates and runs the 1080p layout gate; it must print `ok` with **0 failures** and no `redraw` warning. Look at
the slides you are unsure of: `$PY kit/check_layout.py --html $V/video-slides.html --svg-dir $V/svg --css-dir kit --only 15,37
--shots <scratch dir>`. Report slides, frames and words per chapter against the outline budget (`gen.py` prints them).

### 5 · The Markdown design

`$R markdown SD-NN` regenerates `$Q/SD-NN_<Title>_Reference_Design.md` and lints it; it must print `ok`. Read the start, one full
challenge and the recap. Never edit the `.md`: change the slide or the narration and regenerate.

### 6 · Video

`$R video SD-NN` **in the background** (frames by Playwright element screenshots, then Kokoro TTS through `kit/tts_cached.py`,
which caches every line; a 50-minute video takes roughly half an hour on a cold cache). Output `$V/<slug>-reference.mp4` with
`.srt` and `.vtt` beside it, local only; intermediates are deleted unless `--keep-intermediates`. QA:
- `ffprobe`: H.264 + AAC, 1920×1080, chapters present, no subtitle stream, duration within GUIDELINES §3;
- the `.srt`/`.vtt` start at 00:00 and end within a second of the video; cues ≤ 2 lines of ≤ 42 characters; VTT cues carry `<v Name>`;
- eight frames sampled across the length and one mid-crossfade, read as images; the audio skill's `check_audio.py` on 20 excerpts;
  fix mispronunciations in `theory/video/say.py` (or `META["say"]`) and re-run (only changed lines re-voice).
Everything stays inside the repository: never `~/Movies`, Google Drive or any cloud folder.

### 7 · Publish kit and links

`$V/publish/meta.json` (YouTube title ≤ 100 characters, description, tags, thumbnail text, LinkedIn post with a hook under ~140
characters; labels: synthetic voices, built with Claude Code, numbers illustrative), then `$R publish SD-NN`; **look at the
thumbnail**. Update `solutions/VIDEOS.md`, the bank row in `Question-Bank.md`, `solutions/README.md`, and `$V/README.md` (length,
chapters with times, the challenge list, the rebuild command, QA done, the canon check). Never upload, post, commit or push.

### 8 · Acceptance and report

`$R clean SD-NN`, then go through GUIDELINES §12 line by line: pass or fail with evidence; fix what fails; report each failed
line. Report: files written; length, slides and words; checks run and their results; anything skipped; "not watched end to end";
the paths of the MP4, the Markdown design and the publish kit. `$R all SD-NN` runs diagrams → deck → markdown → video → publish →
clean in one go once the sources are written (`--no-video` stops after the Markdown).

## Partial runs

- **Outline only / script only**: stop after step 1, or after step 5 (`$R all SD-NN --no-video`).
- **Adding a reference**: a new video or chapter to learn from goes in `references/video-examples/NN-<slug>/` with an
  `ANALYSIS.md` like the existing ones; add one row to GUIDELINES §2 and change a rule only if it shows something new.

## Running several questions at once

Each run owns only its `$Q` folder. Shared files (`Question-Bank.md`, `solutions/VIDEOS.md`, `solutions/README.md`,
`theory/video/say.py`) are edited with a short read-modify-write at the moment of the change. Render at most three videos at a time.
