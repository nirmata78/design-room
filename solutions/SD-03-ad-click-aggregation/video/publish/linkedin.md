# LinkedIn kit: Ad Click Aggregation System Design: Staff-Level Reference Solution (Dedup, Event Time, Billing)

Post from a computer, after the YouTube video is public. The link is still pending: rerun with --youtube-url.

**Post** (1222/3000; hook 103 characters, before the "see more" fold): `pbcopy < linkedin-post.txt`

```text
"Use exactly-once" is the answer that fails the ad-click question. The grade is on what you do instead.

I've published a 55-minute reference solution for counting ad impressions and clicks at the Staff bar, run like a real round: one C4 diagram that evolves through six interviewer challenges, on 0 numbered slides.

The idea that unlocks it: one log, one aggregation code run twice. Fast and provisional for the dashboard, exact and pinned for the bill, and every number replaced by key rather than incremented, so a retry, a replay or a fraud correction can never double anything.

What it goes into:
→ The same click three times, and why the broker's exactly-once doesn't help
→ Yesterday's events at 6 a.m., and a clock that says 2031
→ One ad at 2 million impressions a second
→ Fraud after the invoice, without editing it

Best on a second pass: pause after each question and answer it first.

▶ [YouTube link: rerun publish_kit.py with --youtube-url]

It's a scripted walkthrough with synthetic voices, built with Claude Code from design-room, my open-source system design interview simulator.

Where does your pipeline decide which hour an event belongs to?

#SystemDesign #SoftwareEngineering #DistributedSystems
```

**First comment** (287/1250):

```text
Written reference design, stage by stage: https://github.com/nirmata78/design-room/blob/main/solutions/SD-03-ad-click-aggregation/SD-03_Ad_Click_Aggregation_Reference_Design.md

Run this round yourself, with an AI interviewer that won't help you: https://github.com/nirmata78/design-room
```

**Media.** The full video is too long to upload natively (about 15 minutes at most, from a computer), so it goes by link, and its preview shows the thumbnail.
