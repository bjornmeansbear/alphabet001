# alphabet001 — project context

## What this is
A wide, extended, near-monospace monoline typeface with clever ligatures (see `README.md`). Drawn as skeleton paths in Glyphs 3, with a per-path `strokeWidth` attribute (currently 20) doing the stroke-to-outline work rather than hand-drawn filled contours.

**Source of truth:** `Alphabet001.glyphs` (108 glyphs — full upper/lowercase, digits, punctuation, several `.alt` alternates: A, I, J, O, T, a, e, five, h, n, seven, two). No kerning, no OpenType features yet, no compiled binary yet. The `.ufo`/`.sfd` files in `archive/legacy-sources/` are older/partial and superseded by the `.glyphs` source — kept for history, not for editing.

**License note:** repo is GPLv3, unusual for a font project (most use SIL OFL, built specifically for font-embedding ambiguity) — worth a deliberate look if wide distribution is a goal.

## Repo layout
- `Alphabet001.glyphs` — source of truth (see above).
- `tools/` — this project's own tooling (`glyph-metrics/`; sliders queued next, see below).
- `archive/legacy-sources/` — superseded `.sfd`/`.ufo` font sources, kept for history.
- `archive/sketches/` — dated SVG/PNG specimen exports from earlier passes, no longer authoritative.
- `reference/` — inspiration/reference material that isn't this font's source (`letterformtemplate.ai`, `TYPESTRETCH_ForKristan.ai`).
- `housenumbers/` — a separate, unrelated vinyl-cutter house-numbers project that happens to live in this repo; not part of the typeface.

## Conceptual brief
Designer's background is postmodernist/semiotic (Barnbrook, Emigre, David Reinfurt as reference points — form-as-meaning, not neutral formalism). Current typeface direction is inspired by *Typeset in the Future* (Dave Addey) — a critique of Hollywood sci-fi's narrow reliance on cold geometric sans-serifs (Eurostile and kin) as shorthand for "the future," which really reads as institutional/mechanical control.

The counter-brief: type for a **pragmatic utopian solarpunk future** — not just formally (organic/botanical curves, humanist contrast, open apertures, warm terminals vs. sheared/mechanical ones) but *materially*: a typeface that is measurably efficient (low ink use, high text density / paper efficiency, economical construction) is a literal embodiment of "pragmatic utopian," not just a visual reference to one.

## Sustainability brief
The "pragmatic utopian solarpunk" brief above isn't just aesthetic — it maps to a real, if under-theorized, "sustainable type design" discourse. Notes for grounding future work here, roughly strongest to weakest argument:

- **Access** — libre licensing + broad script coverage means fewer typefaces need to be (re)produced at all. This is Dave Crossland's actual argument for Google Fonts/OFL, not ink savings — reuse-over-production is the strongest lever here, and it's a genuine tension with this repo's GPLv3 choice (see License note above).
- **Automation / reduced design labor** — already this project's approach: skeleton + `strokeWidth` construction interpolates a weight axis "nearly free" instead of hand-drawing N masters. Knuth's **Metafont** (1978) is the direct ancestor — true parametric families via constraint equations, a more general version of what OpenType variable fonts approximate. `tools/glyph-metrics/preview_drawbot.py` is this project's small, concrete instance of the idea: the typeface exposed as inputs (`WEIGHT`, `WIDTH`) you play with directly and watch redraw, rather than only fixed finished drawings. Worth learning more Metafont if the sliders should eventually move past "multiply strokeWidth by a factor" toward solving for a target (e.g. a fixed ink budget).
- **Ink** — the `ink_coverage_pct` metric already in `tools/glyph-metrics/`. Real precedent: **Ryman Eco** (Dan Rhatigan/Monotype + Grey London, ~33% less ink via perforated counters) — the same move as the queued perforation slider. Caution: **Ecofont**'s marketed ink savings were found smaller in practice once real printer behavior is accounted for — measure the real thing, not a marketing-friendly proxy.
- **Data** — file size, queued but not started. Variable fonts are a *conditional* win: one file beats N static weights only if a page actually uses multiple weights; a single-weight page is still better served by a subsetted static font.
- **Energy** — under-discussed in the literature searched so far: on OLED, brighter pixels cost more power, so a lighter stroke saves battery in dark mode but saves ink (opposite mechanism) in light-mode print. Same instinct, opposite physics depending on where it renders.
- **Appropriate/vernacular** — the honest connection is Schumacher's "appropriate technology" (local, low-tech, context-fit over universal), not anything carbon-capture-adjacent — no real mechanism links type design to carbon capture directly.

**People/precedents:**
- [Dave Crossland](https://github.com/davelab6) — Google Fonts ops lead; "compress, finesse, express" framing for variable fonts; access-over-ink-savings argument. [Design Notes podcast](https://www.iamli.am/design-notes-podcast/dave-crossland-google-fonts), [Interface Cafe interview](https://interfacecafe.com/how-fonts-change-the-world-dave-crossland-google-fonts/)
- [Colin M. Ford](https://fontsinuse.com/type_designers/2977/colin-m-ford) — type designer, Monotype (formerly Hoefler & Co.), KABK Type & Media grad. No confirmed sustainability-specific writing found yet.
- "Marie O" — unconfirmed identity, need full name to research properly.
- [Ryman Eco](https://www.typeroom.eu/article/earth-we-trust-ryman-eco-sustainable-font-all) — ink-reduction precedent for the perforation slider.
- [Typography and environmental problems (type.today)](https://type.today/en/journal/ecology) — broader ecology-of-type survey.
- [ATypI: Can Type Tools and Community Projects Be Sustainable?](https://atypi.org/presentation/can-type-tools-and-community-projects-be-sustainable/)

## tools/glyph-metrics/
Python tool that loads `Alphabet001.glyphs` directly via `glyphsLib`. Two parts:
- **`compare.py` + `metrics.py`** — scores default vs. `.alt` glyph pairs on ink coverage (filled area as % of em, stroked paths approximated as `arc_length * strokeWidth`), density (advance width), and construction complexity (node count, curve-to-line ratio as an organic-vs-mechanical proxy). Renders `output/comparison.png` plus a terminal ranking table.
- **`stroke.py` + `sliders.py`** — real stroke-to-fill geometry (`skia.Paint.getFillPath`, not the ribbon approximation) driving weight (`strokeWidth` multiplier) and width (x-scale, applied after stroking so caps stay round) sliders. `python sliders.py --glyphs a e n o h --weight 0.5 1 1.5 2` renders a sweep to `output/`.
- **`export_skeleton.py` + `preview_drawbot.py`** — live Cmd+R preview inside DrawBot.app itself (see DrawBot section below), since that app's bundled Python can't see this venv.

Setup/usage in `tools/glyph-metrics/README.md`. Built to make the solarpunk brief testable rather than just eyeballed.

**Real finding from using it:** default `n` and `h` aren't finished letterforms — they render as a straight-line zigzag, not an arch. `n.alt`/`h.alt` are the actual finished letters (curve ratio 0.00→0.40 for only +0.11/+0.15pp ink). Worth promoting those alts to default before drawing much more around them.

**Free vs. costly organic upgrades**, from the ink/curve-ratio numbers: `a.alt` and `two.alt` get curvier while using *less* ink (no tradeoff — the strong version of "pragmatic utopian," material and formal pointing the same way). `A.alt`, `e.alt`, `seven.alt` get curvier but cost real ink (+0.70, +0.30, +6.51pp) — better kept as an opt-in expressive/display alternate (`ss01`/`salt`) than promoted to default.

## Queued next step
Weight and width sliders are built (above). Not started yet:
- **texture/perforation** — Ecofont-style holes punched into the stroke fill for further ink reduction without much legibility cost. `BezierPath.difference` (boolean subtraction) is the mechanism, available in the same `drawbot-skia` dependency already used by `stroke.py`.

Weight/width map directly to standard OpenType variable axes (`wght`, `wdth`) — so this is a path toward an actual variable font, not a bespoke system.

## Adjacent tools (not part of this repo, don't build into them directly)
- `~/Code/img2bez` — Eli Heuer's Rust tool, bitmap→UFO glyph tracer (`kurbo`/`norad`), has an autoresearch loop scoring traced fidelity via IoU.
- `~/Code/runebender-xilem` — Eli Heuer's working native glyph editor (pen/hyperbezier tools, UFO I/O, autotrace via img2bez). Forked locally.
- `~/Code/runebender-comfy` — Eli Heuer's newer, in-progress ComfyUI-based node pipeline for font editing/compilation. Actively being developed by Eli — deliberately not the place to build; this project's tooling should stay narrow and personal rather than extending someone else's in-progress work.

## DrawBot
Native macOS app (not just the `drawbot-skia` package used in `glyph-metrics`) — separate bundled Python, no access to the venv's `glyphsLib`/`skia-python`. Used for fast interactive sketching via its Cmd+R live-reload loop. `tools/glyph-metrics/preview_drawbot.py` is the concrete bridge: `export_skeleton.py` (venv) writes skeleton geometry to JSON, then this script (opened in DrawBot.app itself) reads it and does stroke-to-fill with DrawBot's own native `BezierPath.expandStroke()` — the typeface exposed as `WEIGHT`/`WIDTH` inputs you edit and watch redraw, rather than only fixed finished drawings.
