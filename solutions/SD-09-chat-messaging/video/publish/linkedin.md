# LinkedIn kit: Chat System Design: Staff-Level Mock Interview (1B users, groups, offline, receipts)

Post from a computer, after the YouTube video is public. The link is still pending: rerun with --youtube-url.

**Post** (1613/3000; hook 112 characters, before the "see more" fold): `pbcopy < linkedin-post.txt`

```text
A chat system that never loses a message and never shows one twice. How would you design it for a billion users?

I've published a 44-minute mock system design round at the Staff bar: interviewer, candidate and coach, on 85 numbered slides.

The idea that unlocks it: start from the mailbox, not the socket. Store the message durably, with a server-assigned sequence number, before anything is acknowledged. Every device then catches up by cursor. Online, offline and multi-device become one code path. The WebSocket only delivers early.

What the round goes into:
→ Who decides the order when two people send at once, and what happens when that leader dies mid-write
→ The lost ACK: every crash point, and why dedup has to come before numbering
→ The million-receipt trap in a group of 1,000, found with arithmetic
→ Half a million sockets reconnecting at once
→ Wire formats, C4 and sequence diagrams, the data model and code for each path
→ 5 follow-ups, from end-to-end encryption to a channel with a million subscribers

Attached: the full written design, 53 pages. Every decision with its alternatives, the arithmetic, the failure cases, and the internals of each tool.

▶ The video: [YouTube link: rerun publish_kit.py with --youtube-url]

Best on a second pass: pause after each question and answer it first.

It's a scripted mock with synthetic voices, built with Claude Code from design-room, my open-source system design interview simulator. More rounds are coming, one problem at a time.

Where would you push harder if you were the interviewer?

#SystemDesign #SoftwareEngineering #DistributedSystems
```

**First comment** (222/1250):

```text
Reference solution, stage by stage: https://nirmata78.github.io/design-room/solutions/SD-09-chat-messaging.html

Run this round yourself, with an AI interviewer that won't help you: https://github.com/nirmata78/design-room
```

**Media: attach the reference design.** In the post composer, More (+) → Add a document → `/Users/neo.bsuir/Projects/design-room/solutions/SD-09-chat-messaging/SD-09_Chat_Messaging_Reference_Design.pdf` (53 pages, 2.0 MB; limit 300 pages, 100 MB).
Document title, shown on the viewer: **Chat for a billion users: a Staff-level system design, explained**. A post carries one attachment, so the video stays a link in the text, and the document is what shows in the feed.
