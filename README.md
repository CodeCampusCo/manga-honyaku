# manga-honyaku

A manga translation workflow. Code handles geometry — detection, OCR, text
removal, rendering. An LLM agent handles comprehension — reading order, speaker
attribution, and the translation itself.

The original design, and why the work is split this way:
[`docs/specs/2026-07-26-design.md`](docs/specs/2026-07-26-design.md). It predates
the implementation; where it and the code disagree, the code is right.

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

## Starting a new work

This is run through Claude Code, so the way in is a prompt rather than a command.
Paste this, with your own path:

> Start a new work in this repository. The scans are at `/path/to/the/scans`.
> Follow the `new-manga-work` skill: set up the directory, run detect and
> annotate over the first chapter, and show me the boxes so I can check what the
> detector missed before we go any further. Do not translate anything yet.

It will stop and ask you twice, because two of the steps are judgements about a
page and cannot be settled by a number:

> The boxes look right. Prepare the chapter, work out the size bands, and render
> me a few pages beside the originals so I can see whether the lettering is the
> right size.

Then, once the sizes look right:

> Translate chapter 1. Read each page whole before translating any of it, keep
> `characters.md` and `glossary.md` current as you go, and check the recorded
> sources against a fresh OCR read before you render.

And afterwards, whenever a size looks off:

> `loud` is too big. Try 45.

That last one is the loop the whole design exists to make cheap: one number in
`lettering.json`, one re-render, one look.

### The commands underneath

If you would rather drive it yourself, this is what those prompts do.

```sh
mkdir -p series/<work>
echo /path/to/the/scans > series/<work>/raw.txt
```

Then, in this order — two of the steps are yours to judge, not the tool's:

```sh
uv run python -m manga_honyaku.detect   series/<work>
uv run python -m manga_honyaku.annotate series/<work>
```

**Look at `build/*.boxes.png` before going on.** The detector was trained on
comics in general and a new art style is where it fails; if dialogue bubbles are
being missed, stop here, because everything after this assumes the regions exist.
Missed sound effects do not matter — those stay as artwork.

```sh
uv run python -m manga_honyaku.prepare series/<work>
```

OCR runs here, and each region gets a size tag from what the Japanese in its box
was lettered at. The tags are provisional until the work has its own
`lettering.json`: the measurement divides a box by its character count, so the
pages have to be read before the bands can be worked out.

Write `series/<work>/lettering.json` — the shape is in the
`thai-manga-lettering` skill, which also has how to arrive at the numbers — then

```sh
uv run python -m manga_honyaku.prepare series/<work> --retag
```

which re-applies the tags and touches nothing else. It is safe at any point,
including after pages have been translated, which is when you will want it: the
first `sizes` are a guess, and adjusting them is a matter of rendering a chapter
and looking at it beside the original.

`characters.md`, `glossary.md`, `words.txt` and `summary.md` are written as the
pages are read, not before. `style.md` only if this work departs from the
conventions in the skills.

## Commands

Every stage takes the work's directory, then the pages. Naming no page means the
whole work; naming a directory means everything under it.

```sh
uv run python -m manga_honyaku.detect   series/<work>     # -> build/<id>.detector.json
uv run python -m manga_honyaku.annotate series/<work>     # -> build/<id>.boxes.png
uv run python -m manga_honyaku.prepare  series/<work>     # -> pages/<id>.agent.json
#   prepare also OCRs the Japanese into it, and tags each region with the size
#   the original was lettered at; --no-ocr leaves the reading to the agent
#   the agent then reads the page and edits pages/<id>.agent.json
uv run python -m manga_honyaku.clean    series/<work>     # -> build/<id>.clean.png
                                                           #    build/<id>.masks.png
uv run python -m manga_honyaku.render   series/<work>     # -> out/<id>.png
```

```sh
uv run python -m manga_honyaku.render series/<work> X0006          # one page
uv run python -m manga_honyaku.render series/<work> X0006 X0007    # several
uv run python -m manga_honyaku.render series/<work> 01/ch02        # a chapter
```

Pass every page you want in one command rather than one command per page: the
segmenter's dictionary takes about 200ms to build and is built once per run.

```sh
uv run python -m manga_honyaku.sheet out/X0006.png out/X0007.png -o /tmp/look.png
```

`sheet` scales pages down to the largest size a reader keeps, so a batch costs
what one full-resolution page costs. It reports the width each page ended up at.

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
It is in `fonts/`; see `NOTICE`. `--font` and `--font-bold`, or
`MANGA_HONYAKU_FONT` and `MANGA_HONYAKU_FONT_BOLD`, point elsewhere. A region may
ask for the bolder cut with `weight` — a chapter heading is set in a display face
at twice the ink density of the bubbles.

The face carries no `♥ ♡ ★ ☆ ♪ 「」 ○` and no CJK brackets. `render` reports any
character it cannot draw before drawing the page.

Another face works if its vowel and tone marks have zero advance width — Thai
comic faces do, and that is what lets the marks stack without a shaping engine.

## Apple Silicon

RT-DETR is pinned to CPU. On the MPS backend it fails inside a float64
operation, and the failure surfaces as an empty result rather than an error.
