# Script grammar — reference-solution video (six-chapter, C4-first format)

Speakers: `C` candidate (drives), `I` interviewer, `V` key line (slower), `N` coach (grading notes, challenge intros, bridges).
Write written forms (`API`, `202`, `ClickHouse`); the pronunciation map respells them for the voice and the Markdown keeps them.

**Reveal markers.** `[+]` reveals the next unit of the slide (a table row, a trace event, a card, a strip, the next box, arrow, pill
or badge of the figure), `[+N]` the next N, `[+*]` the rest. One to three sentences after each marker, about exactly what it
revealed. Lines before the first marker are spoken over the empty frame. `gen.py` refuses a slide whose markers do not cover its
units; `REVEAL_REPORT=1 python3 gen.py` lists them all.

```
## 1 Prompt, questions and context                    chapter(1, …)
qs  prompt            I: <the prompt, verbatim>.
dia hook              C: <one hour / one request / one record, three numbers>. The whole design is about <…>.
plain graded          N: Five axes, one at a time.  [+] N: Requirements. Weak: … Strong: …  (×5)  [+] C: <the rule I keep all round>.
key thesis            V: <thesis>.
plain scale           C: The scale first.  [+] C: <volume>.  [+] C: <total>.  [+] C: <peak and cause>.  [+] C: Every number starts from these.
qs clar ×4–6          C: <question>?  [+] I: <short, decisive answer>.  C: <what it moves in the design>.
plain FRs · NFRs      one requirement per [+]
plain properties      V: ps("S1"): <…>.  (one per [+]; liveness by C)
plain scope           [+] C: In scope …  [+] C: Out, on purpose …  [+] C: <the one out-of-scope item worth saying aloud>.
stage c4-context      C: Before any boxes inside it, the system in its context.  [+] one actor or system per step, naming HTTPS vs event.
key core              V: The core is <N> things: <…>.   N: <what was graded in this chapter>.

## 2 Estimates                                         chapter(2, …)
plain table ×2–3      C: <topic>.  [+] C: <arithmetic from the scale line>. That rules out <X> and forces <Y>.  (one row per [+])
dia budget            C: <the budget, stage by stage, and what the spare is for>.

## 3 API and data model                                chapter(3, …)
plain code            C: <endpoint>, serving FR<n>. <the fields that matter: idempotency key, status codes>.
plain table           one endpoint per [+], tagged by FR
dia erd               one table per [+]; end on the rule the keys enforce
dia state             one state or transition per [+]  (when the core entity has a lifecycle)

## 4 The design, driven by challenges                  chapter(4, …)
stage v1              C: Version one, in the order a request travels.  [+] one box per step.  End: why it is correct.
stage flow-v1         C: The happy path, numbered, once.  [+] One: …  (one arrow per step)
tech ×1–2             ST.say("<id>")   (cards for V1's containers)

challenge(n, T, "<title>", "<the interviewer's question>", ["N: <one-sentence intro>"])
trace                 C: The trace.  [+] one event per step, concrete IDs and numbers.  Last line: why the naive answer fails.
dia/stage break       [+] C: <view>. <component> is marked.  [+] C: The naive answer: …  [+] C: But …   (pill, then the two strips)
mech_slide            C: The mechanism.  [+] C: It protects ps(…).  [+] how  [+] rules out  [+] costs
stage/dia sequence    one message per [+]   (when the mechanism is a protocol)
stage vN | dia fix    C: <delta>.  [+] new box or FIX pill per step.  [+] C: one level down …  [+] covers / does not  [+] C: Rejected: <tool>. <why>.
plain pseudo          C: As pseudocode, key lines marked.  C: Line n: …  C: Why it works: …
tech                  ST.say("<id>")   (the first time this container matters)
push                  I: <what if the fix fails / 10× / replay / the checker is wrong>?
cards | dia           the second fix or the honest limit, one card per [+]
say_slide             V: If asked, I'd say: <2–4 sentences>.   N: That fix creates the next question: <…>.

## 5 When you don't need all this                     chapter(5, …)
dia alt               [+] C: <what goes away>.  [+] C: <the one cluster / box that does it all>.  [+] how  [+] what it gives up
key crossover         C: <the arithmetic from chapter 2>.   V: Below <N>, I'd ship this, and say when I'd switch.

## 6 Recap                                             chapter(6, …)
stage recap           C: The final design.  [+] one mechanism badge per step.
plain stack           ST.summary_say()  + N: naming a product is not the signal …
plain mistakes        N: one mistake and its instead per [+]
followups             C: one follow-up and where to start per [+]
key close             V: <the thesis again>.   C: Thanks for watching. The written design, generated from this same script, is linked below.
```
