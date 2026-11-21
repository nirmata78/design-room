# Reference 02 — "OpenAI System Design: Design a URL Shortener Service" (ShowOffer)

| | |
|---|---|
| Source | https://www.youtube.com/watch?v=-ldyMeu6iL4 · channel ShowOffer · 38:42 · 1080p AV1, 30 fps |
| Local files (gitignored) | `original.mp4`, `transcript.timestamped.txt` (YouTube auto-captions, 1006 lines), `subs.en.vtt`, `meta.info.json`, `frames/` (1 per 20 s), `sheet_01.jpg` |
| What it is | A **single-narrator whiteboard walkthrough**: one voice, a live Excalidraw-style canvas with pre-drawn frames, the camera on the diagram only. The "article-as-video" format. |
| Role for us | The **mid-bar, fast, framework-driven** reference. Contrast with ref 01 (deep, incident-driven). |

## 1 · Agenda (YouTube chapters, verified against the transcript)

| Time | Chapter | What happens | Share |
|---|---|---|---|
| 0:00–5:49 | Introduction | Hook ("too simple" is the trap), what the question really tests, the delivery framework in one breath, then user scenarios (4) and in/out of scope. A 50 s sponsor read sits at 4:59–5:52 | 15% |
| 5:49–11:45 | Requirements | FR1–FR4 spoken one by one; NFRs **with numbers**: 100 M new/month, 10 B redirects/month, Base62 capacity table, P95 50–100 ms, CAP **split per workflow** | 15% |
| 11:45–16:28 | Core entities & APIs | 4 entities, 3 endpoints, each API tagged with the FR it serves | 12% |
| 16:28–22:00 | High-level design | "Drive it like a story": one workflow per FR, each a 7-step numbered arrow diagram; deliberately simple (DB lookup, no cache) | 14% |
| 22:00–27:51 | Deep dive 1 — alias generation and custom-alias correctness | capacity → length; random vs hash vs counter+Base62; ID ranges; unique constraint as final authority | 15% |
| 27:51–31:40 | Deep dive 2 — redirect latency and read scalability | viral link → cache-aside → TTL vs invalidation → edge/CDN with the analytics caveat | 10% |
| 31:40–34:43 | Deep dive 3 — async analytics | "bad version" first, then queue; raw events + aggregates; eventual consistency | 8% |
| 34:43–38:42 | Recap & final design | 5-point recap, 2 interview tips, outro/CTA (~1 min) | 10% |

The pace is ~1 deep dive per 3–6 minutes. Only the **requirements and the three deep dives carry numbers**; the HLD is intentionally thin.

## 2 · The script architecture (what to copy)

1. **Hook with a counter-intuitive claim** — *"this feels almost too simple… this question is not testing whether you can store a string"* — then list the five real challenges as questions (alias, latency, DB bottleneck, CAP, analytics).
2. **Announce the framework before using it** — scenarios → FR/NFR → entities → APIs → HLD → challenge-driven deep dives. A visible 5-step **progress ribbon** (Requirements › APIs & Entities › High-Level Design › Deep Dives › Recap) appears on each section title card with the current step highlighted.
3. **One governing rule, repeated**: *"do not go too deep too early"* → present a simple working solution, **say out loud which part is intentionally simple**, and name the deep dive that will fix it ("for now a DB lookup… I'll come back to caching").
4. **Scope control as an on-screen artifact**: a green "IN SCOPE" box beside a red "OUT OF SCOPE" box, then a yellow takeaway: *"the core is three things…"*.
5. **Every FR maps to an API; every API says which FR it serves and what it reads/writes** ("maps to FR1 and FR3").
6. **HLD = story per functional requirement**, not one mega-diagram. Five questions per FR: *what API is triggered? which entity is read/written? which services? where does data go? what state changes?* (this list is itself a slide).
7. **Deep dive grammar — the same loop four times**:
   `weakness in the current design → pause and ask the viewer → naive options (with why each is annoying) → the improvement → "but every solution creates the next question" → next weakness → recommendation line`.
   Examples: *alias space → length → random/hash/counter → single sequence bottleneck → ID ranges*; *every click hits DB → Redis cache-aside → TTL vs freshness → viral/global → CDN, **but** edge skips analytics*.
8. **"Pause and ask you"** moments are explicit (*"a great moment to pause… how many aliases can 6 characters represent?"*) — an active-recall beat for the viewer.
9. **Numbers become decisions**: Base62 table → "5 chars is too small, 6 works for 47 years, **7 is the safer default**" (reserved ranges, deletions, custom aliases, ops flexibility).
10. **Senior-signal one-liners as a closing device**: *"protect the critical path first; redirect is the critical path, analytics is the side effect"*, *"different flows need different guarantees"*, *"don't label the whole system AP or CP — split by workflow"*.
11. **Recap** is a stack of colour-coded bars, one sentence per path (creation → correctness; alias length → capacity math; redirect → DB then cache; custom alias → DB unique constraint is the authority; analytics → async), plus a yellow "interview tips" box.

## 3 · Diagramming approach

**Medium.** A frame-based Excalidraw canvas (hand-drawn font, wobbly strokes). Each slide is one *frame* (16:9, thin grey border, small "Frame N" label top-left); the camera zooms frame to frame. A **separate pre-rendered title card** (large sans heading, blue circle motif, the 5-step ribbon) opens each section. A branded intro card (topic icons around the title) opens the video.

**Colour semantics (consistent across every diagram):**

| Colour | Meaning |
|---|---|
| Blue fill | client / edge / gateway |
| Purple fill | application service |
| Teal/mint fill | data store |
| Yellow/orange | decision, cache, takeaway box |
| Green | success path / "good" option / return value |
| Red/pink | failure, "bad" option, out-of-scope, conflict |
| Black solid arrow | request path |
| Teal/green **dashed** arrow | response / return |
| Purple dashed | async / side call |

**Rules visible in the frames:**
- **Numbered arrows** (`1. POST /api/v1/urls`, `2. forward`, … `7. return short_url`) so the narration can say "step 5" and the viewer can follow. The diagram is a sequence drawn on a component layout.
- **Request goes left→right, response returns as a dashed arrow back to the client** — one picture carries both structure and the happy-path sequence.
- **Data stores list their tables/constraints inside the box** (`users · url_mappings · alias_reservations`, `UNIQUE(short_alias)`, "final correctness gate").
- **Decision diamond** for the unique-constraint outcome with two labelled exits (`yes → 5a. Return short URL`, `duplicate → 5b. Alias unavailable (409)`).
- **Builds**: the same frame is re-shown 3–4 times while elements are added (arrows first, then the DB, then the response path). No animation; the author draws live and the video shows the canvas as it fills. Later deep dives **reuse the baseline diagram** and add exactly one new component (Redis between service and DB; queue + consumers + analytics store).
- **Title + "Q:" line** at the top of each deep-dive frame (*"Q1: Is our alias space large enough?"*) — the question is the slide title.
- **Problem / solution pair** for trade-offs: red "BAD: sync analytics" box next to green "GOOD: async pipeline", with the pipeline strip beneath it (Redirect Svc → Event Queue → Consumers → Analytics Store, each a coloured pill).
- **Capacity tables** are coloured rows: red = too small, green + ★ = chosen, with an arithmetic strip underneath (`100M/month × 12 = 1.2B/yr ⇒ 5 yrs ≈ 6B ⇒ 10 yrs ≈ 12B`).
- **Densities**: ≤ 6 boxes per diagram; 8–14 words per box; one yellow takeaway box per frame.
- **No C4 levels, no sequence-diagram lifelines, no capacity-of-hardware diagrams.** It stays at "component + numbered flow".

## 4 · Delivery and audio

- One human narrator, **~150 wpm** (5,872 caption words over 38.7 min, sponsor read included), conversational ("so", "right?", self-corrections kept in).
- Transitions are verbalised: *"now let's convert the user scenarios into FRs"*, *"so the next question is not whether it works — it is where it breaks first"*.
- No burned-in captions in the sampled frames (YouTube captions only). Background music: not checked by ear.
- A sponsor/CTA block mid-video (~55 s) and a CTA outro (~1 min) — **not** to copy.

## 5 · What it does not do (gaps relative to our staff bar)

- No estimation of QPS, storage or bandwidth (only alias capacity). No read:write peak QPS arithmetic, no cache sizing, no storage-per-year.
- No failure modes beyond "what if queue is slow"; no SLOs, no operations, no cost.
- No curveball or follow-up questions; no interviewer voice. The "interview" is implied, not simulated.
- Technology choices are asserted (Redis, queue) without alternatives tables or evidence.
- Estimated bar: solid **senior (L5)** at best; the closing summary calls it "mid-level and senior-level".

## 6 · Reusable assets for our kit

- The **5-step progress ribbon** on section cards.
- **IN/OUT scope** side-by-side box with a one-line "core is N things" takeaway.
- **FR → API → Entity traceability tags** on every API slide.
- **Numbered-arrow workflow diagrams** per FR, with dashed returns.
- **Q-as-title deep-dive slides** with red "weakness" / green "fix" / yellow "recommendation" boxes.
- The **"every solution creates the next question"** bridge sentence.
- The **recap as colour-coded bars** and the "different flows, different guarantees" thesis.
