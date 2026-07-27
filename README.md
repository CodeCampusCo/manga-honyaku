# manga-honyaku

A manga translation workflow. Code handles geometry — detection, OCR, text
removal, rendering. An LLM agent handles comprehension — reading order, speaker
attribution, and the translation itself.

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

Detection and reading run on your machine. Once the weights are cached nothing
about the pages leaves it, and `HF_HUB_OFFLINE=1` stops the hub being contacted
at all — every stage still runs. `NOTICE` says what the library asks for and why
the unauthenticated-request warning is not about that.

## Starting a new work

Point Claude Code at the scans and ask:

> Start a new work. The scans are at `/path/to/the/scans`.

It follows the `new-manga-work` skill from there — makes the directory, runs
detection, and stops to show you what the detector found. It stops twice more,
for the lettering size and before the first chapter is translated, because those
are looks at a page rather than numbers. You need no other command to begin.

## A work on disk

One directory per work. Nothing is configured but where the scans are.

```
series/<work>/
    raw.txt              one line: the path to the scans
    lettering.json       the size bands, and what each size is worth in Thai
    words.txt            one Thai word per line; the line breaker's dictionary
    glossary.md          terms, honorifics, agreed transliterations
    characters.md        who they are, and how each one speaks
    summary.md           rolling plot summary
    questions.md         unresolved items

    pages/               <id>.agent.json — the translation
    build/               <id>.detector.json .boxes.png .clean.png .masks.png
    out/                 <id>.png
```

A page is identified by its path under the scans, without the suffix: `X0006`,
or `01/ch02/003` where a work ships as volume and chapter directories. `pages/`,
`build/` and `out/` take whatever shape the scans have, so neither layout is a
case anything handles.

`pages/` is kept apart from `build/` because everything in `build/` rebuilds from
the scans in seconds and nothing in `pages/` rebuilds at all.

## Commands

For driving it yourself. Every stage takes the work's directory, then the pages.
Naming no page means the whole work; naming a directory means everything under it.

```sh
uv run python -m manga_honyaku.detect   series/<work>     # -> build/<id>.detector.json
uv run python -m manga_honyaku.annotate series/<work>     # -> build/<id>.boxes.png
uv run python -m manga_honyaku.prepare  series/<work>     # -> pages/<id>.agent.json
#   prepare also OCRs the Japanese into it, and tags each region with the size
#   the original was lettered at; --no-ocr leaves the reading to the agent
#   the agent then reads the page and edits pages/<id>.agent.json
uv run python -m manga_honyaku.check    series/<work>     # before rendering
uv run python -m manga_honyaku.clean    series/<work>     # -> build/<id>.clean.png
                                                           #    build/<id>.masks.png
uv run python -m manga_honyaku.render   series/<work>     # -> out/<id>.png
```

`check` reads every region again and reports any whose text belongs to a
different region on the same page — two lines written onto each other's ids.
Nothing else finds that: the Thai reads plausibly in both places, so re-reading
the page does not show it. It exits non-zero when it finds one. Readings the
agent corrected are counted, not listed, unless you ask with `--differences`.

```sh
uv run python -m manga_honyaku.render series/<work> X0006          # one page
uv run python -m manga_honyaku.render series/<work> X0006 X0007    # several
uv run python -m manga_honyaku.render series/<work> 01/ch02        # a chapter
```

Pass every page you want in one command rather than one command per page: the
segmenter's dictionary takes about 200ms to build and is built once per run.

```sh
uv run python -m manga_honyaku.sheet out/X0006.png out/X0007.png -o /tmp/look.png
uv run python -m manga_honyaku.chapters series/<work> X0006-X0008
```

`chapters` prints what the reading found on the pages you name, from whichever
chapter file holds them, with the rule at the top of those files attached.

`sheet` scales pages down to the size past which reading stops getting easier,
lays them out together, and reports what the result costs to read.
`--crop X1,Y1,X2,Y2` takes a box out of each image first, for reading one bubble
at full detail.

## Stages

The pipeline runs one way — each stage reads the artifact before it and writes
the one after.

`pages/<id>.agent.json` is the working file and the only one that cannot be
rebuilt: everything the agent works out about a page is written into it. `detect`
overwrites its own output freely; `prepare` will not overwrite a working file
without `--force`. To change detection after a page has been read, start again
from the scans.

`--conf` sets the detection threshold (default 0.35). Detection and OCR both
download their weights on first run; neither is vendored.

`clean` erases in-bubble text by repainting the bubble's own paper, and paints
free-floating text out as a plain white rectangle. It only touches regions the
agent has given a role, and never those roled `sfx` or `image_text` — both are
artwork. On a page margin the white is invisible; over drawn artwork it is a
visible patch.

`render` lays the Thai into each region's own box — where the original's
lettering sat — breaks it to that column, and comes down a size while it
overflows. Nothing else: the box is the right rectangle for the translation for
the same reason it was right for the original.

Size comes from a tag on the region, written once when the page was prepared from
what the Japanese in that box was lettered at. `lettering.json` says what each tag
is worth in Thai, quoted against a stated page height, so it can be adjusted by
eye without anything being measured again.

`words.txt` is the line breaker's dictionary: without it a transliterated name is
broken across lines as though it were several words. Keep phrases out of it — a
phrase there is a single token, and a token that will not fit its box brings the
whole bubble's size down.

## Fonts

`render` letters in **2005_iannnnnJPG**, a Thai comic face by iannnnn released
free for commercial use through [f0nt.com](https://www.f0nt.com/release/iannnnnjpg/).
It is in `fonts/`; see `NOTICE`. A work names its own face under `font` in
`lettering.json`, which is where it belongs: `room` on each region counts that
face's widths, so rendering in a different one would letter to a budget nothing
measured. `--font` overrides it for an experiment, and `MANGA_HONYAKU_FONT` sets
the fallback for a work that names none. A region may ask for the bolder cut with
`weight` — a chapter heading is set in a display face at twice the ink density of
the bubbles.

The face carries no `♥ ♡ ★ ☆ ♪ 「」 ○` and no CJK brackets. `render` reports any
character it cannot draw before drawing the page.

Another face works if its vowel and tone marks have zero advance width — Thai
comic faces do, and that is what lets the marks stack without a shaping engine.

## Apple Silicon

RT-DETR is pinned to CPU. On the MPS backend it fails inside a float64
operation, and the failure surfaces as an empty result rather than an error.

## Contributing

[`CONTRIBUTING.md`](CONTRIBUTING.md). The short of it: you cannot run the
pipeline without your own scans, but `uv run pytest` runs without any, and
`master` takes pull requests only.

## Licence

Apache-2.0; see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE). The detection stage
is derived from an Apache-2.0 project, model weights are downloaded rather than
distributed, and the Thai face is included under its designer's release terms —
`NOTICE` says which is which.

**What is not in here is any manga.** `series/` is ignored, and stays ignored: a
work's scans, its translation, and everything derived from them are yours and are
not this repository's to carry. Point `raw.txt` at scans you have the right to
use.

## Design

[`docs/specs/2026-07-26-design.md`](docs/specs/2026-07-26-design.md) is the
original design — why the work is split this way, and what was tried before what
is here now. It predates the implementation; where it and the code disagree, the
code is right, and it says so where it knows it is wrong.
