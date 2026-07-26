---
name: new-manga-work
description: Use when starting a manga that has not been translated here before — making the work's directory, checking the detector against its art style, calibrating its lettering sizes, and seeding the notes files. Covers the order the steps have to happen in and what to check before going further.
---

# Bringing up a new work

The pipeline is the same for every manga. What is new each time is one
directory, five small files, and a calibration that takes one chapter and a look
with your own eyes.

**Guide the person through this rather than doing it silently.** Two of the steps
are theirs: whether the detector found the bubbles, and whether the lettering
looks right. Both are judgements about a page, and neither survives being
answered by a number. Stop at each, show them what to look at, and wait.

Ask for the path to the scans if it was not given. Do not guess it, and do not
copy or move them.

## 1. The directory, and where the scans are

```
series/<work>/
    raw.txt        one line: the path to the scans
```

Everything else appears as it is needed. `pages/`, `build/` and `out/` are made
by the stages that write into them.

The scans may live anywhere — `raw.txt` points at them, so nothing has to be
copied or moved. A work that keeps its scans inside its own directory as `raw/`
needs no `raw.txt` at all.

Ask what the pages are called before assuming. A page's id is its path under the
scans, so a work stored as `01/ch02/003.jpg` is asked for as `01/ch02/003`, and
`pages/`, `build/` and `out/` take that shape too.

## 2. Detect, and check the recall yourself

```sh
uv run python -m manga_honyaku.detect   series/<work>
uv run python -m manga_honyaku.annotate series/<work>
```

Then **look at `build/*.boxes.png` for a chapter** — through
`manga_honyaku.sheet`, four to a sheet — and count what the detector missed.

This is the one step where stopping is cheap and going on is not. The detector
was trained on comics in general, and a new art style is exactly where it fails:
a bubble with a broken outline, lettering over artwork, a font it has not seen.
If dialogue bubbles are being missed, say so and stop. Everything downstream
assumes the regions are there.

Sound effects and background text being missed does not matter — those are
artwork and stay.

## 3. Prepare, which reads the pages and tags their sizes

```sh
uv run python -m manga_honyaku.prepare series/<work>
```

OCR runs here, into `source` on each region, and each region gets a `size` tag
from what the Japanese in its box was lettered at.

**The tags will be wrong until the work has its own `lettering.json`**, because
the bands that assign them are per work and there is nothing to read yet. That is
the right order anyway: the measurement needs the character count, and the
character count comes from the OCR that runs here.

## 4. Calibrate the lettering

The `thai-manga-lettering` skill has this in full — measure, cluster, put the
band boundaries in the gaps, guess the sizes once, then adjust by eye. Write the
result to `series/<work>/lettering.json`, then

```sh
uv run python -m manga_honyaku.prepare series/<work> --retag
```

which re-applies the tags and touches nothing else in the working files. It is
safe after pages have been translated, which is when it is wanted: a band that
turns out to be in the wrong place is found by reading, not by measuring.

**Step 4 of that recipe is the person's, not yours.** Render a chapter, put the
original and the translation side by side, and ask. Numbers cannot answer whether
lettering looks right, and a first guess that is off by a third looks obviously
off the moment anyone sees it.

## 5. Seed the notes as you read, not before

Nothing here is worth writing until a page has been read, and none of it is
worth guessing.

- **`characters.md`** — after the first chapter, when you know who recurs.
  Identify by costume and props; faces are deformed for effect.
- **`words.txt`** — as names appear. Only what means nothing cut in half.
- **`glossary.md`** — as terms are decided. Per work, always, even where another
  work needed the same word.
- **`summary.md`** — after the first chapter.
- **`style.md`** — only if this work departs from the skills. Most never do.

Read the whole page before translating any of it, and diff every recorded
`source` against a fresh OCR read before rendering a batch. Both are in the
`japanese-to-thai-manga` skill.

## 6. The rest is the ordinary loop

```sh
uv run python -m manga_honyaku.clean  series/<work>
uv run python -m manga_honyaku.render series/<work>
```

Translate, clean, render, look. Re-rendering never re-runs detection or OCR, so
adjusting a line and looking again costs seconds.

## The order that matters

Only two orderings are forced, and both bite quietly:

- **Detection before anything.** Changing it after a page has been read means
  starting that page again; there is no merge.
- **OCR before the size bands.** The measurement divides a box by its character
  count, so the pages have to be prepared before the bands can be worked out —
  which means the first tags are provisional and get re-applied once
  `lettering.json` exists.
