"""Unit tests for c4draw.py, the native renderer (2026-11-28): grid layout, shapes, overlays, reveal plans and the 1080p gate.
No Docker: the workspace JSON is what `structurizr export -f json` writes, reduced to the fields the drawer reads."""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from c4draw import Model, Spec, render_view  # noqa: E402
from svg_normalizer import Overlay  # noqa: E402


def _el(i, ident, name, desc, tech="", tags="Element", children=None, key="containers"):
    e = {"id": str(i), "name": name, "description": desc, "tags": tags, "properties": {"structurizr.dsl.identifier": ident}}
    if tech:
        e["technology"] = tech
    if children:
        e[key] = children
    return e


def _rel(i, s, d, desc, tech=""):
    r = {"id": str(i), "sourceId": str(s), "destinationId": str(d), "description": desc, "tags": "Relationship"}
    if tech:
        r["technology"] = tech
    return r


def workspace() -> dict:
    user = _el(1, "user", "Shopper", "Buys things.", tags="Element,Person")
    user["relationships"] = [_rel(20, 1, 3, "Uses", "HTTPS"), _rel(21, 1, 4, "Browses", "HTTPS")]
    pay = _el(2, "pay", "Payments", "Card network.", tags="Element,Software System,External")
    api = _el(4, "shop.api", "Shop API", "Orders and carts.", "Go", "Element,Container,App")
    api["relationships"] = [_rel(22, 4, 5, "Writes orders", "SQL"), _rel(23, 4, 2, "Charges", "HTTPS")]
    db = _el(5, "shop.db", "Orders DB", "One row per order.", "PostgreSQL", "Element,Container,Database")
    q = _el(6, "shop.q", "Events", "Order events.", "Kafka", "Element,Container,Queue")
    api["relationships"].append(_rel(24, 4, 6, "Publishes", "Kafka"))
    shop = _el(3, "shop", "Shop", "Sells things.", tags="Element,Software System", children=[api, db, q])
    return {
        "model": {"people": [user], "softwareSystems": [pay, shop]},
        "views": {
            "systemContextViews": [{"key": "ctx", "softwareSystemId": "3", "elements": [{"id": "1"}, {"id": "2"}, {"id": "3"}],
                                    "relationships": [{"id": "20"}]}],
            "containerViews": [{"key": "cont", "softwareSystemId": "3",
                                "elements": [{"id": i} for i in ("1", "2", "4", "5", "6")],
                                "relationships": [{"id": i} for i in ("21", "22", "23", "24")]}],
        },
    }


GRID = ["user   .     pay",
        "api    db    q  "]


def _boxes(svg: str) -> dict[str, tuple[float, float]]:
    """x, y of the first shape of every element group."""
    out = {}
    for m in re.finditer(r'<g class="c4-el" data-k="e:(\w+)"[^>]*>(<rect|<path|<circle)[^>]*?(?:x|d|cx)="M?([\d.]+)', svg):
        out[m.group(1)] = float(m.group(3))
    return out


def test_model_aliases_shapes_and_types():
    m = Model(workspace())
    assert set(m.els) == {"user", "pay", "shop", "api", "db", "q"}
    assert m.els["db"].shape == "database" and m.els["q"].shape == "queue" and m.els["api"].shape == "app"
    assert m.els["user"].shape == "person" and m.els["pay"].external
    assert m.els["api"].type_line() == "[Container: Go]"
    assert m.els["pay"].type_line() == "[External System]"
    assert m.views["cont"].scope == "shop" and m.internal(m.views["cont"], "api") and not m.internal(m.views["cont"], "user")


def test_render_grid_boundary_technology_and_gate(tmp_path):
    m = Model(workspace())
    meta, overflow = render_view(m, Spec(key="cont", source="cont", slot="stage", grid=GRID), tmp_path)
    svg = (tmp_path / "cont.svg").read_text()
    assert meta.viewbox == (0.0, 0.0, 1800.0, 860.0)        # the slot is the canvas: 1 svg px = 1 frame px
    assert meta.legibility_ok and not overflow and meta.min_rendered_1080p_px >= 18
    assert 'data-k="b:shop"' in svg and "[Software System]" in svg       # boundary around the containers
    assert "[HTTPS]" in svg and "[Container: PostgreSQL]" in svg
    assert "Helvetica" not in svg and "Arial" not in svg
    steps = json.loads((tmp_path / "cont.steps.json").read_text())
    flat = [k for st in steps for k in st]
    assert set(flat) >= {"e:user", "e:api", "l:api-db", "l:user-api"}


def test_derived_views_keep_every_pixel(tmp_path):
    m = Model(workspace())
    render_view(m, Spec(key="cont", source="cont", slot="stage", grid=GRID), tmp_path)
    render_view(m, Spec(key="v1", source="cont", slot="stage", grid=GRID, canvas="stage", overlay=Overlay(hide=["q", "pay"])), tmp_path)
    full, v1 = _boxes((tmp_path / "cont.svg").read_text()), _boxes((tmp_path / "v1.svg").read_text())
    assert "q" not in v1 and "pay" not in v1
    for a in v1:
        assert v1[a] == full[a]                                # nothing moves between V1 and the full view
    assert 'l:api-q' not in (tmp_path / "v1.svg").read_text()


def test_overlays_pills_badges_keep_and_flow(tmp_path):
    m = Model(workspace())
    ov = Overlay(breaks=["db"], fix=["q"], badges={"api": "M1"}, keep=["api", "db"])
    meta, _ = render_view(m, Spec(key="z", source="cont", slot="stage", grid=GRID, overlay=ov), tmp_path)
    svg = (tmp_path / "z.svg").read_text()
    assert 'data-k="p:breaks:db"' in svg and ">BREAKS<" in svg and 'data-k="p:fix:q"' in svg and 'data-k="p:badge:api"' in svg
    assert re.search(r'data-k="e:user" opacity="0.28"', svg)          # not kept: dimmed, still drawn in place
    assert json.loads((tmp_path / "z.steps.json").read_text()) == [["p:breaks:db"], ["p:fix:q"], ["p:badge:api"]]
    render_view(m, Spec(key="f", source="cont", slot="stage", grid=GRID, overlay=Overlay(flow=["user->api", "db->api"])), tmp_path)
    assert json.loads((tmp_path / "f.steps.json").read_text()) == [["f:1"], ["f:2"]]
    assert (tmp_path / "f.svg").read_text().count('class="c4-flow"') == 2


def test_new_reveals_each_box_with_its_edges(tmp_path):
    m = Model(workspace())
    render_view(m, Spec(key="v2", source="cont", slot="stage", grid=GRID, overlay=Overlay(new=["q"])), tmp_path)
    steps = json.loads((tmp_path / "v2.steps.json").read_text())
    assert steps == [["e:q", "p:new:q", "l:api-q"]]


def test_unknown_alias_and_overflow_fail_the_gate(tmp_path):
    m = Model(workspace())
    meta, _ = render_view(m, Spec(key="bad", source="cont", slot="stage", grid=GRID, overlay=Overlay(breaks=["nope"])), tmp_path)
    assert "nope" in meta.unknown_aliases
    ws = workspace()
    ws["model"]["softwareSystems"][1]["containers"][0]["description"] = "A description far too long to fit in a small box " * 3
    meta, overflow = render_view(Model(ws), Spec(key="o", source="cont", slot="stage", grid=GRID), tmp_path)
    assert overflow == ["api"] and not meta.legibility_ok


def test_grid_must_place_every_element(tmp_path):
    m = Model(workspace())
    meta, _ = render_view(m, Spec(key="g", source="cont", slot="stage", grid=["user . pay", "api db ."]), tmp_path)
    assert any("q" in u for u in meta.unknown_aliases)


def test_crop_scales_up_the_kept_boxes(tmp_path):
    m = Model(workspace())
    meta, _ = render_view(m, Spec(key="c", source="cont", slot="full", grid=GRID, canvas="stage",
                                  overlay=Overlay(keep=["api", "db"], crop=True)), tmp_path)
    assert meta.viewbox[2] < 1800 and meta.scale_1080p > 1.0
