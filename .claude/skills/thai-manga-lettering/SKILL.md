---
name: thai-manga-lettering
description: Use when choosing a wording that has to fit a manga speech bubble, or judging why a rendered page looks wrong — what sets a region's size, why a shorter sentence is usually the wrong fix, and what a word list does to a line break. The whole method is two steps.
---

# Lettering Thai into manga bubbles

## The whole of it

**Set the text into the region's own box, and come down a size while it
overflows.** The box is where the original's lettering sat — the detector already gives it,
and the artist already chose it. It is the right rectangle for the translation
for the same reason it was right for the original: it is the shape that fits
that bubble in that panel. A Japanese bubble is a tall oval because the text ran
down it, so the box comes out tall and narrow, and Thai set into it stacks into
short lines on its own. `อ๋อ อันนี้เอง` becomes `อ๋อ / อันนี้ / เอง` because the
column is narrow, not because anything decided it should.

Overflow has exactly one answer *in the renderer*: a smaller size. Not a
different column, not a finer break point, not a special case for this bubble.
The answers in the wording are below.

## When it will not fit

Even calibrated, four regions in ten come down, and **that is the system working,
not a backlog.** The size a region asks for is measured off the original and the
box is the artist's, so the only thing that could close the gap is a shorter
sentence — and a shorter sentence is usually the worse translation. Ruled on a
six-page A/B: the fuller version ran 31% longer, dropped the share keeping its
asked-for size from 71% to 59%, and won. **A size step is cheaper than a dropped
nuance.** Do not read a low fitted-rate as work to do.

Some cannot be won at any length: **a narrow box cannot hold large horizontal
Thai**, because 64 pixels of width is three characters a line whatever size is
asked for, and the breaker comes down until they fit. Accept it, or let it run
outside its box if it sits on white.

## In a narrow box the size is set by the longest token, not by the length

A word cannot be split, so the size a region can hold is `width ÷ the longest
token`, and everything else about the sentence is irrelevant to it. That makes
the wording, not the box, the thing to move: `เธอนำแสงสว่าง` in an 84px column
draws at 31px because `แสงสว่าง` is one dictionary token, and `เธอนำแสง` — the
same line, one word shorter — draws at 70, against a Japanese 72. **The fix for
a caption lettered half-size is usually a different word of the same meaning, not
a shorter sentence.**

Two consequences worth spelling out:

- **Where one sentence spans several boxes, cut it by their widths.** Put the
  short words in the narrow columns. The clause boundary the Japanese used is not
  binding — it was chosen for a script that runs the other way.
- **A name in `words.txt` is unsplittable by construction**, which is right in a
  bubble and expensive in a display column: `“คุณทามากาวะ` drew at 44 in a 136px
  column asking for 110. A space inside it lets the breaker stack it — and the
  original stacked it too, one character per line, so the break is not a loss.

`regions` prints that width as **`line=`** beside `room=`: `room` is what the box
holds altogether, `line` the longest run it holds without a break. A word longer
than `line` brings the region down however short the sentence is, so a wording
weighed against `room` alone is a guess.

**`fit` is arithmetic about one region; only the rendered page compares it to its
neighbours.** A split that buys a size step can still read as a mistake, because
the same word set whole a page later gives the reader the comparison. Where the
numbers and the page disagree about a wording, the page decides.

**Ask before you apply, not after.** `fit` measures a candidate against the
region's own box and draws nothing, which turns the wording pass from a
render-and-look loop into arithmetic:

```sh
uv run python -m manga_honyaku.fit series/<work> 01/05 F1 "เธอนำแสง"
uv run python -m manga_honyaku.fit series/<work> 01/05     # what is already set
```

`weight` is the other thing in the working file, and it is not size. **Ink
density tells a display face from a body face** — dark pixels over the region's
box against the speech bubbles on the same page; a display face measures about
twice.

## Line breaking

- **Where the original divides one utterance between boxes, each piece has to
  read alone.** It divides where its own script lets it, and a kana reads alone;
  a Thai syllable does not. Kept division for division, every box fits and a size
  probe confirms it, while the reader gets a fragment where the original gave a
  word. Move the cuts between whole words and pay the size step. Fitting is not
  reading, and nothing measures the difference — only the rendered page shows it.

- **Give the segmenter a word list of its own.** One word per line, in a file a
  program reads without interpreting anything — a table in a prose document
  needs parsing rules the document never states, and a later edit breaks them in
  silence. Put in it what means nothing cut in half: names, and transliterations
  no Thai dictionary carries — `ฮารุกะ` otherwise segments as `ฮา|รุ|กะ` and
  lands across two lines.

- **Keep phrases out of that list.** In the dictionary a phrase is one token,
  and a token that will not fit its box brings the whole bubble's size down. One
  twelve-character compound measured 139px against a 96px box, so its caption
  lettered at 22px against a tag worth 34 — and dragged the caption sharing its
  utterance down with it. Split into the two ordinary words it is made of, the
  line breaks between them and both captions keep their size.

- **The dictionary is already full of compounds, and one in a narrow box costs
  the same as a phrase you put there yourself.** `ผู้จัดการ` and `ขอโทษ` are
  single tokens the segmenter will not break, so in a 99px balloon they set the
  size at 39 and at 41 where the split halves set it at 49 and 54 — a third
  more, and the fill goes from a third of the box to nearly all of it. **Try a
  different word first**: `ตบหน้า` is one token and `ฟาดหน้า` is two, and they
  letter at 26 and 39 in the same box, so the synonym buys the whole step and
  costs nothing. Only when no synonym is loose does the space earn its place.
  **Nothing tells you which words are compounds except `fit`'s line list** — the
  guess is wrong in both directions.

- **A space is a break point, so a space inside a word cuts the word in half.**
  Thai writes without spaces, so a space in a target reads as a phrase
  separator and the breaker is free to set a line on it: `ล้ม เหลว` arrives
  as two lines and a word the reader has to reassemble. **When a token will
  not fit, change the word, not the spacing** — that is what the paragraph on
  the longest token is for. Deliberate exceptions exist, and the display
  column above is one, but they are cases a work names rather than a
  technique. `audit` reports every space that falls off a segmenter boundary
  with Thai on both sides; one work ran at one or two a chapter for three
  chapters and then twelve in one.

- **Letter regions that share an utterance at one size.** One sentence at two
  sizes reads as two sentences.

- **A held vowel is one token, and a shout box is a column.** A Japanese cry runs
  down a tall narrow box — one character per line — so the box comes out a
  character and a half wide. Thai lengthens by opening the vowel, and `อ๊าาาาาา`
  has no break point in it, so the breaker cannot stack it and the whole region
  comes down to whatever fits on one line: a cry lettered at conversation size,
  in a column left nine-tenths empty. **Break the run into groups** — `อ๊า าา าา
  าา` stacks four lines at the size the region asked for, which is what the
  original does.
  The same catches any long unbroken transliteration in a narrow box.

## What goes here, and what goes in the work's own files

This file holds **method, and facts about the two scripts** — that a name means
nothing cut in half, that the size a region asks for cannot be named without
guessing. Those hold for the next manga too. A work's own directory holds what
measuring that work produced: its `k`, its page height, its word list, and how
its characters speak.

The test when something new is learned: *would this still be true of a different
manga by a different artist?* If yes it belongs here. If a page, a face or a
measurement told you, it belongs to the work that told you.

How the numbers behind all of this are arrived at, and the machinery that was
built and deleted getting there, is [`maintaining-the-letterer.md`](maintaining-the-letterer.md).
**Nothing in it is needed to translate a chapter** — it is for whoever changes
`render`, sets up a new work, or is about to rebuild something that was tried.

Text placed off-centre or into a sliver of a bubble is a mask problem, not a
lettering one — see the `manga-text-removal` skill.
