---
name: new-manga-work
description: Use when starting a manga that has not been translated here before — setting up the work's directory, checking the detector against its art style, calibrating its lettering multiplier, and writing the work's own notes files from the defaults in `defaults.md` beside it. Covers the order the steps have to happen in.
---

# Bringing up a new work

**Do the setup yourself and narrate it.** The person should have to give you
nothing but a path. Do not hand them shell commands to run, and do not ask them to create
files.

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

## 2. Detect

```sh
uv run python -m manga_honyaku.detect   series/<work>
uv run python -m manga_honyaku.annotate series/<work>
```

Build a sheet of `build/*.boxes.png` — `manga_honyaku.sheet`, four pages to a
sheet — and look at it.

The detector was trained on comics in general, and a new art style is exactly
where it fails: a bubble with a broken outline, lettering laid over artwork, a
face it has not seen. If dialogue bubbles are being missed, say so plainly —
a region the detector missed has to be added to the working file by hand — the
`detect` rows of the working-file table in `AGENTS.md` say what it carries — and
nothing adds it for you.

Sound effects and background text being missed is the expected outcome. Where a
scene needs one drawn, its region is added by hand.

## 3. Prepare

```sh
uv run python -m manga_honyaku.prepare series/<work>
```

This runs before `lettering.json` exists. `size` changes again only when a box
does; `room` is re-measured by `--retag` whenever `lettering.json` moves.

OCR runs here into `source`, and each region gets a `size` — a number in the
page's own pixels, measured from its box and the Japanese in it.

That ordering is forced: the measurement divides a box by its character count,
and the character count comes from the OCR that runs here.

## 4. Write the work's notes files

[`defaults.md`](defaults.md), beside this file, holds the Thai manga defaults,
and this is where they land. Copy each row whole — nothing downstream opens
`defaults.md`, so what is left out is gone.

| From `defaults.md` | Into |
| --- | --- |
| the opening paragraph | the top of `voice.md` |
| *Pronouns are re-chosen, not translated* — the whole section, prose and grid | `characters.md` |
| *Honorifics carry the same information — read them* — the whole section | `glossary.md` |
| *Why an accurate line still reads stiff*, *Politeness lands once per utterance*, *Thai lengthens by opening the vowel*, *Conventions that hold across works* — whole | `voice.md` |

A work already standing keeps the files it has: a default changed after its
bring-up does not reach it.

- **`voice.md`** — **the one that comes before the others.** Where the work
  already has one, use it and do not rewrite it. Otherwise copy those four sections of
  `defaults.md` in under its opening paragraph, then add **a dozen lines of your own** under a heading of their own: what
  kind of story this is, how its people sound in Thai, how far it goes toward
  Thai idiom, and anything whose shape has to survive because a joke is built
  on it.
- **`characters.md`** — **before the first page is read.** Placing each person on
  a row is what waits for the first chapter.
- **`glossary.md`** — the honorifics rows first, then terms as they are decided.
- **`words.txt`** — as names appear.
- **`summary.md`** — after the first chapter.
- **`questions.md`** — at the end of the first chapter: what it left open.
- **`style.md`** — **always**, with both headings and "nothing yet" under each:
  *Where this work departs from the skills*, and *What this artist does
  normally*. Nothing later creates this file.
- **`handoff.md`** — at the end of the first session.

## 5. Calibrate the lettering, after the first chapter is translated

One number, `k`, turns that measurement into Thai pixels. **It is judged on set
Thai, so there is nothing to calibrate against until a chapter has been
translated** — hand chapter 1 to `japanese-to-thai-manga` at the shipped `k`,
let it come back cleaned and rendered, then calibrate here. It has a
knee past which raising it does nothing. The method is in
[`../thai-manga-lettering/maintaining-the-letterer.md`](../thai-manga-lettering/maintaining-the-letterer.md),
under *Calibrating `k`, once per work*. Write `series/<work>/lettering.json`, then

```sh
uv run python -m manga_honyaku.prepare series/<work> --retag
```

which re-measures `size` and the `room` that follows, and touches nothing else. It is safe after pages have
been translated, which is when it is usually wanted.

Then render a few pages and build two sheets, one `--show out` and one
`--show raw`, over the same page ids. A first
guess that is off by a third is obvious to anyone looking and invisible to every
measurement you can take. Expect two or three rounds; each round is one number
and one re-render.

## 6. Then hand over

The work is up. `japanese-to-thai-manga` takes it from here.

## The two orderings that bite quietly

- **Detection before anything.** Re-running `detect` over a page that has been
  read rewrites its working file, and there is no merge. Correcting one box is
  different: edit it and `prepare --retag`.
- **OCR before the sizes**, for the reason in step 3. `--retag` re-applies them
  from the working files without touching anything else, so `k` can move after
  pages have been read.
