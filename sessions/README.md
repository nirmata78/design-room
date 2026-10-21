# sessions/

Completed rounds, one directory each. Written by the interviewer at the end of the debrief
(`../CLAUDE.md` §12).

```
sessions/YYYY-MM-DD-SD-nn-slug/
├── interview.md      the workspace as it stood at the end, including §10 interviewer notes
├── scorecard.md      nine dimensions × level weights, evidence, help rungs, time breakdown, self-audit
├── report.md         the per-attempt report: verdict, scorecard, retrospective, feedback, delta, trend, next
└── report.pdf        the same, rendered by ../scripts/build-report.sh — what you re-read before the next round
```

**The most useful thing in here is the diff between two sessions on the same archetype, months
apart.** Scores drift; the §10 notes and the quotes are what actually show whether the habit changed.

`../Progress-Log.md` carries one summary row per session — that's what `surprise me` reads to pick your
weakest archetype, so it matters more than these directories for day-to-day use.

**Confidentiality.** These files persist. No internal system names, production figures, incident
details or ticket identifiers — generalise instead (`../CLAUDE.md` §12, plus any
rule in `../profile.md`). Everything in this directory except this README is gitignored. A mock is the easiest place to leak something by accident, because it feels like
scratch work and isn't.
