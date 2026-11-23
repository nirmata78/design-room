# Review guide · what to read, and what to decide

About 40 minutes covers the essentials. Reading all transcripts is about three hours, the length of the course.

## Suggested path

1. **`AGENDA.md`** (5 min): scope, order, what is condensed or left out.
2. **`review/THESIS-INSERTS.md`** (10 min): the 79 key lines, in the slower voice. If one is wrong or weak, the episode is wrong or weak.
3. **`review/Ep10-transcript.md`** (15 min): the densest episode and the one the plans lean on most. Judge depth, tone and pacing on it, and tell me what to change everywhere.
4. **`theory/sre-video/out/SRE-Episode-10-slides.pdf`** (5 min): how it looks. Then the diagrams you care about in `svg/` (open in a browser).
5. Skim one Priority 3 transcript (ep. 15) to judge the AUX framing and the management-level tone.

## Questions for you

| # | Question | My default |
|---|---|---|
| 1 | **Length.** The course is about 2 h 55 min, 9 to 15 minutes an episode. The earlier series plan assumed 12 to 20. Do you want episodes **longer and deeper**, or is this the right size? | Deepen only priority 1 (10, 11, 12, 13) to about 18 to 22 minutes, keep the rest |
| 2 | **Depth of "one level down".** Each section goes: mechanism → one level down → alternative and price → trap. Too much, or not enough? | As is |
| 3 | **Voices.** The key-line voice and the candidate voice are the same synthetic voice at different speeds (the builder's setting). Want a third distinct voice for key lines? | Keep, then judge on a sample |
| 4 | **Thesis inserts.** 79 across 16 episodes, one every two to three minutes. Too frequent, too rare, or placed wrongly? | As is |
| 5 | **Then and now.** Each episode has one or two panels on what changed since 2016. Too general? They were checked against public sources on 2026-11-12 (`VERIFY.md`). | Yes, before anything is published |
| 6 | **Probe drills.** Three or four per episode, answered by a spoken candidate. Do you want them longer, with a follow-up each (as the design-room course does)? | Add follow-ups in priority 1 only |
| 7 | **AUX framing** for the manager layer (ep. 15 carries the "optional in a Staff or IC round" badge). Right for you, given an EM target? | Keep the badge on ep. 15, remove it if you want that layer treated as core |
| 8 | **Public repository.** This series retells ideas from Google's published SRE books, as its own text, and sits in tracked `theory/`. It follows the repo rule (paraphrase and attribute), and quotes one short line verbatim ("No one really wants to make backups; what people really want are restores"). Keep it tracked, or move it under `private/`? | Your call; nothing is committed |
| 9 | **Additions.** See AGENDA §6: workbook episodes on SLO implementation, alerting on SLOs, a worked large-system design, canarying. Which, if any? | Alerting on SLOs and the worked design first |
| 10 | **Cross-links.** Add "see SRE episode N" to the design-room course's *Read next* slides? | Yes, after review |

## Where I would look for mistakes

- **Anything with a number**: `CLAIMS.md` says which are from the book, which are my arithmetic, and which are illustrative. The ones I was least sure of are marked.
- **The book's stories**: I corrected two details after checking the text. The 2012 music-service case (episode 13) was found by a user report, not by monitoring; and episode 7's three emergency stories were rewritten to match chapter 13. Check the other narratives against the book the same way.
- **Open-analogue claims** in episode 1 (Borg to Kubernetes and so on) and the "since the book" panels everywhere.
- **Episode 11**: the new Paxos section (11.3) is written from the protocol itself; check it against plan 02 part 3 for overlap.

## How to give feedback

Edit nothing in `review/` (it is generated). Quote the slide as *episode · slide number · title* (the transcripts use that header) and say
*cut / shorten / deepen / fix: …*. I change `src/chNN.txt`, regenerate the review files, and re-render only the episodes affected.
