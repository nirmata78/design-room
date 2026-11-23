# LinkedIn kit: Log Replay & Simulation Platform System Design: Staff Reference (Determinism, Caching, Gates)

Post from a computer, after the YouTube video is public. The link is still pending: rerun with --youtube-url.

**Post** (1148/3000; hook 107 characters, before the "see more" fold): `pbcopy < linkedin-post.txt`

```text
"Set the random seed" fixes one of the six ways a replay gives two answers. The grade is on the other five.

I've published a 63-minute reference solution for a log-replay and regression-gate platform at the Staff bar: theory, a three-version design and six challenges, on 473 numbered slides.

The idea that unlocks it: make every run a pure function of a pinned manifest. Then outputs can be cached by the hash of everything that made them, a difference between two builds means the build changed, and the gate can compare pairs instead of guessing at noise.

What it goes into:
→ Message ordering, GPU atomics and the wall clock
→ Merkle keys: what a perception change must recompute
→ Release day against 3,000 engineers
→ A gate that must prove it can fail

Best on a second pass: pause after each question and answer it first.

▶ [YouTube link: rerun publish_kit.py with --youtube-url]

It's a scripted walkthrough with synthetic voices, built with Claude Code from design-room, my open-source system design interview simulator.

How do you know your own regression gate can still fail?

#SystemDesign #SoftwareEngineering #DistributedSystems
```

**First comment** (277/1250):

```text
Written reference design, stage by stage: https://github.com/nirmata78/design-room/blob/main/solutions/SD-98-replay-platform/SD-98_Replay_Platform_Reference_Design.md

Run this round yourself, with an AI interviewer that won't help you: https://github.com/nirmata78/design-room
```

**Media: attach the reference design.** In the post composer, More (+) → Add a document → `../../SD-98_Replay_Platform_Reference_Design.pdf` (21 pages, 1.3 MB; limit 300 pages, 100 MB).
Document title, shown on the viewer: **A reproducible replay and regression-gate platform: a Staff-level reference design**. A post carries one attachment, so the video stays a link in the text, and the document is what shows in the feed.
