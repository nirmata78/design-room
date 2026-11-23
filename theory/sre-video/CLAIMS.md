# Claims ledger

One row per number or factual claim shown or spoken. **Kind:** `published` (the book or workbook states it; chapter given, text checked in the local extraction) ·
`derived` (arithmetic, re-run with `python3`) · `assumption` (a planning figure I chose, labelled on the slide) · `general` (industry knowledge not from the books; see `VERIFY.md`).
**Check:** ✔ checked against the text or re-computed · ◐ paraphrased from memory of the chapter, section heading checked, wording not · ✘ not checked.

| Ep | Claim | Kind | Source or arithmetic | Check |
|---|---|---|---|---|
| 1 | Operations work capped at 50% of an SRE's time | published | ch. 1, *Tenets* | ✔ |
| 1 | On call at most 25%; eight engineers for a single-site, two-person, week-long rota | published | ch. 11; derivation in ch. 5/11 | ✔ |
| 1 | At most two events per 8–12 hour shift | published | ch. 1 and 11 | ✔ |
| 1 | Over the cap, burden shifts back to developers or staff is added | published | ch. 1 | ✔ |
| 1 | Roles of Borg, Colossus, Chubby, Stubby, Borgmon; request path through GSLB, GFE | published | ch. 2 | ◐ |
| 1 | Open analogues (Kubernetes, etcd, ZooKeeper, gRPC, Prometheus) | general | Borg paper, ACM Queue 2016 for the lineage | ✘ |
| 2 | Nines table (per year, 30 days, day) | derived | e.g. 0.0001 × 525,600 = 52.56 min; 0.001 × 43,200 = 43.2 min | ✔ |
| 2 | 99.99% allows 52.56 minutes a year; 2.5 M requests a day allows 250 errors | published | ch. 3 | ✔ |
| 2 | $1 M × 0.0009 = $900 value of 99.9 to 99.99 | published | ch. 3 (and arithmetic) | ✔ |
| 2 | Global Chubby planned outage | published | ch. 4 | ✔ |
| 2 | Burn rates 14.4 / 6 / 1 over 1 h / 6 h / 3 d = 2% / 5% / 10% of a 30-day budget | published | Workbook ch. 5; 14.4 × 1 ÷ 720 = 0.02, 6 × 6 ÷ 720 = 0.05, 1 × 72 ÷ 720 = 0.10 | ✔ |
| 2 | Two hard dependencies in series: 0.999 × 0.999 ≈ 99.8% | derived | 0.998001 | ✔ |
| 3 | Six properties of toil; five values of automation; five-step ladder | published | ch. 5, ch. 7 | ✔ |
| 3 | Empty list read as "everything", fleet-wide disk erase; CDN served from datacenters | published | ch. 7 (and ch. 13) | ✔ |
| 3 | Guardrails list (rate, fraction, sanity check, human gate, dry run) | general | My synthesis of the lesson | — |
| 4 | Four golden signals; symptom vs cause; white-box vs black-box | published | ch. 6 | ✔ |
| 4 | Mean 109 ms for 99 × 100 ms and 1 × 1,000 ms | derived | 0.99 × 100 + 0.01 × 1000 = 109 | ✔ |
| 4 | Worst-case detection 15 + 15 + 120 + 30 = 180 s | assumption | Illustrative intervals; sum re-run | ✔ |
| 4 | Do not average percentiles; merge histograms | general | Standard; ch. 6 bucketing advice | ◐ |
| 4 | RED and USE method names | general | Community shorthands, not in the book | ✘ |
| 5 | Four principles; hermetic builds; configuration models | published | ch. 8 | ✔ |
| 5 | Opening "two rollouts": 40 minutes, 6 minutes, 1 percent | assumption | Illustration; said so aloud | — |
| 5 | Canary sizes 1/5/25%: 6,000 / 30,000 / 150,000 requests; z = 1.4 / 3.2 / 7.1 | derived | 1,000 rps × 600 s × share; baseline 0.1%, regression 0.2%; z = (bad − base) ÷ √(base + bad) | ✔ |
| 5 | "Negative lines of code", boring, minimal APIs | published | ch. 9 | ✔ |
| 6 | 25%, two events, 8 and 6 engineers; night shifts; compensation | published | ch. 11 | ✔ |
| 6 | Troubleshooting as hypothetico-deductive; triage, examine, diagnose, test and treat, cure | published | ch. 12 | ✔ |
| 7 | Roles (commander, operations, communications, planning incl. "ordering dinner"); declare criteria | published | ch. 14 | ✔ |
| 7 | Three emergency stories (test, change, process induced) | published | ch. 13 | ✔ |
| 7 | Postmortem triggers; blameless; reward; Outalator | published | ch. 15, 16 | ✔ ◐ |
| 8 | "Passing proves little, failing proves absence"; zero MTTR via testing | published | ch. 17 | ✔ |
| 8 | Auxon, intent-based capacity planning | published | ch. 18 (outline) | ◐ |
| 9 | 300 clients, 300 backends, 30% subset: 63% and 121% of average, 57 / 90 / 109 connections | published | ch. 20 | ✔ |
| 9 | Round robin up to 2× CPU spread; flow control limit near 100 active requests | published | ch. 20 | ✔ |
| 9 | DNS TTL limits steering; VIP with packet encapsulation (GRE) and consistent hashing | published | ch. 19 | ✔ |
| 9 | Deterministic subsetting: rounds, shared shuffle, fixed slices | published | ch. 20 | ✔ |
| 9 | Power of two choices | general | Mitzenmacher; not in the book | ✘ |
| 10 | A at 1,000 QPS, B fails, A gets about 1,200 | published | ch. 22 | ✔ |
| 10 | Per-request budget 3; per-client budget 10%; growth near 3× to about 1.1× | published | ch. 21 | ✔ |
| 10 | 3 × 3 × 3 = 27 attempts at the database | derived | Three retrying layers, three tries each | ✔ |
| 10 | Client rejection probability max(0, (requests − K × accepts) ÷ (requests + 1)), K = 2, 1.1 | published | ch. 21, equation 21-1 | ✔ |
| 10 | Deadline 30 s, 7 s used, 23 s to B, 4 s used, 19 s to C | published/derived | ch. 22 gives 30, 7, 23; 19 = 23 − 4 | ✔ |
| 10 | Criticality classes; CPU as the provisioning signal | published | ch. 21 | ✔ |
| 10 | Metastable failure as a named class | general | Literature since about 2021 | ✘ |
| 11 | Majority quorums; 2f+1 replicas tolerate f; three minimum; five for failure during maintenance | published | ch. 23 | ✔ |
| 11 | Quorum table 3/4/5/7; floor((N − 1) ÷ 2) | derived | Arithmetic | ✔ |
| 11 | Five replicas in three regions, 30 ms and 80 ms | assumption | Illustrative; labelled on the figure | ✔ |
| 11 | Three case studies; FLP impossibility; leader election not on the data path | published | ch. 23 | ✔ ◐ |
| 12 | Skip rather than double; two synchronisation points; idempotent or look up state | published | ch. 24 | ✔ |
| 12 | Periodic pipeline problems, thundering herd, moiré load | published | ch. 25 | ✔ |
| 12 | Leases and uniquely named outputs ("double correctness guarantee") | published | ch. 25 | ✔ |
| 12 | Container platform cron settings, durable execution engines | general | | ✘ |
| 13 | 6 × 2 × 2 = 24 combinations | published/derived | ch. 26 categories; product re-computed | ✔ |
| 13 | Four days "too long"; 24 hours as a starting threshold | published | ch. 26 | ✔ |
| 13 | Restore: 1 TB 1.7 min, 1 PB 27.8 h, 1 EB 1,157 days at 10 GB/s | derived | size ÷ bandwidth; bandwidth is an assumption | ✔ |
| 13 | Gmail 2011 (largest use of offline backup; restores had been simulated); Music 2012 (found by user, runaway deletion, thousands of tapes) | published | ch. 26 | ✔ |
| 14 | Keyhole: 25× normal peak, over a million requests a second, Christmas Eve 2011 | published | ch. 27 (the two figures are quoted as the book gives them; they do not reconcile with "several thousand" a second, so no arithmetic is built on them) | ✔ |
| 14 | Z ÷ (Z − 1) × peak: 200 / 150 / 133 / 125% for 2 / 3 / 4 / 5 zones | derived | Arithmetic | ✔ |
| 14 | Nine checklist areas; sample questions | published / author | Areas from ch. 27; questions are mine, said so on the slide | ✔ |
| 15 | PRR phases; one to three SREs; three engagement models | published | ch. 32 | ✔ |
| 15 | Production meeting default agenda | published | ch. 31, App. F | ◐ |
| 15 | Learning path stages (orientation … primary) | author | My synthesis of ch. 28 | — |
| 16 | Two Appendix B examples (empty file, six minutes; "/" matching every URL) | published | App. B | ✔ |
| 16 | Industries in ch. 33; swing capacity as "switch on wheels" | published | ch. 33 | ✔ |
| 16 | AI-serving translations | general | My synthesis; labelled as mappings | ✘ |

Quotes: one short line is quoted verbatim, ch. 26: "No one really wants to make backups; what people really want are restores."
