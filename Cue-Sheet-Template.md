# Cue-Sheet Template

**For the interviewer.** Use this when the candidate brings a prompt that is not in
`Question-Bank.md` — a real question from a recruiter, a JD-flavoured problem, or something they
invented. Building one takes about two minutes.

**Write it into `interview.md` §10, not into a new file** — it is scratch for the round. If the
question turns out to be worth keeping, offer at debrief to promote it into the right archetype file
as a Tier-2 compact sheet, and add a row to `Question-Bank.md`.

---

## The shape

```markdown
### SD-nn · Title                                              [Tier 2 · archetype X]

**Read aloud:** *"One sentence. Deliberately under-specified. Names the user and the goal,
not the mechanism."*

**Frequency:** which companies ask this, and at what level.

**The crux.** One sentence: the single decision this problem is really about. Everything else is
scaffolding. *(This is the most important line on the sheet — it tells you where to spend deep-dive
probes.)*

**If they ask (give these, briefly and decisively):**
| Question | Answer |
|---|---|
| How many users / how much traffic? | *a number that makes the problem interesting* |
| Read- or write-heavy? | |
| Freshness / latency target? | |
| Retention? | |
| Payload size? | |
| Consistency needs? | |
| One region or global? | |
| Anything explicitly out of scope? | *give them one free cut, keep the rest for them to find* |

**A good design contains (listen for — not an ordering, not a completeness requirement):**
- 5–9 bullets in plain English. The mechanism, not the brand name.
- Mark **the senior insight** — the one observation that separates a strong answer from a
  competent one.

**Probe ladder:**
- *Requirements:* one probe that tests whether they cut scope deliberately.
- *Estimation:* one probe that forces a number into a decision.
- *Design:* the end-to-end walk, plus one contract question.
- *Deep dive (pick 2–3):* the crux · a failure · a scale jump · a hot-key/skew case ·
  a correctness-under-retry case.
- *EM bar:* how would you know in production · what does it cost · what would you cut ·
  how does this split across teams.

**Curveball:** one new requirement or failure to introduce ~65% through deep dives.

**Weak / Strong / Exceptional:**
- *Weak* — the naive design, named concretely.
- *Strong* — the expected competent answer.
- *Exceptional* — quantifies, sequences an MVP, owns the operational and cost story.

**Traps** — plausible-sounding wrong turns. Do not warn them; note it if they take one, and whether
they catch it themselves.

**Deep reference:** a public write-up, paper or guide section that covers this, if any.
```

---

## Building it fast

1. **Find the crux first.** Ask yourself: if the candidate got everything else right but this one
   thing wrong, would the design fail? That is the crux. Write it before anything else — the rest of
   the sheet follows from it.
2. **Pick numbers that make the problem interesting.** The clarification answers exist to force a
   real decision. "A thousand users" makes every question trivial; "a billion" makes some questions
   silly. Choose the scale where the naive design *just* breaks.
3. **Write the weak band before the strong band.** The naive design is easy to name and it is what
   you will actually be listening for the absence of.
4. **Put the mechanism, never the brand, in the checklist.** "A durable partitioned log" — not
   "Kafka". They should score for the mechanism whichever brand they name, and score nothing for a
   brand with no mechanism behind it.
5. **Six probes is plenty.** You will use three or four.

## Reusable probe bank

Independent of the problem. Draw from these when the sheet runs dry:

- *"Why that choice, and what did you trade away?"*
- *"What are the two or three alternatives, and what's the axis between them?"*
- *"That component just died mid-write. Walk me through it."*
- *"Traffic 10×s next quarter. What breaks first?"*
- *"One key is a thousand times hotter than the rest. What happens?"*
- *"A client retries because it didn't see your response. What does the system do?"*
- *"How do you know, in production, that this is wrong — before a customer tells you?"*
- *"What's the SLO, and what's the alert that fires before the SLO is breached?"*
- *"What does this cost a month, and what's the biggest line item?"*
- *"You have half the time and half the team. What ships?"*
- *"How would you split this across three teams, and what's the contract between them?"*
- *"What's the one-way door here — the decision that's expensive to reverse?"*
- *"What would you have the team prototype first to de-risk this?"*
