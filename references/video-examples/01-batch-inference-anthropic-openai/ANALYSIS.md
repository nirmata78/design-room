# Reference 01 — "Design Batch Inference System (New Version)" (ShowOffer)

| | |
|---|---|
| Source | https://www.youtube.com/watch?v=pHV6xYw7vVA · channel ShowOffer · 1:06:34 · 1080p AV1, 30 fps · published 2026-10-31 |
| Local files (gitignored) | `original.mp4`, `transcript.timestamped.txt` (local faster-whisper `base.en`, 765 segments; YouTube captions were rate-limited — expect homophone errors such as "batcher"→"badger", "queue"→"cube"), `meta.info.json`, `frames/` (1 per 20 s, 200 frames), `sheet_*.jpg` |
| What it is | A **single-narrator whiteboard walkthrough on one evolving canvas**, deep and incident-driven: a baseline built in three versions, then **seven "challenges"** that each break the current design and patch it. A polished icon diagram of the final design closes the video. |
| Role for us | The **deep / staff-bar** reference: failure, fairness, idempotency, observability. Contrast with ref 02 (shallow, framework-driven). |

## 1 · Agenda (YouTube chapters)

| Time | Chapter | What happens | Share |
|---|---|---|---|
| 0:00–5:34 | Introduction — why & what | Why this question, what is being tested; the problem in one picture: clients → GPU fleet, **10 000 requests/s, P95 < 2 s, ~100 per batch, "GPU = black box"** | 8% |
| 5:34–10:23 | Requirements | Clarify scope as questions (sync or async? batch in client or server? how many models? do customers share the GPU fleet?); FRs (submit prompt, select model, run inference and respond); NFRs (P95 ≤ 2 s, fairness, bounded cost) | 7% |
| 10:23–12:19 | APIs and entities | One endpoint `POST /v1/inference`; three entities as boxes: **Request** (req_id, tenant_id, model, deadline, reply_route), **Batch** (batch_id, request_ids, state, lease), **Result** (request_id, output/error) | 3% |
| 12:19–22:09 | High-level design | Built in **versions**: V1 simplest synchronous pipeline (clients → gateway → GPU); V2 server-side batching (size **or** timeout); compatibility lanes (batch key = model + version + params → two lanes); V3 queue + ownership + GPU pool (claim → lease → ACK); the synchronous return path (request tracker with TTL, result router) | 15% |
| 22:09–29:28 | Challenge 1 — dynamic batching strategy | Size-or-time flush; worked cases (R1 at t=0, R2 at 20 ms, R3 at 45 ms → flush at 100 ms); burst case (5 k RPS per model → ~20 ms to fill a batch); the "time-left" budget on the batcher | 11% |
| 29:28–36:30 | Challenge 2 — latency budget with overload | 2 s budget split into stages (150 ms ingress + 100 ms batch + 350 ms queue + 1 s GPU + 100 ms return + 300 ms spare); burst ×2 (100 → 200 batches/s); admission control at the gateway; 429 + retry back-off with jitter vs 503; diagnose with queue age, batch wait, GPU busy; autoscale "new GPU worker?" | 11% |
| 36:30–42:27 | Challenge 3 — failure recovery | Worker crash mid-execution; lease expiry; batch becomes claimable again with attempt+1; **"what if worker A didn't actually die?" → fencing token**; retry whole batch vs unresolved IDs | 9% |
| 42:27–48:46 | Challenge 4 — retry and idempotency | Check-then-act race on claims → atomic claim (CAS / unique claim); batcher crash after ACK before enqueue → **transactional outbox**; client retry with idempotency key → shared idempotency record; gateway 1 crashes, gateway 2 handles the retry | 10% |
| 48:46–54:04 | Challenge 5 — fairness across tenants | Tenant A at 12 k RPS vs tenant B at 2 k against a 10 k RPS system limit; Defense 1 admission control / per-tenant quota at the gateway; Defense 2 fair scheduling in the batcher; Defense 3 isolation policy; "if B is idle do we keep A's original quota?" | 8% |
| 54:04–58:55 | Challenge 6 — timeout and cancellation | Three cases: client disconnects before the GPU, **after the GPU has started a batch containing R1, R2, R3** (can you kill R1 alone?), result arrives at the same moment as the timeout | 7% |
| 58:55–1:05:30 | Challenge 7 — observability | Staged latency distribution + end-to-end; per-stage metrics (oldest request age, batch size, flush reason, pending depth, oldest queued age, expired work, unmatched IDs, late results, return-path latency); **diagnosis rules** (queue age ↑ + GPU util high → overload; batch wait ↑ + GPU util low → batching/compatibility; GPU exec time ↑ → worker/model regression) | 10% |
| 1:05:30–1:06:34 | Ending | Final polished diagram and CTA | 2% |

Roughly **15 min of baseline and 45 min of seven stress tests** — the ratio is the point: the HLD is a launch pad, the challenges are the interview.

## 2 · Script architecture (what to copy)

1. **Slides are numbered and named like a lab notebook**: `00 intro`, `01 the problem`, `02 clarify scope`, … `09 V3`, `10 return path`, then `DD1`…`DD7`. A tiny grey slide label sits top-left, the title top-centre, and a **one-line blue "chip strip"** under the title (`10K RPS · P95 < 2 s · 100 / batch · GPU = black box`) previews what the slide will contain.
2. **Progressive disclosure on one canvas.** The slide opens with just title + chips; items appear as the speaker talks. From V3 onward the *same drawing* is carried through every deep dive; each challenge adds **one annotation or component**, never a redraw.
3. **Versioned baseline** (V1 → V2 → V3) shows *why* each box exists: every version answers the previous version's objection.
4. **Capacity as one-line arithmetic**: `10 000 requests/s ÷ 100 requests/batch = 100 batches/s` and `~1 GPU per batch, ~100 ideal, ~70 at 60 % utilisation` — a number that sizes the fleet, not a table that sits there.
5. **Challenge grammar (×7):** `Q: … ?` (red) → concrete **case** with timestamps/IDs (red) → naive behaviour breaks on the diagram (dashed red outline) → **fix** (green, one named mechanism) → *"what if the fix itself fails?"* (red, second level) → second fix.
   e.g. crash → lease → *what if A didn't die?* → fencing token; claim race → atomic claim → *what if batcher crashes after ACK?* → outbox → *what if the client retries?* → idempotency record → *what if gateway 1 dies?*
6. **Time-annotated worked examples** (`t=0 R1 | t=20 R2 | t=45 R3 → flush at t=100 ms → Batch(3) → Queue A`) are written as text *on* the diagram; mechanism before name.
7. **Diagnose by symptom pairs** in the observability section: two metrics → one conclusion. This is the operations altitude that EM/staff loops look for.
8. **Interviewer-style questions are the slide titles**, answered in place; the viewer is expected to pause.

### 2a · Verbal patterns measured in the transcript

| Pattern | Example (paraphrased from the narration) | Where |
|---|---|---|
| **Interviewer-voice bridge** | "here is a natural follow-up question from the interviewer: *when do you send a batch to the GPU pool?*" / "here can be the next interviewer challenge" | start of every DD |
| **Naive answer first, then break it** | "simplest answer: wait until you have 100 requests… R1 waits forever for the other 97" | DD1, DD2, DD5 |
| **Concrete case with numbers** | `R1 t=0, R2 t=20 ms, R3 t=45 ms`; "traffic doubles: 200 batches/s vs 100 drain → 1 000 batches behind after 10 s" | DD1, DD2 |
| **Precision statement** | "queues and retries give at-least-once attempts, not exactly-once execution; we want **one authoritative client-visible result per logical request**" | DD3 |
| **Distinguish near-synonyms** | "atomic claims reduce duplicate *ownership*; idempotency keys reduce duplicate *logical operations*; conditional commits prevent duplicate *publication*" | DD4 |
| **Staff-level principle line** | "don't react to an end-to-end metric with one generic fix: decompose the path, find the constrained resource, pick a mechanism that changes that resource" | DD2 |
| **Stated hedges** | "illustrative, not a claim about real model performance"; "policy choices, not universal numbers"; "not measured production numbers, initial targets" | throughout |
| **"If asked, I'd say…" closer** | each DD ends with a 2–4 sentence model answer to say in the interview ("I'd propagate an absolute deadline; before GPU execution remove expired work; during a shared batch, cancellation is best effort…") | every DD |
| **Product-contract escape hatch** | "if they want every request accepted during overload, that's a different contract: an async durable job API with a status endpoint" | DD2 |
| **Trade-off stated as two numbers** | "bigger batch → better hardware efficiency, but longer wait; optimise one without the other and you break the SLO" | DD1 |
| **Self-check of the arithmetic** | "summing per-stage P95s does not give the end-to-end P95; stages are correlated, measure the end-to-end distribution" | DD2 |

## 3 · Diagramming approach

**Medium.** Excalidraw hand-drawn style on a white canvas, thin black strokes, single typeface; **colour is used only as annotation**, not as fill:

| Ink | Meaning |
|---|---|
| Black | the baseline system (carried unchanged between slides) |
| Blue | the current *step* being added (V1/V2/V3 boxes, case headers, API boxes) |
| Red | a question, a failure case, a "what if" |
| Green | the fix / defense / metric list (and the new Req Tracker → Result Router return path) |
| Dashed red outline | the component under attack right now (e.g. the batcher in DD1, a crashed worker in DD3) |
| Dashed green outline | the replacement (e.g. worker B taking over) |

**Layout rules visible in the frames**
- A fixed **left→right spine**: `clients → API-GW → Batcher A/B → Queue A/B → GPU worker pool A/B`, with a **return lane underneath**: `Req Tracker (TTL) ↔ Result Router`. The spine never moves, so the viewer builds a map.
- **Lanes by model** (A and B stacked) show the compatibility key; the pool is drawn as a dashed container holding worker circles (A live, A crashed dashed-red, B green on takeover).
- Components are **rounded rectangles with ≤ 3 words**; GPU workers are circles; clients are a circle; the API gateway is a tall rounded bar.
- **Bidirectional arrows** between clients, gateway, batcher, queue and worker (request and ack on one line) keep the picture small; detail goes into the red/green text blocks beneath, not into more arrows.
- **Text blocks under the diagram carry the mechanism** (case lines, `Queue A: B42 [Pending] → Worker A [Claimed], lease until T`, `attempt = 7 → 8`), formatted as a tiny state trace.
- Metrics and fixes are written as **short bullet lists beside the component they belong to** (green, to the right of the GPU pool in DD7).
- **Vertical green dividers** cut the spine into stages for the staged-latency view.
- **No sequence diagrams and no C4**. Sequence is implied by numbered cases and the state trace.
- **Final slide switches style**: a clean, icon-based, colour-coded architecture diagram (clients, API gateway, admission control / rate limit, model queues A/B, batchers, ready-batch queue, dispatcher, GPU worker pool with chip icons, result router, connection map, metrics & observability on a dashed line) — a *marketing-quality recap* after 60 minutes of whiteboard. Colour families: blue = edge, green = guard/compute, pink/purple = queue and batch, amber = ready queue, indigo = control plane.
- One frame early in the video is a **screenshot of the ShowOffer practice page** (problem statement and code editor) — the tie to the product, not part of the design argument.

## 4 · Delivery and audio

- One narrator; very long single takes (about 5–10 min per challenge); slow reveal of the canvas.
- **~130 wpm** (8,644 words over 66.5 min) — calmer than ref 02 (~150 wpm). Live drawing: the narrator says "let me draw it here", "let me copy this", "sorry, I'm wasting some time" — the canvas is built in real time, not pre-rendered.
- Two mid-roll product ads (9:37–10:20 company question bank; 28:43–29:24 design-doc-review service) and a CTA outro (~1 min) — not to copy.
- No on-screen captions in the sampled frames; chapters are in the description.
- Opens with a **scope-narrowing statement** (this is a re-make: LLM-specific topics such as KV cache and decoding are out; "the GPU is a black box worker") — the single most useful framing sentence in the video, because it turns an ML question into a backend-systems question.

## 5 · What it does not do (gaps relative to our staff bar)

- Estimation is **one chain, not a table**: 10 000 req/s ÷ 100 per batch = 100 batches/s; 1 s per batch per GPU → 100 GPUs "mathematical ideal, a lower bound, not a safe fleet"; at ~60 % target utilisation ≈ 170 GPUs ("illustrative, not a claim about real model performance"). Good habit (states the assumption "batches are full"), but no storage, bandwidth, tracker-sizing or cost-per-hour numbers, and no SLO table.
- No interviewer voice, no coach, no scoring or follow-up drills; no estimation exercise for the **request tracker** sizing or the **result path fan-in**.
- Technology names are mostly avoided — it even says *"instead of jumping to Redis or Kafka, the next feature I'll introduce is a batcher"* — and speaks in mechanisms (lease, fencing token, outbox, idempotency record, CAS) — closer to our **"mechanism over brand"** rule than ref 02.
- Uses the same canvas for 60 minutes: efficient for the author, but very few "reset" moments; no recap slides between challenges.

## 6 · Reusable assets for our kit

- **Challenge slide template**: `Q:` title, chip strip, baseline diagram with the target component outlined in red, green fix list, red second-level "what if".
- **Latency-budget bar**: one line, stage ms values that sum to the SLO plus a labelled spare.
- **State-trace text blocks** for failure cases (`state → event → new state`).
- **Diagnosis table**: symptom pair → conclusion.
- **Final "clean architecture" recap slide** after the whiteboard builds.
- **Versioned baseline (V1/V2/V3)** with one objection per step.
