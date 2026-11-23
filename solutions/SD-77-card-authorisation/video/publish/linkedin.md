# LinkedIn kit: Card Authorization System Design: Staff-Level Reference Solution (Holds, Stand-in, Fraud Rules)

Post from a computer, after the YouTube video is public. The link is still pending: rerun with --youtube-url.

**Post** (1187/3000; hook 80 characters, before the "see more" fold): `pbcopy < linkedin-post.txt`

```text
"Check the balance and say yes" is wrong three times over in card authorisation.

I've published a 90-minute reference solution for the card authorisation question, at the Staff bar: theory, a three-version design, eight challenges, and the build cost, on 560 numbered slides.

The idea that unlocks it: an approval is a promise made inside someone else's deadline. It places a hold, not a debit, and the real money moves days later in a file, often for a different amount.

What it goes into:
→ Why two swipes two milliseconds apart need one conditional write per account
→ A reversal that arrives before its authorisation
→ A fraud model at 1.8 seconds: a cut-off and a fail-policy table that risk and finance sign
→ Twenty minutes of stand-in: record what the network decided, even when it overdraws

Best on a second pass: pause after each question and answer it first.

▶ [YouTube link: rerun publish_kit.py with --youtube-url]

It's a scripted walkthrough with synthetic voices, built with Claude Code from design-room, my open-source system design interview simulator.

Who should own the fail-open policy for fraud: engineering, risk or finance?

#SystemDesign #Fintech #Payments
```

**First comment** (283/1250):

```text
Written reference design, stage by stage: https://github.com/nirmata78/design-room/blob/main/solutions/SD-77-card-authorisation/SD-77_Card_Authorisation_Reference_Design.md

Run this round yourself, with an AI interviewer that won't help you: https://github.com/nirmata78/design-room
```

**Media: attach the reference design.** In the post composer, More (+) → Add a document → `../../SD-77_Card_Authorisation_Reference_Design.pdf` (46 pages, 3.3 MB; limit 300 pages, 100 MB).
Document title, shown on the viewer: **Card authorisation: a Staff-level reference design**. A post carries one attachment, so the video stays a link in the text, and the document is what shows in the feed.
