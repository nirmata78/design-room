# Claims checked (2026-11-20)

Carried over from the retired fintech mock series (problems 1–3 = SD-82, SD-95, SD-77); P1/P2/P3 refer to those problems.

All scenario numbers (volumes, latencies, costs, fraud rates) are **illustrative assumptions** stated as the
interviewer's answers; they are not any company's figures. The claims below are factual and were checked.

| Claim | Where | Check |
|---|---|---|
| NSF (R01) bank-debit returns come back within 2 banking days; unauthorised returns (R05, R07, R10, R11…) up to 60 calendar days | P2 §2.6, drill | Nacha rule summaries: [Column ACH returns](https://column.com/docs/ach/returns), [Increase ACH returns](https://www.increase.com/documentation/ach-returns) |
| A returned NSF debit may be re-initiated at most twice, within 180 days; an unauthorised return needs a new authorisation | P2 §2.6, drill | [Nacha Risk and Quality Rules fact sheet](https://www.nacha.org/system/files/2019-05/Risk-and-Quality-Rules-Fact-Sheet.pdf), [Nacha risk topics](https://www.nacha.org/rules/ach-network-risk-and-enforcement-topics) |
| Point-of-sale lenders often decide and service while a partner bank is the lender of record | P1 §1.2 | Typical bank-partnership model; e.g. lender disclosures on POS-finance sites |
| A declined credit applicant must receive the principal reasons (adverse action) | P1 §1.6 | ECOA / Regulation B, 12 CFR 1002.9 |
| Card-industry security standard covers card data, not SSNs; SSNs fall under privacy and lending law | P1 §1.9 | PCI DSS scope = cardholder data; GLBA safeguards for consumer financial data |
| Card networks stand in for an issuer that does not answer in time, within configured limits, and send advices | P3 §3.4, §3.5 | Network stand-in processing (STIP) is standard issuer documentation |
| Instant payment rails (RTP since 2017, FedNow since 2023) spreading | P2 then-and-now | Public launches |
| CEL is used for sandboxed rule evaluation | P3 then-and-now | [cel.dev](https://cel.dev) |

## Recomputed numbers

- P1: 2M/month ÷ (30 × 86,400 s) = 0.77/s ≈ 0.8; ×10 = 8/s; ×4 calls = 32/s. 2M × $1 = $2M; 20 % reuse = $400k.
  2M × 50 KB = 100 GB/month; ×84 months = 8.4 TB.
- P2: 600,000 ÷ 14,400 s = 41.7/s ≈ 42. 20 % = 120,000 card; ÷100/s = 1,200 s = 20 min.
  5M × 4 = 20M lines/month; ×84 × 200 B = 336 GB ≈ 340 GB.
- P3: 4,000 × 0.15 = 600 in flight; ×3 = 1,800 reads. 4,000 × 60 × 2 % = 4,800/min; × $60 × 0.08 % = $230.40/min.
  Available credit 5,000 − 1,240 − 72 = 3,688. Ledger example 1,200 = 1,164 + 36.
