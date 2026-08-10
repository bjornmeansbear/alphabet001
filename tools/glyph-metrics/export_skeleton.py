#!/usr/bin/env python3
"""Export skeleton geometry (contours + per-path strokeWidth) to JSON.

DrawBot.app has its own bundled Python with no access to this tool's venv
(glyphsLib, skia-python aren't installed there, and can't easily be), so the
skeleton data has to cross as a plain file instead of a shared environment.
`preview_drawbot.py` reads this JSON and renders it inside DrawBot.app using
its native BezierPath.expandStroke() -- no skia needed on that side either.

Usage:
    python export_skeleton.py                          # default glyph set
    python export_skeleton.py --glyphs a e n.alt o.alt  # just these
"""

import argparse
import json
import sys
from pathlib import Path

from compare import load
from metrics import contour_recordings, path_stroke_widths
from stroke import glyph_ink_coverage_pct

DEFAULT_SOURCE = Path(__file__).resolve().parents[2] / "Alphabet001.glyphs"
DEFAULT_GLYPHS = ["a", "a.alt", "e", "n", "n.alt", "o", "h", "h.alt", "two", "two.alt"]


def glyph_to_json(ufo_glyph, gs_layer, upm):
    recordings = contour_recordings(ufo_glyph)
    stroke_widths = path_stroke_widths(gs_layer)
    if len(stroke_widths) != len(recordings):
        stroke_widths = [None] * len(recordings)

    contours = []
    for recording, stroke_width in zip(recordings, stroke_widths):
        ops = [[op, [list(pt) for pt in args]] for op, args in recording]
        contours.append({"stroke_width": stroke_width, "ops": ops})

    # Baseline ink coverage at wght=1/wdth=1, exact (via skia -- see stroke.py).
    # preview_drawbot.py has no skia, so it scales this live as an
    # approximation (ink is linear-ish in wght but not exactly, because
    # round cap/join area is a small quadratic term in strokeWidth).
    base_ink_pct = glyph_ink_coverage_pct(ufo_glyph, gs_layer, upm, weight=1.0, width=1.0)

    return {"advance_width": ufo_glyph.width, "base_ink_pct": base_ink_pct, "contours": contours}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--glyphs", nargs="+", default=DEFAULT_GLYPHS)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "output" / "skeleton.json")
    args = parser.parse_args()

    if not args.source.exists():
        print(f"Source not found: {args.source}", file=sys.stderr)
        sys.exit(1)

    font, ufo, upm = load(args.source)
    missing = [g for g in args.glyphs if g not in ufo]
    if missing:
        print(f"Unknown glyph(s): {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    data = {
        "upm": upm,
        "glyphs": {name: glyph_to_json(ufo[name], font.glyphs[name].layers[0], upm) for name in args.glyphs},
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2))
    print(f"Skeleton data for {len(args.glyphs)} glyph(s) written to {args.out}")


if __name__ == "__main__":
    main()
