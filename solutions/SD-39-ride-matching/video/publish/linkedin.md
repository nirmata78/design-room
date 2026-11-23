# LinkedIn kit: Ride Matching / Nearby Drivers System Design: Staff Reference (Geo Index, Claims, Leases)

Post from a computer, after the YouTube video is public. The link is still pending: rerun with --youtube-url.

**Post** (1129/3000; hook 108 characters, before the "see more" fold): `pbcopy < linkedin-post.txt`

```text
Every ride-matching answer draws a geohash. Then two riders get the same driver, and the geohash can't help.

I've published a 61-minute reference solution for nearby drivers and ride matching at the Staff bar: theory, a three-version design and six challenges, on 469 numbered slides.

The idea that unlocks it: two problems, two stores. Where drivers are is 1.25 million writes a second of soft state, kept in memory and allowed to be lost. Who gets which driver is one conditional, fenced write per claim, owned by one matcher per city.

What it goes into:
→ The claim, as one SQL WHERE clause
→ A driver who accepts and vanishes
→ Cell boundaries and a 3,000-driver downtown cell
→ Why "no drivers" can be a successful response

Best on a second pass: pause after each question and answer it first.

▶ [YouTube link: rerun publish_kit.py with --youtube-url]

It's a scripted walkthrough with synthetic voices, built with Claude Code from design-room, my open-source system design interview simulator.

Where does your system keep the one write that must never be wrong?

#SystemDesign #SoftwareEngineering #DistributedSystems
```

**First comment** (273/1250):

```text
Written reference design, stage by stage: https://github.com/nirmata78/design-room/blob/main/solutions/SD-39-ride-matching/SD-39_Ride_Matching_Reference_Design.md

Run this round yourself, with an AI interviewer that won't help you: https://github.com/nirmata78/design-room
```

**Media: attach the reference design.** In the post composer, More (+) → Add a document → `../../SD-39_Ride_Matching_Reference_Design.pdf` (18 pages, 1.0 MB; limit 300 pages, 100 MB).
Document title, shown on the viewer: **Nearby drivers and ride matching: a Staff-level reference design**. A post carries one attachment, so the video stays a link in the text, and the document is what shows in the feed.
