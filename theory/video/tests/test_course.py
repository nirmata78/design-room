#!/usr/bin/env python3
"""Tests for course.py. Run from the repo root:  python3 -m unittest discover theory/video/tests
Regenerate the golden files after an intended change to the builder:  REGEN=1 python3 -m unittest discover theory/video/tests"""
import contextlib, io, os, pathlib, shutil, sys, tempfile, unittest

HERE = pathlib.Path(__file__).resolve().parent
TOOL = HERE.parent
sys.path.insert(0, str(TOOL))
import course  # noqa: E402

GOLD = HERE / "golden"
SAMPLE = (HERE / "sample.txt").read_text(encoding="utf-8")
REGISTER = "id\tname\ttier\tpart\tform\nTST-01\tA small table\tA\t99\tfull\nTST-02\tTwo cards\tB\t99\tfull\n"


class Sandbox(unittest.TestCase):
    """Points the builder at a throw-away src/, build/ and concepts.tsv, so a test never touches the real course."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="sd-course-test-"))
        (self.tmp / "src").mkdir()
        (self.tmp / "concepts.tsv").write_text(REGISTER, encoding="utf-8")
        self.saved = {k: getattr(course, k) for k in ("SRC", "BUILD", "HERE", "SVG")}
        course.SRC, course.BUILD, course.HERE, course.SVG = self.tmp / "src", self.tmp / "build", self.tmp, TOOL / "svg"

    def tearDown(self):
        for k, v in self.saved.items():
            setattr(course, k, v)
        shutil.rmtree(self.tmp)

    def put(self, text, nn="99"):
        (self.tmp / "src" / f"ch{nn}.txt").write_text(text, encoding="utf-8")

    def build(self, nn="99"):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            course.compile_ch(nn)
        d = self.tmp / "build" / f"ch{nn}"
        return (d / "video-slides.html").read_text(encoding="utf-8"), (d / f"ch{nn}.script.md").read_text(encoding="utf-8"), out.getvalue()

    def coverage(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            ok = course.coverage(["99"])
        return ok, out.getvalue()


class TestCompile(Sandbox):
    def test_golden(self):
        self.put(SAMPLE)
        page, script, log = self.build()
        self.assertNotIn("lint", log)
        self.assertNotIn("not drawn yet", log)
        if os.environ.get("REGEN"):
            GOLD.mkdir(exist_ok=True)
            (GOLD / "sample.html").write_text(page, encoding="utf-8")
            (GOLD / "sample.script.md").write_text(script, encoding="utf-8")
        self.assertEqual(page, (GOLD / "sample.html").read_text(encoding="utf-8"))
        self.assertEqual(script, (GOLD / "sample.script.md").read_text(encoding="utf-8"))

    def test_segments_equal_joined_file(self):
        self.put(SAMPLE)
        joined = self.build()[:2]
        (self.tmp / "src" / "ch99.txt").unlink()
        seg = self.tmp / "src" / "ch99"; seg.mkdir()
        cut = SAMPLE.index("\n## ")
        (seg / "a.txt").write_text(SAMPLE[:cut], encoding="utf-8")
        (seg / "b.txt").write_text(SAMPLE[cut + 1:], encoding="utf-8")
        self.assertEqual(self.build()[:2], joined)

    def test_symbol_in_speech_is_linted(self):
        self.put(SAMPLE.replace("Two is two.", "Two is 20% of ten."))
        self.assertIn("symbol in speech", self.build()[2])

    def test_long_line_is_linted(self):
        self.put(SAMPLE.replace("Two is two.", "word " * 111))
        self.assertIn("long line", self.build()[2])


class TestCompanion(Sandbox):
    def test_extracts_every_kind(self):
        self.put(SAMPLE)
        out = self.tmp / "companion.md"
        with contextlib.redirect_stdout(io.StringIO()):
            counts = course.companion(["99"], out)
        self.assertEqual(counts["99"], dict(concepts=2, figures=1, probes=1))
        text = out.read_text(encoding="utf-8")
        for want in ("# Part 99 · Sample part", "- A short note about reading.", "- Read the sample chapter.",
                     "| TST-02 | Two cards | B | Say the line slowly, and mean it. | 99.1 Every slide type |",
                     "](diagrams/video-sample-box.pdf)", "**Trap · The thing people get wrong.** They forget the second step.",
                     "**1. What happens when the box fails?**", "- The request fails over to the **second** box",
                     "> It fails over to the second box, and nobody notices."):
            self.assertIn(want, text)


class TestCoverage(Sandbox):
    def test_sample_is_clean(self):
        self.put(SAMPLE)
        self.assertTrue(self.coverage()[0])

    def test_concept_declared_twice_fails(self):
        self.put(SAMPLE.replace("@ TST-02", "@ TST-02 TST-01"))
        ok, log = self.coverage()
        self.assertFalse(ok)
        self.assertIn("TST-01: declared 2 times", log)

    def test_unknown_id_fails(self):
        self.put(SAMPLE.replace("@ TST-02", "@ TST-02 TST-77"))
        ok, log = self.coverage()
        self.assertFalse(ok)
        self.assertIn("TST-77: not in concepts.tsv", log)

    def test_missing_home_fails(self):
        self.put(SAMPLE.replace("@ TST-02\n", ""))
        ok, log = self.coverage()
        self.assertFalse(ok)
        self.assertIn("TST-02 (Two cards): no home slide", log)


if __name__ == "__main__":
    unittest.main()
