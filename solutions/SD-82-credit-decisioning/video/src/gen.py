import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dsl
dsl.META.update(title='SD-82 credit decisioning: slides', heading='# SD-82 Instant credit at the point of sale: reference solution (Staff L6/L7)', stem='credit-decisioning-reference', automark=True,
                say='POS=P-O-S SSN=S-S-N APR=A-P-R API=A-P-I APIs=A-P-Is ID=I-D IDs=I-Ds SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is SQL=S-Q-L EM=E-M AUX=aux QR=Q-R KB=kilobytes GB=gigabytes TB=terabytes p95=P-ninety-five p99=P-ninety-nine p50=P-fifty C4=C-four CI=C-I')
import ch0_2, ch3, ch4_5, ch5_1, ch6_7a, ch7b_9
ch5_1.attach_rejl()
n, pages = dsl.write(pathlib.Path(__file__).resolve().parent.parent)
tot = sum(dsl.words(p) for p in "CIVN")
print("slides", n, "frames", pages, "words", {p: dsl.words(p) for p in "CIVN"}, "total", tot)
print("by chapter", dsl.words_by_chapter())
