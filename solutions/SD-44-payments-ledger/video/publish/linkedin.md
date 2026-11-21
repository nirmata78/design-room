# LinkedIn kit: Payment System & Double-Entry Ledger Design: Staff-Level Reference Solution

Post from a computer, after the YouTube video is public. The link is still pending: rerun with --youtube-url.

**Post** (1166/3000; hook 97 characters, before the "see more" fold): `pbcopy < linkedin-post.txt`

```text
Your payment call times out. Did the customer pay? "Mark it failed" is how double charges happen.

I've published a 74-minute reference solution for the payment system and double-entry ledger question, at the Staff bar: theory, a three-version design, eight challenges, and the build cost, on 160 numbered slides.

The idea that unlocks it: exactly-once does not exist across a network boundary. So you design for one effect per intent, a state for "we don't know yet", and a reconciliation that finds what everything else missed.

What it goes into:
→ A timeout is a state: UNKNOWN, then an inquiry by your own reference
→ Idempotency keys are inserted, not checked
→ A balance is a sum of immutable entries, never a column
→ Reconciliation is a component, not a safety net

Best on a second pass: pause after each question and answer it first.

▶ [YouTube link: rerun publish_kit.py with --youtube-url]

It's a scripted walkthrough with synthetic voices, built with Claude Code from design-room, my open-source system design interview simulator.

When your books and the processor's disagree by two, where do you start?

#SystemDesign #SoftwareEngineering #Fintech
```

**First comment** (277/1250):

```text
Written reference design, stage by stage: https://github.com/nirmata78/design-room/blob/main/solutions/SD-44-payments-ledger/SD-44_Payments_Ledger_Reference_Design.md

Run this round yourself, with an AI interviewer that won't help you: https://github.com/nirmata78/design-room
```

**Media: attach the reference design.** In the post composer, More (+) → Add a document → `../../SD-44_Payments_Ledger_Reference_Design.pdf` (31 pages, 2.1 MB; limit 300 pages, 100 MB).
Document title, shown on the viewer: **Payment processing and the double-entry ledger: a Staff-level reference design**. A post carries one attachment, so the video stays a link in the text, and the document is what shows in the feed.
