# SD-82 · Instant credit at the point of sale: reference-solution video

Staff bar (L6/L7), manager layer marked AUX. **Length 1:32:04**, 20 chapters, **168 numbered slides** in **567 reveal frames**, **10,932 spoken words** (candidate 86.0 %, interviewer 4.1 %, key line 4.0 %, coach 6.0 %). Scripted walkthrough with synthetic voices;
figures are illustrative, not any lender's numbers, and statements about lending rules are general, not legal advice.
**The technical content has not been reviewed by a person, and the video has not been watched end to end.** It replaces
problem 1 of the earlier course-builder fintech video (retired) as the reference for this question. Written companion:
`../SD-82_Credit_Decisioning_Reference_Design.md` (and PDF).

## Chapters

| Time | Chapter |
|---|---|
| 00:00 | 0 Cold open |
| 02:32 | 1 Requirements and scope |
| 07:43 | 2 Estimates |
| 12:15 | 3 Theory |
| 20:34 | 4 API and entities |
| 24:19 | 5 High-level design |
| 32:35 | 5.1 Components and technologies |
| 44:47 | 5.2 When you don't need all this |
| 46:28 | 6 Bridge |
| 47:13 | 7 Challenges |
| 47:30 | 7.1 Challenge 1: The bureau is slow |
| 53:54 | 7.2 Challenge 2: The bureau is down for everyone |
| 58:36 | 7.3 Challenge 3: The phone drops |
| 1:03:16 | 7.4 Challenge 4: Funding fails after booking |
| 1:07:18 | 7.5 Challenge 5: Explain a decision fourteen months later |
| 1:13:28 | 7.6 Challenge 6: A new model approves six percent more |
| 1:17:23 | 7.7 Challenge 7: Where identity data lives |
| 1:21:15 | 7.8 Challenge 8: How would you know it is broken? |
| 1:25:16 | 8 Build cost |
| 1:29:17 | 9 Recap |

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

## Retrofit, 2026-11-22

Brought to the current standard by `RETROFIT.md`: the Google theme (`video.css`, `google-theme.css`), progressive reveal (every table row,
card, trace event and figure step appears as it is spoken), sidecar captions (`.srt` and `.vtt` beside the MP4, nothing burned in), the
technology chapter **5.1** generated from `../stack.json` (container view with technologies, one slide per technology with its rejected
alternatives, the stack on one slide, the drill interlude) and a **Rejected** line on every challenge's fix slide.

**93 of the 161 slides were written before reveal markers existed; their markers were placed automatically** (`dsl.META["automark"]`:
the narration is cut at sentences and dealt to the reveal units by word overlap). Watch those slides and move a marker by hand where one
lands badly. Not done in this pass: the C4 context moved to the end of chapter 1, a mechanism map in the theory chapter, extra sequences per
requirement, component views. The previous sources are kept in `.v1-retrofit-2026-11-22/` until the author has watched this version.

## Review for a lending EM loop, 2026-11-22

Reviewed against an EM-level lending checklist and rebuilt (`.v2-review-2026-11-22/` held the previous sources during the run and has been removed). Changes:

- Challenge 1: cost tiers (tier-0 in-house checks before one parallel gather; full waterfall rejected at the counter); soft inquiry recorded.
- Challenge 5: the rulebook by name (ECOA / Regulation B, FCRA, fair lending, model risk), each mapped to fields of the decision record.
- 5.1: a C4 component view of the decision orchestrator. 5.2: the alternate path (one bureau and refer; crossover ≈ 330,000 applications a month).
- Build cost: contracts between teams (owner → consumers → change rule), Conway's law stated; LoanBooked consumed by SD-95 and SD-99.
- Consistency: stack.json no longer says the orchestrator awaits bank data, and late calls are recorded, not cancelled; the gather code is labelled pseudocode (the service is Go).
- Layout gate: 57 failures → **0** (C4 views redrawn wide, overlay notes dropped where the strip repeated them, code ≤ 56 × 12, ERD sizes).

QA of this build: `check_layout.py` 0 failures; `ffprobe` H.264 + AAC 1920×1080, 20 chapters, no subtitle stream; `.srt`/`.vtt` beside the MP4, no line over 42 characters, every VTT cue with a voice span; Whisper check on 20 excerpts found only transcription noise; frames of the new slides read as images. **Not watched end to end.**
