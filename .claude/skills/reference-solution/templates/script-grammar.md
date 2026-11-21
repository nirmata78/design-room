# Script grammar — reference-solution video

Speakers: `C` candidate (drives), `I` interviewer, `V` key line (slower), `N` coach (grading notes only).
Cues as in the kit: `[slide: v-NN]`, `[pause: S]`. Angle brackets are slots to fill.

```
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=af_bella@0.86 E=af_sarah@0.94 -->  <!-- house set approved 2026-11-12: V = key line, E = aside (traps, then-and-now); see slide-video-kit STANDARD §2 -->
<!-- labels: N=COACH -->

## 0 Cold open
[slide: title]        C: <Problem> looks simple. It is not testing <the obvious thing>. It tests <3–5 real things>.
[slide: graded]       N: Here is what the interviewer grades. <one sentence on where the signal is>
[slide: ribbon]       C: I'll go in this order: scope, numbers, the theory, a simple design, then I break it.

## 1 Requirements
[slide: q-clarify]    C: Before I draw anything: <clarifying question>?
                      I: <short, decisive answer>.
                      (repeat for each question that changes the design; 4–6)
[slide: fr]           C: So, functionally: one, <FR1>. Two, <FR2>. …
[slide: nfr]          C: And the numbers: <NFR with value>, because <reason>.
[slide: scope]        C: In scope: … Out of scope: …, and I'm saying so on purpose.
[slide: core]         V: The core is <N> things: <…>.            [pause: 0.8]

## 2 Estimates
[slide: est-N]        C: <quantity> times <quantity> is <result>. That is <label: illustrative / a target>.
                      C: What it tells me: <decision>.

## 3 Theory
[slide: th-is]        C: What this is: <definition>. What it is not: <neighbour>, because <difference>.
[slide: th-props]     V: Safety: <must never happen>. Liveness: <must eventually happen>.   [pause: 0.8]
[slide: th-tension]   C: The tension is <A against B>. <walk the picture>
[slide: th-mech-N]    C: <Mechanism>. It protects <property>. It works like this: <steps>.
                      C: It rules out <failure>. It costs <cost>.
[slide: th-matrix]    C: <N> ways to do this. <Row 1> fails when <…>. <Row 2> fails when <…>.
                      V: I pick <row>. I give up <cost>.          [pause: 0.8]
[slide: th-failures]  C: What will go wrong, in order: <list>. I'll come back to each.

## 4 API and entities
[slide: api-N]        C: <endpoint>. It serves <FR>. It writes <entity>. On the wire: <walk request and response>.

## 5 High-level design
[slide: v1]           C: Version one, the simplest thing that works: <walk boxes and arrows>.
                      C: The objection: <what breaks or is missing>.
[slide: v2]           C: Version two answers that: <what is new, and only that>.
[slide: v3]           C: … This is the baseline. It stays on screen from here on.
[slide: flow-FRn]     C: <FR> end to end. Step one: … Step two: … (use the numbers on the arrows)
[slide: c4, seq]      C: <element-by-element walk, as STANDARD §1b asks>

## 6 Bridge
[slide: bridge]       V: It works. The question now is where it breaks first.   [pause: 1.0]
[slide: map]          C: <N> places. <name each on the baseline>

## 7 Challenge k  (repeat 6–8 times)
[slide: ck-q]         I: <the challenge, as a question>?            [pause: 2.0]
[slide: ck-naive]     C: The first answer is <naive>. It holds when <condition>.
[slide: ck-trace]     C: Take a case. At <t0>, <event>. At <t1>, <event>. Now <the bad line>.
[slide: ck-break]     C: Here is where that lands: <box>.
[slide: ck-fix]       C: The fix is <mechanism>: <how, on the picture>.
[slide: ck-seq/code]  C: <walk the numbered messages or the commented steps>
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

- At least 40–70 spoken words on every diagram slide; walk each box and each numbered arrow.
- The interviewer never praises and never names a mechanism first.
- The coach speaks only on the slides marked `N` above.
- A hedge once per chapter: "these numbers are illustrative" or "this is an initial target".
- Count the words per chapter against the outline before building.
