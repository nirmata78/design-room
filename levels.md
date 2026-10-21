# Levels & tracks — what the bar is, and how the round changes

A system-design round is not one test with one bar. **A Staff Engineer and an Engineering Manager can
draw the same diagram and get opposite verdicts**, because the panel is asking a different question
about each: *can this person own the hardest technical decisions?* versus *can this person own a
system, its operations and the team that runs it?* Senior managers and directors face a third
question: *can this person set direction for several systems and the organisation around them?*

`design-room` therefore calibrates on **two axes**: the **track** (individual contributor or manager)
and the **level** within it. Pick both at session start, or set them once in `profile.md`.

---

## 1 · The six levels

| Code | Level | Track | Typical titles | The question the panel is asking |
|---|---|---|---|---|
| `senior` | L5 / E5 | IC | Senior Engineer | Can they design a well-specified system cleanly and go deep when probed? |
| `staff` | L6 / E6 | IC | Staff Engineer | Can they frame a vague, large problem and make the hard technical calls — and say why? |
| `principal` | L7+ / E7+ | IC | Senior Staff · Principal | Can they set technical direction across many teams and years, and be right about the bets? |
| `em` | L6 / M1 | Manager | Engineering Manager | Can they own a system end to end — design, operations, cost — and deliver it through a team? |
| `senior-em` | L7 / M2 | Manager | Senior EM · Manager of Managers | Can they run several systems and teams, sequence multi-quarter work, and manage risk across them? |
| `director` | L8 / D1 | Manager | Director · Head of Engineering | Can they set an org's technical and investment strategy, and make the portfolio trade-offs? |

**Default: `em`.** Override per session (`Mock me as staff`) or in `profile.md`.

> **Does the IC/manager split make sense for a design round?** Yes — and getting it wrong is a common
> way to fail. Staff candidates who answer like managers ("I'd have the team load-test it") without
> going two levels deep read as **under-levelled technically**. EM candidates who disappear into
> B-tree internals for twenty minutes and never mention on-call or cost read as **senior ICs who want
> the title**. Directors who design boxes instead of investment decisions read as **EMs**. The
> interviewer will tell you which way you drifted.

---

## 2 · Dimension weights

All nine dimensions are always scored 1–4 **against the target level's bar**. Weights change how
much each counts toward the **weighted score** in the report. **H** = 1.5 · **N** = 1.0 · **L** = 0.5.

| # | Dimension | senior | staff | principal | em | senior-em | director |
|:-:|---|:-:|:-:|:-:|:-:|:-:|:-:|
| 1 | Requirements & scoping | N | N | H | N | H | H |
| 2 | Estimation | N | N | N | N | N | L |
| 3 | High-level design | H | N | L | N | L | L |
| 4 | Technical depth | H | **H** | N | N | L | L |
| 5 | Trade-off reasoning | N | **H** | **H** | N | N | N |
| 6 | Operations, reliability & cost | L | N | N | **H** | **H** | **H** |
| 7 | Communication & collaboration | N | N | N | H | N | N |
| 8 | Handling ambiguity & pushback | N | H | H | N | H | H |
| 9 | Leadership signal | L | N | H | **H** | **H** | **H** |

**Weighted score** = Σ(weight × score) ÷ Σ(weight), over **scored** dimensions only. An unscored
dimension never counts as a 2.

### 2.1 · Dimension 9 means different things on the two tracks

| Track | "Leadership signal" listens for |
|---|---|
| **IC** | **Technical leadership.** Sets direction others can follow; designs for the team that will build it; names the decision that needs an RFC and who must agree; anticipates the migration path; mentors through the design ("I'd want the on-call engineer to be able to answer X from the dashboard"). At `principal`: multi-year bets, platform leverage, and which problems the org should *not* solve. |
| **Manager** | **Organisational and delivery leadership.** MVP-first; sequences the riskiest work first; splits the system along team seams; names staffing, on-call load and the operational cost of the design; zooms out to business impact. At `director`: investment and portfolio trade-offs, org design, build-vs-buy, risk appetite. |

---

## 3 · What changes in the room, by level

The interviewer changes **manner and emphasis**, never the rubric.

| | senior | staff | principal | em | senior-em | director |
|---|---|---|---|---|---|---|
| **Prompt** | as written, clarifications answered fully | under-specified | deliberately vague; "the business wants…" | as written | wider: two systems or a migration | a business problem, not a system |
| **Who drives deep dives** | interviewer picks | **candidate is expected to pick** the risky component | candidate picks and justifies why it's the bet | interviewer picks, includes ops | candidate picks, includes sequencing | interviewer steers to org/portfolio within ~15 min |
| **Depth expected** | two levels on one component | two to three levels on two components; mechanisms, not brands | one level everywhere, three where the bet is | two levels on one component | one level, then trade-offs | box-level is enough; decisions are what count |
| **Typical curveball** | a component fails | requirements change mid-design | a constraint invalidates the strategy | an incident or a cost spike | a team or a dependency disappears | budget cut 30%, or a regulator |
| **Wrap emphasis** | bottlenecks | trade-offs you'd revisit | what you'd stop the org doing | SLOs, on-call, cost | sequencing and risk register | investment, org shape, metrics |

### 3.1 · Archetype fit

| Level | Where loops usually draw from | Most revealing in this bank |
|---|---|---|
| `senior` | A–G, I, J (build rounds) | SD-02, SD-20, SD-25, SD-38, SD-47 |
| `staff` | A–G, I, J at depth, **K** | SD-15, SD-19, SD-28, SD-66, SD-71, SD-84, SD-87 |
| `principal` | C, D at strategy depth, **K** | SD-27, SD-33, SD-83, SD-85, SD-86, SD-88 |
| `em` | all build archetypes + **H** | SD-08, SD-44, SD-55, SD-57, SD-58, SD-59 |
| `senior-em` | H, **K** strategy, F/D at scale | SD-56, SD-59, SD-60, SD-90, SD-92 |
| `director` | **H**, K strategy rounds | SD-60, SD-62, SD-89, SD-90, SD-91, SD-92 |

Every question's level fit is in the **Levels** column of [`Question-Bank.md`](Question-Bank.md).

---

## 4 · From weighted score to outcome

| Weighted score | Outcome at the target level |
|---|---|
| ≥ 3.25 | **Strong hire** |
| 2.75 – 3.24 | **Hire** |
| 2.25 – 2.74 | **Lean no / mixed** — usually one dimension sank it; the report names it |
| < 2.25 | **No hire** |

Two overrides, both applied by the interviewer and stated in the report:

- **A 1 on a High-weight dimension caps the outcome at "lean no"**, whatever the average. A staff
  candidate with no depth, or an EM with no operational story, does not get hired on charm.
- **Apparent level.** The report also says where the round *actually* landed — e.g. *"staff-level
  depth, senior-level framing"*. If that differs from the target, it is the most useful line on the page.

---

## 5 · Choosing your level honestly

Practise **one level above** where you are confident. The round is calibrated to the target, so a 3
at `staff` is worth more than a 4 at `senior`, and the gap is shown to you in dimension terms rather
than as a vague "not quite". When you consistently score ≥3 at the target, move up for a week and see
which dimension breaks first.
