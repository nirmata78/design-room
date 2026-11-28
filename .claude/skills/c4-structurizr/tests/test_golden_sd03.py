"""Style lock (2026-11-28): the SD-03 diagrams are the approved look of every C4 picture the reference-solution skill draws.
This test re-draws them from a frozen `structurizr export -f json` of SD-03 (no Docker) and requires the SVG bytes to match.

If you change c4draw.py on purpose, look at the new PNGs first, then refresh the golden files:
    C4_SAVE_JSON=$PWD/.claude/skills/c4-structurizr/tests/golden/sd03/workspace.json \\
      python3 .claude/skills/c4-structurizr/scripts/render_c4.py --dsl solutions/SD-03-ad-click-aggregation/workspace.dsl \\
      --spec solutions/SD-03-ad-click-aggregation/views.json --out solutions/SD-03-ad-click-aggregation/video/svg
    cp solutions/SD-03-ad-click-aggregation/views.json .claude/skills/c4-structurizr/tests/golden/sd03/
    for k in <the keys below>; do cp solutions/SD-03-ad-click-aggregation/video/svg/$k.svg .claude/skills/c4-structurizr/tests/golden/sd03/; done
"""
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from c4draw import Model, render_view  # noqa: E402
from render_c4 import WorkspaceSpec, native_specs  # noqa: E402

GOLDEN = HERE / "golden" / "sd03"
KEYS = sorted(p.stem for p in GOLDEN.glob("*.svg"))


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    out = tmp_path_factory.mktemp("sd03")
    model = Model(json.loads((GOLDEN / "workspace.json").read_text(encoding="utf-8")))
    spec = WorkspaceSpec.model_validate_json((GOLDEN / "views.json").read_text(encoding="utf-8"))
    metas = {}
    for key, _vspec, sp in native_specs(model, spec):
        if key in KEYS:
            metas[key] = render_view(model, sp, out)
    return out, metas


def test_golden_set_is_complete():
    assert {"c4-context", "containers", "comp-stream", "comp-billing"} <= set(KEYS)


@pytest.mark.parametrize("key", KEYS)
def test_svg_matches_approved_look(rendered, key):
    out, metas = rendered
    meta, overflow = metas[key]
    assert meta.legibility_ok and not overflow and not meta.unknown_aliases
    assert (out / f"{key}.svg").read_text(encoding="utf-8") == (GOLDEN / f"{key}.svg").read_text(encoding="utf-8"), (
        f"{key}.svg drifted from the approved SD-03 look; see this file's docstring")
