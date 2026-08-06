"""Metrics for comparing glyph variants: ink coverage, density, construction complexity.

alphabet001 is drawn as monoline skeleton paths with a Glyphs "stroke" filter
(a per-path `strokeWidth` attribute) rather than as pre-filled outlines, so
`fontTools`'s AreaPen can't be pointed at the glyph directly -- an open
skeleton path has zero enclosed area. Instead, stroked paths are treated as a
constant-width ribbon and their ink contribution is approximated as
`arc_length * strokeWidth`. This ignores end-cap and join overlap, which is a
fine trade for a comparative/exploratory tool but means the numbers are
relative, not a precise ink-volume measurement.
"""

import math

from fontTools.misc.bezierTools import calcCubicArcLength, calcQuadraticArcLength
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.recordingPen import RecordingPen


def path_length(recording):
    """Total arc length of a recorded pen path (handles line/curve/qcurve)."""
    length = 0.0
    current = None
    start = None
    for op, args in recording:
        if op == "moveTo":
            current = args[0]
            start = current
        elif op == "lineTo":
            pt = args[0]
            length += math.dist(current, pt)
            current = pt
        elif op == "curveTo":
            p1, p2, p3 = args
            length += calcCubicArcLength(current, p1, p2, p3)
            current = p3
        elif op == "qCurveTo":
            # Chain of quadratic segments sharing implied on-curve midpoints,
            # final arg is the real on-curve end point.
            points = [current] + list(args)
            for i in range(len(points) - 2):
                length += calcQuadraticArcLength(points[i], points[i + 1], points[i + 1])
            length += 0  # noop: qCurveTo is rare in this cubic-only source
            current = args[-1]
        elif op == "closePath":
            if current is not None and start is not None and current != start:
                length += math.dist(current, start)
            current = start
    return length


def segment_counts(recording):
    """Count of straight vs curved segments, for a rough organic/mechanical ratio."""
    lines = curves = 0
    for op, args in recording:
        if op == "lineTo":
            lines += 1
        elif op in ("curveTo", "qCurveTo"):
            curves += 1
    return lines, curves


def node_count(recording):
    """Total on/off-curve points drawn, a rough proxy for path complexity."""
    count = 0
    for op, args in recording:
        if op in ("moveTo", "lineTo", "curveTo", "qCurveTo"):
            count += len(args)
    return count


def contour_recordings(ufo_glyph):
    """Draw each contour of a UFO glyph into its own RecordingPen, in source order."""
    recordings = []
    for contour in ufo_glyph:
        pen = RecordingPen()
        contour.draw(pen)
        recordings.append(pen.value)
    return recordings


def path_stroke_widths(gs_layer):
    """Per-path strokeWidth attribute (or None) from the Glyphs source, in path order."""
    return [p.attributes.get("strokeWidth") for p in gs_layer.paths]


def glyph_ink_area(ufo_glyph, gs_layer):
    """Approximate total filled ink area for a glyph.

    Stroked (monoline) contours contribute arc_length * strokeWidth.
    Un-stroked closed contours contribute their enclosed polygon area directly.
    """
    recordings = contour_recordings(ufo_glyph)
    stroke_widths = path_stroke_widths(gs_layer)
    # Defensive: fall back to no-stroke-info if counts don't line up.
    if len(stroke_widths) != len(recordings):
        stroke_widths = [None] * len(recordings)

    total_area = 0.0
    total_lines = total_curves = total_nodes = 0
    for recording, stroke_width in zip(recordings, stroke_widths):
        lines, curves = segment_counts(recording)
        total_lines += lines
        total_curves += curves
        total_nodes += node_count(recording)

        if stroke_width:
            total_area += path_length(recording) * stroke_width
        else:
            area_pen = AreaPen(glyphSet=None)
            for op, args in recording:
                getattr(area_pen, op)(*args)
            total_area += abs(area_pen.value)

    return total_area, total_lines, total_curves, total_nodes


def glyph_metrics(name, ufo_glyph, gs_layer, upm):
    """Compute the three comparison metrics for a single glyph."""
    ink_area, lines, curves, nodes = glyph_ink_area(ufo_glyph, gs_layer)
    advance_width = ufo_glyph.width

    em_area = advance_width * upm
    ink_coverage_pct = (ink_area / em_area * 100) if em_area else 0.0

    total_segments = lines + curves
    curve_ratio = (curves / total_segments) if total_segments else 0.0

    return {
        "name": name,
        "advance_width": advance_width,
        "ink_area": ink_area,
        "ink_coverage_pct": ink_coverage_pct,
        "node_count": nodes,
        "segment_count": total_segments,
        "curve_ratio": curve_ratio,
    }
