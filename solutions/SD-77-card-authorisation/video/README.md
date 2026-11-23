# SD-77 · Card authorisation and issuer processing: reference-solution video

Staff bar (L6/L7), manager layer marked AUX. **Length 75:24**, 18 chapters, **156 numbered slides**, **9,223 spoken
words** (candidate 86.2 %, interviewer 4.9 %, key line 4.8 %, coach 4.2 %). Scripted walkthrough with synthetic voices;
figures are illustrative, not any issuer's, processor's or network's numbers; not legal, compliance or scheme-rule
advice. **The technical content has not been reviewed by a person, and the video has not been watched end to end.**
It replaces problem 3 of the 2026-11-20 fintech series (retired). Written companion:
`../SD-77_Card_Authorisation_Reference_Design.md` (and PDF, 41 pages).

## Chapters

| Time | Chapter |
|---|---|
| 00:00 | 0 Cold open |
| 02:32 | 1 Requirements and scope |
| 07:43 | 2 Estimates |
| 12:46 | 3 Theory |
| 21:35 | 4 API and entities |
| 26:03 | 5 High-level design |
| 35:53 | 5.1 Components and technologies |
| 47:06 | 6 Bridge |
| 47:49 | 7 Challenges |
| 48:07 | 7.1 Challenge 1: The tip |
| 53:03 | 7.2 Challenge 2: Two swipes, one balance |
| 57:38 | 7.3 Challenge 3: The same message twice, and in the wrong order |
| 1:02:02 | 7.4 Challenge 4: The model is slow tonight |
| 1:07:00 | 7.5 Challenge 5: A burst, seconds apart |
| 1:11:07 | 7.6 Challenge 6: A new attack at 2 a.m. |
| 1:15:38 | 7.7 Challenge 7: We were down for twenty minutes |
| 1:20:46 | 7.8 Challenge 8: Declines doubled in ten minutes |
| 1:24:51 | 8 Build cost |
| 1:27:29 | 9 Recap |

## The eight challenges

| # | Challenge | The fix |
|---|---|---|
| 1 | The tip | A hold, not a debit; clearing moves the amount from hold to posted in one write; expiry by merchant type, after the day's file |
| 2 | Two swipes, one balance | One conditional write per account partition; sub-limits per card for large shared accounts |
| 3 | Twice, and out of order | Idempotency on the network reference, written with the hold; tombstones for early reversals |
| 4 | The model is slow tonight | A 60 ms cut-off; a fail-policy table with hourly exposure caps, owned by risk and finance |
| 5 | A burst, seconds apart | Inline burst counters (one round trip); pattern features from the stream; features logged |
| 6 | A new attack at 2 a.m. | Rules as versioned data: backtest, shadow, slice, enforce; expiry; shadow cannot measure false positives |
| 7 | Down for twenty minutes | Record every stand-in advice once, even past zero; over-limit as a state; idempotent clearing files |
| 8 | Declines doubled | Decision SLIs (approval rate by merchant type), symptom pairs, a runbook that starts with changes |

## Rebuild

```bash
solutions/SD-77-card-authorisation/video/build-video.sh            # diagrams -> slides + script -> frames -> card-authorisation-reference.mp4
solutions/SD-77-card-authorisation/video/build-video.sh --frames   # stop after the frames
cat solutions/SD-77-card-authorisation/booklet-src/*.md > solutions/SD-77-card-authorisation/SD-77_Card_Authorisation_Reference_Design.md
solutions/SD-77-card-authorisation/build-sd-booklet.sh SD-77_Card_Authorisation_Reference_Design   # the written reference design (PDF)
python3 ~/.claude/skills/slide-video-kit/scripts/publish_kit.py solutions/SD-77-card-authorisation/video/publish/meta.json
```

Slides and script are generated together from `src/*.py` (the SD-94 DSL): edit the sources, not `video-slides.html` or
the script. The booklet is assembled from `booklet-src/`. The MP4 stays in this folder; never copy it to a cloud folder.

## QA done

- ffprobe: H.264 1920×1080 + AAC + chapter data, no subtitle stream, 18 chapters, 75:24.
- All 156 frames read on contact sheets; fixed: five slides whose tall baseline view shrank (strips moved to chips), the
  budget bar's colliding labels, cropped notes on the overlay views, the container view's routing.
- Whisper on 24 × 30 s excerpts: near-homophones only (write/right, and/in). Targeted windows: "issuer",
  "authorisation", "chargebacks", "I-S-O eighty-five eighty-three", "merchant category code" all heard correctly. "auth"
  is never spoken; it is respelled "authorisation" in `theory/video/say.py` (added for this video; also fixes SD-44's
  "auth pending" on its next rebuild). "chargeback" is respelled "charge-back" (was heard as "charger back").
- Sync probe at 73:56: audio "Eight fixes, each with its property" over slide 154 with the same caption.
- Eight frames sampled across the length, read as images.
- Not watched end to end.

## Canon check

| Canonical point | Source | Covered at, or dismissed because |
|---|---|---|
| Authorisation vs clearing and settlement; holds | cue sheet; issuer documentation | M1; challenge 1; flow FR3 |
| Available balance = balance − holds | cue sheet | M1; challenge 1 trace |
| Network deadline and stand-in, advices | cue sheet | Ch. 1 Q2; the central tension; challenge 7 |
| Idempotency on network identifiers; out-of-order reversals | cue sheet | M2; challenge 3 |
| Per-cardholder serialisation | cue sheet | M3; challenge 2 |
| Fraud scoring inside a budget; fail open or closed per risk class | cue sheet; retired fintech problem 3 | M4; challenge 4 |
| Velocity: inline bursts, stream aggregates | cue sheet; retired problem 3 | M5; challenge 5 |
| Rules as versioned data; backtest → shadow → slice → enforce | cue sheet; retired problem 3 | M6; challenge 6 |
| Shadow cannot measure false positives | cue sheet | challenge 6 second push |
| Clearing matching with fuzzy fallback; unmatched both ways | cue sheet | challenge 1 second fix; FR3 |
| Curveball: clearing file late and duplicated | cue sheet | challenge 7 second push |
| A hold never cleared after 30 days | cue sheet probe | challenge 1 (lifetimes by merchant type) |
| Runbook "declines doubled"; who owns the fail policy | cue sheet EM bar | challenge 8; challenge 4 second fix; ch. 8 |
| Card data scope | general canon | Ch. 1 Q6: tokens only; dismissed aloud as a cut |
| 3-D Secure | cue sheet input list | dismissed: its result arrives as an input field |
| What changed recently | — | network risk scores arrive with the request as a feature (booklet Stage 7); tokenised cards; sandboxed rule languages such as CEL (booklet appendix F) |

## Retrofit, 2026-11-22

Brought to the current standard by `RETROFIT.md`: the Google theme (`video.css`, `google-theme.css`), progressive reveal (every table row,
card, trace event and figure step appears as it is spoken), sidecar captions (`.srt` and `.vtt` beside the MP4, nothing burned in), the
technology chapter **5.1** generated from `../stack.json` (container view with technologies, one slide per technology with its rejected
alternatives, the stack on one slide, the drill interlude) and a **Rejected** line on every challenge's fix slide.

**101 of the 168 slides were written before reveal markers existed; their markers were placed automatically** (`dsl.META["automark"]`:
the narration is cut at sentences and dealt to the reveal units by word overlap). Watch those slides and move a marker by hand where one
lands badly. Not done in this pass: the C4 context moved to the end of chapter 1, a mechanism map in the theory chapter, extra sequences per
requirement, component views. The previous sources are kept in `.v1-retrofit-2026-11-22/` until the author has watched this version.
