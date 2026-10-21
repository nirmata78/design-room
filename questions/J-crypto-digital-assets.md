# Archetype J · Crypto & digital assets

**SD-71 – SD-76.** Slice with `grep -n '^### SD-72' questions/J-crypto-digital-assets.md`, then Read
with `offset`. Do not read this file whole.

**What this archetype tests as a family:** **custody of irreversible value against an adversary, with
an external ledger you do not control.** A bank transfer can be reversed; a signed on-chain transaction
cannot, and a leaked key is a total loss. Meanwhile the blockchain itself is an eventually-consistent
external system that can **reorganise** — rewrite its recent history. The recurring probe: *"what is
your source of truth, and what happens when it disagrees with the chain?"*

**Calibration note.** This is a domain archetype. **Do not reward jargon.** A candidate who can explain
*why* a deposit needs N confirmations, or *why* hot wallets hold a small fraction of funds, scores; one
who recites protocol names does not. These questions also appear at fintechs and payment companies
adding digital-asset products — they are not crypto-company-only. Archetype F's money rules (double
entry, idempotency, reconciliation) all still apply; this archetype adds keys and reorgs.

---

### SD-71 · Exchange matching engine & order book   [T1 · CX★ FT]

**Read aloud:** *"Design the core of a trading exchange: clients submit buy and sell orders, the
exchange matches them and reports trades."*

**Crux.** **Determinism and ordering.** Matching must be strictly sequential per instrument (price-time
priority), so the engine is **single-threaded per order book** and the design is about making that one
thread extraordinarily fast and **recoverable**: an input log that is the source of truth, deterministic
replay, and everything else (market data, balances, settlement) downstream of the sequenced log.
Candidates who reach for a distributed database with locks have missed it.

**If they ask:**

| Question | Answer |
|---|---|
| Instruments? | 500 trading pairs; the top 5 carry 70% of volume |
| Load? | 200k orders/sec peak across all books, 50k/sec on the hottest book; ~90% are cancels or modifies |
| Latency? | Order acknowledgement p99 under 1 ms inside the engine; clients are over the internet |
| Order types? | Limit, market, cancel; post-only and immediate-or-cancel nice to have |
| Balances? | Users must have funds before an order is accepted (no credit) |
| Availability? | Downtime halts trading — minutes are tolerable a few times a year, data loss is not |
| Fairness? | Regulators and users require price-time priority and an auditable sequence |

**Listen for:**
- **A sequencer**: every order gets a global sequence number per book and is written to a durable,
  replicated log **before** matching — **← the senior insight: the log is the database; the in-memory
  book is a cache that can be rebuilt by replay.**
- **In-memory order book** per instrument: price levels (sorted map) with FIFO queues per level,
  O(1)-ish best-bid/ask, O(1) cancel via an order-id index.
- **Single-threaded matching per book**, sharding by instrument across cores/machines; no locks.
- **Pre-trade risk check** (funds reservation) before the sequencer, so the engine never matches an
  unfunded order — and the race between reservation and cancel.
- **Hot standby** replaying the same log deterministically for failover; snapshots to bound replay time.
- **Outputs as events**: trades, order updates, market data (incremental + snapshots) fanned out to
  clients; downstream settlement updates balances in a double-entry ledger.
- **Gateway layer** handling sessions, auth, rate limits and throttling — so abusive clients can't
  flood the sequencer.

**Probe ladder:**
- *Requirements:* "What does 'fair' mean here, precisely?" · "What's out of scope?" (custody, KYC)
- *Estimation:* "50k orders/sec on one book on one thread — how many microseconds per order, and is
  that realistic?" (≈20 µs: yes, in memory, without allocation or I/O on the hot path)
- *Design:* walk a limit order that partially fills against three resting orders.
- *Deep dives:* **"The primary engine dies mid-match. What does the standby do, and could a trade be
  reported twice or lost?"** · "Why not run matching in a database transaction?" · "A market maker sends
  40k cancels a second. What protects everyone else?" · "How do you rebuild the book after a restart,
  and how long does it take?"
- *EM/Staff bar:* "How do you deploy a new version of the engine without halting trading — or do you?"
  · "A bug matched orders at the wrong price for 90 seconds. What's the operational and customer
  response?"

**Curveball:** *"Regulators require that you can reproduce the exact state of every order book at any
microsecond in the last five years."* Tests whether they realise the sequenced input log plus
deterministic replay already gives this, and the storage/retention arithmetic.

**Weak / Strong / Exceptional.** *Weak* — orders in a relational table, matching via queries and row
locks, horizontal scaling of matching for one book. *Strong* — sequencer + durable log, in-memory book
with efficient structures, single-threaded per book, pre-trade risk, deterministic standby, event
outputs. *Exceptional* — articulates log-as-source-of-truth and replay as the answer to recovery,
audit and testing at once; handles gateway-level throttling; and is honest that deployment of the
engine is a scheduled, halted operation or a carefully replayed cut-over.

**Traps.** Distributed locks on the book. Matching across shards for one instrument. Treating market
data as an afterthought (it is often the larger bandwidth problem).

---

### SD-72 · Custodial wallet — hot, warm and cold key management   [T1 · CX★ FT]

**Read aloud:** *"Design the wallet system for an exchange that holds customers' crypto: deposits come
in, withdrawals go out, and the private keys must never be stolen."*

**Crux.** **Security architecture is the design.** Funds are split into tiers by how fast they can move
and how much an attacker could take: a small **hot** tier for automated withdrawals, **warm** with
multi-party approval, **cold** offline. The engineering is the **signing path** — who or what can cause
a key to sign, under which policy — plus **rebalancing** between tiers and an **internal ledger** that
is reconciled against the chain.

**If they ask:**

| Question | Answer |
|---|---|
| Assets? | 30 assets on 10 chains; ~$5B under custody |
| Withdrawals? | 100k/day; users expect most within minutes; some are large (>$1M) |
| Deposits? | Each user has deposit addresses per chain |
| Threats? | External attackers, compromised employee laptops, malicious insiders, supply-chain attacks |
| Requirements? | No single person can move funds; withdrawals to new addresses get extra checks; full audit |
| Insurance? | Covers only cold storage |

**Listen for:**
- **Tiering by risk**: hot (e.g. a few % of assets, automated, rate-limited), warm (multi-approver),
  cold (offline/HSM, ceremonies); **← the senior insight: the hot-wallet balance is a deliberately
  chosen maximum loss, sized from withdrawal velocity, not a technical detail.**
- **Key protection**: HSMs or multi-party computation / multisig so no single machine or person holds
  a whole key; quorum policies.
- **Policy engine on the signing path**, separate from the application: limits per user/time window,
  allow-lists, velocity checks, new-address cooling periods, large-withdrawal human approval — enforced
  **at the signer**, so a compromised application server cannot bypass it.
- **Internal double-entry ledger** as the customer balance source of truth; on-chain wallets as
  omnibus pools; continuous **reconciliation** of ledger totals vs chain balances.
- **Withdrawal state machine**: requested → risk-checked → approved → signed → broadcast → confirmed,
  idempotent, with nonce/UTXO management and fee bumping for stuck transactions.
- **Rebalancing** hot↔warm↔cold by thresholds, itself under approval policy.
- **Audit and monitoring**: every signature traced to an approved request; anomaly alerts; incident
  "freeze" switch.

**Probe ladder:**
- *Requirements:* "What's the maximum you're willing to lose in a hot-wallet compromise, and who
  decided?" · "What's out of scope?"
- *Estimation:* "100k withdrawals/day with a 2-hour peak — how much must the hot wallet hold to serve
  95% without touching warm storage?"
- *Design:* walk a $2M withdrawal to a never-seen address from request to confirmation.
- *Deep dives:* **"An attacker has root on your withdrawal API server. What can they steal?"** (correct
  answer: at most what the signer's policy allows in the window — if they say "everything", the policy
  is in the wrong place) · "A withdrawal was broadcast but is stuck for six hours due to low fees. What
  happens?" · "The ledger says 1,000 BTC; the chain says 999.6. What now?" · "How do you rotate keys?"
- *EM/Staff bar:* "Who is on call for the wallet, and what can they do at 3 a.m. without a second
  person?" · "Product wants instant withdrawals for all amounts. What do you say?"

**Curveball:** *"A popular browser-extension library you depend on is compromised in a supply-chain
attack, and your ops engineers' laptops ran it last night."* Tests whether approvals depend on
endpoints that could be compromised, and the freeze/rotation response.

**Weak / Strong / Exceptional.** *Weak* — keys encrypted in a database, the app signs directly,
balances read from the chain. *Strong* — tiered custody with sized hot wallet, HSM/MPC, policy enforced
at the signer, internal ledger + reconciliation, withdrawal state machine, rebalancing. *Exceptional* —
frames hot-wallet size as a risk budget, separates policy from application with an independent trust
domain, designs for insider threat (quorums, no single human), and has an incident freeze-and-rotate
playbook.

**Traps.** Treating "encrypted at rest" as key security. Policy checks only in the application tier.
Using chain balance as customer balance.

---

### SD-73 · Deposit detection & crediting across chains   [T2 · CX]

**Read aloud:** *"Customers send crypto to their deposit addresses. Design the system that notices
deposits and credits their accounts."*

**Crux.** **The chain can reorganise**, so a deposit that appears can disappear. Crediting is a
**confidence state machine** — seen, pending N confirmations, credited — with N chosen per chain and
amount, and the system must handle reorgs, duplicates and node failures without ever crediting twice
or missing a deposit.

**Numbers if asked:** 10 chains with block times from 1 second to 10 minutes, 50M deposit addresses,
200k deposits/day, required confirmations differ per chain, own full nodes plus a third-party provider,
and customers want to trade deposited funds as fast as possible.

**Listen for:** **own nodes (several, per chain) as the source**, third-party APIs as a cross-check only
· **block-by-block ingestion with parent-hash checking** to detect reorgs and roll back affected
deposits · **address → user lookup** at scale (50M addresses: bloom filter or indexed set) ·
**confirmation policy per chain and amount**, with partial early credit (trade but not withdraw) as a
product-risk choice · **idempotency** keyed on (chain, tx hash, output index) · **double-entry credits**
into the internal ledger, with reversal entries on reorg · **lag monitoring** (head height vs indexed
height per chain) and alerting · **reconciliation** of credited deposits against wallet balances.

**Probes:** *"A 3-block reorg removes a deposit you already credited. Walk me through it."* · *"Your node
falls 400 blocks behind. What do customers see?"* · *"Why not trust the third-party API?"* · *"How many
confirmations for a $50 deposit versus a $5M one, and who decides?"* · *(EM bar)* *"A chain halts for
12 hours. What's your customer communication and system state?"*

**Weak / Strong / Exceptional.** *Weak* — polls a third-party API, credits on first sight. *Strong* —
own nodes, reorg-aware ingestion, confirmation state machine per chain, idempotent ledger credits with
reversals, lag monitoring. *Exceptional* — treats the confirmation count as a risk-priced product
decision, allows tiered early availability, and reconciles end to end.

---

### SD-74 · Blockchain indexer & on-chain data API   [T2 · CX]

**Read aloud:** *"Design a service that indexes a blockchain and lets applications query it — balances,
transaction history, token transfers — quickly."*

**Crux.** It is **CDC from an append-only log that occasionally rewrites its tail.** Ingestion must be
reorg-aware, derived tables must be rebuildable, and query patterns (history by address, balances at a
block) need indexes the chain itself does not provide.

**Numbers if asked:** a chain with 1B transactions total and ~1M new per day, 12-second blocks, queries
of 20k/sec mostly "history for address X" and "balance of token T for address X", freshness within 2
blocks, decoding of smart-contract events for 5,000 popular contracts.

**Listen for:** **ingestion pipeline**: raw blocks → decoded events → derived tables, each stage
replayable · **reorg handling** by tracking canonical chain and rolling back derived rows by block, or
by deferring finality-sensitive tables · **storage choice by query**: wide-column/partitioned tables
keyed by address for history, point-in-time balances via snapshots plus deltas · **backfill** of 1B
historical transactions in parallel by block range, separate from live tailing · **schema/ABI
evolution** for contract decoding · **caching hot addresses** (exchanges, popular contracts are extreme
hot keys) · **freshness SLI** expressed in blocks behind head.

**Probes:** *"How do you backfill 1B transactions without hurting live ingestion?"* · *"One address has
40M transactions. What does a history query do?"* · *"A reorg of 2 blocks happens. Which tables change
and how?"* · *"A popular contract's event schema was decoded wrong for a month. How do you fix it?"* ·
*(EM bar)* *"Run our own nodes or buy node access — what's the cost and risk?"*

**Weak / Strong / Exceptional.** *Weak* — query the node directly for everything. *Strong* — staged
replayable pipeline, reorg rollback, address-partitioned history, separate backfill, hot-key handling.
*Exceptional* — designs derived data as rebuildable views of an immutable raw layer, so decoding bugs
and reorgs are both "replay from block N".

---

### SD-75 · Margin & liquidation engine   [T2 · CX FT]

**Read aloud:** *"Users trade with leverage. Design the system that tracks their margin in real time and
liquidates positions before they go negative."*

**Crux.** **A race against the price.** Every price tick changes the margin of thousands of accounts,
and liquidating late means the exchange absorbs losses. The design is about **incremental risk
computation**, **prioritising the most at-risk accounts**, and **liquidating in a way that does not
crash the market further** — under extreme volatility, which is exactly when load peaks.

**Numbers if asked:** 2M open positions, 500 instruments, price updates up to 100/sec per instrument in
volatile periods, liquidation must begin within ~100 ms of breaching maintenance margin, cascading
liquidations happen in crashes, and an insurance fund absorbs shortfalls.

**Listen for:** **mark price** from an index of several venues (not last trade — resists manipulation)
· **positions indexed by liquidation price** per instrument, so a tick finds affected accounts by range
query rather than scanning all accounts · **cross-margin accounts** needing aggregate recomputation ·
**prioritised liquidation queue** by distance below margin · **liquidation execution**: partial
liquidation first, then the insurance fund, then auto-deleveraging as last resort · **load shedding**
of non-critical work during volatility, never of liquidation · **determinism and audit** of every
liquidation decision.

**Probes:** *"BTC drops 15% in a minute. What does your system do, second by second?"* · *"Why not
liquidate on the last traded price?"* · *"How do you find the 3,000 accounts affected by one tick
without scanning 2M?"* · *"Liquidations themselves move the price down. What stops a spiral?"* ·
*(EM bar)* *"The insurance fund lost $20M in one night. What's the post-incident review about?"*

**Weak / Strong / Exceptional.** *Weak* — periodic batch job over all accounts. *Strong* — index-based
mark price, liquidation-price index for range lookup, prioritised queue, partial liquidation and
insurance fund. *Exceptional* — designs for the peak-volatility case as the normal case, protects the
liquidation path with explicit resource isolation, and addresses market-impact feedback.

---

### SD-76 · Fiat on-ramp & proof of reserves   [T2 · CX FT]

**Read aloud:** *"Design the system that lets users buy crypto with bank transfers and cards, and that
lets the company prove publicly that it holds all customer assets."*

**Crux.** Two halves joined by the ledger. **On-ramp** is a payments problem with asymmetric
reversibility — card payments can be charged back for months but the crypto delivered cannot be — so
risk holds and limits are the design. **Proof of reserves** is a cryptographic-accounting problem:
prove liabilities (customer balances) without revealing them, and assets (on-chain holdings) with
ownership proofs.

**Numbers if asked:** 3M users, card and bank-transfer rails through two payment processors, chargeback
window up to 120 days, card fraud on crypto purchases is high, monthly public attestation, auditors
need to verify independently.

**Listen for:** **order state machine** spanning fiat payment, risk decision, crypto delivery, and
settlement with each step idempotent · **holds and limits** by payment method and user history —
bank transfers settle slower but reverse less · **double-entry ledger** across fiat and crypto,
reconciled against processor reports and the chain · **liability proof** via a Merkle tree of
customer balances where each user can verify inclusion, with the privacy caveats · **asset proof** via
signed messages from custody addresses · **the gap**: proof of reserves without proof of liabilities
is meaningless, and attestation is a point-in-time snapshot.

**Probes:** *"A user buys $5,000 of BTC by card, withdraws it, and charges back 60 days later. What did
your design do?"* · *"How does a user verify they're included in the liabilities?"* · *"Why isn't a
wallet balance screenshot a proof of reserves?"* · *"Processor reports disagree with your ledger by
$12k. Workflow?"* · *(EM bar)* *"Who signs off the monthly attestation, and what's their risk?"*

**Weak / Strong / Exceptional.** *Weak* — payment then immediate delivery, reserves as a balance
dashboard. *Strong* — risk-held delivery by rail, idempotent order saga, cross-asset ledger and
reconciliation, Merkle liability proof plus signed asset proofs. *Exceptional* — names the
reversibility asymmetry as the crux, explains why liabilities matter more than assets, and acknowledges
snapshot-gaming limits of attestation.
