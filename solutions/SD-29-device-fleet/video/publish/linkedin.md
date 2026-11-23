# LinkedIn kit: IoT Device Fleet Control Plane System Design: Staff Reference (OTA, Rollouts, Shadows)

Post from a computer, after the YouTube video is public. The link is still pending: rerun with --youtube-url.

**Post** (1111/3000; hook 110 characters, before the "see more" fold): `pbcopy < linkedin-post.txt`

```text
"Push a rollback" is the answer that fails the device-fleet question. A device in a crash loop never hears it.

I've published a 62-minute reference solution for a device-fleet control plane at the Staff bar: theory, a three-version design and six challenges, on 481 numbered slides.

The idea that unlocks it: design for the device you can't reach. Publish desired state instead of commands, release in waves that contain every kind of hardware and halt themselves, and let every device return to its last known good on its own.

What it goes into:
→ A/B slots, a watchdog, and what "healthy" must include
→ Why 1 % is not a sample
→ 200,000 devices reconnecting in one minute
→ Connected is not converged

Best on a second pass: pause after each question and answer it first.

▶ [YouTube link: rerun publish_kit.py with --youtube-url]

It's a scripted walkthrough with synthetic voices, built with Claude Code from design-room, my open-source system design interview simulator.

What does your fleet do when an update bricks the device that received it?

#SystemDesign #SoftwareEngineering #DistributedSystems
```

**First comment** (271/1250):

```text
Written reference design, stage by stage: https://github.com/nirmata78/design-room/blob/main/solutions/SD-29-device-fleet/SD-29_Device_Fleet_Reference_Design.md

Run this round yourself, with an AI interviewer that won't help you: https://github.com/nirmata78/design-room
```

**Media: attach the reference design.** In the post composer, More (+) → Add a document → `../../SD-29_Device_Fleet_Reference_Design.pdf` (18 pages, 1.0 MB; limit 300 pages, 100 MB).
Document title, shown on the viewer: **A device-fleet control plane: a Staff-level reference design**. A post carries one attachment, so the video stays a link in the text, and the document is what shows in the feed.
