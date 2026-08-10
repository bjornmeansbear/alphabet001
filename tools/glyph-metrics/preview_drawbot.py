"""Live weight/width preview for alphabet001 -- open THIS file in DrawBot.app
(not the venv). Drag the wght/wdth sliders in the floating window; the
drawing updates live (no manual Cmd+R needed).

Uses DrawBot's own native BezierPath.expandStroke() for the stroke-to-fill
conversion, so it needs no skia/glyphsLib -- DrawBot.app's bundled Python
can't see those (they live in tools/glyph-metrics/.venv, a separate
environment). Geometry instead comes from output/skeleton.json; regenerate
it with `python export_skeleton.py` (in the venv) whenever the glyphs it
covers change, or to cover a different set of glyphs.

wght/wdth are named for the real OpenType axis tags they stand in for
(see CLAUDE.md's "Queued next step") -- this is a sketch of those two axes,
not a bespoke naming scheme.
"""

import json
from pathlib import Path

Variable(
    [
        dict(name="wght", ui="Slider", args=dict(value=1.0, minValue=0.25, maxValue=3.0)),
        dict(name="wdth", ui="Slider", args=dict(value=1.0, minValue=0.5, maxValue=1.8)),
    ],
    globals(),
)

GLYPHS = ["a", "a.alt", "e", "n", "n.alt", "o", "h", "h.alt"]

DATA_PATH = Path(__file__).parent / "output" / "skeleton.json"
CELL = 260
MARGIN = 30
LABEL_H = 20


def build_contour(ops):
    path = BezierPath()
    for op, args in ops:
        if op == "moveTo":
            path.moveTo(tuple(args[0]))
        elif op == "lineTo":
            path.lineTo(tuple(args[0]))
        elif op == "curveTo":
            path.curveTo(*(tuple(p) for p in args))
        elif op == "closePath":
            path.closePath()
    return path


def glyph_fill_path(glyph, weight, width):
    combined = BezierPath()
    for contour in glyph["contours"]:
        skeleton = build_contour(contour["ops"])
        stroke_width = contour["stroke_width"]
        filled = skeleton.expandStroke(stroke_width * weight, lineCap="round", lineJoin="round") if stroke_width else skeleton
        combined.appendPath(filled)
    if width != 1.0:
        combined.scale(width, 1)
    return combined


data = json.loads(DATA_PATH.read_text())
missing = [name for name in GLYPHS if name not in data["glyphs"]]
if missing:
    raise ValueError(f"Not in {DATA_PATH.name} -- re-export with export_skeleton.py --glyphs ...: {missing}")

upm = data["upm"]
page_w = MARGIN * 2 + CELL * len(GLYPHS)
page_h = MARGIN * 2 + CELL + LABEL_H

size(page_w, page_h)
fill(1, 1, 1)
rect(0, 0, page_w, page_h)
font("Helvetica")

for i, name in enumerate(GLYPHS):
    box_x = MARGIN + i * CELL
    box_y = MARGIN
    scale_factor = CELL / upm

    path = glyph_fill_path(data["glyphs"][name], wght, wdth)

    save()
    translate(box_x, box_y)
    scale(scale_factor)
    translate(0, 200)
    fill(0.1, 0.35, 0.15)
    drawPath(path)
    restore()

    fill(0)
    fontSize(11)
    text(f"{name}  wght {wght:g}  wdth {wdth:g}", (box_x, box_y + CELL + 4))
