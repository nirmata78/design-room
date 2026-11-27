"""Unit tests for svg_normalizer.py (Invariants I2, I3, I4)."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from svg_normalizer import FORBIDDEN_FONTS_RE, normalize_svg  # noqa: E402


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
    assert steps == [["e:api"], ["e:db", "l:e0"]]


def test_spatial_permanence_override_viewbox(tmp_path: pathlib.Path) -> None:
    raw = tmp_path / "raw.svg"
    out = tmp_path / "frame1.svg"
    raw.write_text(SAMPLE_JOINTJS_SVG, encoding="utf-8")

    locked_vb = (50.0, 50.0, 1200.0, 400.0)
    meta = normalize_svg(raw, out, key="f1", override_viewbox=locked_vb)
    assert meta.viewbox == locked_vb
    assert 'viewBox="50.0 50.0 1200.0 400.0"' in out.read_text(encoding="utf-8")
