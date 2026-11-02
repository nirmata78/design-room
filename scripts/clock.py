#!/usr/bin/env python3
"""The round clock: real wall-clock time, phase budgets, alarms. Certifying sessions only.

    scripts/clock.py start [--pace typing-adjusted|realtime|hour|<N>] [--mode full|hld|framing|wrap|review]
    scripts/clock.py status            # elapsed, current phase by budget, time left — one line
    scripts/clock.py schedule          # the whole plan with wall-clock times
    scripts/clock.py watch [--notify]  # live ticking display for the candidate's second terminal
    scripts/clock.py wait              # block until the next alarm, print it, exit (interviewer, in background)
    scripts/clock.py mark <label>      # log an actual phase transition (for "where the time went")
    scripts/clock.py pause | resume | stop

State lives in .clock.json at the repo root (gitignored). Paused time is excluded from elapsed.
Stdlib only. Practice sessions do not use the clock (CLAUDE.md §16).
"""
import argparse
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE = ROOT / ".clock.json"

# Phase budgets in minutes (CLAUDE.md §4.1). "slack" is not a phase; it pads the total.
FULL = {
    "realtime":        [("Framing", 1), ("P1 Requirements & scope", 8), ("P2 Estimation", 6),
                        ("P3 High-level design", 12), ("P4 Deep dives", 15), ("P5 Wrap", 6), ("Slack", 2)],
    "typing-adjusted": [("Framing", 1), ("P1 Requirements & scope", 12), ("P2 Estimation", 9),
                        ("P3 High-level design", 18), ("P4 Deep dives", 22), ("P5 Wrap", 9), ("Slack", 4)],
    # the hour-long requirement-drip round: ~3 min intro, 55 of design, ~3 for their question
    "hour":            [("Framing", 3), ("P1 Requirements & scope", 5), ("P2 Estimation", 4),
                        ("P3 API, data model & HLD", 16), ("P4 Deep dives + new requirements", 20),
                        ("P5 Wrap + summary", 9), ("Their question", 3)],
}
OTHER_MODES = {
    "framing": [("Prompt 1: scope + estimate", 5), ("Prompt 2: scope + estimate", 5), ("Prompt 3: scope + estimate", 5)],
    "hld":     [("Framing", 1), ("P1 Requirements & scope", 8), ("P2 Estimation", 6), ("P3 High-level design", 15)],
    "wrap":    [("P5 Failure, SLOs, cost, summary", 12)],
    "review":  [("Read the design", 4), ("Critique", 12), ("Prioritise + summarise", 4)],
}
WARN_BEFORE_END = 10 * 60  # the T−10 announcement (CLAUDE.md §4.2)


def load():
    if not STATE.exists():
        sys.exit("clock: not started — run `scripts/clock.py start`")
    return json.loads(STATE.read_text())


def save(s):
    STATE.write_text(json.dumps(s, indent=2))


def hms(sec):
    sec = int(max(0, sec))
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


def ms(sec):
    sec = int(max(0, sec))
    return f"{sec // 60}:{sec % 60:02d}"


def plan(pace, mode):
    if mode != "full":
        return OTHER_MODES[mode]
    if pace in FULL:
        return FULL[pace]
    total = int(pace)  # a custom total: scale the typing-adjusted shape
    base = FULL["typing-adjusted"]
    scale = total / sum(m for _, m in base)
    phases = [(n, max(1, round(m * scale))) for n, m in base]
    drift = total - sum(m for _, m in phases)
    name, m = phases[-1]
    phases[-1] = (name, max(1, m + drift))
    return phases


def elapsed(s, now=None):
    now = now or time.time()
    paused = s["paused_total"] + ((now - s["paused_at"]) if s.get("paused_at") else 0)
    return now - s["start"] - paused


def where(s, e):
    """(index, name, seconds left in phase) for elapsed e; index == len when over time."""
    t = 0
    for i, (name, m) in enumerate(s["phases"]):
        t += m * 60
        if e < t:
            return i, name, t - e
    return len(s["phases"]), "OVER TIME", 0


def alarms(s):
    """Every alarm in elapsed seconds: each phase boundary, T−10, the end."""
    out, t = [], 0
    total = s["total"] * 60
    for i, (name, m) in enumerate(s["phases"]):
        t += m * 60
        nxt = s["phases"][i + 1][0] if i + 1 < len(s["phases"]) else None
        if nxt:
            out.append((t, f"PHASE  budget for '{name}' is spent → '{nxt}'"))
    if total > WARN_BEFORE_END + 60:
        out.append((total - WARN_BEFORE_END, "T-10   ten minutes left — announce it once"))
    out.append((total, "END    time is up — stop and go to the debrief"))
    return sorted(set(out))


def line(s):
    e = elapsed(s)
    i, name, left = where(s, e)
    total = s["total"] * 60
    tag = " [PAUSED]" if s.get("paused_at") else ""
    if i >= len(s["phases"]):
        return f"{hms(e)} elapsed · OVER TIME by {ms(e - total)}{tag}"
    return (f"{hms(e)} / {ms(total)} · {name} · {ms(left)} left in phase · "
            f"{ms(total - e)} left in round{tag}")


def notify(text):
    if sys.platform == "darwin":
        subprocess.run(["osascript", "-e", f'display notification "{text}" with title "design-room clock"'],
                       check=False, capture_output=True)


def cmd_start(a):
    if STATE.exists() and not a.force:
        s = json.loads(STATE.read_text())
        if not s.get("stopped"):
            sys.exit("clock: a round is already running — `stop` it or pass --force")
    phases = plan(a.pace, a.mode)
    now = time.time()
    s = {"start": now, "pace": a.pace, "mode": a.mode, "phases": phases,
         "total": sum(m for _, m in phases), "paused_total": 0, "paused_at": None,
         "marks": [], "stopped": None}
    save(s)
    print(f"START {time.strftime('%H:%M:%S', time.localtime(now))} · {a.mode} · {a.pace} · {s['total']} min")
    cmd_schedule(None)


def cmd_schedule(_):
    s = load()
    t = s["start"]
    print(f"{'phase':<38}{'min':>4}  {'from':>8}  {'to':>8}")
    for name, m in s["phases"]:
        end = t + m * 60
        print(f"{name:<38}{m:>4}  {time.strftime('%H:%M', time.localtime(t)):>8}  "
              f"{time.strftime('%H:%M', time.localtime(end)):>8}")
        t = end
    if s["paused_total"]:
        print(f"(wall-clock times above exclude {ms(s['paused_total'])} of pauses)")


def cmd_status(_):
    print(line(load()))


def cmd_watch(a):
    fired = set()
    try:
        while True:
            s = load()
            e = elapsed(s)
            for at, msg in alarms(s):
                if e >= at and at not in fired:
                    fired.add(at)
                    if at > e - 2:  # only ring for alarms crossed while watching
                        sys.stdout.write("\a")
                        print(f"\r{' ' * 100}\r⏰ {msg}")
                        if a.notify:
                            notify(msg.split(None, 1)[1])
            sys.stdout.write(f"\r⏱  {line(s)}   ")
            sys.stdout.flush()
            if s.get("stopped"):
                print("\nclock stopped")
                return
            time.sleep(1)
    except KeyboardInterrupt:
        print()


def cmd_wait(_):
    """Sleep until the next alarm, print it and exit — run in the background by the interviewer."""
    while True:
        s = load()
        if s.get("stopped"):
            print("clock stopped")
            return
        e = elapsed(s)
        upcoming = [(at, msg) for at, msg in alarms(s) if at > e + 0.5]
        if not upcoming:
            print(f"END    over time · {line(s)}")
            return
        at, msg = upcoming[0]
        if s.get("paused_at"):
            time.sleep(5)
            continue
        time.sleep(min(at - e, 30))  # re-check: a pause or resume may move the alarm
        s = load()
        if not s.get("paused_at") and elapsed(s) >= at:
            print(f"{time.strftime('%H:%M:%S')}  {hms(at)}  {msg}")
            print(line(s))
            return


def cmd_mark(a):
    s = load()
    e = elapsed(s)
    s["marks"].append([round(e), a.label])
    save(s)
    print(f"{time.strftime('%H:%M:%S')}  {hms(e)}  {a.label}")


def cmd_pause(_):
    s = load()
    if not s.get("paused_at"):
        s["paused_at"] = time.time()
        save(s)
    print(line(s))


def cmd_resume(_):
    s = load()
    if s.get("paused_at"):
        s["paused_total"] += time.time() - s["paused_at"]
        s["paused_at"] = None
        save(s)
    print(line(s))


def cmd_stop(_):
    s = load()
    if s.get("paused_at"):
        cmd_resume(None)
        s = load()
    s["stopped"] = time.time()
    save(s)
    e = elapsed(s)
    print(f"STOP {time.strftime('%H:%M:%S')} · {hms(e)} elapsed of {s['total']} min"
          f"{' · OVER by ' + ms(e - s['total'] * 60) if e > s['total'] * 60 else ''}")
    prev = 0
    for at, label in s["marks"]:
        print(f"  {hms(at)}  (+{ms(at - prev)})  {label}")
        prev = at


def main():
    ap = argparse.ArgumentParser(description="design-room round clock")
    sub = ap.add_subparsers(dest="cmd", required=True)
    st = sub.add_parser("start")
    st.add_argument("--pace", default="typing-adjusted",
                    help="realtime (50) · typing-adjusted (75) · hour (60) · or total minutes")
    st.add_argument("--mode", default="full", choices=["full", *OTHER_MODES])
    st.add_argument("--force", action="store_true")
    w = sub.add_parser("watch")
    w.add_argument("--notify", action="store_true", help="macOS notification on every alarm")
    m = sub.add_parser("mark")
    m.add_argument("label")
    for c in ("status", "schedule", "wait", "pause", "resume", "stop"):
        sub.add_parser(c)
    a = ap.parse_args()
    if a.cmd == "start" and a.pace not in FULL and not a.pace.isdigit():
        ap.error(f"unknown pace {a.pace!r}")
    globals()[f"cmd_{a.cmd}"](a)


if __name__ == "__main__":
    main()
