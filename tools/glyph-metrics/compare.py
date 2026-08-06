#!/usr/bin/env python3
"""Compare default vs .alt glyph variants in Alphabet001.glyphs on ink coverage,
paper/density, and construction complexity. Renders a specimen sheet and prints
a ranking table.

Usage:
    python compare.py                  # every default/.alt pair in the source
    python compare.py --glyph a        # just the "a" / "a.alt" pair
    python compare.py --source path.glyphs --out report
"""

import argparse
import sys
from pathlib import Path

import glyphsLib
from drawbot_skia.drawbot import Drawing

from metrics import glyph_metrics

DEFAULT_SOURCE = Path(__file__).resolve().parents[2] / "Alphabet001.glyphs"
ROW_HEIGHT = 260
GLYPH_BOX = 200
MARGIN = 40
LABEL_GAP = 24


def find_alt_pairs(font, only_glyph=None):
    names = {g.name for g in font.glyphs}
    pairs = []
    for name in sorted(names):
        if name.endswith(".alt"):
            continue
        alt_name = f"{name}.alt"
        if alt_name in names:
            if only_glyph and name != only_glyph:
                continue
            pairs.append((name, alt_name))
    return pairs


def load(source_path):
    font = glyphsLib.load(str(source_path))
    ufos = glyphsLib.to_ufos(font)
    ufo = ufos[0]
    upm = font.upm or 1000
    return font, ufo, upm


def compute_pair_metrics(font, ufo, upm, base_name, alt_name):
    base_layer = font.glyphs[base_name].layers[0]
    alt_layer = font.glyphs[alt_name].layers[0]
    base = glyph_metrics(base_name, ufo[base_name], base_layer, upm)
    alt = glyph_metrics(alt_name, ufo[alt_name], alt_layer, upm)
    return base, alt


def draw_glyph(db, ufo_glyph, gs_layer, x, y, box, upm):
    """Draw one glyph, scaled to fit `box` units, at bottom-left corner (x, y)."""
    scale = box / upm
    stroke_widths = [p.attributes.get("strokeWidth") for p in gs_layer.paths]
    if len(stroke_widths) != len(list(ufo_glyph)):
        stroke_widths = [None] * len(list(ufo_glyph))

    with db.savedState():
        db.translate(x, y)
        db.scale(scale)
        db.translate(0, 200)  # nudge for descenders within the box
        for contour, stroke_width in zip(ufo_glyph, stroke_widths):
            from drawbot_skia.drawbot import BezierPath
            from fontTools.pens.recordingPen import RecordingPen

            pen = RecordingPen()
            contour.draw(pen)
            bez = BezierPath()
            pen.replay(bez)

            if stroke_width:
                db.fill(None)
                db.stroke(0.1, 0.35, 0.15, 1)
                db.strokeWidth(stroke_width)
            else:
                db.fill(0.1, 0.35, 0.15, 1)
                db.stroke(None)
            db.drawPath(bez)


def render_specimen(font, ufo, upm, pairs, results, out_path):
    db = Drawing()
    width = MARGIN * 3 + GLYPH_BOX * 2 + 260
    height = MARGIN * 2 + ROW_HEIGHT * len(pairs)
    db.newDrawing()
    db.newPage(width, height)
    db.fill(1, 1, 1, 1)
    db.rect(0, 0, width, height)

    db.font("Helvetica")
    for i, (base_name, alt_name) in enumerate(pairs):
        row_top = height - MARGIN - i * ROW_HEIGHT
        box_y = row_top - GLYPH_BOX

        base_layer = font.glyphs[base_name].layers[0]
        alt_layer = font.glyphs[alt_name].layers[0]
        draw_glyph(db, ufo[base_name], base_layer, MARGIN, box_y, GLYPH_BOX, upm)
        draw_glyph(db, ufo[alt_name], alt_layer, MARGIN * 2 + GLYPH_BOX, box_y, GLYPH_BOX, upm)

        base_m, alt_m = results[base_name, alt_name]
        text_x = MARGIN * 3 + GLYPH_BOX * 2
        db.fill(0, 0, 0, 1)
        db.fontSize(11)
        lines = [
            f"{base_name}  vs  {alt_name}",
            "",
            f"ink coverage   {base_m['ink_coverage_pct']:.2f}%  vs  {alt_m['ink_coverage_pct']:.2f}%",
            f"advance width  {base_m['advance_width']:.0f}  vs  {alt_m['advance_width']:.0f}",
            f"nodes          {base_m['node_count']}  vs  {alt_m['node_count']}",
            f"curve ratio    {base_m['curve_ratio']:.2f}  vs  {alt_m['curve_ratio']:.2f}",
        ]
        for j, line in enumerate(lines):
            db.text(line, (text_x, box_y + GLYPH_BOX - 16 - j * 16))

    db.saveImage(str(out_path))
    db.endDrawing()


def print_table(pairs, results):
    header = f"{'glyph':<10}{'ink %':>10}{'width':>10}{'nodes':>8}{'curve ratio':>13}"
    print(header)
    print("-" * len(header))
    for base_name, alt_name in pairs:
        base_m, alt_m = results[base_name, alt_name]
        for m in (base_m, alt_m):
            print(
                f"{m['name']:<10}{m['ink_coverage_pct']:>9.2f}%{m['advance_width']:>10.0f}"
                f"{m['node_count']:>8}{m['curve_ratio']:>13.2f}"
            )
        ink_delta = alt_m["ink_coverage_pct"] - base_m["ink_coverage_pct"]
        print(f"  -> alt uses {ink_delta:+.2f}pp ink vs default")
        print()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--glyph", type=str, default=None, help="Only compare this base glyph name")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "output" / "comparison.png")
    args = parser.parse_args()

    if not args.source.exists():
        print(f"Source not found: {args.source}", file=sys.stderr)
        sys.exit(1)

    font, ufo, upm = load(args.source)
    pairs = find_alt_pairs(font, only_glyph=args.glyph)
    if not pairs:
        print("No default/.alt pairs found.", file=sys.stderr)
        sys.exit(1)

    results = {}
    for base_name, alt_name in pairs:
        results[base_name, alt_name] = compute_pair_metrics(font, ufo, upm, base_name, alt_name)

    print_table(pairs, results)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    render_specimen(font, ufo, upm, pairs, results, args.out)
    print(f"\nSpecimen written to {args.out}")


if __name__ == "__main__":
    main()
