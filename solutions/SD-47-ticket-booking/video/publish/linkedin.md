# LinkedIn kit: Ticket Booking System Design (Seat Reservation Under Contention): Staff-Level Reference Solution

Post from a computer, after the YouTube video is public. The link is still pending: rerun with --youtube-url.

**Post** (1321/3000; hook 102 characters, before the "see more" fold): `pbcopy < linkedin-post.txt`

```text
A seat looks like a row with a boolean. The hard part is the million people and the payment around it.

I've published a 104-minute reference solution for ticket booking under contention (fifty thousand seats, a million fans), at the Staff bar: theory, a three-version design, eight challenges, and the build cost, on 652 numbered slides.

The idea that unlocks it: this is a rejection system. Only 2 % of fans can succeed, so the design converts a stampede into a stream: a waiting room that admits people at a rate the shop can serve, a seat with three states, and a claim that is one statement and not two.

What it goes into:
→ Two fans on one seat, mechanically
→ A hold that expires while the payment is still thinking, and why a timeout is not a decline
→ A fair line, and what bots do to first-come
→ How you would know it is broken when the dashboard is green

Best on a second pass: pause after each question and answer it first.

▶ [YouTube link: rerun publish_kit.py with --youtube-url]

It's a scripted walkthrough with synthetic voices, built with Claude Code from design-room, my open-source system design interview simulator.

When a hold expires and the payment then succeeds, do you refund, or extend the hold? What does your product owner prefer?

#SystemDesign #SoftwareEngineering #DistributedSystems
```

**First comment** (279/1250):

```text
Written reference design, chapter by chapter: https://github.com/nirmata78/design-room/blob/main/solutions/SD-47-ticket-booking/SD-47_Ticket_Booking_Reference_Design.md

Run this round yourself, with an AI interviewer that won't help you: https://github.com/nirmata78/design-room
```

**Media: attach the reference design.** In the post composer, More (+) → Add a document → `../../SD-47_Ticket_Booking_Reference_Design.pdf` (67 pages, 2.2 MB; limit 300 pages, 100 MB).
Document title, shown on the viewer: **Ticket booking under contention: a Staff-level reference design**. A post carries one attachment, so the video stays a link in the text, and the document is what shows in the feed.
