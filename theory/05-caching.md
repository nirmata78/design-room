# 5 · Caching — making reads cheap without lying too much

A cache keeps a **copy** of data closer to the reader, trading **freshness and correctness risk** for
latency and cost. In read-heavy systems the cache hit ratio *is* the economics of the system: at a
99% hit ratio the database sees 1% of reads; at 90% it sees ten times that.

---

## Where caches live

| Layer | Example | Holds | Invalidated by |
|---|---|---|---|
| Client / browser | HTTP cache, app memory | per-user responses, static assets | `Cache-Control`, ETags, app logic |
| CDN / edge | CloudFront, Fastly, Akamai | static and cacheable shared responses | TTL, purge API, versioned URLs |
| Service-local (in-process) | a map in each app server | very hot, small, tolerant-of-staleness data | TTL; pub/sub invalidation |
| Distributed cache | Redis, Memcached | shared working set across servers | TTL, explicit delete, CDC-driven |
| Database buffer pool | the DB's own page cache | pages | the engine |

## The four write/read patterns

| Pattern | Read | Write | Use when |
|---|---|---|---|
| **Cache-aside** (lazy) | app reads cache; on miss reads DB and populates | app writes DB, then **deletes** the cache key | the default; simple, resilient to cache loss |
| **Read-through** | cache library loads from DB on miss | as cache-aside | you want the loading logic centralised |
| **Write-through** | cache always has data | write to cache and DB synchronously | reads must almost never miss; write latency acceptable |
| **Write-behind** (write-back) | cache always has data | write to cache; flush to DB asynchronously | write bursts must be absorbed — **risks data loss** on cache failure |

{: .why }
> **Why delete rather than update the cache on write?** Two concurrent writers can update the DB in
> one order and the cache in the other, leaving the cache permanently wrong. Deleting makes the next
> read reload the truth. A small race remains (a reader can repopulate with a stale value read just
> before the write), which is why TTLs stay as a backstop and why some systems use **versioned
> values** or delayed double-delete.

## Invalidation strategies

1. **TTL only** — simplest; staleness bounded by the TTL. Good for data that tolerates seconds or
   minutes of staleness.
2. **Explicit delete on write** — the writer deletes the key (cache-aside).
3. **Change-data-capture driven** — a consumer of the database's change stream deletes or updates
   affected keys. Decouples writers from cache knowledge; the cache lags by the CDC delay.
4. **Versioned keys** — the key includes a version (`post:123:v7`); a new version is a new key, old
   ones expire. Excellent for immutable content and CDN assets.

{: .say }
> "The feed tolerates a few seconds of staleness, so posts are cached with a short TTL plus CDC-driven
> invalidation for deletes — a deleted post must disappear within seconds, which TTL alone can't promise."

## Failure modes and their fixes

| Problem | What happens | Fix |
|---|---|---|
| **Stampede / thundering herd** | a hot key expires; thousands of requests miss at once and hammer the DB | **request coalescing** (single-flight: one loader, others wait); **probabilistic early refresh**; serve stale while revalidating |
| **Hot key** | one key's traffic exceeds one cache node | replicate the key across nodes (`key#1…key#k`), client-side local cache, CDN |
| **Cold start / cache loss** | a restarted cache sends 100% of reads to the DB | warm before taking traffic; **size the DB to survive a partial cache loss**; shed load |
| **Penetration** | requests for non-existent keys always miss | cache negative results briefly; bloom filter of existing keys |
| **Inconsistency** | cache and DB disagree indefinitely | TTL as a backstop; delete-on-write; CDC invalidation |
| **Large values** | network and memory blow up | cache IDs and small projections; hydrate separately |

{: .key }
> **Size the database for cache failure, not for the hit ratio.** If the cache serves 99% of 100k
> reads/s and one of ten cache shards dies, the DB suddenly sees ~10k extra reads/s — ten times its
> usual 1k. Either the DB can take it, or the design needs load shedding.

## Distributing a cache

- **Consistent hashing** (with virtual nodes) maps keys to cache nodes so adding a node remaps only
  ~1/N of keys ([Partitioning](03-partitioning-and-storage.md)).
- **Replication** of cache shards trades memory for availability; many designs accept losing a shard
  and refilling from the source.
- **Eviction:** LRU or LFU-ish policies; set memory limits and watch eviction rate as an SLI.

## Sizing and economics

- **Working set**, not total data: what fraction of keys receive most reads? (Often 20% of keys serve
  80%+ of reads.)
- **Memory** = hot keys × (value size + overhead ~50–100 B per key in Redis-class stores).
- **Hit ratio → backend load**: backend QPS = total QPS × (1 − hit ratio). Moving from 95% to 99% cuts
  backend load 5×.

---

## Traps

{: .warn }
> **Caching as the fix for a slow query** without deciding the staleness contract. Say how stale the
> data may be, and how you invalidate.

{: .warn }
> **A cache that has become the source of truth** — write-behind without durability, or data that
> exists only in the cache. If losing the cache loses data, it's a database, and should be designed
> like one.
