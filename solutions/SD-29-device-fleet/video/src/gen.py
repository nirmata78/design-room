import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dsl
# Compact cut (GUIDELINES §3.4): no build-cost chapter, so the recap is chapter 8 and the ribbon has no "Cost" stage.
dsl.STAGES[:] = ["Requirements", "Estimates", "Theory", "API + data", "Design", "Challenges", "Recap"]
dsl.META.update(title="SD-29 device fleet: slides", heading="# SD-29 Device-fleet control plane: reference solution (Staff L6/L7, compact cut)",
                stem="device-fleet-reference", automark=True, chapters=8,
                say="API=A-P-I SDK=S-D-K TB=terabytes PB=petabytes GB=gigabytes HTTP=H-T-T-P HTTPS=H-T-T-P-S ID=I-D IDs=I-Ds "
                    "MQTT=M-Q-T-T mTLS=M-T-L-S TLS=T-L-S CDN=C-D-N EMQX=E-M-Q-X HSM=H-S-M PKI=P-K-I QoS=Q-O-S IoT=I-o-T TSDB=T-S-D-B URL=U-R-L CPU=C-P-U CPUs=C-P-Us GPU=G-P-U GPUs=G-P-Us Kafka=Kahf-kah ClickHouse=Click-House GCS=G-C-S MCAP=M-cap "
                    "SHA-256=shaw-two-fifty-six DAG=dag Kueue=queue Bigtable=Big-table CI=C-I EM=E-M")
import ch0_3, ch4_5, ch6_8, ch7b_8
n, pages = dsl.write(pathlib.Path(__file__).resolve().parent.parent)
tot = sum(dsl.words(p) for p in "CIVN")
print("slides", n, "frames", pages, "words", {p: dsl.words(p) for p in "CIVN"}, "total", tot)
print("by chapter", dsl.words_by_chapter())
