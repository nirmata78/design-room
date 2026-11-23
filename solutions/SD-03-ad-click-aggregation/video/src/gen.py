import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dsl
# Compact cut (GUIDELINES §3.4): no build-cost chapter, so the recap is chapter 8 and the ribbon has no "Cost" stage.
dsl.STAGES[:] = ["Requirements", "Estimates", "Theory", "API + data", "Design", "Challenges", "Recap"]
dsl.META.update(title="SD-03 event counting: slides", heading="# SD-03 Event counting and billing rollups: reference solution (Staff L6/L7, compact cut)",
                stem="ad-click-aggregation-reference", automark=True, chapters=8,
                say="SLO=S-L-O SLOs=S-L-Os SLI=S-L-I TTL=T-T-L API=A-P-I APIs=A-P-Is SDK=S-D-K SDKs=S-D-Ks TB=terabytes PB=petabytes "
                    "MB=megabytes GB=gigabytes HTTP=H-T-T-P HTTPS=H-T-T-P-S SQL=S-Q-L ID=I-D IDs=I-Ds CPU=C-P-U p99=P-ninety-nine "
                    "Kafka=Kahf-kah Kafka's=Kahf-kahs dedup=dee-dupe Flink=Flink ClickHouse=Click-House Iceberg=Iceberg GCS=G-C-S UUIDv7=U-U-I-D-version-seven RocksDB=Rocks-D-B "
                    "HyperLogLog=Hyper-Log-Log CTR=click-through_rate ack=ack acks=acks EM=E-M")
import ch0_2, ch3, ch4_5, ch6_7, ch7b_8
n, pages = dsl.write(pathlib.Path(__file__).resolve().parent.parent)
tot = sum(dsl.words(p) for p in "CIVN")
print("slides", n, "frames", pages, "words", {p: dsl.words(p) for p in "CIVN"}, "total", tot)
print("by chapter", dsl.words_by_chapter())
