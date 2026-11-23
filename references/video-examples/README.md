# Reference examples — style and structure studies

Two third-party system-design walkthroughs (ShowOffer channel) and one book chapter, kept as **private study copies** and
decomposed into what we can reuse in our own video kit. **The rules drawn from them are in the project skill
[`reference-solution`](../../.claude/skills/reference-solution/GUIDELINES.md)**; this folder is the evidence.

| # | Folder | Video | Length | Character |
|---|---|---|---|---|
| 01 | [`01-batch-inference-anthropic-openai/`](01-batch-inference-anthropic-openai/ANALYSIS.md) | Design Batch Inference System (new version) · https://www.youtube.com/watch?v=pHV6xYw7vVA | 66:34 | deep, 7 incident-style challenges on one evolving canvas |
| 02 | [`02-url-shortener-openai/`](02-url-shortener-openai/ANALYSIS.md) | Design a URL Shortener Service · https://www.youtube.com/watch?v=-ldyMeu6iL4 | 38:42 | shallow, framework-driven, one workflow per FR |
| 03 | [`03-url-shortener-xu-book/`](03-url-shortener-xu-book/ANALYSIS.md) | *System Design Interview* (Xu, vol. 1), chapter 8 · book text in `private/books/`, not here | ~2,000 words | the older written canon: four steps, estimate chain, two-option table; no failure or operations |

**Start here:** the skill's `GUIDELINES.md` for what we decided; then [`REPLICATION.md`](REPLICATION.md) for the earlier working notes — side-by-side comparison, what to adopt (15 ranked items), the whiteboard skin spec,
the build plan for our kit, and the reusable script grammar.

## Per-folder contents

| File | Tracked in git? | What |
|---|---|---|
| `ANALYSIS.md` | yes | agenda with timestamps, script architecture, diagramming approach, gaps, reusable assets |
| `original.mp4` | **no** (gitignored) | the downloaded video, 1080p |
| `transcript.timestamped.txt` | **no** | `[hh:mm:ss] text` — 02 from YouTube captions, 01 from local faster-whisper (`base.en`) |
| `subs.en.vtt` | no | raw captions (02 only; 01 was rate-limited by YouTube, HTTP 429) |
| `meta.info.json` | no | yt-dlp metadata (chapters, description) |
| `frames/` | no | one frame per 20 s (`t0001.jpg` = 0:00) |
| `sheet_*.jpg` | no | contact sheets (4×4 of every 6th frame; 01 has 3, 02 has 1) |

Media and transcripts are third-party content: they stay on this machine (see `.gitignore`); only our own analysis is tracked.
Do not quote the transcripts in published material beyond short fair-use excerpts, and do not republish the videos.
