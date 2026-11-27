# Status · Plan 03 (`c4-structurizr` skill & progressive video bake-off)

Plan: [`03-c4-structurizr-skill-and-progressive-video.md`](03-c4-structurizr-skill-and-progressive-video.md)

| Card | Unit | State | Duration / Perf | Notes & Open Questions |
| :--- | :--- | :--- | :--- | :--- |
| **C3-01** | Containerized Structurizr runtime (`Dockerfile.c4` + `c4_runtime.sh`) | `done` | `3.11s` healthcheck | Built `local/structurizr-c4:playwright` over `structurizr/structurizr:preview` with offline Google OFL fonts; warm daemon `structurizr-c4-daemon` (`--shm-size=1gb`) running |
| **C3-02** | `lxml` Viewport & Progressive Normalizer + `pytest` suite | `done` | `0.06s` pytest (`2/2`) | `svg_normalizer.py`, `render_c4.py`, `c4-google-tokens.dsl`; zero forbidden fonts; organic JointJS wrapping (`metadata false`) |
| **C3-03** | Progressive Bake-Off: 4 C4 types × Techniques A, B, C (`10–18s` MP4s) | `awaiting author review` | 16 MP4s (`1920×1080`) | Generated 12 individual MP4s + 4 `2×2` side-by-side comparison reels in `.claude/skills/c4-structurizr/examples/bakeoff/out/mp4/` (gitignored) |
| **C3-04** | Finalize `c4-structurizr` skill (`SKILL.md`, `README.md`, Grok schema) | `done (provisional)` | — | `SKILL.md`, `README.md`, `schemas/tool-definition.json` committed; provisional default Mode C until author selects winner from C3-03 |
| **C3-05** | Multi-domain smoke verification (3 archetypes) | `done` | 3 MP4s (`11s` each) | Microservices + outbox, Kafka/Flink streaming, Edge CDN + Redis cache all passed `render_c4.py` (`exit 0`, `0` token violations) |

## Open Decision for Author Review
- Watch the 4 `2×2` comparison reels in `.claude/skills/c4-structurizr/examples/bakeoff/out/mp4/*_compare_2x2.mp4` (Top-Left: Mode A Cross-Dissolve, Top-Right: Mode B Native Animation, Bottom-Left: Mode C Directional Live-Draw, Bottom-Right: Static Reference) and pick the default progressive mode to lock in `SKILL.md`.
