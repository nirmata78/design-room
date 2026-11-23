# LinkedIn kit: Distributed Denylist (IP Blocking) Design: Staff-Level Reference Solution

Post from a computer, after the YouTube video is public. The link is still pending: rerun with --youtube-url.

**Post** (1343/3000; hook 129 characters, before the "see more" fold): `pbcopy < linkedin-post.txt`

```text
A denylist looks like a hash set. The hard part is what lets a ban reach every server fast without letting a mistake do the same.

I've published a 107-minute reference solution for the distributed denylist (IP blocking) question, at the Staff bar: theory, a three-version design, seven challenges, and the build cost, on 599 numbered slides.

The idea that unlocks it: the check must be local and the list cannot be. The pipe that delivers a ban in ten seconds delivers a mistake in ten seconds, so a push gets the discipline of a binary: versions, a canary gated on block rate, an allowlist that always wins, and a rollback that is a new version.

What it goes into:
→ A node two hours behind, and what a poll actually fetches
→ A stale node: stale is not open, and who signs the bound
→ A list too big for memory: why a Bloom filter alone blocks real users
→ The cost in people and months

Best on a second pass: pause after each question and answer it first.

▶ [YouTube link: rerun publish_kit.py with --youtube-url]

It's a scripted walkthrough with synthetic voices, built with Claude Code from design-room, my open-source system design interview simulator.

When a node cannot reach the update service, should it fail open, fail closed, or neither? Who should sign that decision?

#SystemDesign #SoftwareEngineering #DistributedSystems
```

**First comment** (277/1250):

```text
Written reference design, stage by stage: https://github.com/nirmata78/design-room/blob/main/solutions/SD-94-denylist-system/SD-94_Denylist_System_Reference_Design.md

Run this round yourself, with an AI interviewer that won't help you: https://github.com/nirmata78/design-room
```

**Media: attach the reference design.** In the post composer, More (+) → Add a document → `../../SD-94_Denylist_System_Reference_Design.pdf` (44 pages, 1.7 MB; limit 300 pages, 100 MB).
Document title, shown on the viewer: **A distributed denylist system: a Staff-level reference design**. A post carries one attachment, so the video stays a link in the text, and the document is what shows in the feed.
