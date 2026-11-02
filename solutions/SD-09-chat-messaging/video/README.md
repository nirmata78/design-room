# SD-09 chat and messaging — mock-round video (v2, Staff L6/L7)

A narrated mock system-design round at the **Staff L6/L7** bar, **43:33 at 1080p, 24 chapters, 85 numbered slides** (AUX = EM layer, optional), in local
Kokoro voices (interviewer, candidate, candidate key lines spoken slower, coach) with burned-in captions and
chapters. Built with the `system-design-video` skill to `slide-video-kit/STANDARD.md`, with SD-08 v3 as the model; content follows
`../../SD-09-chat-messaging.md`, and goes deeper where the Staff bar asks.

| File | Role |
|---|---|
| `chat-mock.script.md` | the spoken script: `[slide: v-NN]` / `[pause: s]` cues, `I:` / `C:` / `V:` (key line) / `N:` coach |
| `video-slides.html` + `video.css` + `deck.css` | 85 one-idea 16:9 slides; diagrams inlined from `svg/` |
| `diagrams.py` → `svg/` | socket vs mailbox, the log and its cursors, a Chen conceptual ERD, the physical tables, wide-column partitions, the hot keys and their writers, C4 context, send-path and sync-path containers, the message-service component view, eleven sequences (commit before ACK, send to an offline user, two devices, sync, a missed push, concurrent sends, leader failover, the lost ACK, receipts, the reconnect, a month offline), delivery routing, groups compared, the edit/delete delta, phasing, five follow-up diagrams |
| `build-video.sh` | diagrams → slides → `frames/` → `chat-mock.mp4` (`--frames` stops after the frames) |
| `publish/` | YouTube and LinkedIn kit from `meta.json`, by `slide-video-kit/scripts/publish_kit.py`: `youtube.md` (fields and upload steps), `linkedin.md`, paste-ready text, `thumbnail.png`, a native teaser |

Shape: requirements ("neither loss nor duplicates"), six terms with two pictures, the thesis ("start from the mailbox, not the
socket"), estimates as arithmetic (2 TB of sockets, 20 PB a year, a million receipts per group message), wire formats for send,
deliver, sync and the push platform, the data model in five views, technology against the alternatives, the send path and the
sync path each as C4 → rule → sequence → code, four deep dives (ordering and failover; the lost ACK at every crash point; groups,
inbox coalescing and the tier line; a gateway dying with 500 k connections, and a month offline), edit and delete as a delta,
failures, probe-conversation SLOs, cost, the close; then five follow-ups: **(1)** end-to-end encryption by Friday; **(2)** a deploy
restarts a zone; **(3)** a broadcast channel with a million subscribers; **(4)** storage cost down 40%; **(5)** forty pages a month (AUX).

Beyond the `.md`, for depth: the sequencer is a partition's Raft leader, dedup runs before numbering, partitions are capped by a
bucket computed from seq, the session registers before sync reads, and receipts split at a configurable tier line (~32 members).

QA: Whisper excerpts 80–86% (flagged words are homophones: sync/sink, leader/liter), sync probe at 40:00, sampled frames; not
watched end to end. The MP4 and `frames/` are gitignored; rebuild with `video/build-video.sh` (about 15 minutes). Copied to Drive as
`Interview videos/System design/SD-09-chat-messaging.mp4`. v1 (L6 EM, 21:38) is in `.v1-em-2026-10-29/`.

**Written companion:** [`../SD-09_Chat_Messaging_Reference_Design.md`](../SD-09_Chat_Messaging_Reference_Design.md), which shares these diagrams (`../build-sd-booklet.sh SD-09_Chat_Messaging_Reference_Design`). It goes deeper than the video; the video's v2.1 render carries its code and sync corrections.
