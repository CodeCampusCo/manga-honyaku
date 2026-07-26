# manga-honyaku

A manga translation workflow. Code handles geometry — detection, OCR, text
removal, rendering. An LLM agent handles comprehension — reading order, speaker
attribution, and the translation itself.

Design: [`docs/specs/2026-07-26-design.md`](docs/specs/2026-07-26-design.md).

## Setup

```sh
uv sync
```

The detector weights are not in this repository. `ogkalu/comic-text-and-bubble-detector`
(Apache-2.0, ~170 MB) is downloaded into the Hugging Face cache on first run.
To reuse a copy you already have:

```sh
export MANGA_HONYAKU_DETECTOR=/path/to/comic-text-and-bubble-detector
```

## Stages

Each stage is a separate command over the same `work/` directory, so editing a
translation and re-rendering never re-runs detection.

The pipeline runs one way — each stage reads the artifact before it and writes
the one after.

```sh
uv run python -m manga_honyaku.detect   raw/*.jpg --work work   # -> work/<page>.detector.json
uv run python -m manga_honyaku.annotate raw/*.jpg --work work   # -> work/<page>.boxes.png
uv run python -m manga_honyaku.prepare  raw/*.jpg --work work   # -> work/<page>.agent.json
#   prepare also OCRs the Japanese into it; --no-ocr leaves that to the agent
#   the agent then reads the page and edits work/<page>.agent.json
uv run python -m manga_honyaku.clean    raw/*.jpg --work work   # -> work/<page>.clean.png
                                                                #    work/<page>.masks.png
uv run python -m manga_honyaku.render   raw/*.jpg --work work   # -> out/<page>.png
```

`work/<page>.agent.json` is the working file and the only one that cannot be
rebuilt: everything the agent works out about a page is written into it. `detect`
overwrites its own output freely; `prepare` will not overwrite a working file
without `--force`. To change detection after a page has been read, start again
from raw.

`--conf` sets the detection threshold (default 0.35). Detection and OCR both
download their weights on first run; neither is vendored.

`clean` erases in-bubble text by repainting the bubble's own paper, and paints
free-floating text out as a plain white rectangle. It only touches regions the
agent has given a role, and never those roled `sfx` or `image_text` — both are
artwork. On a page margin the white is invisible; over drawn artwork it is a
visible patch.

`render` needs a Thai font: pass `--font` or set `MANGA_HONYAKU_FONT`. None is
bundled. The font's vowel and tone marks must have zero advance width — Thai
comic faces do, and it is what lets the marks stack without a shaping engine.
Anything the font cannot draw is reported before the page is drawn, because a
missing glyph comes out as an empty box that still looks like lettering.

Thai is laid out inside each region's own box, so the translation sits where the
Japanese sat, and centred on the bubble within it. Lettering is sized as a
fixed fraction of the size the original was lettered at, which `render` recovers
from each region's box and the length of its Japanese. The size is chosen before
the text is wrapped, so the same original size gives the same Thai size
everywhere; a region that cannot hold its line at that size is the only one that
comes down. A region may override that with
`scale`, and ask for a bolder cut with `weight` if `--font-bold` is given — a
chapter heading is set in a display face at twice the ink density of the bubbles
and needs both.
`series/glossary.md`
is read as a word list: without it a transliterated name is broken across lines
as though it were several words.

## Apple Silicon

RT-DETR is pinned to CPU. On the MPS backend it fails inside a float64
operation, and the failure surfaces as an empty result rather than an error.
