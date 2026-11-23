# Status · SRE course

Updated at the end of the authoring session. State vocabulary follows `plans/STATUS-02.md`.

| Ep | State | Slides · words · est. min | Checks run | For the author |
|---|---|---|---|---|
| 1 | transcript, diagrams and frames done | 22 · 1,275 · 9 | lint 0 · overflow 0 · figures viewed | |
| 2 | same | 28 · 1,740 · 12 | same | Burn-rate numbers verified against workbook ch. 5 |
| 3 | same | 21 · 1,288 · 9 | same | |
| 4 | same | 28 · 1,667 · 12 | same | RED and USE attributed to their authors (VERIFY.md) |
| 5 | same | 27 · 1,492 · 11 | same | Canary table is my arithmetic from stated assumptions |
| 6 | same | 23 · 1,350 · 10 | same | |
| 7 | same | 26 · 1,527 · 11 | same | Three emergency stories rewritten to match ch. 13 |
| 8 | same | 22 · 1,319 · 10 | same | |
| 9 | same | 25 · 1,586 · 11 | same | |
| 10 | same | 31 · 2,043 · 15 | same | The episode to review first |
| 11 | same | 28 · 1,811 · 13 | same | Paxos internals added (section 11.3, three figures, two probes) |
| 12 | same | 26 · 1,612 · 12 | same | |
| 13 | same | 24 · 1,502 · 11 | same | Music-2012 story corrected (found by a user) |
| 14 | same | 21 · 1,290 · 9 | same | The book's Keyhole figures do not reconcile; none is computed from |
| 15 | same | 24 · 1,474 · 11 | same | AUX badge on the management-layer slides |
| 16 | same | 19 · 1,325 · 10 | same | AI-serving table is my synthesis |

**Rendered (2026-11-12):** all 16 episodes and the merged course, `~/Movies/SRE-course/SRE-Full.mp4` (2:47:22, 1080p, 113 chapters, 0.42 GB), plus one MP4 per
episode in the same folder. Checks run: stream probe (H.264 and AAC, no subtitle stream, 113 chapters), Whisper intelligibility on 24 excerpts of the full
course and 10 of episode 11, a sync probe on episode 1, frames sampled from episodes 1, 11 and 15. Pronunciation fixes in `theory/video/say.py`: "rota",
"Paxos", "GitOps". **Not listened to end to end**; episodes 2 to 16 were not individually frame-reviewed beyond overflow checks.

**Changes to shared files:** `theory/video/course.py` (a `now` panel kind; `aux` flag accepted on any slide) and `theory/video/sd.css` (`.panel.now`).
Plan files were not edited. Nothing was committed.

**Open questions:** see `REVIEW-GUIDE.md`.
