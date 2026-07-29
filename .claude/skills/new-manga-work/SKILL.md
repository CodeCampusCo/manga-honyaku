---
name: new-manga-work
description: Use when starting a manga that has not been translated here before — setting up the work's directory, checking the detector against its art style, calibrating its lettering multiplier, and seeding the notes files. Covers the order the steps have to happen in, and the two points where the person has to look at a page before you go on.
---

# Bringing up a new work

**Do the setup yourself and narrate it.** The person should need to give you a
path and then answer two questions about what they see. Do not hand them shell
commands to run, and do not ask them to create files.

Two of the steps are theirs, and neither can be settled by a number:

1. **Did the detector find the bubbles on this art style?**
2. **Is the lettering the right size?**

At each, show them what to look at, say what you would conclude, and wait. Those
are the only two places to stop.

## 1. Set the work up

Ask for the path to the scans if it was not given, and ask what to call the work
if the path does not make it obvious. Then:

```sh
mkdir -p series/<work>
echo <path to the scans> > series/<work>/raw.txt
```

The scans stay where they are — nothing is copied, moved or symlinked. A work
whose scans live inside its own directory as `raw/` needs no `raw.txt`.

Look at what is actually in the scan directory before going further. A page's id
is its path under the scans, so `01/ch02/003.jpg` is asked for as `01/ch02/003`,
and `pages/`, `build/` and `out/` take that shape too. Say which shape this work
has rather than assuming it is flat.

## 2. Detect, then stop

```sh
uv run python -m manga_honyaku.detect   series/<work>
uv run python -m manga_honyaku.annotate series/<work>
```

Build a sheet of `build/*.boxes.png` — `manga_honyaku.sheet`, four pages to a
sheet — look at it yourself, and show it to them with a count of what you think
was missed.

This is the one step where stopping is cheap and going on is not. The detector
was trained on comics in general, and a new art style is exactly where it fails:
a bubble with a broken outline, lettering laid over artwork, a face it has not
seen. If dialogue bubbles are being missed, say so plainly and stop — everything
downstream assumes the regions are there, and no later stage can add them.

Sound effects and background text being missed is the desired outcome. Those are
artwork and stay.

## 3. Prepare

```sh
uv run python -m manga_honyaku.prepare series/<work>
```

OCR runs here into `source`, and each region gets a `size` — a number in the
page's own pixels, measured from its box and the Japanese in it.

That ordering is forced: the measurement divides a box by its character count,
and the character count comes from the OCR that runs here.

## 4. Calibrate the lettering, then stop

One number, `k`, turns that measurement into Thai pixels. Finding it needs a
translated chapter to look at, and it has a knee past which raising it does
nothing — the `thai-manga-lettering` skill has the method under *Starting a new
work*. Write `series/<work>/lettering.json`, then

```sh
uv run python -m manga_honyaku.prepare series/<work> --retag
```

which re-applies the tags and touches nothing else. It is safe after pages have
been translated, which is when it is usually wanted.

Then render a few pages, put them beside the originals in one sheet, and **stop
and ask**. A first guess that is off by a third is obvious to anyone looking and
invisible to every measurement you can take. Expect two or three rounds; each
round is one number and one re-render.

## 5. Seed the notes as you read, never before

- **`characters.md`** — after the first chapter, when you know who recurs.
- **`words.txt`** — as names appear. Only what means nothing cut in half.
- **`glossary.md`** — as terms are decided. Per work, even where another work
  needed the same word.
- **`summary.md`** — after the first chapter.
- **`questions.md`** — at the end of each chapter: what it left open. What it
  answered goes to `characters.md`, and the item leaves this file. Easy to
  forget, because nothing in the pipeline asks for it.
- **`style.md`** — only if this work departs from the skills. Most never do.

## 6. Then the ordinary loop

Read a chapter and write down what you saw, translate it, then

```sh
uv run python -m manga_honyaku.check  series/<work>
uv run python -m manga_honyaku.clean  series/<work>
uv run python -m manga_honyaku.render series/<work>
```

Re-rendering never re-runs detection or OCR, so adjusting a line and looking
again costs seconds. Reading the whole chapter before translating any of it,
what to write down while reading, and why `check` runs before rendering are all
in the `japanese-to-thai-manga` skill.

## The two orderings that bite quietly

- **Detection before anything.** Changing it after a page has been read means
  starting that page again; there is no merge.
- **OCR before the sizes**, for the reason in step 3. `--retag` re-applies them
  from the working files without touching anything else, so `k` can move after
  pages have been read.
