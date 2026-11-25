# LinkedIn kit: Loan Servicing System Design (BNPL): Ledger, Collections Scheduler, Returns | Staff Reference

Post from a computer, after the YouTube video is public. The link is still pending: rerun with --youtube-url.

**Post** (1206/3000; hook 120 characters, before the "see more" fold): `pbcopy < linkedin-post.txt`

```text
Your bank debit settled on the 2nd. On the 3rd it came back. "Settled means paid" is where loan servicing designs break.

I've published a 106-minute reference solution for the loan servicing question (instalment loans, BNPL-style) at the Staff bar: theory, a three-version design, eight challenges, and the build cost, on 703 numbered slides.

The idea that unlocks it: throughput is never the problem here. 600,000 collections on the 1st is 42 a second. The limits are the processor's contract and the bank's cut-off, and the hard part is correctness over months.

What it goes into:
→ A timeout is UNKNOWN: query by the same key, never resend with a new one
→ A return is a state and a reversal, and retry rules are policy
→ A refund is a transaction plus a new schedule version
→ Reconcile line by line, three ways; never by totals

Best on a second pass: pause after each question and answer it first.

▶ [YouTube link: rerun publish_kit.py with --youtube-url]

It's a scripted walkthrough with synthetic voices, built with Claude Code from design-room, my open-source system design interview simulator.

What's the strangest month-end break you've chased?

#SystemDesign #Fintech #SoftwareEngineering
```

**First comment** (275/1250):

```text
Written reference design, stage by stage: https://github.com/nirmata78/design-room/blob/main/solutions/SD-95-loan-servicing/SD-95_Loan_Servicing_Reference_Design.md

Run this round yourself, with an AI interviewer that won't help you: https://github.com/nirmata78/design-room
```

**Media.** The full video is too long to upload natively (about 15 minutes at most, from a computer), so it goes by link, and its preview shows the thumbnail.
