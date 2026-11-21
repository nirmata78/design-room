# SD-82 · Instant credit at the point of sale: reference-solution video

Staff bar (L6/L7), manager layer marked AUX. **Length 69:59**, 18 chapters, **149 numbered slides**, **8,574 spoken
words** (candidate 86.0 %, interviewer 4.5 %, key line 4.7 %, coach 4.8 %). Scripted walkthrough with synthetic voices;
figures are illustrative, not any lender's numbers, and statements about lending rules are general, not legal advice.
**The technical content has not been reviewed by a person, and the video has not been watched end to end.** It replaces
problem 1 of the earlier course-builder fintech video (retired) as the reference for this question. Written companion:
`../SD-82_Credit_Decisioning_Reference_Design.md` (and PDF).

## Chapters

| Time | Chapter |
|---|---|
| 00:00 | 0 Cold open |
| 02:30 | 1 Requirements and scope |
| 07:37 | 2 Estimates |
| 12:05 | 3 Theory |
| 20:11 | 4 API and entities |
| 23:47 | 5 High-level design |
| 31:30 | 6 Bridge |
| 32:14 | 7 Challenges |
| 32:31 | 7.1 The bureau is slow |
| 37:05 | 7.2 The bureau is down for everyone |
| 41:26 | 7.3 The phone drops |
| 45:48 | 7.4 Funding fails after booking |
| 49:32 | 7.5 Explain a decision fourteen months later |
| 53:52 | 7.6 A new model approves six percent more |
| 57:32 | 7.7 Where identity data lives |
| 61:08 | 7.8 How would you know it is broken? |
| 64:49 | 8 Build cost (AUX) |
| 67:24 | 9 Recap |

## The eight challenges

| # | Challenge | The fix |
|---|---|---|
| 1 | The bureau is slow | Scatter-gather under one 2 s deadline; a breaker per vendor; the second bureau only on failure, never a race; late answers recorded |
| 2 | The bureau is down for everyone | A signed missing-data table (second bureau · small known customers under a cap · refer · decline with a real reason); token buckets per vendor; caps per merchant |
| 3 | The phone drops | Conditional update at a version, `UNIQUE(application_id)`, the outbox in the same commit; at-least-once relay, de-duplicating consumers |
| 4 | Funding fails after booking | Funding as its own state machine; UNKNOWN means query, never resend; three-way reconciliation with owned breaks |
| 5 | Explain a decision later | An immutable record of inputs, versions and ranked reasons; old models loadable; nightly replay; crypto-shredding at retention end |
| 6 | A new model approves more | Backtest → shadow → a capped 5 % challenger slice → early signals at 30–45 days → widen by policy change |
| 7 | Where identity lives | A vault; only it and the vendor adapters see real values; tokens and features everywhere else; the right rulebook |
| 8 | How would you know | SLIs on the decision (offers in 3 s, approval per merchant per hour, fallback against cap, booked-not-funded), symptom pairs, canaried policy changes |

## Rebuild

```bash
solutions/SD-82-credit-decisioning/video/build-video.sh            # diagrams -> slides + script -> frames -> credit-decisioning-reference.mp4
solutions/SD-82-credit-decisioning/video/build-video.sh --frames   # stop after the frames
cat solutions/SD-82-credit-decisioning/booklet-src/0*.md > solutions/SD-82-credit-decisioning/SD-82_Credit_Decisioning_Reference_Design.md
solutions/SD-82-credit-decisioning/build-sd-booklet.sh SD-82_Credit_Decisioning_Reference_Design   # the written reference design (PDF)
python3 ~/.claude/skills/slide-video-kit/scripts/publish_kit.py solutions/SD-82-credit-decisioning/video/publish/meta.json
```

Slides and script are generated together from `src/*.py` (the SD-94 DSL): edit the sources, not `video-slides.html` or
the script. The booklet is assembled from `booklet-src/`. Challenge views that show nothing in the top row of the baseline
are cropped below it in `diagrams.py`, so the picture keeps its size next to the text strips. The MP4 stays in this folder;
never copy it to a cloud folder or anywhere outside the repository.

## QA done

- ffprobe: H.264 1920×1080 + AAC + chapter data, no subtitle stream, 18 chapters, 69:59.
- All 149 frames read on contact sheets (eight to a sheet); fixed: challenge diagrams that shrank beside their strips
  (views cropped), the latency bar's overlapping labels, baseline box texts that overflowed, the containers view's crossing edges.
- Audio (faster-whisper base.en, 20 × 30 s excerpts): confidence −0.16 to −0.42, 17 substitutions, all near-homophones or
  function words (trace/trays, pull/poll, a signed/assign, "a refer" heard as "a referrer"); no term mispronounced.
- Sync probe at 65:25: the transcribed line and the burned caption on slide 140 match.
- Eight frames sampled across the length: slides and captions correct.
- Booklet: 41 pages, about 14.3k words, built clean (≈ and superscripts written as LaTeX), no leaked fences; all pages tiled
  and looked at, pages 10 and 27 zoomed.

## Canon check

| Canonical point | Covered at, or dismissed because |
|---|---|
| Scatter-gather with timeouts and circuit breakers | Theory M1; C1 |
| No hedged requests to paid vendors | Options matrix row B; C1 |
| Missing-data policy with refer, owned by credit risk, capped | Theory M2; C2 |
| Application state machine, idempotency keys, unique loan, outbox | M3, M4; C3 |
| A credit pull is not compensated; only funding is | Theory 1 (not a saga); C3 table; C4 |
| Reproducible decision record with versions and reasons (adverse action) | M5; C5 |
| Champion and challenger with exposure caps, early signals, fairness | C6 |
| PII vault and tokenisation; the card standard is not the SSN rulebook | M6; C7 |
| Bureau cost as the largest line; report reuse | Ch. 2; build cost |
| Lender of record (partner bank) | Ch. 1, question 3 |
| Durable workflow engines | Options matrix row D, the honest equal |
| Cash-flow underwriting with bank data | Optional input never awaited at the counter (ch. 1 Q4; booklet stage 7) |
| Merchant fraud and merchant underwriting | Dismissed aloud (scope; failure catalogue): merchant risk, another system |
| What changed recently | Workflow engines common; bank data through aggregators; regulators asking for explainable models and documented fairness testing |

## Publish kit

`publish/`: YouTube title (96/100), description with chapters (3,183/5,000), tags, thumbnail (checked), LinkedIn post
(hook 104 characters) and first comment. Not uploaded, not posted.
