# Status · Plan 03 (`c4-structurizr` skill & progressive video bake-off)

Plan: [`03-c4-structurizr-skill-and-progressive-video.md`](03-c4-structurizr-skill-and-progressive-video.md)

| Card | Unit | State | Duration / Perf | Notes & Decisions |
| :--- | :--- | :--- | :--- | :--- |
| **C3-01** | Containerized Structurizr runtime (`Dockerfile.c4` + `c4_runtime.sh`) | `done` | `3.11s` healthcheck | Built `local/structurizr-c4:playwright` over `structurizr/structurizr:preview` with offline Google OFL fonts; warm daemon `structurizr-c4-daemon` (`--shm-size=1gb`); dropped unused `Dockerfile.local-war` |
| **C3-02** | `lxml` Viewport & Progressive Normalizer + `pytest` suite | `done` | `0.06s` pytest (`2/2`) | `svg_normalizer.py`, `render_c4.py`, `c4-google-tokens.dsl`; zero forbidden fonts; organic JointJS wrapping (`metadata false`) |
| **C3-03** | Progressive Bake-Off: 4 C4 types × Techniques A, B, C (`10–18s` MP4s) | `done` | Author reviewed | Author selected **Mode A** (Master SVG + `0.35s` cross-dissolve, optional `--ghost` default `0.0`); dropped Mode B & Mode C and removed temporary bake-off/example artifacts |
| **C3-04** | Finalize `c4-structurizr` skill (`SKILL.md`, `README.md`, Grok schema) | `done` | — | Mode A locked as official default; wired for Claude CLI (`.claude/skills/`), Antigravity/Gemini (`.agents/skills/` symlink), and Grok (`schemas/tool-definition.json`) |
| **C3-05** | Multi-domain smoke verification (3 archetypes) | `done` | Verified | Microservices + outbox, Kafka/Flink streaming, Edge CDN + Redis cache all passed `render_c4.py` (`exit 0`, `0` token violations); temporary smoke outputs cleaned up |
