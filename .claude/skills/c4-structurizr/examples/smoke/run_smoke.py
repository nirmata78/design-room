#!/usr/bin/env python3
"""Run C3-05 multi-domain smoke verification (3 archetypes -> SVG/PNG + 10-12s Mode C MP4)."""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from progressive_video import render_mode_c  # noqa: E402
from render_c4 import run_render  # noqa: E402

DOMAINS = [
    ("smoke-01-microservices", "Smoke 1 · Transactional Microservices", "Idempotent API + PostgreSQL Ledger/Outbox + Relay Worker"),
    ("smoke-02-streaming-data", "Smoke 2 · Event-Driven Streaming Platform", "Edge Sensors -> Ingest Gateway -> Kafka Pipe -> Flink -> ClickHouse"),
    ("smoke-03-edge-caching", "Smoke 3 · Edge CDN + Multi-Tier Cache", "Global CDN -> Catalog Service -> Redis Cache -> PostgreSQL"),
]


def main() -> None:
    out_svg = HERE / "out" / "svg"
    out_mp4 = HERE / "out" / "mp4"
    out_mp4.mkdir(parents=True, exist_ok=True)

    rc, _ = run_render(HERE / "workspace.dsl", out_svg, HERE / "views.json", export_png=True)
    if rc != 0:
        raise SystemExit(f"Smoke render_c4 failed with exit code {rc}")

    for key, title, caption in DOMAINS:
        render_mode_c(out_svg / f"{key}.svg", out_mp4 / f"{key}.mp4", title=title, caption=caption, target_duration=11.0)
        print(f"Smoke OK: {out_mp4 / f'{key}.mp4'}")


if __name__ == "__main__":
    main()
