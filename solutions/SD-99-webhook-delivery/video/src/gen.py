import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dsl
dsl.META.update(title='SD-99 webhook delivery: slides', heading='# SD-99 Outbound webhook and partner event-delivery platform: reference solution (Staff L6/L7)', stem='webhook-delivery-reference', automark=True,
                say='API=A-P-I APIs=A-P-Is SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is HTTP=H-T-T-P SQL=S-Q-L ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E UUID=U-U-I-D ACH=A-C-H NSF=N-S-F BNPL=B-N-P-L APR=A-P-R TB=terabytes GB=gigabytes MB=megabytes KB=kilobytes UNKNOWN=unknown RETURNED=returned SETTLED=settled PENDING=pending PAID_PENDING=paid-pending SFTP=S-F-T-P HMAC=H-MAC SHA256=SHA-two-fifty-six SSRF=S-S-R-F POS=P-O-S ERP=E-R-P DNS=D-N-S URL=U-R-L URLs=U-R-Ls IP=I-P IPs=I-Ps KMS=K-M-S mTLS=mutual-T-L-S TLS=T-L-S DLQ=D-L-Q CI=C-I JSON=jason p99=P-ninety-nine p95=P-ninety-five SDK=S-D-K SDKs=S-D-Ks')
import ch0_2, ch3, ch4_5, ch5_1, ch6_7a, ch7b_9
ch5_1.attach_rejl()
n, pages = dsl.write(pathlib.Path(__file__).resolve().parent.parent)
tot = sum(dsl.words(p) for p in "CIVN")
print("slides", n, "frames", pages, "words", {p: dsl.words(p) for p in "CIVN"}, "total", tot)
print("by chapter", dsl.words_by_chapter())
