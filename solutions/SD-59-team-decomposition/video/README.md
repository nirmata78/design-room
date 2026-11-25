# SD-59 · Multi-team decomposition and API contracts: reference-solution video

Principal / senior engineering-manager bar, **compact cut** (GUIDELINES §3.4), 2026-11-25 format. **Length 51:17**, 17 chapters, **117 numbered slides** in **404 reveal frames**, **6,036 spoken words**. Subject system: the loan-servicing platform of SD-95. Scripted walkthrough with synthetic voices; numbers are illustrative, not any company's figures. **The technical content has not been reviewed by a person, and the video has not been watched end to end.**

Output: `team-decomposition-reference.mp4` (local only, gitignored) with `.srt` and `.vtt` beside it. Written companion: `../SD-59_Team_Decomposition_Reference_Design.md` (GitHub Markdown; diagrams are PlantUML/C4 SVG, shared with the video). Publish kit: `publish/`. Plan: `OUTLINE.md`.

**Shorter than the compact target.** About 6,000 spoken words against the 7,800–8,800 of GUIDELINES §3.4, so the video runs about 51 minutes. The challenges are lean (about 2.5 minutes each) and the theory carries the weight. A longer cut would add a worked numeric case to challenges 2 and 4 and a drill interlude.

## Chapters

| Time | Chapter |
|---|---|
| 00:00 | 0 Cold open |
| 02:26 | 1 Requirements and scope |
| 06:54 | 2 Estimates |
| 09:07 | 3 Theory |
| 22:42 | 4 Contracts and entities |
| 24:33 | 5 High-level design |
| 29:14 | 5.1 Components and technologies |
| 31:29 | 5.2 When you don't need all this |
| 32:18 | 6 Bridge |
| 32:41 | 7 Challenges |
| 32:56 | 7.1 Challenge 1: Which team is on the critical path? |
| 35:33 | 7.2 Challenge 2: A dependency arrives two months late |
| 38:03 | 7.3 Challenge 3: Two teams, one table, incompatible changes |
| 40:35 | 7.4 Challenge 4: Two teams disagree on a contract |
| 43:12 | 7.5 Challenge 5: You lose a team at month three |
| 45:32 | 7.6 Challenge 6: How would you know the split is wrong? |
| 48:05 | 8 Recap and follow-ups |

## The six challenges

| # | Challenge | The fix |
|---|---|---|
| 1 | Which team is on the critical path? | contract and generated mock in week two; consumers build in parallel |
| 2 | A dependency arrives two months late | consumer-driven tests run in the provider's CI; additive v2 with a sunset |
| 3 | Two teams, one table, incompatible changes | one owner; versioned views; expand, migrate, contract |
| 4 | Two teams disagree on a contract | decision record, two-day window, the provider decides ties |
| 5 | You lose a team at month three | pause one component, freeze its contract, cut scope |
| 6 | How would you know the split is wrong? | three leading indicators with thresholds set in advance; own failure mode |

## What the 2026-11-25 engine did here

Theory rendered first (`build-video.sh` runs the theory pass and its layout gate before the rest); every mechanism a composite infographic with its diagram type (C4, ERD, sequence, state machine); each option its own infographic with pros, cons, a C4 view and red pitfall boxes; properties by slug; V1 to V3 as C4 deltas with the failing case of each as a sequence; events dashed blue against HTTPS solid; no failure catalogue, follow-up questions in the recap; Markdown instead of a PDF booklet. Rebuild: `./build-video.sh` (`--theory` for the theory pass only).

## QA done

`check_layout.py`: 0 failures on the theory pass and on the whole deck (4 `dense` warnings and one `redraw` of `opt-a`, deliberate: the cold-open hook reuses option A). `ffprobe`: H.264 + AAC, 1920×1080, chapters present. Captions are sidecar files; SRT lines at most 42 characters. Two frames read as images. Not done: an end-to-end listen, `check_audio.py` excerpts, a sync probe.

## Canon check

| Point the standard treatments make | Where |
|---|---|
| Conway's law, stated in the candidate's own words | mechanism 1; the thesis |
| Domain seams, not technical layers | option A rejected; V1 objection |
| Contracts defined and versioned before code, additive-only, deprecation windows | mechanism 2; contracts chapter |
| Consumer-driven contract tests; mocks so nobody is idle | mechanism 3; challenges 1 and 2 |
| Critical path and dependency graph explicit | challenge 1; the ownership model |
| Ownership of shared components | mechanism 4; challenge 3 |
| Sequencing against skills | clarifying question 2 |
| Time-zone seams are the most stable contracts | clarifying question 4 |
| What the manager owns personally | recap: contracts, graph, milestones, escalation |
| Integration skeleton early | mechanism 5; FR4 |
| Not over-decomposing | option D |
| Leading indicators; naming one's own failure mode | mechanism 6; challenge 6 |
| The reorg curveball | challenge 5 |

## Reworked on 2026-11-25 (the new engine)

Theory rendered first and rewritten: five parts, no failure catalogue; every mechanism is a composite infographic paired with the diagram type that fits (sequence, state machine, ERD, C4); each option of the matrix has its own infographic with pros, cons, a C4 view and red pitfall boxes. Properties are named by slug (`[S1-…]`), never bare codes. V1 to V3 are C4 container deltas (PlantUML), the version objections are sequence diagrams, event versus HTTPS boundaries are drawn distinctly, and the external rail or endpoint shapes are on the wire slides. Chapter 9 ends with follow-up questions. The written design is Markdown only. Challenge overlays (`ch*-attack` / `ch*-fix`) are unchanged from the earlier native diagrams. Not watched end to end.
