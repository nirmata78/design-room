import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dsl
dsl.META.update(title="SD-08 news feed: slides", heading="# SD-08 News feed / home timeline: reference solution (Staff L6/L7)",
                stem="news-feed-reference", automark=True,
                say="SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is TTL=T-T-L API=A-P-I APIs=A-P-Is RAM=ram TB=terabytes MB=megabytes GB=gigabytes KB=kilobytes HTTP=H-T-T-P SQL=S-Q-L CDN=C-D-N CDC=C-D-C DAU=D-A-U ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E RFC=R-F-C Redis=Reddis MVP=M-V-P QPS=Q-P-S CPU=C-P-U p99=P-ninety-nine p95=P-ninety-five p50=P-fifty Kafka=Kaf-ka Cassandra=Cass-andra")
import ch0_2, ch3, ch4_5, ch5_1, ch6_7a, ch7b_9
ch5_1.attach_rejl()
n, pages = dsl.write(pathlib.Path(__file__).resolve().parent.parent)
tot = sum(dsl.words(p) for p in "CIVN")
print("slides", n, "frames", pages, "words", {p: dsl.words(p) for p in "CIVN"}, "total", tot)
print("by chapter", dsl.words_by_chapter())
