# SD-03 · Event counting & billing rollups — reference-solution video

**The pilot of the 2026-11-28 format** (issue #5): six chapters, the design as one C4 container view that evolves through six
interviewer challenges, every C4 picture from `../workspace.dsl` + `../views.json`, and the written design generated from the same
sources as the video. Re-rendered the same day with c4-structurizr's native renderer (c4model.com look, Google palette, a
grid per view), full component views in the video, `zoom()` slides and the frame-and-card theme.

**Length:** 56:36 · 114 logical slides, 350 frames · 6,717 spoken words (candidate 82 %) · 1080p, sidecar captions.
**Files (local, gitignored):** `ad-click-aggregation-reference.mp4`, `.srt` (upload to YouTube), `.vtt`.
**Written design:** [`../SD-03_Ad_Click_Aggregation_Reference_Design.md`](../SD-03_Ad_Click_Aggregation_Reference_Design.md) (generated). **Publish kit:** `publish/`.

## Chapters

| Time | Chapter |
|---|---|
| 0:00 | 1 Prompt, questions and context |
| 8:17 | 2 Estimates |
| 11:48 | 3 API and data model |
| 15:15 | 4 Design, driven by challenges (V1) |
| 17:43 | 4.1 Challenge 1: An hour is too late → V2 |
| 22:52 | 4.2 Challenge 2: The same click, three times |
| 29:18 | 4.3 Challenge 3: Yesterday's events at 6 a.m. |
| 37:10 | 4.4 Challenge 4: One ad at 2 million a second |
| 42:19 | 4.5 Challenge 5: Fraud after the invoice → V3 |
| 47:10 | 4.6 Challenge 6: “Your numbers are 3 % high” |
| 50:58 | 5 When you don't need all this |
| 52:29 | 6 Recap |

## Challenges

1. An hour is too late (freshness): one aggregation run twice; V2 adds the live aggregator and the live store; options A–E.
2. The same click, three times (correctness, crux): event IDs minted at the source, keyed dedup state; push: a four-hour replay → replace by key and version.
3. Yesterday's events at 6 a.m. (correctness): event time clamped, watermark − 2 min, 1 h lateness; the bill closes at H + 48 h.
4. One ad at 2 million a second (overload): combine per subtask, merge 512 partials; shard rows summed on read.
5. Fraud after the invoice (correctness): V3 adds the fraud system's invalidations; versions and adjustment lines, nothing billed is edited.
6. "Your numbers are 3 % high" (observability): a reconciler in the billing job — conservation per hop, live against final, canaries.

## Rebuild

```bash
python3 .claude/skills/reference-solution/scripts/ref_solution.py all SD-03 --no-video   # diagrams → deck (gate) → Markdown
python3 .claude/skills/reference-solution/scripts/ref_solution.py video SD-03            # MP4 + .srt/.vtt, then clean; log in logs/
python3 .claude/skills/reference-solution/scripts/ref_solution.py publish SD-03
```

## QA done (2026-11-28)

- c4-structurizr (native renderer): 23 C4 views (context, master, alternate, two component views, 18 derived) in 3.2 s; every
  label ≥ 18 px at 1080p and every text inside its box.
- Layout gate: 114 slides, **0 failures**, 0 redraw warnings, 5 density warnings (technology cards, the options matrix, the
  follow-ups table: 102–116 words; kept, the tables are the content).
- ffprobe: H.264 + AAC, 1920 × 1080, 12 chapters, no subtitle stream, 56:36.
- Captions: SRT and VTT, 751 cues, ≤ 2 lines of ≤ 42 characters, every VTT cue with a `<v Name>` span.
- Twelve frames sampled across the length (chapter cards in the four-colour frame, C4 views mid-reveal, a dimmed zoom and its
  cards slide, a trace with no empty rows, the recap badges).
- Render: 15.0 min wall on a warm TTS cache (frames 41 s, voices 1.7 min, encode 12.6 min); the timestamped log is in `logs/`.
- Markdown: generated, `md_github.py` lint passes (every figure resolves to `video/svg/`).
- Not watched end to end by a person; no Whisper pronunciation pass was run on this cut.

## Canon check

See `OUTLINE.md` § Canon check: durable log, idempotency keys, event time and watermarks, Lambda against Kappa, exactly-once
unpacked, hot keys and sharded counters, reconciliation, retroactive invalidation and reproducible history are covered;
HyperLogLog is a recap follow-up; fraud detection, ad serving and budget pacing are dismissed aloud.
