#!/usr/bin/env python3
"""md_github.py — make a reference-design .md render cleanly on GitHub (added 2026-11-25; booklet PDFs are no longer built).

  md_github.py <file.md> [--write]     lint (always) and rewrite (with --write); idempotent.

Rewrites (pandoc-only syntax → GitHub):
  ::: key|why|say|warn|load {title=".."}  →  a GitHub alert  > [!IMPORTANT|NOTE|TIP|WARNING|CAUTION]  with a bold title line
  ![cap](diagrams/x.pdf){width=..}        →  ![cap](diagrams/x.svg)   (the .svg exists: the build copies it; PDFs are not made)
  ```{=latex} … ```  and  \\newpage        →  removed
Lint (fails with exit 1):
  figure target missing · bare property codes (S1, L2 not followed by a slug) · unbalanced ::: fences · lines over 400 characters
  inside a table row is only a warning. Mermaid fences (```mermaid) are allowed: GitHub draws them.
"""
import pathlib, re, sys
ALERT = {"key": ("IMPORTANT", "Top-3 number"), "why": ("NOTE", "Why? What is it?"), "say": ("TIP", "Say it in the room"),
         "warn": ("WARNING", "Trap"), "load": ("CAUTION", "Under load")}

def convert(t):
    t = re.sub(r"```\{=latex\}.*?```\n?", "", t, flags=re.S)
    t = re.sub(r"^\\newpage\s*$", "", t, flags=re.M)
    t = re.sub(r"\]\((diagrams/[\w.-]+)\.pdf\)(\{[^}]*\})?", r"](\1.svg)", t)
    out, buf, kind, title = [], None, None, None
    for ln in t.split("\n"):
        m = re.match(r"^:::\s*(?:\{\.(\w+)(?:\s+title=\"([^\"]*)\")?\s*\}|(\w+))\s*$", ln)
        if buf is None and m:
            kind, title, buf = (m.group(1) or m.group(3)), m.group(2), []; continue
        if buf is not None and re.match(r"^:::\s*$", ln):
            a, dflt = ALERT.get(kind, ("NOTE", kind))
            out.append(f"> [!{a}]"); out.append(f"> **{title or dflt}**"); out.append(">")
            out += [("> " + b if b.strip() else ">") for b in buf]; out.append(""); buf = None; continue
        (buf if buf is not None else out).append(ln)
    return "\n".join(out)

def lint(path, t):
    errs = []
    root = path.parent
    for fig in re.findall(r"\]\((diagrams/[^)\s]+)\)", t):
        if not (root / fig).exists(): errs.append(f"missing figure {fig}")
    if len(re.findall(r"^:::", t, flags=re.M)) % 2: errs.append("unbalanced ::: fences")
    for i, ln in enumerate(t.split("\n"), 1):
        if re.search(r"(?<![\w-])(?:S[1-9]|L[1-4])(?![\w-])", re.sub(r"`[^`]*`", "", ln)) and not ln.lstrip().startswith("|--"):
            errs.append(f"line {i}: bare property code: {ln.strip()[:70]}")
    return errs

if __name__ == "__main__":
    f = pathlib.Path(sys.argv[1]); t = f.read_text(encoding="utf-8")
    if "--write" in sys.argv:
        t = convert(t); f.write_text(t, encoding="utf-8")
    errs = lint(f, t)
    print("\n".join(errs) or f"{f.name}: GitHub-ready"); sys.exit(1 if errs else 0)
