import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dsl
dsl.META.update(title='SD-95 instalment loan servicing: slides', heading='# SD-95 Instalment loan servicing: ledger and collections scheduler: reference solution (Staff L6/L7)', stem='loan-servicing-reference', automark=True,
                say='API=A-P-I APIs=A-P-Is SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is HTTP=H-T-T-P SQL=S-Q-L ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E UUID=U-U-I-D ACH=A-C-H NSF=N-S-F BNPL=B-N-P-L APR=A-P-R TB=terabytes GB=gigabytes MB=megabytes KB=kilobytes UNKNOWN=unknown RETURNED=returned SETTLED=settled PENDING=pending PAID_PENDING=paid-pending SFTP=S-F-T-P')
import ch0_2, ch3, ch4_5, ch5_1, ch6_7a, ch7b_9
ch5_1.attach_rejl()
n, pages = dsl.write(pathlib.Path(__file__).resolve().parent.parent)
tot = sum(dsl.words(p) for p in "CIVN")
print("slides", n, "frames", pages, "words", {p: dsl.words(p) for p in "CIVN"}, "total", tot)
print("by chapter", dsl.words_by_chapter())
