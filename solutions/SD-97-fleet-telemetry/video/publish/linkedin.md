# LinkedIn kit: Fleet Telemetry & Live Map System Design: Staff Reference (Geo Index, Hot/Cold Paths)

Post from a computer, after the YouTube video is public. The link is still pending: rerun with --youtube-url.

**Post** (1201/3000; hook 124 characters, before the "see more" fold): `pbcopy < linkedin-post.txt`

```text
A live fleet map is not one database of positions. It's two products off one stream, and most of it you've already designed.

I've published a 60-minute reference solution for fleet telemetry and a live location map at the Staff bar: theory, a three-version design and six challenges, on 502 numbered slides.

The idea that unlocks it: one log keyed by vehicle, read twice. A live view that overwrites by cell for the map, and a history that appends by vehicle for replay. The vehicle numbers its own messages and decides what goes first when it reconnects.

What it goes into:
→ A vehicle leaving a tunnel with three minutes of buffer
→ Why not key the log by geo cell
→ 100,000 vehicles reconnecting at once
→ A map that's stale while every dashboard is green

It composes three earlier reference solutions: event counting, ride matching and a device fleet.

▶ [YouTube link: rerun publish_kit.py with --youtube-url]

It's a scripted walkthrough with synthetic voices, built with Claude Code from design-room, my open-source system design interview simulator.

Which part of your system orders data by arrival when it should order by sequence?

#SystemDesign #SoftwareEngineering #DistributedSystems
```

**First comment** (277/1250):

```text
Written reference design, stage by stage: https://github.com/nirmata78/design-room/blob/main/solutions/SD-97-fleet-telemetry/SD-97_Fleet_Telemetry_Reference_Design.md

Run this round yourself, with an AI interviewer that won't help you: https://github.com/nirmata78/design-room
```

**Media: attach the reference design.** In the post composer, More (+) → Add a document → `../../SD-97_Fleet_Telemetry_Reference_Design.pdf` (15 pages, 1.0 MB; limit 300 pages, 100 MB).
Document title, shown on the viewer: **Device telemetry and a live location map: a Staff-level reference design**. A post carries one attachment, so the video stays a link in the text, and the document is what shows in the feed.
