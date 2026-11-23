# theory/kafka-video · Kafka in system design

A six-module narrated course, built with the shared builder in `theory/video`. The review of the original agenda is in [`AGENDA.md`](AGENDA.md), and the fact check in [`VERIFY.md`](VERIFY.md).

| Path | What |
|---|---|
| `src/chNN.txt` | Slides and narration of module NN (source of truth) |
| `diagrams_kafka.py` → `svg/` | The 22 figures |
| `series.json` | Builder settings |
| `publish/meta.json` | Source of the YouTube kit |

Output stays local, in `theory/kafka-video/out/` (gitignored): `Kafka-Full.mp4` (42:44, 33 chapters), one MP4 and slide PDF per module, and the YouTube kit in `publish/`. Rebuild the kit with `publish_kit.py publish/meta.json` from that folder, after copying `publish/meta.json` there.

```bash
# from theory/video
python3 ../kafka-video/diagrams_kafka.py
python3 course.py --root ../kafka-video frames
python3 course.py --root ../kafka-video video -j3
python3 course.py --root ../kafka-video merge
```
