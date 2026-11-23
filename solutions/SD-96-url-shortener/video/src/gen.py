import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dsl
dsl.META.update(title="SD-96 URL shortener: slides", heading="# SD-96 URL shortener: reference solution (Staff L6/L7)",
                stem="url-shortener-reference",
                say="URL=U-R-L URLs=U-R-Ls CDN=C-D-N CDNs=C-D-Ns TTL=T-T-L TTLs=T-T-Ls SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is API=A-P-I APIs=A-P-Is RAM=ram TB=terabytes MB=megabytes GB=gigabytes KB=kilobytes HTTP=H-T-T-P HTTPS=H-T-T-P-S SQL=S-Q-L DNS=D-N-S ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E RFC=R-F-C QR=Q-R UUID=U-U-I-D Redis=Reddis p99=P-ninety-nine p50=P-fifty base62=base-sixty-two 301=three-oh-one 302=three-oh-two 404=four-oh-four 410=four-ten 409=four-oh-nine 201=two-oh-one 422=four-twenty-two LRU=L-R-U etcd=et-see-dee PostgreSQL=postgres-Q-L ClickHouse=click-house ristretto=ris-tretto Feistel=Fy-stel Kubernetes=koo-ber-net-eez")
import ch0_2, ch3, ch4_5, ch6_7a, ch7b_9
n, pages = dsl.write(pathlib.Path(__file__).resolve().parent.parent)
tot = sum(dsl.words(p) for p in "CIVN")
print("slides", n, "frames", pages, "words", {p: dsl.words(p) for p in "CIVN"}, "total", tot)
print("by chapter", dsl.words_by_chapter())
