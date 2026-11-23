# LinkedIn kit: Webhook Delivery System Design: Outbox, Per-Endpoint Isolation, Retries, Signing | Staff Reference

Post from a computer, after the YouTube video is public. The link is still pending: rerun with --youtube-url.

**Post** (1230/3000; hook 118 characters, before the "see more" fold): `pbcopy < linkedin-post.txt`

```text
One merchant's server takes ten seconds to answer. If your webhook workers are shared, every other merchant waits too.

I've published a 89-minute reference solution for the webhook delivery question at the Staff bar, set at a point-of-sale lender: theory, a three-version design, seven challenges, buy against build, and the team seams, on 549 numbered slides.

The idea that unlocks it: volume is not the problem. 2,400 deliveries a second is 600 calls in flight. One endpoint at ten seconds needs 1,200. So every endpoint gets its own budget.

What it goes into:
→ An outbox, so no event exists without its commit
→ A queue per endpoint as rows: the row is the queue, the timer and the lock
→ Full jitter, a breaker and a ramp, so recovery doesn't knock the endpoint over again
→ The internal event is not the public contract: dated versions and an owning team

Best on a second pass: pause after each question and answer it first.

▶ [YouTube link: rerun publish_kit.py with --youtube-url]

It's a scripted walkthrough with synthetic voices, built with Claude Code from design-room, my open-source system design interview simulator.

Who owns the webhook payload in your organisation?

#SystemDesign #SoftwareEngineering #APIs
```

**First comment** (259/1250):

```text
Written reference design, stage by stage: https://github.com/nirmata78/design-room/blob/main/solutions/SD-99-webhook-delivery/SD-99_Webhook_Delivery_Reference_Design.md

Run this round yourself, with an AI interviewer: https://github.com/nirmata78/design-room
```

**Media.** The full video is too long to upload natively (about 15 minutes at most, from a computer), so it goes by link, and its preview shows the thumbnail.
