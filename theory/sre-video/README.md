# theory/sre-video · SRE course, then and now

A review-ready kit for a 16-episode narrated course on the Google SRE book, modernised. **Everything except the video itself exists.**
Start with [`AGENDA.md`](AGENDA.md), then [`REVIEW-GUIDE.md`](REVIEW-GUIDE.md).

## What is here

| Path | What | Edited by hand? |
|---|---|---|
| `AGENDA.md` | Episodes, timings, coverage of the book, alignment with the plans | yes |
| `REVIEW-GUIDE.md` | Where to start, and the decisions that need you | yes |
| `src/chNN.txt` | **The source of truth**: slides and narration of episode NN (the course builder's format) | yes |
| `series.json` | Builder settings for this series | yes |
| `diagrams_sre.py` → `svg/` | 33 figures, drawn from code | yes (script) |
| `review/EpNN-transcript.md` | Reader transcript per episode: every slide, its on-screen text, who speaks what | generated |
| `review/THESIS-INSERTS.md` | All 79 slower-voice key lines in one list | generated |
| `review/DIAGRAMS.md`, `review/stats.json` | Diagram index, per-episode counts | generated |
| `CLAIMS.md` | Ledger: every number and factual claim, and how it is backed | yes |
| `VERIFY.md` | The "then and now" claims, checked against public sources on 2026-11-12, with the corrections made | yes |
| `STATUS.md` | State of each episode, and the checks that were run | yes |

Slide decks (one PDF per episode, 1080p frames behind them) are written to `theory/sre-video/out/SRE-Episode-NN-slides.pdf` (gitignored).

## Commands (run from `theory/video`)

```bash
python3 ../sre-video/diagrams_sre.py                       # redraw all figures into svg/
python3 course.py --root ../sre-video compile              # lint, word count, estimated minutes
python3 course.py --root ../sre-video frames [NN…]         # render slides, check overflow, write the slide PDFs
python3 ../sre-video/export_review.py                      # regenerate review/ from src/
python3 course.py --root ../sre-video video [NN…] -j3          # voices and one MP4 per episode, then: merge → SRE-Full.mp4
```

Two small changes were made to the shared builder for this series, both additive: a `now` panel kind (label "Then and now") in
`theory/video/course.py` and `sd.css`, and an `aux` flag (the existing EM-layer badge in `video.css`) on any slide.

## Rules this kit follows

- The course tells the story as its own. It does not say "the book says"; where a source must be named it is Google. No paragraph of Google's SRE books is read out and no figure is redrawn line for line. Google's free SRE books and workbook are listed as further reading on each episode's last slide.
- Numbers shown on a slide and spoken match; arithmetic was re-run (`CLAIMS.md`). Illustrative figures are labelled as such on the slide.
- Facts about Google's internal systems are stated in the past tense or as "at Google", never as how Google works today.
- "Then and now" claims were checked against public documentation (`VERIFY.md`); one was corrected (continuous profiling is still an alpha signal in OpenTelemetry).

## Not done

No audio, no video, no pronunciation pass (`check_audio.py`), no human review of the technical content, nothing watched end to end.
