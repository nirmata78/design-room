#!/usr/bin/env python3
"""Recompute every derived claim in claims/pNN.md (C-NN-K) and fill the "Recomputed" column.

A ledger row:  | Slide | Claim | Kind | Check | Stated | Recomputed |
Kind is derived, published, assumption or given. For a derived row, Check is a Python expression in backticks
(math is imported) and Stated is the number the slide or narration gives; a trailing "±N%" in Check sets the
tolerance (default 10%, because the course rounds on purpose). Exit status 1 if any derived row is off.

  claims_check.py [NN …] [--write]"""
import math, pathlib, re, sys
HERE = pathlib.Path(__file__).resolve().parent / "claims"

def num(s):
    s = s.replace(",", "").replace("−", "-").strip()
    m = re.search(r"-?\d+(\.\d+)?(e-?\d+)?", s)
    return float(m.group(0)) if m else None

def check(path, write):
    out, bad, n = [], [], 0
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("|") else []
        if len(cells) == 6 and cells[2] == "derived":
            m = re.match(r"`(.+?)`\s*(?:±\s*([\d.]+)\s*%)?$", cells[3])
            if not m: bad.append(f"{path.name}: no expression: {cells[1][:60]}"); out.append(line); continue
            got = eval(m.group(1), {"math": math, **{k: getattr(math, k) for k in ("log", "log2", "log10", "sqrt", "exp", "ceil", "floor")}})
            want, tol = num(cells[4]), float(m.group(2) or 10) / 100
            ok = want is not None and (abs(got - want) <= tol * max(abs(want), abs(got)) or abs(got - want) < 1e-9)
            n += 1
            shown = f"{got:.4g}" if abs(got) < 1e6 else f"{got:.3e}"
            cells[5] = shown + ("" if ok else " **OFF**")
            if not ok: bad.append(f"{path.name}: {cells[0]} · {cells[1][:60]}: stated {cells[4]}, recomputed {shown}")
            line = "| " + " | ".join(cells) + " |"
        out.append(line)
    if write: path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return n, bad

if __name__ == "__main__":
    write = "--write" in sys.argv
    want = [a.zfill(2) for a in sys.argv[1:] if a.isdigit()]
    total, allbad = 0, []
    for p in sorted(HERE.glob("p*.md")):
        if want and p.stem[1:] not in want: continue
        n, bad = check(p, write); total += n; allbad += bad
        print(f"{p.name}: {n} derived rows, {len(bad)} off")
    for b in allbad: print("  " + b)
    sys.exit(1 if allbad else 0)
