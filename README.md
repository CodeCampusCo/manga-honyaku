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

```sh
uv run python -m manga_honyaku.detect   raw/*.jpg --work work   # -> work/<page>.json
uv run python -m manga_honyaku.annotate raw/*.jpg --work work   # -> work/<page>.boxes.png
uv run python -m manga_honyaku.clean    raw/*.jpg --work work   # -> work/<page>.clean.png
                                                                #    work/<page>.masks.png
```

`--conf` sets the detection threshold (default 0.35).

`clean` erases in-bubble text only. Free-floating text is left in place: most of
it is sound effects, which must not be disturbed, and the rest sits on artwork
that only an inpainting model could restore.

`render` is not implemented yet.

## Apple Silicon

RT-DETR is pinned to CPU. On the MPS backend it fails inside a float64
operation, and the failure surfaces as an empty result rather than an error.
