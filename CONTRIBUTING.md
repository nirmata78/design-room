# Contributing

Thanks for helping make the room harder to bluff.

## What's most useful

- **New questions**, especially for under-covered archetypes (G · media & delivery has only four;
  J · crypto and K · Staff+ have six each) and more **inverted rounds** in H and K, where the candidate
  reviews a flawed artifact. Domains with thin coverage: `mobility`, `search`, health-tech, gaming.
- **Level calibration** (`levels.md`), if you've sat on Staff+, senior-manager or director panels.
- **Sharper probes.** A good probe is one sentence, names nothing the candidate hasn't named, and
  separates people who understand a mechanism from people who know its name.
- **Company calibration** (`CLAUDE.md` §7.3), if you have recent first-hand loop experience. Keep it to
  what interviewers *emphasise*, never to leaked questions.
- **Interviewer behaviour bugs.** If Claude leaked a component, praised, multi-probed or ran over
  time, open an issue with the excerpt (scrub anything confidential first).

## Adding a question

1. Write the sheet with [`Cue-Sheet-Template.md`](Cue-Sheet-Template.md). A **T1** sheet has the full
   probe ladder by phase and the traps; a **T2** sheet is prompt, numbers, checklist, five probes and
   three bands.
2. Append it to the right file in `questions/` as `### SD-nn · Title   [T1 · G★ M]`. **IDs are global
   and monotonic** — take the next free number even if it lands in an older archetype, and add the
   range to that file's header. The interviewer finds sheets with `grep -n '^### SD-nn'`, so the
   heading format is load-bearing.
3. Add a row to [`Question-Bank.md`](Question-Bank.md) with **Kind** (Build · Review · Strategy),
   **Domain** and **Levels** (see [`levels.md`](levels.md)), and bump the counts in the README.
4. Run a round on it yourself before opening the PR. A sheet that hasn't survived a live round
   usually has a clarification answer missing.

## Ground rules

- **No leaked interview questions** and nothing under NDA. Every prompt here is a well-known public
  archetype; keep it that way.
- **No real employer data** in examples — internal system names, figures, incidents.
- **Never commit your own `profile.md`, `Progress-Log.md` or `sessions/`.** They are gitignored; don't
  force-add them.
- Use **they/them** for the candidate.

## Changing the engine

`CLAUDE.md` is the interviewer's operating manual. Changes there change every session, so explain in
the PR which failure mode you observed and how the change prevents it.
