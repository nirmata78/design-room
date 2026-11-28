# SD-25 · Rate limiter (distributed) — reference-solution video

**Re-cut on 2026-11-28 in the six-chapter, C4-first format** (issue #5; the SD-03 pilot's patterns). The design is one C4
container view that evolves through six interviewer challenges. Every C4 picture comes from `../workspace.dsl` + `../views.json`,
and the written design is generated from the same sources as the video. It replaces the older short solution
(`solutions/SD-25-rate-limiter.md`) and the L6 EM mock-round video (`limiter-mock`); both are in git history.

**Length:** 66:23 · 117 logical slides, 376 frames · about 8,030 spoken words (candidate about 83 %) · 1080p, sidecar captions.
This is over the 40–60 minute target, which is a soft limit; the hard limit is 90. No slide was cut to save time.
**Files (local, gitignored):** `rate-limiter-reference.mp4`, `.srt` (upload this one to YouTube), `.vtt`.
**Written design:** [`../SD-25_Rate_Limiter_Reference_Design.md`](../SD-25_Rate_Limiter_Reference_Design.md) (generated). **Publish kit:** `publish/`.

## Chapters

| Time | Chapter |
|---|---|
| 0:00 | 1 Prompt, questions and context |
| 9:19 | 2 Estimates |
| 13:44 | 3 API and data model |
| 18:02 | 4 Design, driven by challenges (V1) |
| 20:59 | 4.1 Challenge 1: 1,000 at 11:59:59, 1,000 at 12:00:00 |
| 26:51 | 4.2 Challenge 2: Take the round trip off the hot path → V2 |
| 36:52 | 4.3 Challenge 3: The quota service is down |
| 42:35 | 4.4 Challenge 4: One quota, three regions → V3 |
| 47:47 | 4.5 Challenge 5: 10× burst for 30 seconds, every hour |
| 53:53 | 4.6 Challenge 6: "You limited us while we were under" → V4 |
| 60:09 | 5 When you don't need all this |
| 61:38 | 6 Recap |

## Challenges

1. **The boundary burst** (correctness): five algorithms compared; a token bucket in one atomic Lua script, timed by the shard's clock. Push: two servers race for the last token, so the rejected answer is a get, compare, set from the client.
2. **The round trip off the hot path** (overload, the crux): leased tokens sized by demand. V2 adds the quota service. The API server's component view is shown whole here. Push: uneven balancing, the hot customer, and the cold-start bound N × c.
3. **The quota service is down** (failure recovery): static stability. The server keeps its last lease for 10 s, then falls to a floor of 3 × limit ÷ servers. Each limit's owner decides fail-open or fail-closed. Push: the policy service is down while servers restart, which the last-known-good copy on disk covers.
4. **One quota, three regions** (geography): regional budgets re-split every 2 s; V3 adds the peer regions. Push: a partition freezes the split, which makes the limit stricter, never looser.
5. **10× burst for 30 s every hour** (the curveball): scheduled tiers with an owner and an expiry. Push: a typo sets limits to zero, so the change is validated, shadowed, canaried and rolled back.
6. **"You limited us while we were under"** (observability): V4 adds the decision log and store, a decision recorder, a false-limit SLI and symptom pairs. Push: the log itself drops records, so counters reconcile it and a canary customer checks it.

## Rebuild

```bash
python3 .claude/skills/reference-solution/scripts/ref_solution.py all SD-25 --no-video   # diagrams → deck (gate) → Markdown
python3 .claude/skills/reference-solution/scripts/ref_solution.py video SD-25            # MP4 + .srt/.vtt, then clean; log in logs/
python3 .claude/skills/reference-solution/scripts/ref_solution.py publish SD-25
```

## QA done (2026-11-28)

- c4-structurizr (native renderer): 21 C4 views (context, master, alternate, one component view, 17 derived). Every label is at least 18 px at 1080p and every text fits inside its box. The component view uses a 3 × 6 grid; a 4-row grid squeezed the limit store's cylinder.
- Layout gate: 117 slides, **0 failures**, 0 redraw warnings. There are 8 density warnings (5 technology cards, the grades table, the sizing table, one cards slide: 96–136 words). They were kept, as on SD-03.
- ffprobe: H.264 + AAC, 1920 × 1080, 12 chapters, no subtitle stream, 66:23.
- Captions: SRT and VTT with 899 cues, each at most 2 lines of 42 characters, and every VTT cue has a `<v Name>` span. The first cue starts at 0:01.2, after the opening pause. The last cue ends 3 s before the video, at the closing pause.
- Ten frames sampled across the length: a table mid-reveal, a chapter card, a trace, the options matrix, a mechanism, the V3 delta mid-reveal, an interviewer push, a cards slide and the stack table.
- Whisper check (`check_audio.py`) on 20 excerpts of 30 s: confidence −0.18 to −0.39. "syncer" (heard as "sensor") and "cron" (heard as "crawl") were respelled in `META["say"]` and the video was re-voiced. The remaining differences are homophones (sync/sink, write/right).
- Markdown: generated, and the `md_github.py` lint passes.
- Nobody has watched it end to end.

## Canon check

See `OUTLINE.md` § Canon check. Covered: algorithms compared with the boundary burst, atomic check-and-take, where the count
lives, the 2-per-server arithmetic, hot keys, fail-open against fail-closed, multi-region, response headers, availability over
accuracy, per-decision observability and the curveball. Dismissed aloud: DDoS at the edge and billing-grade counts. Concurrency
limits, load shedding, build-or-buy and the week-one plan are recap follow-ups.
