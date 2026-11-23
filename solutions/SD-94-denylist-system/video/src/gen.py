import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dsl
dsl.META.update(title='SD-94 denylist system: slides', heading='# SD-94 Blocking / denylist system: reference solution (Staff L6/L7)', stem='denylist-reference', automark=True,
                say='denylist=deny-list CIDR=C-I-D-R IPv4=I-P-v-four IPv6=I-P-v-six IP=I-P IPs=I-P-s SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is TTL=T-T-L API=A-P-I APIs=A-P-Is RAM=ram TB=terabytes MB=megabytes GB=gigabytes KB=kilobytes HTTP=H-T-T-P HTTPS=H-T-T-P-S gRPC=g-R-P-C SQL=S-Q-L CDN=C-D-N NAT=nat DDoS=dee-dos TLS=T-L-S ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E RFC=R-F-C DR=D-R UUID=U-U-I-D xDS=x-D-S Redis=Reddis fsync=F-sync ppm=P-P-M JVM=J-V-M LB=load_balancer')
import ch0_2, ch3, ch4_5, ch5_1, ch6_7a, ch7b_9
ch5_1.attach_rejl()
n, pages = dsl.write(pathlib.Path(__file__).resolve().parent.parent)
tot = sum(dsl.words(p) for p in "CIVN")
print("slides", n, "frames", pages, "words", {p: dsl.words(p) for p in "CIVN"}, "total", tot)
print("by chapter", dsl.words_by_chapter())
