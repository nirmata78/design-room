# Verified claims

All "Then and now" claims and asides were checked against public sources on **2026-11-12** (web search; primary pages where the
search returned them). Where a claim was wrong or too strong it was changed in `src/chNN.txt`.

| Ep | Claim | Result | Source |
|---|---|---|---|
| 1 | Kubernetes grew from Borg's and Omega's lessons; open analogues of internal systems | Confirmed. Kubernetes keeps Omega's shared store with watching components, and is open source | ACM Queue 2016, "Borg, Omega, and Kubernetes" |
| 2, 4 | Multiwindow burn-rate alerting; a burn rate of 14.4 over one hour spends 2 percent of a 30-day budget | Confirmed. Paired with a 5-minute short window; a second tier is 6 hours at burn rate 6 (5 percent) | Google SRE workbook, "Alerting on SLOs" |
| 4 | Exemplars link a metric to a trace | Confirmed. Needs OpenMetrics or remote write, and Prometheus stores a bounded number | Prometheus and OpenTelemetry docs |
| 4 | Continuous profiling as a fourth signal | **Corrected.** Profiles are in alpha in OpenTelemetry; slides now say "becoming" and "still in alpha" | OpenTelemetry concepts, Profiles |
| 4 | RED and USE | Confirmed and attributed: RED from Tom Wilkie (2015, services), USE from Brendan Gregg (resources) | Grafana blog; Gregg's USE method page |
| 5 | Software bill of materials and signed build provenance | Confirmed. SLSA build levels 1 to 3: provenance, signed provenance, hardened builds. An SBOM is an inventory, a different thing | slsa.dev v1.x |
| 9 | Maglev: a software network load balancer using consistent hashing and connection tracking | Confirmed. NSDI 2016; in service at Google since 2008 | Maglev paper |
| 9 | Power of two choices | Confirmed. Mitzenmacher, 2001; Envoy documents it as a policy | Envoy docs |
| 9 | Meshes and proxies offer retries, outlier ejection, health checks, budgets | Confirmed in general; defaults vary by product and version, so no default is stated | Envoy, Istio docs |
| 10 | Metastable failures as a named class | Confirmed. Bronson et al., HotOS 2021: vulnerable, metastable and stable states; the sustaining effect, not the trigger, is the cause | HotOS 2021 |
| 11 | Raft in widely used coordination stores; Paxos lineage; bounded clock uncertainty in managed databases | Confirmed. etcd and Consul use Raft. ZooKeeper uses its own protocol (ZAB), and the slides do not claim Raft for it. Spanner pairs TrueTime intervals with Paxos groups | Raft paper (2014); Spanner (OSDI 2012); Paxos Made Live |
| 11 | Paxos mechanics (new section) | Written from the protocol as published: prepare and promise, accept and accepted, the highest-numbered accepted value rule, majority overlap, promises persisted | Paxos literature; Raft paper |
| 12 | Cron job overlap and missed-start policies | Confirmed. Kubernetes `concurrencyPolicy` is Allow (default), Forbid or Replace; `startingDeadlineSeconds` bounds how late a start may be; over 100 missed schedules and the controller gives up | Kubernetes docs |
| 12 | Durable execution engines replay an event history | Confirmed. Recovery re-runs deterministic code against recorded results; long histories slow recovery | Temporal and Dapr docs |
| 13 | Immutable backups and retention locks | Confirmed. Object Lock compliance mode cannot be shortened or overridden even by the root user | AWS S3 documentation |
| 8 | Chaos engineering with a hypothesis and a limited blast radius | Confirmed. Steady-state hypothesis, small start, kill switch | principlesofchaos.org |
| 3, 6, 7, 14, 15 | General practice claims (policy engines, AI-assisted triage, incident tooling, readiness as code, platform engineering) | Kept as hedged statements. Not product claims | n/a |
| 16 | AI-serving table | A mapping of the ideas, not a claim about a product | n/a |

**Not verified:** exact default values of any mesh or proxy; the platform-engineering "paved road" attribution (no source found, and the slides name no company).
