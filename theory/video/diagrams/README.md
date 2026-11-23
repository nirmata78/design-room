# Diagram specifications

One file per course part (`pNN.md`). Each section is one figure, named exactly as the transcript
(`src/chNN.txt`) refers to it in a `= dia` slide. The specification is complete: the boxes, the
arrows, the labels and the numbers are given. Draw what is specified; do not add or remove content.
If a specification is impossible to draw legibly, split nothing and change nothing: write the
problem into `plans/STATUS-02.md` and draw the closest legible version.

## Rules for every figure

- Output `theory/video/svg/<name>.svg`, written by `theory/video/diagrams_pNN.py` (one function per
  figure, a `main()` that writes them all). Python standard library plus the kit's helpers only.
- Canvas 1600 px wide; height as specified (default 720). White background.
- Helpers: `~/.claude/skills/slide-video-kit/scripts/seqsvg.py` for sequence diagrams,
  `c4svg.py` for boxes and arrows, `erdsvg.py` for tables. Worked sources:
  `solutions/SD-09-chat-messaging/video/diagrams.py`. Charts are plain SVG strings.
- Text at least 21 px; labels on arrows at least 20 px, placed above the line, never across a box.
- At least 80 px between boxes that carry a labelled arrow.
- Sequence diagrams: at most seven participants and ten messages; `Seq(1500, size=22, row=50)`;
  the message a specification marks **highlight** gets `hl=True`.
- Colours: blue for the normal path, red for the failure or the thing the slide is about, green for
  the repaired path, amber for a warning, grey for background elements. Never colour alone: the
  label carries the meaning.
- Numbers and names are copied from the specification character for character.

## Checking

Render each SVG to PNG and look at it:

```bash
rsvg-convert -w 1600 theory/video/svg/<name>.svg -o /tmp/<name>.png
```

Check: nothing overlaps, nothing is cut off, every label in the specification is present and
spelled as given, the highlighted element is the one specified.
