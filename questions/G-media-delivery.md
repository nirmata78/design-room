# Archetype G · Media & delivery

**SD-51 – SD-54.** Slice with `grep -n '^### SD-51' questions/G-media-delivery.md`, then Read with
`offset`. Do not read this file whole.

**What this archetype tests as a family:** **moving large amounts of bytes cheaply.** Egress and
storage dominate the bill by an order of magnitude over compute, so a design that never mentions money
cannot score above 3 no matter how correct it is. The recurring probe: *"what does a terabyte of this
cost you, and where does it go?"*

---

### SD-51 · Video upload, transcode & streaming   [T1 · G★ N★ M]

**Read aloud:** *"Design a video platform — creators upload, and viewers worldwide watch on any
device."*

**Crux.** **Two systems joined by a queue.** The upload/transcode pipeline is a batch fan-out problem
where the unit of work must be a *segment*, not a file; the delivery side is a CDN and cost problem.
Candidates who design one and wave at the other cap out at 3, and the transcode fan-out arithmetic is
where the interesting decisions live.

**If they ask:**

| Question | Answer |
|---|---|
| Uploads? | 500 hours of video uploaded per minute |
| Views? | 1B hours watched per day |
| Upload size? | 100 MB to 100 GB; creators have flaky connections |
| Time to publish? | Ideally minutes for short videos; hours acceptable for long ones |
| Devices? | Phones to TVs, bandwidth from 1 Mbps to 100 Mbps |
| Start latency? | Video must start playing in under 2 seconds |
| Retention? | Forever, but most views are of recent content |
| Live? | Out of scope — that's SD-52 |

**Listen for:**
- **Resumable chunked upload direct to object storage**, never through an application server, with a
  manifest — and the flaky-connection requirement making resumability a hard need.
- **Transcode as a fan-out pipeline off a queue**: one source video → many renditions
  (resolutions × codecs × bitrates), each an independent parallel task.
- **← The senior insight: split the video into segments and transcode segments in parallel**, rather
  than one worker per rendition. A 10-hour video transcoded whole takes hours regardless of fleet size;
  segmented, it takes minutes. This is the single most valuable idea in the sheet — probe toward it
  with *"a 10-hour upload — how long until it's watchable?"* and never name it.
- **The fan-out arithmetic**: 500 hours/minute × ~6 renditions ≈ 3,000 video-hours/minute of transcode,
  which is an enormous fleet — and the cost consequence that drives **rendition laddering on demand**
  (transcode the common ones eagerly, rare ones lazily on first request, and 4K only for videos that
  earn it).
- **Adaptive bitrate streaming** (HLS/DASH): segmented output plus a manifest, the client choosing
  rendition per segment, which is what makes one pipeline serve a phone and a TV.
- **CDN as the delivery tier** with a stated hit-ratio target, origin shielding, and the observation
  that **egress is the dominant cost line** — a hit ratio improvement is worth more than any compute
  optimisation.
- **Popularity skew**: a tiny fraction of videos gets most views, so caching works extremely well;
  cold long-tail content can live on cheaper storage with a slower first-byte.
- **Progressive publication**: make the 360p rendition available first so the video is watchable while
  higher renditions are still processing.
- **Pipeline failure handling** — a transcode failing for one rendition shouldn't block the others; a
  poison video shouldn't stall the queue; and idempotent retry so a re-run doesn't duplicate output.
- **Thumbnails, captions and metadata** as separate pipeline outputs, and DRM if they raise it.

**Probe ladder:**
- *Requirements:* "What's out of scope?" · "Which matters more — time to publish, or transcode cost?"
- *Estimation:* "500 hours a minute, 6 renditions — what's your transcode fleet?" · **"1 billion hours
  watched a day at, say, 3 Mbps — what's your egress in petabytes and roughly in money?"** (the number
  that should reframe the entire design around CDN hit ratio) · "What's a year of uploads in storage?"
- *Design:* the walk of one upload from creator's browser to a viewer's TV · "What exactly does the
  client request when it plays?"
- *Deep dives:* **"A creator uploads a 10-hour 4K video. How long until it's watchable, and what
  determines that?"** (drive toward segmented parallel transcode) · "The 1080p rendition fails and the
  rest succeed. What does the viewer see?" · "A viewer's bandwidth drops mid-video. What happens, and
  what did you build to make that work?" · "Your CDN hit ratio drops from 95% to 85%. What's the impact
  on origin and on cost?" · "A video goes viral in 10 minutes. Walk me through it."
- *EM bar:* "What's your cost per hour watched, and what are the three levers?" (hit ratio, codec
  efficiency, rendition ladder) · "What's the SLI for playback quality, measured where?" (client-side —
  rebuffer ratio and startup time; server metrics don't see the viewer's experience, and that
  distinction is a strong signal) · "Split this across teams." · "What would you buy?"

**Curveball:** *"A new codec halves bandwidth but costs 3× to encode and only 60% of devices support
it."* Tests whether they can compute the trade (egress saving versus encode cost), handle a
per-device-capability rendition ladder, and sequence a gradual migration.

**Weak / Strong / Exceptional.** *Weak* — upload to a server, transcode synchronously to one format,
serve from the origin, no ABR, no cost discussion. *Strong* — resumable direct upload, queue-driven
parallel transcode, ABR with segments and manifests, CDN with a hit-ratio target, progressive
publication, per-rendition failure isolation. *Exceptional* — segments the transcode to make publish
time independent of video length, derives the egress bill and lets it drive the design, laddering
renditions by demand, measures quality client-side, and states cost per hour watched.

**Traps.** Transcoding whole files (publish time scales with duration — probe it). Ignoring egress
cost. Believing server-side metrics measure playback quality. Eagerly transcoding every rendition for
every video, including the 90% nobody watches.


---

### SD-52 · Live streaming at low latency   [T2 · M★ N]

**Read aloud:** *"Design live streaming — a broadcaster goes live and a million viewers watch with a
few seconds' delay."*

**Crux.** **Latency and resilience are directly opposed.** Every buffer, every segment boundary, and
every retry that makes the stream robust also adds delay — and there is no configuration that gives
both. The design is a stated position on that dial, per use case.

**Numbers if asked:** 10k concurrent broadcasts, the largest with 2M concurrent viewers, target
glass-to-glass latency 3–5 seconds (and under 1 second if interactivity is required — ask which),
broadcaster uplinks are unreliable, viewers span all device types and bandwidths, replay must be
available immediately after the stream ends.

**Listen for:** **ingest with redundancy** (a backup ingest endpoint, and what happens when the
broadcaster's connection drops for 5 seconds) · **transcode in real time** to a rendition ladder, with
the hard constraint that real-time transcode cannot fall behind, so it must shed quality rather than
queue · **fan-out hierarchy** (origin → mid-tier → edge) since 2M viewers cannot pull from one origin ·
**the segment-duration trade-off made explicit**: shorter segments cut latency and increase request
overhead and vulnerability to jitter; low-latency HLS/DASH with partial segments, or WebRTC for
sub-second at much higher cost per viewer · **client buffer** as the other half of the latency budget,
and that a smaller buffer means more rebuffering · **viewer join spikes** — a million people arriving
when the event starts, all needing the manifest and the first segments · **immediate replay** by
retaining the live segments as the VOD asset (cheap and elegant — the good answer) · **degradation
policy** when the broadcaster's upstream degrades: drop renditions, not the stream.

**Probes:** *"Your target is 3 seconds. Where does every one of those 3 seconds go?"* (a genuinely
revealing question — encode, segment, upload, fan-out, client buffer) · *"The broadcaster's connection
drops for 5 seconds. What do 2 million viewers see?"* · *"You want sub-second latency. What changes
architecturally, and what does it cost per viewer?"* · *"A million viewers join in the first 30
seconds. What breaks?"* · *(EM bar)* *"What's the cost per viewer-hour, and how does it compare with
VOD?"*

**Weak / Strong / Exceptional.** *Weak* — RTMP ingest to one server, viewers pull from it, 10-second
segments, no fan-out hierarchy, no degradation plan. *Strong* — redundant ingest, real-time rendition
ladder, hierarchical fan-out, an explicit segment-duration position, client buffer reasoned about,
join-spike handling, replay from live segments. *Exceptional* — budgets the latency
component-by-component, states the WebRTC-versus-LL-HLS choice with cost per viewer, degrades quality
rather than dropping the stream, and prices viewer-hours.

---

### SD-53 · CDN / edge cache design   [T2 · G N A]

**Read aloud:** *"Design a CDN — the edge caching layer that serves our content from close to the
user."*

**Crux.** **Hit ratio is the entire economic argument**, and it is won or lost on cache-key design and
tiering. A 90% hit ratio versus 98% is a factor of five in origin traffic, and the candidate should be
computing rather than asserting.

**Numbers if asked:** 100 edge locations, 10 Tbps peak egress, 500B requests/day, content ranges from
1 KB API responses to 100 GB video segments, some content is personalised and uncacheable,
invalidation must take effect within 30 seconds globally, origin can serve only 5% of peak.

**Listen for:** **request routing** to an edge — anycast versus DNS-based, with the trade-off (anycast
is fast to converge and hard to steer; DNS is steerable and slow to change) · **a cache hierarchy**:
edge → regional shield → origin, so a cold edge miss doesn't hit the origin — **the shield tier is the
single most effective hit-ratio mechanism and the thing to probe for** · **cache-key design** as the
main lever: which headers, query parameters and cookies vary the key, and the point that an
over-specific key (session cookie in the key) destroys the hit ratio and is a real production
incident class · **tiering by object size** — small objects in memory, large in SSD, with distinct
eviction policies · **invalidation/purge** propagated to 100 locations in 30 seconds, and the standard
alternative of **versioned URLs so invalidation is never needed**, which they should prefer · **origin
shielding and request coalescing** so 10,000 simultaneous misses for the same object become one origin
request (the thundering-herd protection that also protects the origin during a cold start) ·
**uncacheable/personalised content** routed through but not cached, and edge compute if they raise it ·
**hit ratio, origin offload and bytes-served-per-location** as the operating metrics.

**Probes:** *"Ten thousand users request the same uncached object simultaneously. How many requests
reach the origin?"* · *"Your hit ratio is 90%. Origin can take 5% of peak. What happens?"* · *"A team
adds a cookie to the cache key. What happens to the hit ratio and when do you notice?"* · *"Purge one
object from 100 locations within 30 seconds. How — and why would you rather not have to?"* · *(EM bar)*
*"What's the cost per terabyte delivered, and what's the marginal value of a point of hit ratio?"*

**Weak / Strong / Exceptional.** *Weak* — caches at each edge, TTL-based, purge by iterating locations,
no hierarchy, no coalescing. *Strong* — anycast or DNS routing with the trade-off named, shield tier,
deliberate cache-key design, size-based tiering, request coalescing, versioned URLs preferred to purge.
*Exceptional* — computes origin load at several hit ratios and designs to protect the origin, treats
cache-key discipline as a governed platform contract, and prices a point of hit ratio in money.

---

### SD-54 · Partner data-feed / large-file delivery   [T1 · G A N]

**Read aloud:** *"Design a service that delivers large custom datasets to external business partners —
some on a fixed schedule, some on demand — and guarantees each partner gets correct, fresh,
access-controlled data."*

**Crux.** **Separating *generating* a dataset from *delivering* it.** Once generation produces a
versioned, immutable artifact, everything else — re-delivery, on-demand plus scheduled, verification,
audit — becomes easy. Designs that generate on request are structurally unable to answer half the
probes.

**If they ask:**

| Question | Answer |
|---|---|
| Partners? | Hundreds |
| Dataset sizes? | Megabytes to tens of gigabytes |
| Freshness? | Yesterday's data by 6 a.m. |
| Access pattern? | Partners pull via API, and also want bulk file drops |
| Sensitivity? | Data is sensitive — access control and auditability matter |
| Corrections? | Occasional re-delivery of corrected data must be supported |
| Per-partner variation? | Yes — each partner gets a different slice/schema |
| SLA consequences? | Contractual. Missing 6 a.m. is a customer-facing incident |

**Listen for:**
- **A clean split: generation (a scheduled, orchestrated job producing a versioned immutable output)
  versus delivery (an API plus bulk access).** ← The crux; everything else follows.
- **Versioning and immutability** so a partner can re-fetch exactly what they got last Tuesday, and a
  correction is a new version rather than a mutation.
- **Large files served without passing through an app server** — pre-signed URLs or a managed transfer
  drop, direct from object storage. Streaming 30 GB through the API tier is the classic error.
- **Per-partner access control plus audit logging** — and the ability to *prove* later that Partner X
  never accessed Partner Y's data, which is a different requirement from preventing it.
- **A scheduler/orchestrator** with dependency awareness, retries, and **alerting on failure that is
  loud enough to act on before 6 a.m.** — including the "job succeeded but produced an empty file"
  case, which no simple success/fail check catches.
- **Idempotent generation and delivery**, so a retry neither duplicates nor corrupts.
- **A manifest with checksums and row counts** so the partner can verify completeness — cheap, and it
  converts a category of disputes into a self-service check.
- **On-demand and scheduled sharing one generation path**, so the same dataset isn't built twice.
- **The missed-deadline runbook**: what happens at 5:30 a.m. when the job is still running — partial
  delivery, stale-but-labelled data, or a proactive notification. **← This is the EM half of the
  question and the thing most candidates never raise.**
- Data-quality gates blocking publication, plus the judgment call of late-but-right versus
  on-time-but-wrong.
- Retention of old versions, and the cost of keeping many versions of tens of gigabytes.

**Probe ladder:**
- *Requirements:* "What's out of scope?" · "Is late data or wrong data worse? Who decides?"
- *Estimation:* "Hundreds of partners × tens of GB × how many versions retained — what's your storage
  bill?" · "What's the egress cost of a full daily delivery to every partner?"
- *Design:* the walk of one scheduled delivery, and then the same dataset requested on demand ·
  "What's the exact artifact a partner receives, and what identifies it?"
- *Deep dives:* **"The nightly job fails at 3 a.m. Walk me through the next three hours — who knows,
  what happens, and does a partner get stale data without knowing?"** · **"A partner says yesterday's
  file was wrong. Re-deliver it without breaking anyone else."** (versioning) · "How do you serve a
  30 GB file without melting your servers?" · "On-demand and scheduled both want today's data. How do
  you avoid generating it twice, and what if they arrive simultaneously?" · "How do you stop Partner X
  seeing Partner Y's data, and how do you prove it six months later in an audit?" · "The job succeeds
  but the output has 3 rows instead of 3 million. What catches that?"
- *EM bar:* **"What's your SLA for the 6 a.m. deadline, and what do you do the morning it's about to be
  missed?"** (ask this every time — it is the question that finds the EM) · "What's the cost per
  partner per month?" · "Twenty partners, twenty schemas. How do you keep this from becoming twenty
  bespoke pipelines?" (a platform-thinking probe with a real answer: a declarative per-partner
  configuration over one engine)

**Curveball:** *"A partner is in the EU and their data may not transit the US, and they now want
delivery four times a day rather than nightly."* Tests whether generation and delivery are decoupled
enough to change cadence per partner, and whether residency was a design parameter or an assumption.

**Weak / Strong / Exceptional.** *Weak* — one endpoint that builds and streams the dataset on every
request, no versioning, no failure handling, no audit. *Strong* — generation separated from delivery,
versioned immutable outputs, object storage with pre-signed links, orchestrated scheduling with retries
and alerting, per-partner authz with audit logs, idempotent delivery. *Exceptional* — designs the
missed-deadline runbook, treats checksums and manifests as a dispute-prevention feature, prices version
retention, catches the empty-output case, and generalises twenty partners into one configurable engine.

**Traps.** Streaming large files through the application tier. Mutating a dataset in place to correct
it (breaks re-fetch and audit). Treating job success as data success. No answer for the morning the
deadline is about to be missed.

**Deep reference:** [`guides/interviewer-guide.md`](../guides/interviewer-guide.md) §6
Problem B.
