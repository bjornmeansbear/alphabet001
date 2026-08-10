# glyph-metrics

Compares default vs `.alt` glyph variants in `Alphabet001.glyphs` on three axes: ink coverage (filled area, stroked paths approximated as `arc_length * strokeWidth`), paper/density (advance width), and construction complexity (node count, curve-to-line ratio as a rough organic-vs-mechanical signal). Renders a side-by-side specimen sheet plus a terminal ranking table.

Built to make the "pragmatic utopian" brief testable, not just eyeballed — does a given variant actually cost less ink/paper, and does it lean more organic or more geometric.

## Setup

```
cd tools/glyph-metrics
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```
python compare.py                 # every default/.alt pair (12 today)
python compare.py --glyph a       # just a / a.alt
python compare.py --out foo.png   # custom output path
```

Output: `output/comparison.png` + a table printed to stdout.

## Weight/width sliders

```
python sliders.py --glyphs a e n o h --weight 0.5 1 1.5 2   # weight sweep
python sliders.py --glyphs a e n o h --width 0.6 1 1.4      # width sweep
open output/sliders.png
```

Real stroke-to-fill geometry (`stroke.py`, `skia.Paint.getFillPath`), not the ribbon approximation `metrics.py` uses for scoring. `--weight` scales `strokeWidth` before stroking; `--width` scales x *after* stroking so round caps/joins stay circular instead of squashing into ellipses.

### Live preview in DrawBot.app

This venv (glyphsLib, skia-python) and DrawBot.app (its own bundled Python) are separate environments — a script using this venv's packages can't run inside the app. To get real Cmd+R live-reload there instead:

```
python export_skeleton.py                    # writes output/skeleton.json
```

Then open `preview_drawbot.py` **in DrawBot.app itself** (not the venv) — it reads that JSON and does the stroke-to-fill conversion with DrawBot's own native `BezierPath.expandStroke()`, so it needs nothing from this venv. Edit `WEIGHT` / `WIDTH` / `GLYPHS` at the top of the file and hit Cmd+R. Re-run `export_skeleton.py --glyphs ...` whenever you want a different glyph set or the source `.glyphs` file changes.

## Known limits

- Ink coverage ignores stroke end-caps and self-joins — it's a ribbon approximation (`length * width`), fine for comparison, not a precise ink-volume figure.
- Numbers are relative to *this* font's own variants, not benchmarked against other typefaces.
- No file-size or variable-axis metrics yet — both need a compiled binary/designspace, which the source doesn't have. Worth adding once alphabet001 has masters and an actual `fontmake`/`fontc` export step, since skeleton+stroke construction makes a weight axis nearly free (interpolate `strokeWidth` rather than building separate outline masters).
