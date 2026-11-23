# LinkedIn kit: URL Shortener System Design: Staff-Level Reference Solution (Codes, Hot Keys, 301 vs 302)

Post from a computer, after the YouTube video is public. The link is still pending: rerun with --youtube-url.

**Post** (1335/3000; hook 85 characters, before the "see more" fold): `pbcopy < linkedin-post.txt`

```text
Everyone has drawn the URL shortener. The grade is on what happens after the diagram.

I've published a 106-minute reference solution for the URL shortener question, at the Staff bar: theory, a three-version design, every component one level down with the technology picked and the rivals rejected, eight challenges, and the build cost, on 643 numbered slides.

The idea that unlocks it: the redirect is the product. It is one memory read, and counting, takedowns and the edge all live beside it, each with a number on how late it may be.

What it goes into:
→ Why base-62 of a counter is still a counter, and a keyed shuffle that keeps codes unique
→ One link at 40,000 clicks a second: a hot key, not a load problem
→ 301 or 302 as a product decision
→ A phishing link dead everywhere in five minutes, as a sum of cache lifetimes
→ etcd, not Redis INCRBY, for ID ranges: asynchronous replication can hand out the same range twice

Best on a second pass: pause after each question and answer it first.

▶ [YouTube link: rerun publish_kit.py with --youtube-url]

It's a scripted walkthrough with synthetic voices, built with Claude Code from design-room, my open-source system design interview simulator.

301 or 302 for a short link: which would you ship, and who should decide?

#SystemDesign #SoftwareEngineering #DistributedSystems
```

**First comment** (273/1250):

```text
Written reference design, stage by stage: https://github.com/nirmata78/design-room/blob/main/solutions/SD-96-url-shortener/SD-96_URL_Shortener_Reference_Design.md

Run this round yourself, with an AI interviewer that won't help you: https://github.com/nirmata78/design-room
```

**Media: attach the reference design.** In the post composer, More (+) → Add a document → `../../SD-96_URL_Shortener_Reference_Design.pdf` (36 pages, 1.9 MB; limit 300 pages, 100 MB).
Document title, shown on the viewer: **A URL shortener: a Staff-level reference design**. A post carries one attachment, so the video stays a link in the text, and the document is what shows in the feed.
