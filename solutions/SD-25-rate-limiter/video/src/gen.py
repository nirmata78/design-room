"""SD-25 rate limiter (distributed) — the one source of the video and the written design (issue #5 format).
    python3 gen.py      → ../video-slides.html + ../<stem>.script.md (build intermediates) and
                          ../../SD-25_Rate_Limiter_Reference_Design.md (tracked, GitHub Pages ready)
Run through the kit's ref_solution.py (deck / markdown stages); diagrams first (ref_solution.py diagrams SD-25)."""
import pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]                                            # the solution folder
sys.path.insert(0, str(ROOT.parents[1] / ".claude/skills/reference-solution/kit"))
sys.path.insert(0, str(HERE))
import dsl  # noqa: E402

dsl.META.update(
    title="SD-25 rate limiter: slides", stem="rate-limiter-reference",
    heading="# SD-25 Rate limiter (distributed): reference solution (Staff L6/L7)",
    svg=str(ROOT / "video" / "svg"),
    say="SLO=S-L-O SLI=S-L-I TTL=T-T-L API=A-P-I APIs=A-P-Is HTTPS=H-T-T-P-S SQL=S-Q-L ID=I-D IDs=I-Ds CPU=C-P-U "
        "p99=P-ninety-nine Kafka=Kahf-kah ClickHouse=Click-House gRPC=G-R-P-C RESP=R-E-S-P Lua=Loo-ah "
        "PostgreSQL=Postgres-Q-L etcd=et-see-dee DDoS=D-dos LB=load-balancer 429=four-twenty-nine 429s=four-twenty-nines "
        "202=two-oh-two 503=five-oh-three V1=version_one V2=version_two V3=version_three V4=version_four µs=microseconds syncer=sinker cron=kron",
    md=dict(title="SD-25 · Rate limiter (distributed) — reference design",
            description="Per-customer quotas enforced across 500 API servers in three regions in under a millisecond: token buckets in "
                        "memory, leases that follow demand, a failure mode per limit — a Staff-level system design answer, driven by "
                        "interviewer challenges.",
            question_id="SD-25", level="Staff L6/L7", tags=["rate-limiting", "token-bucket", "leases", "static-stability", "c4"],
            lede="A rate limiter sits on every request, so its latency and availability matter more than its accuracy. Decide in "
                 "memory from a token bucket, lease the global budget to where the traffic lands, and know exactly how wrong you can be."))
dsl.props(S1="bounded-overshoot", S2="never-the-outage", S3="no-false-limits", L1="change-in-10s", L2="decide-in-1ms")

import ch1, ch2, ch3, ch4, ch5_6  # noqa: E401,E402,F401

n, pages = dsl.write(ROOT / "video")
md = dsl.write_reference_markdown(ROOT / "SD-25_Rate_Limiter_Reference_Design.md")
tot = sum(dsl.words(p) for p in "CIVN")
print("slides", n, "frames", pages, "words", {p: dsl.words(p) for p in "CIVN"}, "total", tot, "≈ min", round(tot * 0.505 / 60, 1))
print("by chapter", dsl.words_by_chapter())
print("markdown", md.name)
