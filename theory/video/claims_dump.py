#!/usr/bin/env python3
"""Print the slides of a part that carry arithmetic (on screen or spoken), compactly, for the claims ledger (C-NN-K)."""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import course
OPS = re.compile(r"[×÷=≈^⁰¹²³⁴⁵⁶⁷⁸⁹]|\d\s*[x*/]\s*\d|\btimes\b|\bdivided\b|\bover\b.*\d|\d+\s*%|percent")
for nn in sys.argv[1:]:
    title, recs = course.records(nn.zfill(2))
    for r in recs:
        body = [b for b in r["body"] if OPS.search(b)]
        speech = [s for c, s in r["speech"] if OPS.search(s) or re.search(r"\d", s)]
        body = [b for b in r["body"] if re.search(r"\d", b)]
        if not body and not speech: continue
        t = r["fields"][1] if len(r["fields"]) > 1 else (r["fields"][0] if r["fields"] else "")
        print(f"### [{r['section'][:4]}] {t}")
        for b in body: print("  S| " + b)
        for c, s in r["speech"]:
            if re.search(r"\d|\b(one|two|three|four|five|six|seven|eight|nine|ten|twenty|thirty|forty|fifty|hundred|thousand|million|billion|percent|half|third|quarter|times)\b", s): print(f"  {c}| " + s)
