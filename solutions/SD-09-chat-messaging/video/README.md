# SD-09 chat and messaging — mock-round video

A narrated mock system-design round at the **L6 Engineering Manager** bar, **21:38 at 1080p, 19 chapters**, in local
Kokoro voices (interviewer, candidate, candidate key lines spoken slower, coach) with burned-in captions and
chapters. Built with the `system-design-video` skill to `slide-video-kit/STANDARD.md`; content follows
`../../SD-09-chat-messaging.md`.

| File | Role |
|---|---|
| `chat-mock.script.md` | the spoken script: `[slide: v-NN]` / `[pause: s]` cues, `I:` / `C:` / `V:` (key line) / `N:` coach |
| `video-slides.html` + `video.css` + `deck.css` | 50 one-idea 16:9 slides; diagrams inlined from `svg/` |
| `diagrams.py` → `svg/` | C4 context, send-path and sync-path container views, the message-service component view, six sequences (send to an offline user, sync, the lost ACK, concurrent sends, receipts, the reconnect storm), groups compared, the edit/delete delta, phasing, four follow-up diagrams |
| `build-video.sh` | diagrams → slides → `frames/` → `chat-mock.mp4` (`--frames` stops after the frames) |

Shape: requirements ("neither loss nor duplicates"), the thesis ("start from the mailbox, not the socket"), three
numbers (2 TB of connections, 20 PB a year, a million receipts per group message), the WebSocket frames, the data
model, the C4 walk, four deep dives (ordering by a per-conversation sequencer, idempotent send and the lost ACK,
groups and receipts, a gateway dying with 500 k connections), edit and delete as a mid-round delta (plus what
end-to-end encryption would change), failures, probe-conversation SLOs, cost, phasing and teams, the close; then four
manager follow-ups: **(1)** the CEO announced end-to-end encryption; **(2)** a deploy restarts a zone; **(3)** a team
paged forty times a month; **(4)** storage cost down 40%. QA: Whisper excerpts 81–88% (homophones), a sync probe at
19:10, sampled frames; not watched end to end. The MP4 and `frames/` are gitignored; rebuild with
`video/build-video.sh` (about 15 minutes).
