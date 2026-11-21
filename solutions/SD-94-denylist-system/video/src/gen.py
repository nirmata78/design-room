import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dsl
import ch0_2, ch3, ch4_5, ch6_7a, ch7b_9
n = dsl.write(pathlib.Path(__file__).resolve().parent.parent)
tot = sum(dsl.words(p) for p in "CIVN")
print("slides", n, "words", {p: dsl.words(p) for p in "CIVN"}, "total", tot)
