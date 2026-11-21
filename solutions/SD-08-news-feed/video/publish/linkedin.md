# LinkedIn kit: News Feed System Design: Staff-Level Reference Solution (Fan-out, Celebrities, Ranking)

Post from a computer, after the YouTube video is public. The link is still pending: rerun with --youtube-url.

**Post** (1262/3000; hook 111 characters, before the "see more" fold): `pbcopy < linkedin-post.txt`

```text
Every news feed answer says "hybrid push and pull". The grade is on the line between them, and nobody draws it.

I've published a 74-minute reference solution for the news feed question at the Staff bar: theory, a three-version design, eight challenges, and the build cost, on 164 numbered slides.

The idea that unlocks it: one celebrity post is a hundred million writes, about fifteen minutes of a whole fan-out fleet. So the line is set from both sides of the arithmetic, crossing it needs no backfill, and correctness (deletes, blocks) lives on the read path, never in the copies.

What it goes into:
→ Where the threshold sits, and the account that crosses it overnight
→ Why a delete is one write, not a fan-out
→ A lost cache shard, and the rebuild that can become the outage
→ How you'd know the feed got worse with every dashboard green

Best on a second pass: pause after each question and answer it first.

▶ [YouTube link: rerun publish_kit.py with --youtube-url]

It's a scripted walkthrough with synthetic voices, built with Claude Code from design-room, my open-source system design interview simulator.

Where would you put the push/pull line for your product, and how would you measure it?

#SystemDesign #SoftwareEngineering #DistributedSystems
```

**First comment** (265/1250):

```text
Written reference design, stage by stage: https://github.com/nirmata78/design-room/blob/main/solutions/SD-08-news-feed/SD-08_News_Feed_Reference_Design.md

Run this round yourself, with an AI interviewer that won't help you: https://github.com/nirmata78/design-room
```

**Media: attach the reference design.** In the post composer, More (+) → Add a document → `../../SD-08_News_Feed_Reference_Design.pdf` (30 pages, 2.2 MB; limit 300 pages, 100 MB).
Document title, shown on the viewer: **The news feed: a Staff-level reference design**. A post carries one attachment, so the video stays a link in the text, and the document is what shows in the feed.
