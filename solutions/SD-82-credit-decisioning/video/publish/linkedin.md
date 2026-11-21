# LinkedIn kit: Instant Credit (BNPL) System Design: Staff Reference Solution (Slow Bureaus, One Atomic Booking)

Post from a computer, after the YouTube video is public. The link is still pending: rerun with --youtube-url.

**Post** (1209/3000; hook 104 characters, before the "see more" fold): `pbcopy < linkedin-post.txt`

```text
Eight loan applications a second. Any database takes that. So why does this round fail strong engineers?

I've published a 70-minute reference solution for instant credit at the point of sale, at the Staff bar: theory, a three-version design, eight challenges, and the build cost, on 149 numbered slides.

The idea that unlocks it: the core is small and boring on purpose, one database and one atomic step. The design lives at the slow edges and in what you keep.

What it goes into:
→ Never race two credit bureaus: every pull is paid and may show on the customer's file
→ "Our vendor was slow" is not a decline reason, which is why "refer" exists
→ A credit pull can't be compensated; only funding the merchant can
→ Shadow mode can't tell you whether newly approved people repay

Best on a second pass: pause after each question and answer it first.

▶ [YouTube link: rerun publish_kit.py with --youtube-url]

It's a scripted walkthrough with synthetic voices, built with Claude Code from design-room, my open-source system design interview simulator.

When a vendor is down, who should decide what happens at the counter: engineering, credit risk or compliance?

#SystemDesign #Fintech #DistributedSystems
```

**First comment** (283/1250):

```text
Written reference design, stage by stage: https://github.com/nirmata78/design-room/blob/main/solutions/SD-82-credit-decisioning/SD-82_Credit_Decisioning_Reference_Design.md

Run this round yourself, with an AI interviewer that won't help you: https://github.com/nirmata78/design-room
```

**Media: attach the reference design.** In the post composer, More (+) → Add a document → `../../SD-82_Credit_Decisioning_Reference_Design.pdf` (41 pages, 3.5 MB; limit 300 pages, 100 MB).
Document title, shown on the viewer: **Instant credit at the point of sale: a Staff-level reference design**. A post carries one attachment, so the video stays a link in the text, and the document is what shows in the feed.
