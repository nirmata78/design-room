"""Unit tests for svg_normalizer.py (Invariants I2, I3, I4) and the views.json overlays (issue #5)."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from svg_normalizer import FORBIDDEN_FONTS_RE, Overlay, normalize_svg  # noqa: E402


SAMPLE_JOINTJS_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="2400" height="1600" style="width: 2400px; height: 1600px; background: #ffffff" viewBox="0 0 2400 1600">
  <g joint-selector="layers">
    <g id="j_1" transform="translate(100,100)">
      <rect x="0" y="0" width="420" height="240" rx="12" fill="#8AB4F8" stroke="#1967D2" stroke-width="2"/>
      <text font-size="34px" font-weight="bold" font-family="Tahoma, Verdana, Helvetica, Arial" x="210" y="80" text-anchor="middle">Servicing API</text>
      <text font-size="17px" font-family="Tahoma, Verdana, Helvetica, Arial" x="210" y="115" text-anchor="middle">[Container: Go]</text>
    </g>
    <g id="j_2" transform="translate(760,100)">
      <rect x="0" y="0" width="420" height="240" rx="12" fill="#188038" stroke="#FBBC05" stroke-width="6"/>
      <text font-size="34px" font-weight="bold" font-family="Tahoma, Verdana, Helvetica, Arial" x="210" y="80" text-anchor="middle">Servicing DB</text>
      <text font-size="17px" font-family="Tahoma, Verdana, Helvetica, Arial" x="210" y="115" text-anchor="middle">[Container: PostgreSQL]</text>
    </g>
    <g id="j_3" transform="translate(0,0)">
      <path joint-selector="line" d="M 520 220 L 760 220" stroke="#202124" stroke-width="3" marker-end="url(#arr)"/>
      <text font-size="24px" font-family="Tahoma, Verdana, Helvetica, Arial" x="640" y="205" text-anchor="middle">one commit</text>
    </g>
    <g id="j_99" transform="translate(20,1500)">
      <text font-size="36px" font-family="Tahoma, Verdana, Helvetica, Arial">Container View: Loan Servicing</text>
    </g>
    <g id="j_100" transform="translate(20,1545)">
      <text font-size="20px" font-family="Tahoma, Verdana, Helvetica, Arial">Friday, November 27, 2026 at 1:30 PM CET</text>
    </g>
  </g>
</svg>"""


def test_normalizer_enforces_tokens_crop_and_legibility(tmp_path: pathlib.Path) -> None:
    raw = tmp_path / "raw.svg"
    out = tmp_path / "out.svg"
    raw.write_text(SAMPLE_JOINTJS_SVG, encoding="utf-8")

    meta = normalize_svg(
        raw,
        out,
        key="sample",
        slot="full",
        alias_by_title={"Servicing API": "api", "Servicing DB": "db"},
        reveal_steps=["api", "db"],
    )

    svg = out.read_text(encoding="utf-8")
    # Footer stripped
    assert "Container View:" not in svg
    assert "Friday, November 27" not in svg
    # Zero forbidden fonts (I4)
    assert meta.forbidden_fonts_found == []
    assert not FORBIDDEN_FONTS_RE.search(svg)
    assert "Inter, Roboto, sans-serif" in svg
    # Tight-cropped responsive viewBox
    assert 'width="2400"' not in svg
    assert meta.viewbox[2] < 1300
    # 1080p legibility gate (I3)
    assert meta.legibility_ok is True
    assert meta.min_rendered_1080p_px >= 18.0
    # NEW pill injected on #FBBC05 stroke-width=6 card
    assert ">NEW<" in svg
    # Progressive steps sidecar (I2)
    steps = json.loads(out.with_suffix(".steps.json").read_text(encoding="utf-8"))
    assert steps == [["e:api"], ["e:db", "p:new:db", "l:e0"]]


def test_spatial_permanence_override_viewbox(tmp_path: pathlib.Path) -> None:
    raw = tmp_path / "raw.svg"
    out = tmp_path / "frame1.svg"
    raw.write_text(SAMPLE_JOINTJS_SVG, encoding="utf-8")

    locked_vb = (50.0, 50.0, 1200.0, 400.0)
    meta = normalize_svg(raw, out, key="f1", override_viewbox=locked_vb)
    assert meta.viewbox == locked_vb
    assert 'viewBox="50.0 50.0 1200.0 400.0"' in out.read_text(encoding="utf-8")



# ── overlays: a three-box pipeline A -> B -> C, laid out like a Structurizr export ──
def _box(i: int, x: int, title: str) -> str:
    return (f'<g id="j_{i}" transform="translate({x},100)"><rect width="400" height="220" rx="20" fill="#8AB4F8" stroke="#1967D2" '
            f'stroke-width="2"/><text font-size="42px" font-weight="bold" font-family="Tahoma" x="200" y="40">{title}</text>'
            f'<text font-size="30px" font-family="Tahoma" x="200" y="110">A description.</text>'
            f'<text font-size="21px" display="none" style="display: block;" x="200" y="40"><tspan style="fill-opacity: 0;">-</tspan></text></g>')


def _edge(i: int, x0: int, x1: int, label: str) -> str:
    return (f'<g id="j_{i}"><path joint-selector="line" d="M {x0} 210 L {x1} 210" stroke="#202124" stroke-width="3"/>'
            f'<g label-idx="0" transform="matrix(1,0,0,1,{(x0 + x1) // 2},210)"><rect x="-80" y="-24" width="160" height="48" fill="#fff"/>'
            f'<text font-size="40px">{label}</text></g></g>')


PIPE = ('<svg xmlns="http://www.w3.org/2000/svg" width="2400" height="1200" viewBox="0 0 2400 1200"><g joint-selector="layers">'
        + _box(1, 100, "Alpha") + _box(2, 800, "Beta") + _box(3, 1500, "Gamma")
        + _edge(4, 500, 800, "calls") + _edge(5, 1200, 1500, "writes") + "</g></svg>")
ALIASES = {"Alpha": "a", "Beta": "b", "Gamma": "c"}


def _render(tmp_path: pathlib.Path, name: str, **kw):
    raw = tmp_path / "pipe.svg"
    raw.write_text(PIPE, encoding="utf-8")
    out = tmp_path / f"{name}.svg"
    meta = normalize_svg(raw, out, key=name, alias_by_title=ALIASES, **kw)
    steps = json.loads(out.with_suffix(".steps.json").read_text(encoding="utf-8"))
    return meta, out.read_text(encoding="utf-8"), steps


def test_invisible_placeholder_text_is_not_measured(tmp_path: pathlib.Path) -> None:
    meta, _, _ = _render(tmp_path, "plain")
    assert meta.min_font_svg_px == 30.0          # the 21px "-" placeholder Structurizr leaves in every box is ignored
    assert meta.viewbox == (72.0, -12.0, 1856.0, 360.0)  # shapes only (text never inflates the box) + pill headroom


def test_hide_cuts_a_version_and_keeps_positions(tmp_path: pathlib.Path) -> None:
    master, _, _ = _render(tmp_path, "master")
    meta, svg, steps = _render(tmp_path, "v1", overlay=Overlay(hide=["c"]), override_viewbox=master.viewbox)
    assert "Gamma" not in svg and "writes" not in svg      # the box and every edge touching it are gone
    assert meta.viewbox == master.viewbox                  # locked: Alpha and Beta stay where they were
    assert 'transform="translate(800,100)"' in svg
    assert steps == [["e:a"], ["e:b", "l:e0"]]


def test_new_reveals_only_new_boxes_with_their_edges(tmp_path: pathlib.Path) -> None:
    _, svg, steps = _render(tmp_path, "v2", overlay=Overlay(new=["c"]))
    assert ">NEW<" in svg and "#FBBC05" in svg
    assert steps == [["e:c", "p:new:c", "l:e1"]]           # a and b are carried: visible from frame 0


def test_status_pills_and_badges(tmp_path: pathlib.Path) -> None:
    meta, svg, steps = _render(tmp_path, "ch1", overlay=Overlay(breaks=["b"], fix=["c"], badges={"a": "M1 · Dedup"}))
    assert ">BREAKS<" in svg and ">FIX<" in svg and ">M1 · Dedup<" in svg
    assert 'stroke="#EA4335"' in svg and 'stroke="#34A853"' in svg
    assert steps == [["p:fix:c"], ["p:breaks:b"], ["p:badge:a"]]
    assert meta.full is False


def test_keep_crop_zooms_and_dims(tmp_path: pathlib.Path) -> None:
    plain, _, _ = _render(tmp_path, "plain")
    meta, svg, _ = _render(tmp_path, "zoom", overlay=Overlay(keep=["b", "c"], crop=True, focus=["c"]))
    assert meta.viewbox[2] < plain.viewbox[2]               # cropped to Beta and Gamma
    assert meta.viewbox[0] > 700
    assert "Alpha" not in svg and "calls" not in svg        # a zoom drops what it does not keep
    _, dimmed, _ = _render(tmp_path, "dim", overlay=Overlay(keep=["b", "c"]))
    assert 'opacity="0.25"' in dimmed                       # without crop, the rest is dimmed instead
    assert meta.scale_1080p > plain.scale_1080p


def test_flow_numbers_one_arrow_per_step(tmp_path: pathlib.Path) -> None:
    _, svg, steps = _render(tmp_path, "flow", overlay=Overlay(flow=["a->b", "b->c"]))
    assert steps == [["f:1"], ["f:2"]]
    assert 'data-k="f:1"' in svg and 'data-k="f:2"' in svg and "#1967D2" in svg


def test_unknown_alias_is_reported(tmp_path: pathlib.Path) -> None:
    meta, _, _ = _render(tmp_path, "bad", overlay=Overlay(breaks=["zeta"], flow=["a->c"]))
    assert meta.unknown_aliases == ["a->c", "zeta"]


def test_legibility_gate_uses_min_px(tmp_path: pathlib.Path) -> None:
    meta, _, _ = _render(tmp_path, "tiny", slot="split")
    assert meta.legibility_ok is False                      # 1856 wide into 820 px: 30 px text renders at ~13 px
    meta2, _, _ = _render(tmp_path, "md", slot="split", min_px=0)
    assert meta2.legibility_ok is True                      # Markdown-only views skip the 1080p gate


def test_ids_are_namespaced_per_view(tmp_path: pathlib.Path) -> None:
    raw = tmp_path / "ids.svg"
    raw.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><marker id="m1"/></defs>'
                   '<g id="j_1" transform="translate(10,10)"><rect width="40" height="20" fill="#fff" stroke="#000"/>'
                   '<text font-weight="bold" font-size="20px">Box</text></g>'
                   '<path d="M 0 0 L 9 9" marker-end="url(#m1)" stroke="#000"/></svg>', encoding="utf-8")
    out = tmp_path / "v.svg"
    normalize_svg(raw, out, key="flow-live")
    svg = out.read_text(encoding="utf-8")
    assert 'id="flow-live--m1"' in svg and 'url(#flow-live--m1)' in svg and 'id="m1"' not in svg
