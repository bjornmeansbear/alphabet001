"""Skeleton stroke -> filled outline conversion via Skia.

alphabet001 is drawn as skeleton paths with a per-path `strokeWidth`
attribute (see metrics.py's module docstring for why AreaPen can't be
pointed at the glyph directly). `metrics.py` approximates ink from that as
`arc_length * strokeWidth` for comparison purposes. This module instead does
the real thing -- `skia.Paint.getFillPath` converts a stroked skeleton path
into its exact filled outline -- which is what the weight/width sliders need
to actually draw a glyph rather than just score it.

weight scales strokeWidth before stroking (a wght-axis analog). width scales
the x-axis of the already-*filled* outline, applied after stroking so round
caps/joins stay circular instead of being squashed into ellipses (a
wdth-axis analog).
"""

import skia

from metrics import contour_recordings, path_stroke_widths

_CAPS = {"round": skia.Paint.kRound_Cap, "square": skia.Paint.kSquare_Cap, "butt": skia.Paint.kButt_Cap}
_JOINS = {"round": skia.Paint.kRound_Join, "miter": skia.Paint.kMiter_Join, "bevel": skia.Paint.kBevel_Join}


def _replay_to_skia(recording):
    """Draw a RecordingPen recording (line/curve, cubic-only) onto a skia.Path."""
    path = skia.Path()
    for op, args in recording:
        if op == "moveTo":
            path.moveTo(*args[0])
        elif op == "lineTo":
            path.lineTo(*args[0])
        elif op == "curveTo":
            p1, p2, p3 = args
            path.cubicTo(*p1, *p2, *p3)
        elif op == "qCurveTo":
            # Not expected in this cubic-only source (see metrics.py); fail
            # loudly rather than silently drawing the wrong shape.
            raise NotImplementedError("qCurveTo not expected in this source")
        elif op == "closePath":
            path.close()
    return path


def contour_to_fill(recording, stroke_width, cap="round", join="round"):
    """Convert one skeleton contour to its filled outline.

    If `stroke_width` is falsy, the contour is assumed already-closed/filled
    (e.g. the dot in `period`) and is returned as drawn, unstroked.
    """
    src = _replay_to_skia(recording)
    if not stroke_width:
        return src

    paint = skia.Paint(
        Style=skia.Paint.kStroke_Style,
        StrokeWidth=stroke_width,
        StrokeCap=_CAPS[cap],
        StrokeJoin=_JOINS[join],
    )
    dst = skia.Path()
    paint.getFillPath(src, dst)
    return dst


def glyph_fill_path(ufo_glyph, gs_layer, weight=1.0, width=1.0):
    """Build one combined filled skia.Path for a glyph at a given weight/width.

    Returns (skia.Path, advance_width).
    """
    recordings = contour_recordings(ufo_glyph)
    stroke_widths = path_stroke_widths(gs_layer)
    if len(stroke_widths) != len(recordings):
        stroke_widths = [None] * len(recordings)

    combined = skia.Path()
    for recording, stroke_width in zip(recordings, stroke_widths):
        scaled_width = stroke_width * weight if stroke_width else stroke_width
        combined.addPath(contour_to_fill(recording, scaled_width))

    if width != 1.0:
        combined.transform(skia.Matrix.Scale(width, 1))

    advance_width = ufo_glyph.width * width
    return combined, advance_width


def path_area(skia_path):
    """Exact filled area of a skia.Path, via fontTools' AreaPen.

    Measures the *final* geometry directly rather than the unstroked
    skeleton, so it stays correct regardless of weight. Note that
    `glyph_ink_coverage_pct` below turns out to be exactly invariant to
    `width` by construction: width is a post-stroke x-only scale (see module
    docstring), and area under any single-axis affine scale changes by
    exactly that factor no matter the shape's orientation -- the same factor
    advance_width scales by, so they cancel in the ink/em ratio precisely,
    not approximately. Ink and density really are orthogonal levers here,
    provably: `wght` moves ink, `wdth` moves paper/page count, and neither
    axis's slider can accidentally be "secretly" doing the other's job.
    """
    from fontTools.pens.areaPen import AreaPen

    pen = AreaPen(glyphset=None)
    it = skia.Path.Iter(skia_path, True)
    verb, pts = it.next()
    while verb != skia.Path.kDone_Verb:
        if verb == skia.Path.kMove_Verb:
            pen.moveTo((pts[0].fX, pts[0].fY))
        elif verb == skia.Path.kLine_Verb:
            pen.lineTo((pts[1].fX, pts[1].fY))
        elif verb == skia.Path.kCubic_Verb:
            pen.curveTo((pts[1].fX, pts[1].fY), (pts[2].fX, pts[2].fY), (pts[3].fX, pts[3].fY))
        elif verb == skia.Path.kQuad_Verb:
            pen.qCurveTo((pts[1].fX, pts[1].fY), (pts[2].fX, pts[2].fY))
        elif verb == skia.Path.kConic_Verb:
            quads = skia.Path.ConvertConicToQuads(pts[0], pts[1], pts[2], it.conicWeight(), 2)
            for i in range(1, len(quads) - 1, 2):
                pen.qCurveTo((quads[i].fX, quads[i].fY), (quads[i + 1].fX, quads[i + 1].fY))
        elif verb == skia.Path.kClose_Verb:
            pen.closePath()
        verb, pts = it.next()
    return abs(pen.value)


def glyph_ink_coverage_pct(ufo_glyph, gs_layer, upm, weight=1.0, width=1.0):
    """Exact ink coverage (% of em) at a given weight/width, replacing the
    ribbon approximation in metrics.py with the real filled-path area."""
    path, advance_width = glyph_fill_path(ufo_glyph, gs_layer, weight=weight, width=width)
    em_area = advance_width * upm
    return (path_area(path) / em_area * 100) if em_area else 0.0
