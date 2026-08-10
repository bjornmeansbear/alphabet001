#!/usr/bin/env python3
"""Render alphabet001 glyphs at variable weight/width, using real
stroke-to-fill geometry (see stroke.py) instead of the ribbon approximation
in metrics.py.

Usage:
    python sliders.py --glyphs a e n o --weight 0.5 1 1.5 2   # weight sweep
    python sliders.py --glyphs a e n o --width 0.6 1 1.4      # width sweep
    python sliders.py --glyphs a --weight 0.5 1 2 --width 0.7 1 1.3  # grid
"""

import argparse
import itertools
import sys
from pathlib import Path

from drawbot_skia.drawbot import Drawing

from compare import load
from stroke import glyph_fill_path

DEFAULT_SOURCE = Path(__file__).resolve().parents[2] / "Alphabet001.glyphs"
CELL = 260
LABEL_H = 26
MARGIN = 30


def render_grid(font, ufo, upm, glyph_names, weights, widths, out_path):
    combos = list(itertools.product(weights, widths))
    cols = len(combos)
    rows = len(glyph_names)

    cell_w = CELL
    cell_h = CELL + LABEL_H
    page_w = MARGIN * 2 + cell_w * cols
    page_h = MARGIN * 2 + cell_h * rows + LABEL_H

    db = Drawing()
    db.newDrawing()
    db.newPage(page_w, page_h)
    db.fill(1, 1, 1, 1)
    db.rect(0, 0, page_w, page_h)
    db.font("Helvetica")

    for col, (weight, width) in enumerate(combos):
        db.fill(0, 0, 0, 1)
        db.fontSize(10)
        db.text(f"wght {weight:g}  wdth {width:g}", (MARGIN + col * cell_w + 8, page_h - MARGIN - 14))

    for row, name in enumerate(glyph_names):
        gs_layer = font.glyphs[name].layers[0]
        row_top = page_h - MARGIN - LABEL_H - row * cell_h
        for col, (weight, width) in enumerate(combos):
            path, advance = glyph_fill_path(ufo[name], gs_layer, weight=weight, width=width)
            box_x = MARGIN + col * cell_w
            box_y = row_top - cell_h

            scale = CELL / upm
            db.fill(0.1, 0.35, 0.15, 1)
            db.stroke(None)
            with db.savedState():
                db.translate(box_x, box_y + LABEL_H)
                db.scale(scale)
                db.translate(0, 200)
                from drawbot_skia.drawbot import BezierPath

                bez = BezierPath(path=path)
                db.drawPath(bez)

        db.fill(0, 0, 0, 1)
        db.fontSize(11)
        db.text(name, (MARGIN - 4, row_top - cell_h + 8))

    db.saveImage(str(out_path))
    db.endDrawing()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--glyphs", nargs="+", default=["a", "e", "n", "o", "h"])
    parser.add_argument("--weight", nargs="+", type=float, default=[1.0], help="strokeWidth multipliers")
    parser.add_argument("--width", nargs="+", type=float, default=[1.0], help="x-scale multipliers")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "output" / "sliders.png")
    args = parser.parse_args()

    if not args.source.exists():
        print(f"Source not found: {args.source}", file=sys.stderr)
        sys.exit(1)

    font, ufo, upm = load(args.source)
    missing = [g for g in args.glyphs if g not in ufo]
    if missing:
        print(f"Unknown glyph(s): {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    render_grid(font, ufo, upm, args.glyphs, args.weight, args.width, args.out)
    print(f"Specimen written to {args.out}")


if __name__ == "__main__":
    main()
