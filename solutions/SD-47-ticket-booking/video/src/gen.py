import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dsl
dsl.META.update(title='SD-47 ticket booking: slides', heading='# SD-47 Ticket booking under contention: reference solution (Staff L6/L7)', stem='ticket-reference', automark=True,
                say='TTL=T-T-L CDN=C-D-N API=A-P-I APIs=A-P-Is SQL=S-Q-L JWT=J-W-T FIFO=fifo WAF=waff SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is HTTP=H-T-T-P HTTPS=H-T-T-P-S UUID=U-U-I-D ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E PSP=payment_provider DB=database KB=kilobytes MB=megabytes GB=gigabytes TB=terabytes TLS=T-L-S HMAC=H-mac RPC=R-P-C SSE=S-S-E AIMD=A-I-M-D NOWAIT=no_wait CAPTCHA=capcha Redis=Reddis Kafka=Kafka Lua=loo-ah T0=T_zero SLA=S-L-A RAM=ram ETA=E-T-A p99=P-ninety-nine QPS=Q-P-S WebSocket=web_socket Postgres=Postgres PostgreSQL=Postgres_S-Q-L idempotency=idem-potency idempotent=idem-potent')
import ch0_2, ch3, ch4_5, ch5_1, ch6_7a, ch7b_9
ch5_1.attach_rejl()
n, pages = dsl.write(pathlib.Path(__file__).resolve().parent.parent)
tot = sum(dsl.words(p) for p in "CIVN")
print("slides", n, "frames", pages, "words", {p: dsl.words(p) for p in "CIVN"}, "total", tot)
print("by chapter", dsl.words_by_chapter())
