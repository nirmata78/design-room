# Fact check (2026-11-18)

Version-specific claims in the course, checked against the sources listed. Numbers of the running example are illustrative and were recomputed by script.

| Claim | Where | Source |
|---|---|---|
| Kafka 4.0 runs only in KRaft mode; ZooKeeper removed | 3.4, 6.3 | [Kafka upgrade notes](https://kafka.apache.org/41/getting-started/upgrade/) |
| New consumer protocol generally available in 4.0; clients opt in; `group.protocol` default is `classic` | 1.5, 6.3 | [Upgrade notes](https://kafka.apache.org/41/getting-started/upgrade/), [consumer configs 4.4](https://kafka.apache.org/44/configuration/consumer-configs/) |
| Eligible leader replicas on by default for new clusters in 4.1 | 6.3 | [Upgrade notes 4.2 page, 4.1 section](https://kafka.apache.org/42/getting-started/upgrade/) |
| Share groups: preview in 4.1, production ready in 4.2 | 6.2, 6.3 | [Upgrade notes](https://kafka.apache.org/42/getting-started/upgrade/) |
| Dead-letter queues for share groups in 4.4 (KIP-1191) | 6.2, 6.3 | [4.4.0 announcement](https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/) |
| Share groups: per-record accept, release, reject; more consumers than partitions; no ordering across batches | 6.2 | [KIP-932](https://cwiki.apache.org/confluence/display/KAFKA/KIP-932%3A+Queues+for+Kafka) |
| Diskless topics accepted March 2026 as a direction, details in follow-up KIPs; not named in the 4.4 announcement | 6.3 | [KIP-1150](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1150%3A+Diskless+Topics), [Aiven](https://aiven.io/blog/kip-1150-accepted-and-the-road-ahead) |
| Defaults: `min.insync.replicas` 1, unclean election off, retention 7 days, about 1 MB message limit, `delete.retention.ms` 1 day | 3.2, 5.3, 6.4 | [Topic configs](https://kafka.apache.org/42/configuration/topic-configs/) |
| Defaults: `acks=all`, idempotence on; null keys use sticky partitioning | 2.3, 3.2 | [Producer configs](https://kafka.apache.org/42/configuration/producer-configs/) |
| Defaults: auto commit on, `read_uncommitted`, `max.poll.interval.ms` 5 minutes | 1.5, 4.1, 4.2 | [Consumer configs 4.4](https://kafka.apache.org/44/configuration/consumer-configs/) |
| Compaction: active segment not compacted, order and offsets kept, tombstones can be missed by lagging readers | 5.3 | [Design docs](https://kafka.apache.org/44/design/design/) |
| Exactly once to outside systems needs their cooperation | 4.2 | [Design docs](https://kafka.apache.org/44/design/design/) |
| 3 or 5 controllers, majority required; combined mode not recommended for critical deployments | 3.4 | [KRaft operations](https://kafka.apache.org/44/operations/kraft/) |
| Tiered storage: no compacted topics; no storage plugin shipped | 3.5 | [Tiered storage](https://kafka.apache.org/44/operations/tiered-storage/) |
| About 4,000 partitions per broker is a rule of thumb, not enforced | 3.1 | [Apache wiki](https://cwiki-test.apache.org/confluence/x/0STcC) |
| librdkafka defaults to CRC32 (`consistent_random`); `murmur2_random` matches Java | 2.5 | [librdkafka configuration](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md) |
| Backward means consumers upgrade first, forward means producers first | 6.1 | [Confluent schema evolution](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) |

## Running example, recomputed

| Result | Arithmetic |
|---|---|
| 6.05 TB, 18.1 TB, 25.9 TB | 10 MB/s × 86,400 × 7; × 3; ÷ 0.7 |
| 5 brokers, then 6 | 25.9 ÷ 6 = 4.3; plus one spare |
| Writes 90 MB/s, network out 150 MB/s | 30 × 3; 90 to consumers + 60 replication |
| 48 partitions | 12,000 ÷ 500 × 2 |
| Hot key 960/s, 1.7 million behind per hour | 0.08 × 12,000; (960 − 500) × 3,600 |
| Rebuild about 8 h, about 70 min with tiering | 3 TB ÷ 100 MB/s; one seventh of that |
| Catch-up 30 MB/s | 10 + 36,000 MB ÷ 1,800 s |
