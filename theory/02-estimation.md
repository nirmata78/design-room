# 2 · Estimation — numbers that change decisions

Back-of-the-envelope estimation is not arithmetic for its own sake. It exists to **rule options in or
out** before you draw them. Orders of magnitude are the point; a 1.5× error never matters and a 1000×
error always does.

---

## The method in four moves

1. **Pick the driving quantity** — usually the peak write or read rate, or the stored volume.
2. **Chain the units aloud**: *users × actions/day ÷ seconds/day × peak factor = requests/s*.
3. **Round aggressively** to one significant figure and powers of ten.
4. **Read the result back into a decision**: *"…which means a single primary can't take the writes,
   so I'll partition by user."*

{: .say }
> "Let me size the three things that matter: the peak write rate, the read rate, and the storage —
> I'll round hard; I'm after the order of magnitude."

## The number kit

### Time

| Quantity | Value | Shortcut |
|---|---|---|
| Seconds per day | 86,400 | **≈ 10⁵** |
| Seconds per month | ~2.6 × 10⁶ | ≈ 2.5 M |
| Seconds per year | ~3.15 × 10⁷ | ≈ π × 10⁷ |
| 1 request/s sustained | ~86 k/day · ~2.6 M/month | |
| 1 M/day | ≈ 12/s average | **≈ 10/s for every million per day** |

**Peak-to-average:** consumer traffic 2–3× daily peak; launches, on-sales and campaigns 10–100×.
Always ask what the peak is — and whether *you* cause it (campaigns can be throttled; Black Friday
can't).

### Latency — orders of magnitude

| Operation | Approx. | Note |
|---|---|---|
| L1 cache / main-memory reference | ~1 ns / ~100 ns | |
| Read 1 MB sequentially from memory | ~10 µs | |
| SSD random read | ~20–100 µs | NVMe at the low end |
| Read 1 MB sequentially from SSD | ~0.2–1 ms | |
| Round trip inside a datacentre | ~0.2–0.5 ms | |
| Read 1 MB over a 10 Gbps link | ~1 ms | |
| HDD seek | ~5–10 ms | |
| Round trip within a continent | ~20–50 ms | |
| Round trip across continents | **~100–250 ms** | US-east ↔ Europe ~80 ms; ↔ Asia ~150–250 ms |

{: .key }
> **The cross-continent round trip is the most decision-changing number in system design.** Any
> design that puts a cross-continent quorum on the write path has a write latency of 100–250 ms, full
> stop. See [Replication & consistency](04-replication-and-consistency.md).

### Throughput — what one box roughly does

| Component | Order of magnitude | Caveat |
|---|---|---|
| Stateless app server | 1–10 k req/s per instance | depends entirely on the work per request |
| Relational primary (OLTP) | ~10 k simple writes/s; ~50–100 k reads/s with cache-friendly indexes | hot rows and fsync dominate |
| Redis-class in-memory store | ~100 k+ ops/s per shard (single-threaded core) | network-bound beyond that |
| Kafka-class log broker | ~100 MB/s+ per broker | partitions are the unit of parallelism |
| WebSocket gateway | ~100 k–1 M idle connections per large host | memory per connection (~10–50 KB) dominates |

### Storage and money

| Quantity | Value |
|---|---|
| 1 KB × 1 B items | 1 TB |
| 1 KB × 1 M/s | 1 GB/s ≈ 86 TB/day |
| Replication factor | ×3 is typical |
| Columnar compression | ~5–10× |
| Availability 99.9% | ~8.8 h/year · ~43 min/month |
| Availability 99.99% | ~53 min/year · ~4.3 min/month |
| Cloud object storage | ~$20 per TB-month (standard tier) |
| Cloud egress | ~$50–90 per TB (often the hidden cost) |

---

## Worked shapes that recur

**Read rate from users.** 500 M DAU × 5 sessions × 1 feed load ÷ 10⁵ s ≈ **25 k/s average**, ~75 k/s
peak → a cache tier, not a database, serves this.

**Fan-out amplification.** One post × 200 followers = 200 timeline writes. 50 M posts/day × 200 ÷ 10⁵
≈ **100 k writes/s** — feasible. One celebrity post × 100 M followers = 100 M writes — at 1 M writes/s
that's **100 seconds per post**: that number kills pure fan-out-on-write.

**Per-node quota split.** 1,000 requests/min ÷ 500 servers = **2 per server per minute** — useless,
so a rate limit can't be naively divided among nodes.

**Connections.** 100 M concurrent × ~20 KB = **2 TB of RAM** for sockets alone; at ~500 k per host,
**~200 gateway hosts** before redundancy.

**Hot account.** One merchant receiving 5 k payments/s → 5 k updates/s on one balance row — row-lock
contention says *append entries, derive the balance*.

---

## Traps

{: .warn }
> **Estimating everything.** Ten numbers in a table eat eight minutes and none drive a decision.
> Three numbers, each with a "which means".

{: .warn }
> **Averages for latency or capacity.** Build for the peak; promise the p99.

{: .warn }
> **Forgetting replication and indexes** when sizing storage — the real footprint is often 3–5× the
> raw data.
