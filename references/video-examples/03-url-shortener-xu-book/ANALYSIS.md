# Reference 03 — "Design a URL shortener", chapter 8 of *System Design Interview: An Insider's Guide* (Alex Xu, vol. 1)

| | |
|---|---|
| Source | Book chapter, about 2,000 words and 8 figures. The author's private study extract is at `private/books/xu-system-design-interview-1/chapters/08-chapter-8-design-a-url-shortener.md` (gitignored, never published) |
| What it is | The **written canon**: the four-step answer many candidates and interviewers learned first. It is several years older than references 01 and 02 |
| Role for us | The **baseline of expectations**. A reference solution must cover what this chapter covers, then go further. It is also the direct comparison for reference 02, which treats the same question |

This file is our own summary and assessment. It quotes nothing from the book and reproduces no figure.

## 1 · Agenda (the chapter's four steps)

| Step | What happens | Share |
|---|---|---|
| 1 Understand the problem, set scope | A short candidate and interviewer dialogue fixes the inputs: write volume per day, "as short as possible", the allowed characters, no update or delete. Then a back-of-envelope chain: writes per second, reads per second from an assumed read-to-write ratio, records over ten years, storage | ~20% |
| 2 High-level design, get buy-in | Two REST endpoints (create, redirect); the redirect flow; permanent against temporary redirect and what each means for server load and for analytics; a hash table as the first mental model | ~25% |
| 3 Deep dive | Data model (move from the in-memory table to a relational row); alias length from the capacity number; two ways to make the alias (truncated hash with collision handling, base-62 conversion of a unique ID) with a comparison table and a worked conversion; the create flow step by step with real values; the redirect flow with a cache in front of the store | ~45% |
| 4 Wrap-up | A list of topics for spare time: rate limiting, scaling the web tier, scaling the store, analytics, availability and consistency | ~10% |

## 2 · Script architecture (what to copy)

1. **Scope is set by dialogue.** The candidate asks; the interviewer answers with one number or one constraint.
   Each answer is used later. This is the interviewer voice our format keeps.
2. **Estimates come right after scope, as a chain.** Each line feeds the next, and the last number
   (total records) decides the alias length two sections later. A number that changes a decision.
3. **"Get buy-in" is an explicit step.** The simple design is shown and agreed before any depth.
   It matches the "simple version first" rule of references 01 and 02.
4. **A small decision with a clear trade.** Permanent against temporary redirect: one saves load, the other
   keeps click data. A two-option trade stated in two sentences.
5. **Two options in one comparison table**, row by row: fixed or variable length, need for an ID generator,
   collisions possible or not, whether the next alias can be guessed.
6. **A worked example with real values.** One number converted to base 62 by hand; one row traced through the
   create flow with an actual ID and the resulting alias. Mechanism shown, not only named.
7. **Cross-references to building blocks.** The ID generator and the rate limiter point to their own chapters.
   A design is assembled from parts the reader already holds.
8. **A wrap-up list** of what else could be discussed, each in one or two sentences.

## 3 · Diagramming approach

- Plain box-and-arrow figures: client, load balancer, web servers, cache, database. No colour semantics.
- One **flowchart** for the create path (input, lookup, decision, generate, convert, save).
- One **request and response exchange** between client and server for the redirect.
- **Tables carry the reasoning**: alias length against capacity, hash outputs, the two-approach comparison,
  the stored row.
- No versioned build, no numbered arrows, no failure pictures.

## 4 · What it does not do (and where it has aged)

- **No failure handling.** Nothing on a duplicate custom alias, a hot key, a cache that loses its contents,
  an ID generator that is down, or a store that is slow.
- **No operations, service-level objectives or cost**, and no multi-region discussion.
- **Analytics is one wrap-up bullet.** Reference 02 makes it a full deep dive with an asynchronous pipeline.
- **Technology is asserted** (a relational store, a cache, a bloom filter) with no alternatives table.
- **Uniqueness is handled by check-then-insert** in the described flow; the race between two writers and the
  role of a unique constraint as the final authority are not discussed. Reference 02 covers this.
- **Check the arithmetic.** The storage line multiplies the ten-year record count by the record size and by
  ten years again; by the chapter's own inputs the total is nearer 36.5 TB than the figure printed. A useful
  reminder for our own "show the arithmetic" rule: a viewer will redo the sum.
- **Scale differs between sources**: this chapter assumes 100 million new links a day, reference 02 assumes
  100 million a month. Both arrive at seven characters, for different reasons. State the inputs before the
  conclusion.

## 5 · The canon this chapter sets for the question

An interviewer who learned from it expects to hear, at least:

- the read-to-write ratio and the capacity over the service's life;
- alias length derived from capacity over a 62-character alphabet;
- truncated hash against counter plus base 62, with the trade between them;
- permanent against temporary redirect, tied to whether clicks are counted;
- a cache in front of the store on the redirect path;
- where unique IDs come from in a distributed deployment.

Our reference solution covers each or dismisses it aloud (GUIDELINES §9), then adds what the chapter lacks:
the uniqueness invariant, failure and overload behaviour, observability, and cost.

## 6 · Reusable devices for our kit

- The **clarifying dialogue** opening, with every answer used later.
- The **estimate chain** whose last number sizes a design element.
- The **worked example with real values** on the mechanism slide.
- The **two-option comparison table**, extended by us to an options matrix with a "fails when" column.
- The **wrap-up list**, turned by us into the challenge map: each bullet becomes a challenge instead of a mention.
