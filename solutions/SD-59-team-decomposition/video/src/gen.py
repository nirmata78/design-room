import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dsl
# Compact cut (GUIDELINES §3.4): no build-cost chapter, so the recap is chapter 8 and the ribbon has no "Cost" stage.
dsl.STAGES[:] = ["Requirements", "Estimates", "Theory", "Contracts", "Design", "Challenges", "Recap"]
dsl.META.update(title="SD-59 multi-team decomposition: slides", heading="# SD-59 Multi-team decomposition and API contracts: reference solution (Principal / senior EM, compact cut)",
                stem="team-decomposition-reference", automark=True, chapters=8,
                say="SLO=S-L-O SLOs=S-L-Os SLI=S-L-I API=A-P-I APIs=A-P-Is HTTP=H-T-T-P HTTPS=H-T-T-P-S ID=I-D IDs=I-Ds EM=E-M PR=P-R PRs=P-Rs CI=C-I "
                    "ADR=A-D-R ADRs=A-D-Rs RFC=R-F-C OpenAPI=Open-A-P-I protobuf=proto-buff Pact=Pact SDK=S-D-K UTC=U-T-C p99=P-ninety-nine QA=Q-A")
import ch0_2, ch3, ch4_5, ch6_7, ch8
n, pages = dsl.write(pathlib.Path(__file__).resolve().parent.parent)
dsl.sync_theory_md(pathlib.Path(__file__).resolve().parents[2] / "SD-59_Team_Decomposition_Reference_Design.md")
import re as _re
_md = pathlib.Path(__file__).resolve().parents[2] / "SD-59_Team_Decomposition_Reference_Design.md"
if _md.exists():
    _t = _md.read_text(encoding="utf-8")
    _t = _re.sub(r"<!-- challenges:begin -->.*?<!-- challenges:end -->", lambda m: "<!-- challenges:begin -->\n" + ch6_7.md_challenges() + "\n<!-- challenges:end -->", _t, flags=_re.S)
    _md.write_text(_t, encoding="utf-8")
tot = sum(dsl.words(p) for p in "CIVN")
print("slides", n, "frames", pages, "words", {p: dsl.words(p) for p in "CIVN"}, "total", tot)
print("by chapter", dsl.words_by_chapter())
