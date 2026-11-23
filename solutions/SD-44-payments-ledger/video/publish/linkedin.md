# LinkedIn kit: Payment System & Double-Entry Ledger Design: Staff-Level Reference (Idempotency, Outbox, Gateway)

Post from a computer, after the YouTube video is public. The link is still pending: rerun with --youtube-url.

**Post** (1169/3000; hook 103 characters, before the "see more" fold): `pbcopy < linkedin-post.txt`

```text
"Retry with backoff" is the answer that double-charges a customer. The grade is on what you do instead.

I've published a 82-minute reference solution for a payment system and its double-entry ledger at the Staff bar: theory, a three-version design, and six challenges, on 549 numbered slides.

The idea that unlocks it: exactly-once does not exist across the bank boundary, so build one effect per intent, a state for "not knowing yet", and books you can reconcile.

What it goes into:
→ The bank timed out: an UNKNOWN state and an inquiry by your own reference
→ Why partition by merchant, not by account (and a million one-time cards)
→ Gateway or direct processor, with the break-even
→ Debezium, and what to use instead below 1,000 events a second

Best on a second pass: pause after each question and answer it first.

▶ [YouTube link: rerun publish_kit.py with --youtube-url]

It's a scripted walkthrough with synthetic voices, built with Claude Code from design-room, my open-source system design interview simulator.

Do you integrate a gateway or a processor directly, and at what volume did you switch?

#SystemDesign #SoftwareEngineering #DistributedSystems
```

**First comment** (277/1250):

```text
Written reference design, stage by stage: https://github.com/nirmata78/design-room/blob/main/solutions/SD-44-payments-ledger/SD-44_Payments_Ledger_Reference_Design.md

Run this round yourself, with an AI interviewer that won't help you: https://github.com/nirmata78/design-room
```

**Media: attach the reference design.** In the post composer, More (+) → Add a document → `../../SD-44_Payments_Ledger_Reference_Design.pdf` (41 pages, 1.9 MB; limit 300 pages, 100 MB).
Document title, shown on the viewer: **Payment processing and the double-entry ledger: a Staff-level reference design**. A post carries one attachment, so the video stays a link in the text, and the document is what shows in the feed.
