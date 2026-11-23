# Status · Plan 02 (theory course)

| ID | State | Counts | Changes made | For the author |
|---|---|---|---|---|
| C-01-D1 | done | 5 of 5 figures | `diagrams_p01.py` → `svg/p1-{load-curve,latency-ladder,series-parallel,utilisation-curve,fanout}.svg`; each rendered and checked against `diagrams/p01.md` | see below |
| C-01-F | done | 66 slides, 0 lint, 0 overflow, coverage 11/11 | 1.36 *Two formulas, both short enough to remember*: two `code` lines too wide (rule 2b), the trailing definition moved to its own line, words unchanged — `W = S ÷ (1 − ρ)        S = service time, ρ = utilisation` → two lines; `L = λ × W              requests in the system = …` → two lines | — |
| C-01-V | review build | 27:52 real (est. 31.3), 1920×1080 + AAC, 15 chapters = 15 sections, no subtitle stream | first render for the author's review; sync probe at 90% and 38% passed; `check_audio.py` (C-S3) run later, see C-S3 | — |
| C-02-D1–D3 | done | 12 of 12 figures | `diagrams_p02.py` (shared helpers in `dg.py`) → `svg/p2-*.svg`; each rendered and checked against `diagrams/p02.md` | — |
| C-02-F | done | 111 frames, 0 lint, 0 overflow, coverage 15/15 | 2.51 *The check and the write are one conditional operation*: two `code` lines too wide (rule 2b); "on its own monotonic clock" and "on its own clock" moved to their own indented lines, words unchanged | — |
| C-03-D1–D2 | done | 7 of 7 figures | `diagrams_p03.py` → `svg/p3-*.svg`; fan-out messages drawn as one arrow with a head at each receiver (spec allows it for p3-paxos-duel; used also for p3-append and p3-readindex) | — |
| C-03-F | done | 64 frames, 0 lint, 0 overflow, coverage 8/8 | 3.10 *What is on disk before anyone answers*: "to the fastest majority" moved to its own line. 3.29 *One group cannot hold a large store…*: the indent before "each node leads…" removed and the spaces before "=" reduced, words unchanged | — |
| C-04-D1–D2 | done | 8 of 8 new figures (`p2-pause` reused) | `diagrams_p04.py` → `svg/p4-*.svg`; in p4-stale-discovery the old and new owner of 10.0.0.7 are one participant labelled "old: shard 7 → new: shard 12" (the closest legible version of "one lifeline that changes colour") | — |
| C-04-F | done | 62 frames, 0 lint, 0 overflow, coverage 6/6 | 4.6 *Four details an interviewer reaches on the second "why?"*: panel past the footer by 90 px; split in two at the natural line (items 1–2, items 3–4), the narration split at its existing line break (rule 2c); text unchanged. 4.13 *The leader's own clock…*: "The leader treats its leadership as ending at grant time plus the lease minus a safety margin for drift, measured from when it **sent** the request." → "The leader ends its leadership at grant time plus the lease, minus a margin for drift, counted from when it **sent** the request." (rule 2b) | — |
| C-02-V | built | 31:55 real (est. 35.3), 1920×1080 + AAC, 19 chapters = 19 sections, no subtitle stream | six frames at 10–90 % looked at, each caption belongs to its slide; `check_audio.py` (C-S3) run later, see C-S3 | — |
| C-05-D1–D2 | done | 9 of 9 figures | `diagrams_p05.py` → `svg/p5-*.svg`; p5-dual-write's lost publish is drawn solid to the cross (the helper's lost-message style) | — |
| C-05-F | done | 90 frames, 0 lint, coverage 14/14; overflow: one 3 px residual on 5.7 (see changes) | 5.7 *Failover, step by step*: panel 26 px past the footer; "**1. Detect.** Missed heartbeats, say 3 × 10 s: about 30 s, chosen against false failovers." → "**1. Detect.** Missed heartbeats: 3 × 10 s = 30 s, set against false failovers." (rule 2b). A 3 px slide-scroll remains at the check's 1280 px viewport with no element past the footer; the 1080p frame was looked at and nothing is cut. 5.47 *The write latency each one costs, in numbers*: "a far client pays its round trip to the leader, up to **80 ms**, plus local commit." → "far clients pay up to **80 ms** round trip, plus local commit." | — |
| C-06-D1–D2 | done | 8 of 8 figures | `diagrams_p06.py` → `svg/p6-*.svg`; p6-ring adds the small legend "a key belongs to the next node clockwise" so colour does not carry the meaning alone | — |
| C-06-F | done | 78 frames, 0 lint, 0 overflow, coverage 11/11 | 6.47 *Time plus worker plus sequence, in 64 bits*: `code` too wide (rule 2b); "41 bits: milliseconds since a custom epoch" → "41 bits: ms since a custom epoch" (the slide's next line already says "41 bits of ms"); "uses them locally" moved to its own indented line | — |
| C-07-D1–D3 | done | 11 of 11 figures | `diagrams_p07.py` → `svg/p7-*.svg`; p7-lsm-read greys L4 and L5 as "not read" to show "stop at the first match" | — |
| C-07-F | done | 94 frames, 0 lint, 0 overflow, coverage 15/15 | 7.19 *Inside one sorted table*: "dropped only when compaction reaches the bottom level." → "dropped only at compaction into the bottom level." (rule 2b). 7.36 *Choose by the access pattern*: `sm` flag (rule 2a) | — |
| C-08-D1–D3 | done | 13 of 13 figures | `diagrams_p08.py` → `svg/p8-*.svg`; p8-2pc and p8-2pc-blocked show the phases as grey bands across the participants; the "long amber bars" of p8-2pc-blocked are drawn as one tall amber note across both shards | — |
| C-08-F | done | 76 frames, 0 lint, 0 overflow, coverage 10/10 | 8.14 *100 buyers, the last unit, and the retry arithmetic*: `code` too wide (rule 2b); "pessimistic lock per unit row: 100 waits in a line, at 2 ms each -> 200 ms for the last" split after the colon, as the slide's other two cases are laid out, words unchanged | — |
| C-09-D1–D2 | done | 7 of 7 figures | `diagrams_p09.py` → `svg/p9-*.svg`; p9-lease keeps the four participants of p9-stale-set (as specified), so step 6 "Reader B: get k" is drawn on the reader lifeline with the label naming Reader B | — |
| C-09-F | done | 77 frames, 0 lint, 0 overflow, coverage 11/11 | 9.6 *Five patterns, by who populates, who invalidates, what failure does*: `sm` flag (rule 2a) | — |
| C-10-D1–D3 | done | 11 of 11 figures | `diagrams_p10.py` → `svg/p10-*.svg` | — |
| C-10-F | done | 101 frames, 0 lint, 0 overflow, coverage 17/17 | none | — |
| C-11-D1–D3 | done | 10 of 10 figures | `diagrams_p11.py` → `svg/p11-*.svg`; p11-deadline marks the cancel path with a grey "alternative: the user gives up" band | — |
| C-11-F | done | 99 frames, 0 lint, 0 overflow, coverage 16/16 | 11.43 *An idempotent POST on the wire*: `code` too wide (rule 2b); "same bytes, replayed" moved to its own aligned line | — |


## Parallel work (second session)

A second session works **from the last part backwards** (parts 17, 16, 15, 14, 13, …) on D, F and V; this session's rows are marked `(s2)`. The first session continues forwards. Whoever reaches a part first adds its row before starting.

| ID | State | Counts | Changes made | For the author |
|---|---|---|---|---|
| C-16-D1 (s2) | done | 1 of 1 figure | `diagrams_p16.py` → `svg/p16-migration.svg` | — |
| C-16-F (s2) | done | 111 frames, 0 lint, 0 overflow, coverage 18/18 | 16.7 *Two kinds of token, two kinds of caller* (author change): the table held two tables; the "Caller" rows became a takeaway line, narration unchanged | — |
| C-16-V (s2) | built | 34.2 min real (est. 36.3), 1920×1080 + AAC, 22 chapters = 22 sections, no subtitle stream | sync probe at 90% passed; C-S3 run later | — |
| C-15-D1–D2 (s2) | done | 8 of 8 figures | `diagrams_p15.py` → `svg/p15-*.svg`; p15-lease numbers its steps ①–④ in the labels instead of the helper's message counters | — |
| C-15-F (s2) | done | 62 frames, 0 lint, 0 overflow, coverage 9/9 | none | — |
| C-15-V (s2) | built | 20.6 min real (est. 22.1), 13 chapters = 13 sections | sync probe at 90% passed | — |
| C-14-D1 (s2) | done | 4 of 4 figures | p14-histograms: host counts chosen so the fleet p99 really falls in 300–1000 (97% of count below 300); the spec's label "99% of count below here" became "97% of count below 300 → so p99 is in 300–1000" | — |
| C-14-F (s2) | done | 69 frames, 0 overflow, coverage 11/11 | 14.15 *A series is a name plus one combination of label values*: the series line wrapped after `status="200",` (rule 2b) | — |
| C-14-V (s2) | built | 22.3 min real (est. 23.1), 15 chapters = 15 sections | sync probe at 90% passed | — |
| C-13-D1–D2 (s2) | done | 7 of 7 figures | p13-cells shows "LB · app · cache · DB" as two text lines per cell | — |
| C-13-F (s2) | done | 92 frames, 0 overflow, coverage 14/14 | 13.37 *The next five minutes after a zone is lost at peak*: "balancers eject its backends within seconds" → "balancers eject it in seconds" (rule 2b) | — |
| C-13-V (s2) | built | 30.4 min real (est. 32.3), 18 chapters = 18 sections | sync probe at 90% passed | — |
| C-17-F (s2) | done | 58 frames, 0 overflow, coverage 22/22 | reuses p11-l4-l7, p7-lsm-write, p4-registry, p10-segments, p15-planes | — |
| C-17-V (s2) | built | 15.6 min real (est. 15.8), 11 chapters = 11 sections | sync probe at 90% passed | — |
| C-12-D1 (s2) | done | 3 of 3 figures | `diagrams_p12.py` → `svg/p12-*.svg`; p12-queue: r7 is drawn only at the head (dropped), the queue holds r3–r11 and the rejected arrival is r12 | — |
| C-12-F (s2) | done | 67 frames, 0 overflow, coverage 9/9 | none | — |
| C-12-V (s2) | built | 21.9 min real (est. 23.9), 13 chapters = 13 sections | sync probe at 90% passed | — |
| C-01-V rebuild (s2) | built | 27.4 min, 15 chapters | after the p1-load-curve author fix; frames re-rendered, 0 overflow | — |
| C-M1 (s2) | done | coverage 217/217; `SD-Full-Course.mp4` 7:45:14 = sum of parts, 273 chapters, 1.19 GB; `INDEX.md` 217 rows with timestamps | — | — |
| C-03-V | built | 20:12 real (est. 23.0), 1920×1080 + AAC, 14 chapters = 14 sections, no subtitle stream | six frames at 10–90 % looked at, captions match their slides; `check_audio.py` (C-S3) run later, see C-S3 | — |
| C-04-V | built | 23:19 real (est. 26.9), 1920×1080 + AAC, 11 chapters = 11 sections, no subtitle stream | six frames at 10–90 % looked at, captions match their slides; `check_audio.py` (C-S3) run later, see C-S3 | — |
| C-05-V | built | 32:16 real (est. 35.6), 1920×1080 + AAC, 18 chapters = 18 sections, no subtitle stream | six frames at 10–90 % looked at, captions match their slides; `check_audio.py` (C-S3) run later, see C-S3 | — |
| C-06-V | built | 26:48 real (est. 30.2), 1920×1080 + AAC, 15 chapters = 15 sections, no subtitle stream | six frames at 10–90 % looked at, captions match their slides; `check_audio.py` (C-S3) run later, see C-S3 | — |
| C-07-V | built | 32:40 real (est. 36.5), 1920×1080 + AAC, 19 chapters = 19 sections, no subtitle stream | six frames at 10–90 % looked at, captions match their slides; `check_audio.py` (C-S3) run later, see C-S3 | — |
| C-08-V | built | 28:04 real (est. 30.2), 1920×1080 + AAC, 14 chapters = 14 sections, no subtitle stream | six frames at 10–90 % looked at, captions match their slides; `check_audio.py` (C-S3) run later, see C-S3 | — |
| C-09-V | built | 27:13 real (est. 30.2), 1920×1080 + AAC, 15 chapters = 15 sections, no subtitle stream | six frames at 10–90 % looked at, captions match their slides; `check_audio.py` (C-S3) run later, see C-S3 | — |
| C-10-V | built | 35:04 real (est. 38.1), 1920×1080 + AAC, 21 chapters = 21 sections, no subtitle stream | six frames at 10–90 % looked at, captions match their slides; `check_audio.py` (C-S3) run later, see C-S3 | — |
| C-11-V | built | 35:15 real (est. 37.1), 1920×1080 + AAC, 20 chapters = 20 sections, no subtitle stream | six frames at 10–90 % looked at, captions match their slides; `check_audio.py` (C-S3) run later, see C-S3 | — |
| C-S1 (s2) | done | sample part: 15 slides of every type, 123 words; 1920×1080 + AAC + 1 chapter, no subtitle stream | `tests/sample.txt`, `svg/sample-box.svg`; `src/ch99.txt` and its MP4 deleted after the probe | — |
| C-S2 (s2) | done | 9 tests pass; a one-character change to the golden HTML fails `test_golden` (tried, restored) | `tests/test_course.py`, `tests/golden/`: golden compile, segments = joined file, symbol and long-line lint, duplicate / unknown / missing concept fail `coverage` | — |
| C-S3 (s2) | done | 188 terms (say.py keys + acronym-like words in narration) voiced and transcribed with Whisper `small.en`; 9 flagged, rechecked in sentences | `say.py` (rule 3): Kafka `Kaf-ka` → `Kahf-kuh`; added InnoDB `inno-D-B`, RPCs `R-P-Cees`, DDSketch `D-D-sketch`, Count-Min `count min`, IPv4 `I-P-v-four`, IPv6 `I-P-v-six`. Kubernetes, GC and CAP were misheard only in the one-word list and were fine in sentences: unchanged. Parts 6, 8, 9, 10, 11 and 17 speak a changed term and were rebuilt | — |
| C-S4 (s2) | done | part 1: 11 concept rows, 5 figures, 6 probes; test added | `course.py companion`, `records()`, `reading_plan()` | — |
| C-01-K … C-17-K (s2) | done | 17 ledgers, 360 derived rows recomputed by `claims_check.py`, 0 off; every spoken number matches its slide | `claims/pNN.md`, `claims_check.py`, `claims_dump.py`; no transcript changed | see the end of p01, p03, p08, p12, p14, p16, p17 |
| C-06/08/09/10/11/17-V rebuild (s2) | built | 26:48, 28:04, 27:13, 35:04, 35:15, 15:35; chapters = sections; no subtitle stream | only the re-spelled lines re-voiced; sync probe at 90% on all six passed | — |
| C-M1 re-run (s2) | done | `SD-Full-Course.mp4` 7:45:15 = sum of parts, 273 chapters, 1.19 GB; `INDEX.md` 217 rows | — | — |
| C-M2 (s2) | done | companion 33,000 words → 102-page PDF, no missing glyphs, pages looked at | `md()` maps ≈ and superscript digits for LaTeX; concept table weighted to the "line to say" column; A4 margins | — |
| C-M3 (s2) | done | claims grep: no quantity with two values across parts (regions 30/70/80 ms, Pub/Sub limits, RS (6, 3), retry budget agree); privacy grep clean | `theory/video/README.md`, one line in `theory/README.md`; **no Google Drive copy** (author's decision, 2026-11-13); plan 01 no longer names question banks | — |

## For the author

- **Two versions of `diagrams_p13.py` and `diagrams_p14.py` (s2).** The first session overwrote both scripts at 23:17 without knowing the second session was drawing them. The SVGs on disk (`svg/p13-*`, `svg/p14-{histograms,logs,columnar}`), the part 13 and 14 frames and both videos come from the **second session's** scripts, which are no longer on disk. Re-running the current scripts will redraw these figures in the first session's style. Decide which source to keep before anyone re-runs them.

- **Resolved (s2, author, 2026-11-13):** curve points changed in `diagrams/p01.md` and `diagrams_p01.py` so the curve is above 1,200 for about 6 h, with a mean of about 1,160; the narration is unchanged; part 1 re-rendered. Original note: **p1-load-curve vs. its narration.** The spec's curve points (…12 h 1,500 … 23 h 1,600, 24 h 700) sit above
  the 1,200 average from about 10:30 to 23:30, about **13 hours**, while the spec's note and slide 1.10's
  narration say "about six hours" and "overloaded for six hours". The curve's own mean is also about 1,600,
  not 1,200. Drawn as specified; either the points or the "six hours" should change.
- **Spec gaps resolved by the drawer:** latency-ladder axis starts at 10 ns (unlabelled) so the 100 ns bar
  has length; fan-out labels three green leaves "10 ms"; the load-curve top band (4,000–12,000) is compressed
  and labelled "axis break · top band compressed".
