"""SD-03 event counting and billing rollups — the one source of the video and the written design (issue #5 format).
    python3 gen.py      → ../video-slides.html + ../<stem>.script.md (build intermediates) and
                          ../../SD-03_Ad_Click_Aggregation_Reference_Design.md (tracked, GitHub Pages ready)
Run through the kit's ref_solution.py (deck / markdown stages); diagrams first (ref_solution.py diagrams SD-03)."""
import pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]                                            # the solution folder
sys.path.insert(0, str(ROOT.parents[1] / ".claude/skills/reference-solution/kit"))
sys.path.insert(0, str(HERE))
import dsl  # noqa: E402

dsl.META.update(
    title="SD-03 event counting: slides", stem="ad-click-aggregation-reference",
    heading="# SD-03 Event counting and billing rollups: reference solution (Staff L6/L7)",
    svg=str(ROOT / "video" / "svg"),
    say="SLO=S-L-O SLOs=S-L-Os TTL=T-T-L API=A-P-I SDK=S-D-K SDKs=S-D-Ks TB=terabytes PB=petabytes GB=gigabytes "
        "HTTPS=H-T-T-P-S SQL=S-Q-L ID=I-D IDs=I-Ds CPU=C-P-U p99=P-ninety-nine Kafka=Kahf-kah dedup=dee-dupe "
        "ClickHouse=Click-House UUIDv7=U-U-I-D-version-seven RocksDB=Rocks-D-B HyperLogLog=Hyper-Log-Log 202=two-oh-two "
        "V1=version_one V2=version_two V3=version_three",
    md=dict(title="SD-03 · Event counting and billing rollups — reference design",
            description="Count ad impressions and clicks once: live within 10 seconds for the dashboard, exact, versioned and "
                        "reproducible for the bill — a Staff-level system design answer, driven by interviewer challenges.",
            question_id="SD-03", level="Staff L6/L7", tags=["stream-processing", "exactly-once", "event-time", "billing", "c4"],
            lede="Count once, from one log, with one piece of code run twice: fast and provisional for the dashboard, exact and "
                 "pinned for the bill. Never increment a number you can recompute — replace it."))
dsl.props(S1="count-once", S2="right-hour-right-version", S3="reproducible", L1="final-in-48h", L2="fresh-in-10s")

import ch1, ch2, ch3, ch4, ch5_6  # noqa: E401,E402,F401

n, pages = dsl.write(ROOT / "video")
md = dsl.write_reference_markdown(ROOT / "SD-03_Ad_Click_Aggregation_Reference_Design.md")
tot = sum(dsl.words(p) for p in "CIVN")
print("slides", n, "frames", pages, "words", {p: dsl.words(p) for p in "CIVN"}, "total", tot, "≈ min", round(tot * 0.505 / 60, 1))   # 0.505 s a word all-in, measured on this video
print("by chapter", dsl.words_by_chapter())
print("markdown", md.name)
