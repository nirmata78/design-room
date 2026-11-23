import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dsl
# Compact cut (GUIDELINES §3.4): no build-cost chapter, so the recap is chapter 8 and the ribbon has no "Cost" stage.
dsl.STAGES[:] = ["Requirements", "Estimates", "Theory", "API + data", "Design", "Challenges", "Recap"]
dsl.META.update(title="SD-44 payments and the double-entry ledger: slides",
                heading="# SD-44 Payment processing and the double-entry ledger: reference solution (Staff L6/L7, compact cut)",
                stem="payments-ledger-reference", automark=True, chapters=8,
                say="API=A-P-I APIs=A-P-Is SLO=S-L-O SLOs=S-L-Os SLI=S-L-I TTL=T-T-L HTTP=H-T-T-P HTTPS=H-T-T-P-S SQL=S-Q-L ID=I-D IDs=I-Ds EM=E-M "
                    "UUID=U-U-I-D CDC=C-D-C KYC=K-Y-C FX=F-X PCI=P-C-I PSP=P-S-P TB=terabytes GB=gigabytes MB=megabytes KB=kilobytes p99=P-ninety-nine "
                    "UNKNOWN=unknown AUTH_PENDING=auth-pending PostgreSQL=Postgres-Q-L Debezium=Deb-ee-zee-um Kafka=Kaf-ka TigerBeetle=Tiger-Beetle "
                    "WebFlux=Web-Flux Quarkus=Kwar-kus GraalVM=Graal-V-M JVM=J-V-M GIL=G-I-L JDBC=J-D-B-C gRPC=g-R-P-C REST=rest Rust=Rust "
                    "Spark=Spark Stripe=Stripe Adyen=Eye-den WAL=W-A-L ISO=I-S-O NOTIFY=notify")
import ch0_2, ch3, ch4_5, ch6_7, ch7b_8
n, pages = dsl.write(pathlib.Path(__file__).resolve().parent.parent)
tot = sum(dsl.words(p) for p in "CIVN")
print("slides", n, "frames", pages, "words", {p: dsl.words(p) for p in "CIVN"}, "total", tot)
print("by chapter", dsl.words_by_chapter())
