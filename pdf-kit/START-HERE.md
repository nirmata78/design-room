# Notification Platform reference interview: source files

Everything needed to rebuild, edit or extend `Notification_Platform_Reference_Interview.pdf`.

## Where the content lives

| File | Role |
|---|---|
| `examples/notification-platform/notification-platform.html` | **The source of truth.** All text, tables, boxes and code. Edit this. |
| `examples/notification-platform/svg/*.svg` | The 11 diagrams, one file each, referenced from the HTML as `<!--SVG:name-->` |
| `examples/notification-platform/notification-platform.md` | A readable Markdown export of the same content (box labels shown as **[Label]**). Handy for reviewing or feeding to another session; not used by the build |
| `examples/notification-platform/notification-platform.pdf` | The built PDF (11 pages) |
| `style.css`, `fonts/`, `build.py`, `check.py` | The PDF style kit: see `README.md` |
| `examples/url-shortener/`, `examples/redis-ticketing/` | The two earlier guides in the same style, as further examples |

## Rebuild

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && python -m playwright install chromium
python build.py examples/notification-platform/notification-platform.html \
  --footer "Notification platform · reference system design interview"
python check.py examples/notification-platform/notification-platform.pdf   # page images + half-empty-page warnings
```

## Diagrams

| File | Shows |
|---|---|
| clock | the 45-minute round |
| cost | volume share vs cost share (SMS = 2% of volume, ~94% of cost) |
| context | C4 level 1: tenants, platform, providers |
| containers | C4 level 2: intake, Kafka topics, policy, channel workers, stores |
| lifecycle | notification states: ACCEPTED … SUPPRESSED / DEFERRED / FAILED |
| gates | the six ordered policy gates |
| isolation | P0 / P1 / P2 isolated by topic, consumers, lanes, provider capacity |
| p0seq | password reset during a 400 M campaign (sequence) |
| halt | canary → hold → release, and kill-switch propagation |
| fallback | wrong vs right fallback |
| retry | backoff with full jitter, circuit breaker |
| fu-tenant | video follow-up 1: tenant asks vs the contract check, and the exception path |
| fu-incident | video follow-up 2: duplicate storm, first hour to week one |
| fu-roadmap | video follow-up 3: three teams over four quarters, migration milestones |
| fu-cost | video follow-up 4: SMS bill doubled, slice to SMS pumping, contain and fix |

## Mock-round video (L6 Engineering Manager framing)

`examples/notification-platform/video/` holds a narrated mock round, about 28 minutes at **1080p**, in local Kokoro
voices (interviewer, candidate, candidate key lines spoken slower, coach) with burned-in captions and chapters.
Built with the `system-design-video` skill (`~/.claude/skills/system-design-video/`).

| File | Role |
|---|---|
| `notification-mock.script.md` | the spoken script: `[slide: v-NN]` and `[pause: s]` cues, `I:` / `C:` / `V:` (key line) / `N:` coach |
| `video-slides.html` + `video.css` + `deck.css` | 51 one-idea 16:9 slides; diagrams inlined from `../svg/` |
| `diagrams.py` | source of the C4 and sequence diagrams below (generators in the `slide-video-kit` skill) |
| `build-video.sh` | diagrams → slides → `frames/` → `notification-mock.mp4` (`--frames` stops after the frames) |

New diagrams (generated, do not hand-edit): `c4-context`, `c4-containers-send`, `c4-containers-feedback`,
`c4-component-policy`, `seq-p0` (reset during a campaign), `seq-dedup` (redelivery and duplicates),
`seq-campaign` (canary and release), `seq-halt` (kill switch), `seq-fallback` (definite failure only).

Shape: requirements, the governance thesis, estimates, API, stores, the C4 walk, four deep dives (the gates,
priority isolation, campaigns and the kill switch, fallback and providers), a mid-round requirement, operations, the
EM layer and the close; then four manager follow-ups: **(1)** a VP wants their promo as P0 and the caps lifted;
**(2)** a duplicate storm from a tenant minting a new dedupKey per retry; **(3)** twelve engineers, a year, twenty
teams to migrate; **(4)** the SMS bill doubled (SMS pumping). MP4 and frames are gitignored; rebuild with
`video/build-video.sh` (about 15 minutes).

## Ideas for expanding it in a new session

Prompt suggestion: *"Using START-HERE.md and README.md in this folder, extend notification-platform.html with … ; keep the style, put new diagrams in svg/, rebuild with build.py, review with check.py and fix half-empty pages."*

- A deep dive on **digests** (keyed windows per user and category, Flink or Kafka Streams).
- **Multi-region**: home-region processing, preference replication, provider failover per region.
- **Push internals**: APNs HTTP/2 multiplexing, FCM topics vs per-token sends, token registry lifecycle.
- **Audit and compliance**: immutable preference history, GDPR deletion across inbox, log and analytics.
- An audio mock interview generated from the content, like the URL shortener one.

Source design: SD-12 Notification and Push Platform reference solution (19 October 2026).
