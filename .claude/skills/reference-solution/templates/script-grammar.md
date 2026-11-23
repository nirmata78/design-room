# Script grammar — reference-solution video

Speakers: `C` candidate (drives), `I` interviewer, `V` key line (slower), `N` coach (grading notes only).
Cues as in the kit: `[slide: v-NN]`, `[pause: S]`. Angle brackets are slots to fill.

**Reveal markers (2026-11-21).** In the chapter sources, `[+]` reveals the next unit of the slide (a table row, a trace event, a
card, a strip, the next box or arrow of the figure in request-flow order), `[+N]` the next N, `[+*]` the rest. Write one to three
sentences after each marker, about exactly what it revealed. Lines before the first marker are spoken over the empty frame (title
and header only). `gen.py` writes the `[slide:]`/`[reveal:]` cues and refuses a slide whose markers do not cover its units.

```
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=af_bella@0.86 E=af_sarah@0.94 -->  <!-- house set approved 2026-11-12: V = key line, E = aside (traps, then-and-now); see slide-video-kit STANDARD §2 -->
<!-- labels: N=COACH -->

## 0 Cold open
[slide: title]        C: <Problem> looks simple. It is not testing <the obvious thing>. It tests <3–5 real things>.
[slide: graded]       N: Here is what the interviewer grades. <one sentence on where the signal is>
[slide: ribbon]       C: I'll go in this order: scope, numbers, the theory, a simple design, then I break it.

## 1 Requirements
[slide: scale]        C: The scale first. <volume> a month, <total> over <retention>, and a peak of <peak> when <cause>.
                      C: Every number I use later starts from one of these three.        (GUIDELINES §3.1)
[slide: q-clarify]    C: Before I draw anything: <clarifying question>?
                      I: <short, decisive answer>.
                      (repeat for each question that changes the design; 4–6)
[slide: fr]           C: Four functional requirements.  [+]  C: One, <FR1>.  [+]  C: Two, <FR2>. …
[slide: nfr]          C: And the numbers: <NFR with value>, because <reason>.
[slide: scope]        [+] C: In scope: …  [+] C: Out of scope: …, and I'm saying so on purpose.
[slide: c4-context]   C: Before any boxes inside it, the system in its context.  [+] C: <person>: <what they do>.  [+] … (one actor or system per step; end on "nothing external sits on the hot path")
[slide: core]         V: The core is <N> things: <…>.            [pause: 0.8]

## 2 Estimates
[slide: est-N]        C: <what this table sizes>, from <the scale-line number>.  [+] C: <quantity> times <quantity> is <result>, <label>. What it tells me: <decision>.  [+] …

## 3 Theory
[slide: th-is]        C: What this is: <definition>. What it is not: <neighbour>, because <difference>.
[slide: th-props]     V: Safety: <must never happen>. Liveness: <must eventually happen>.   [pause: 0.8]
[slide: th-tension]   C: The tension is <A against B>. <walk the picture>
[slide: th-mech-N]    C: <Mechanism>. It protects <property>. It works like this: <steps>.
                      C: It rules out <failure>. It costs <cost>.
[slide: th-matrix]    C: <N> ways to do this. <Row 1> fails when <…>. <Row 2> fails when <…>.
                      V: I pick <row>. I give up <cost>.          [pause: 0.8]
[slide: th-map]       C: Where each mechanism will live.  [+] C: <mechanism n>: <container>, <one clause>.  [+] … (a table, not a drawing: the system is drawn once, in chapter 5; the labels return as badges on it)
[slide: th-seq]       C: Mechanism <n> at work.  [+] C: <message 1, at protocol level: the conditional write, the log append, the quorum>.  [+] …
                      C: <what it needs and does not need: no clock, no lock, no timeout>.
[slide: th-failures]  C: What will go wrong.  [+] C: <F1>.  [+] C: <F2> … I'll come back to each.

## 4 API and entities
[slide: api-N]        C: <endpoint>. It serves <FR>. It writes <entity>. On the wire: <walk request and response>.

## 5 High-level design
[slide: v1]           C: Version one, the simplest thing that works: <walk boxes and arrows>.          (the canonical C4 container view, upto=1: its only full drawing)
                      C: The objection: <what breaks or is missing>.
[slide: v2]           C: Version two answers that: <what is new, and only that>.                     (new=2: carried boxes at once, then the new ones)
[slide: v3]           C: … This is the baseline. From here on it only changes by deltas.
[slide: c4-containers] C: <what a container means here>. In the order a request travels.          (the same picture, walked: not a second drawing)
                      [+] C: <container>: <what it is>, <what it owns>, <its number from the estimates>, <what it is not>.  (≥ 40 words each)
                      C: <read the layout: what sits on the hot path, what sits beside it>.
[slide: flow-FRn]     [+] C: <FR> end to end.  [+] C: One: <arrow 1>.  [+] C: Two: <arrow 2> …
[slide: seq-FRn]      C: As a sequence.  [+] C: <message 1>.  [+] C: <message 2> …   (one per functional requirement)

## 5.1 Components and technologies
[slide: card]         C: Now one level down: every container with what it runs on, and what I rejected.
[slide: c4-tech]      [+] … one step per container, naming the product on its type line.
[slide: c4-comp-X]    C: Inside <service>, in the order a request meets them.  [+] C: <component>: <library or mechanism>, <timeout or bound>. …
[slide: tech-X]       [+] C: <container>: <product, size, topology>. <the exact write or read, the configuration that matters>.
                      [+] C: Why: <the property that decides>.
                      [+] C: Rejected: <named alternative>: <the property or failure that rules it out>.  (≥ 2; say "an honest equal" when it is)
[slide: stack]        C: The stack on one slide.  [+] C: <container>: <choice>, because <deciding reason>.  [+] …
                      N: Naming a product is not the signal. Naming the property that rules out its rival is.
[slide: drill-q]      N: Swap seats: which box would you drill, and what is your one question? Pause and pick one.   [pause: 3.0]
[slide: drill]        N: Here is where interviewers usually go.  [+] I: <box>. <probe>?  [pause: 1.2]  N: <what a strong answer names>.  (4–5 rows, from DRILL())

## 5.2 When you don't need all this (alternate path, 3–4 min)
[slide: alt]          C: Before I break it: below <crossover number>, I would not build all this.      (ALTERNATE, a delta on the canonical view)
                      [+] C: <the simpler box>: <how it works, one level down>.
                      [+] C: What it gives up: <the bottleneck>, <the failover gap or the window>.
                      [+] C: The line: at <number from the scale line> the full design pays for itself.
                      V: Below <N>, I'd ship the simple one, and say when I'd switch.   [pause: 0.8]

## 6 Bridge
[slide: bridge]       V: It works. The question now is where it breaks first.   [pause: 1.0]
[slide: map]          C: <N> places. <name each on the baseline>

## 7 Challenge k  (repeat 6–8 times)
[slide: ck-q]         I: <the challenge, as a question>?            [pause: 2.0]
[slide: ck-naive]     C: The first answer is <naive>. It holds when <condition>.
[slide: ck-trace]     C: The trace.  [+] C: At <t0>, <event>.  [+] C: At <t1>, <event>.  [+] C: <the bad line>.  [+] C: <the hedge>.
[slide: ck-break]     C: Here is where that lands: <component>, inside <container>.        (C4 component view, attack=, the rest dimmed)
[slide: ck-fix]       C: The fix is <mechanism>: <how, on the picture>.                   (same view, fix= or a NEW component; "V4" tag if the design changed)
                      [+] C: One level down: <what is written or appended, the key and the condition>.
                      [+] C: It covers <failure>. It does not cover <failure>; <what does>.
                      [+] C: Rejected: <the tool an interviewer would name>. <the property or failure that rules it out>.   (rejl(*REJ(k)))
[slide: ck-seq/code]  C: <walk the numbered messages, or the key lines of the pseudocode: pseudo(src, hl=(…)); a real language only when its idiom is the point>
[slide: ck-why]       C: Why it works: it protects <property> because <reason>.
[slide: ck-q2]        I: And if <the fix itself fails>?              [pause: 1.5]
[slide: ck-fix2]      C: Then <second mechanism or honest limit>. That costs <cost>.
[slide: ck-say]       V: If asked, I'd say: "<2–4 sentences>."       [pause: 1.0]
                      C: That fix creates the next question.

## 8 Build cost (AUX)
[slide: cost]         N: This part is the manager layer. In an IC round it is optional.
                      C: Version one is <scope>, <people> for <months>. I'd buy <X>, build <Y>. The top risk is <Z>.

## 9 Recap
[slide: final]        C: <one sentence per path, on the clean diagram>
[slide: mistakes]     N: The mistakes that cost most in this round: <3–5>.
[slide: close]        V: <thesis, restated>.                          [pause: 1.0]
```

Rules that the grammar does not show:

- At least 40–70 spoken words on every diagram slide; walk each box and each numbered arrow, in reveal order.
- Versions follow the challenges: say the version when it changes ("this is version four"), and never when it does not.
- A data model is narrated entity by entity, each relationship as it is drawn ("a user authors posts: one to many").
- The narration carries the detail; the slide carries a few words (GUIDELINES §7.6). When a strip runs past two lines, cut the
  strip, not the sentence.
- One to three sentences per reveal step; more than ~12 steps on one slide means two slides.
- Name the concrete technology wherever a box is mentioned after 5.1 (Redis, not "the cache"; etcd, not "the allocator").
- The interviewer never praises and never names a mechanism first.
- The coach speaks only on the slides marked `N` above.
- A hedge once per chapter: "these numbers are illustrative" or "this is an initial target".
- Count the words per chapter against the outline before building.
