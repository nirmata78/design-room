import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dsl
dsl.META.update(title='SD-77 card authorisation: slides', heading='# SD-77 Card authorisation and issuer processing: reference solution (Staff L6/L7)', stem='card-authorisation-reference', automark=True,
                say='API=A-P-I APIs=A-P-Is SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E ISO=I-S-O MCC=M-C-C PAN=P-A-N BIN=B-I-N CEL=C-E-L TB=terabytes GB=gigabytes MB=megabytes KB=kilobytes p99=P-ninety-nine p50=P-fifty TLS=T-L-S YAML=yammel')
import ch0_2, ch3, ch4_5, ch5_1, ch6_7a, ch7b_9
ch5_1.attach_rejl()
n, pages = dsl.write(pathlib.Path(__file__).resolve().parent.parent)
tot = sum(dsl.words(p) for p in "CIVN")
print("slides", n, "frames", pages, "words", {p: dsl.words(p) for p in "CIVN"}, "total", tot)
print("by chapter", dsl.words_by_chapter())
