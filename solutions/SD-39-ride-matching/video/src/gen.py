import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dsl
# Compact cut (GUIDELINES §3.4): no build-cost chapter, so the recap is chapter 8 and the ribbon has no "Cost" stage.
dsl.STAGES[:] = ["Requirements", "Estimates", "Theory", "API + data", "Design", "Challenges", "Recap"]
dsl.META.update(title="SD-39 ride matching: slides", heading="# SD-39 Nearby drivers and ride matching: reference solution (Staff L6/L7, compact cut)",
                stem="ride-matching-reference", automark=True, chapters=8,
                say="API=A-P-I SDK=S-D-K TB=terabytes PB=petabytes GB=gigabytes HTTP=H-T-T-P HTTPS=H-T-T-P-S ID=I-D IDs=I-Ds "
                    "ETA=E-T-A H3=H-three PostGIS=Post-G-I-S SQL=S-Q-L etcd=et-see-dee gRPC=G-R-P-C NYE=New-Year's-Eve CPU=C-P-U CPUs=C-P-Us GPU=G-P-U GPUs=G-P-Us Kafka=Kahf-kah ClickHouse=Click-House GCS=G-C-S MCAP=M-cap "
                    "SHA-256=shaw-two-fifty-six DAG=dag Kueue=queue Bigtable=Big-table CI=C-I EM=E-M")
import ch0_3, ch4_5, ch6_8, ch7b_8
n, pages = dsl.write(pathlib.Path(__file__).resolve().parent.parent)
tot = sum(dsl.words(p) for p in "CIVN")
print("slides", n, "frames", pages, "words", {p: dsl.words(p) for p in "CIVN"}, "total", tot)
print("by chapter", dsl.words_by_chapter())
