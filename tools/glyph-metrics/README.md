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

## Known limits

- Ink coverage ignores stroke end-caps and self-joins — it's a ribbon approximation (`length * width`), fine for comparison, not a precise ink-volume figure.
- Numbers are relative to *this* font's own variants, not benchmarked against other typefaces.
- No file-size or variable-axis metrics yet — both need a compiled binary/designspace, which the source doesn't have. Worth adding once alphabet001 has masters and an actual `fontmake`/`fontc` export step, since skeleton+stroke construction makes a weight axis nearly free (interpolate `strokeWidth` rather than building separate outline masters).
