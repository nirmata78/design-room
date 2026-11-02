# SD-47 ticket booking — mock-round video (v2, Staff L6/L7)

A narrated mock system-design round at the **Staff engineer, L6/L7** bar (FAANG and top-tier companies), **38:14 at
1080p, 22 chapters**, in local Kokoro voices (interviewer, candidate, candidate key lines spoken slower, coach) with
burned-in captions. **Every slide carries its number** (top right) so feedback can say "slide 23"; slides tagged
**AUX** are the engineering-manager layer and are explicitly optional in a Staff round. Built with the
`system-design-video` skill to `slide-video-kit/STANDARD.md` §1a; content follows
`../SD-47_Ticket_Booking_Reference_Design.md`. The v1 EM-framed 28-minute version is in `.v1-em-2026-10-28/`.

| File | Role |
|---|---|
| `ticket-mock.script.md` | the spoken script, `[slide: v-NN]` cues (NN = the printed slide number) |
| `video-slides.html` + `video.css` + `deck.css` | 74 slides |
| `diagrams.py` → `svg/` | C4 context, two container views, inventory component view, seat states, eight sequences, the load funnel with formulas, the CDN state response, the availability bitmap byte by byte, two ERDs (`erdsvg.py`), the Redis key space, the AIMD controller, five follow-up diagrams |
| `build-video.sh` | diagrams → slides → `frames/` → `ticket-mock.mp4` (`--frames` stops early; `--max-minutes 45`) |

What v2 adds (the author's review of 2026-10-29): every estimate as a calculation (slides 9–12); wire formats for the
join, the CDN state, admission and the JWT, the bitmap, holds (201/409/429) and orders (slides 13–19); ERDs and the
Redis key space (20–22); PostgreSQL, Redis, Kafka and the CDN each against rejected alternatives (23–27); the claim
SQL and five rejected concurrency answers (34–35); the join Lua script (39); the seat-map pipeline as a deep dive
(44–46); the sweeper and freeze SQL (49, 53). Follow-ups: twenty dates at once, the failover, fairness, the CDN bill,
and (AUX) three teams in twelve weeks. QA: Whisper excerpts 73–86% (homophones; "PostgreSQL" heard as "postker sql"),
a sync probe at 35:00, sampled frames; not watched end to end. The MP4 and `frames/` are gitignored.
