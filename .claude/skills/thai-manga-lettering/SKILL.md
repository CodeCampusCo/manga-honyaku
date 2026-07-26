---
name: thai-manga-lettering
description: Use when fitting Thai (or any alphabetic script) into manga speech bubbles — choosing lettering size, breaking lines, or judging why rendered pages look wrong. The whole method is two steps; most of this file is about what not to build.
---

# Lettering Thai into manga bubbles

## The whole of it

**Set the text into the region's own box, and come down a size while it
overflows.** That is the method. There is nothing else.

The box is where the original's lettering sat — the detector already gives it,
and the artist already chose it. It is the right rectangle for the translation
for the same reason it was right for the original: it is the shape that fits
that bubble in that panel. A Japanese bubble is a tall oval because the text ran
down it, so the box comes out tall and narrow, and Thai set into it stacks into
short lines on its own. `อ๋อ อันนี้เอง` becomes `อ๋อ / อันนี้ / เอง` because the
column is narrow, not because anything decided it should.

Overflow has exactly one answer: a smaller size. Not a different column, not a
finer break point, not a special case for this bubble.

## What not to build

Every one of these was built, shipped, and deleted. They are listed because each
looked necessary at the time, and each was a way of recovering a column the box
had already given:

| Machinery | What it was for | Why it went |
| --- | --- | --- |
| A centroid-expansion rectangle from the mask | Finding a column inside the bubble curve | The box is the column. The computed one came out 86% of the bubble's width — wider than the original's own lettering — so short phrases fit on one line and never stacked. |
| A corner collision test against the mask | Keeping lines inside the curve | Only needed because the computed rectangle was not inside the curve. With the box, nothing to test: one line crossed the outline in 668. |
| Narrowing the column a tenth at a time, keeping the tallest layout | Getting a stack out of a too-wide column | A search for the column the box gives for free. It also needed a squeeze count, which needed tuning, which was wrong. |
| A ladder of finer break points — word, syllable, cluster | Breaking a phrase the segmenter returns whole | Only fired because the column was too wide to force a break. |
| Rejoining splits inside a run of repeated letters | `จางงง` coming back as `จาง / งง` | A patch on the ladder. |
| Marking word-list terms unsplittable | a name coming back as three syllables | A patch on the ladder, and it had to be threaded through four functions. |

The pattern is worth naming: **when a fix needs a fix, the thing being fixed is
usually the wrong mechanism.** Three of the six above exist only to repair the
two above them.

The one thing worth porting from MangaTranslator is
**`find_optimal_breaks_dp`** (`core/text/text_processing.py`) — Knuth-Plass in
shape, minimising the sum of slack cubed, plus a penalty when a continuation line
would start with a short Thai token. That is the line breaker doing its own job,
not a search around it. Their geometry and shaping stack are not worth porting.

## Size comes from the original: a tag, and a stylesheet

A letterer works from a small set of sizes. **Give the translation the same set,
let the original choose which one each region gets, and keep what each one is
worth somewhere a person can change it by eye.** That is a tag on the element and
a stylesheet beside it, and the split is the same one HTML makes for the same
reason.

- **Measure once, when the page is prepared, and write the answer down.**
  `sqrt(box_area / japanese_character_count)` — Japanese sets on a square grid,
  so it holds whichever way the text ran. The number is a property of the
  artwork and never changes, so measuring it at every render is work done
  repeatedly to reach the same answer.
- **Cluster the measurements to find the bands, once.** The artist's own sizes
  come out in a handful of clumps with gaps between them; put the boundaries in
  the gaps. 656 bubbles across three chapters clustered at 41, 52, 69 and 109px.
  Do this per work — but check it, because it may not move: those three chapters
  had medians of 46.2, 45.4 and 45.9.
- **Store the tag, not the size.** `"size": "loud"` in the working file. What
  `loud` is worth in Thai belongs in the stylesheet, because it is the one thing
  here a person has to judge with their eyes rather than measure.
- **Do not average, and do not chase precision.** Take a first value, render,
  look, adjust the one number. The measurement's job was to sort regions into
  groups; the group's size is not a measurement at all.
- **Tags are for bubbles.** Free-floating text is not speech and belongs to no
  set; it fills the box it was drawn into. A chapter heading is this case.
- **Exclude a pause-only region.** Its box is sized for a beat of silence; one
  character in a large box measures as enormous lettering.
- **A tag that overflows brings that one region down; the tag does not move.**

Why bands at all, rather than `thai = measured × k`? Because the measurement is
noisy — the detector's box is looser on some regions than others, and
punctuation and furigana count as characters. Across 46 groups of bubbles that
were one sentence in the original, and so were certainly lettered the same, the
measured sizes spread by 10% at the median and 32% at the ninth decile, and 11
of the 46 straddled a band boundary. A continuous mapping puts that noise
straight onto the page.

`weight` is the other thing in the working file, and it is not size. **Ink
density tells a display face from a body face** — dark pixels over the region's
box against the speech bubbles on the same page; a display face measures about
twice.

## Starting a new work

The method transfers; none of the numbers do. Every work has its own hand, and
every scan its own resolution. The whole calibration is one file:

```json
{
  "page_height": 1600,
  "line_spacing": 1.32,
  "floor": 9,
  "bands": { "quiet": 35, "normal": 47, "loud": 60, "shout": 88 },
  "sizes": { "quiet": 24, "normal": 34, "loud": 50, "shout": 67, "display": 101 }
}
```

`bands` is the ceiling in the **original's** pixels that gives a region its tag,
read once when the page is prepared. `sizes` is what each tag is worth in **the
translation's** pixels, read at every render. `page_height` is the page both are
quoted for, so the same file survives a rescan at another resolution — without
it, a larger scan measures larger throughout and puts every bubble in the
loudest band there is.

Five steps, once per work:

1. **Detect and prepare a chapter.** Nothing here needs the translation.
2. **Measure every region**: `sqrt(box_area / japanese_character_count)`.
3. **Cluster the measurements and look at where they clump.** One work came out
   at 41, 52, 69 and 109px with gaps between; the boundaries go in the gaps, not
   at even intervals. Four or five clumps is what to expect — a letterer works
   from a small set, which is the whole premise.
4. **Take a first `sizes` from the clump centres and render.** Do not average, do
   not tune the numbers on paper. The clump centres are in the original's script
   at the original's proportions; the translation's script has its own, and only
   a person looking at a page can say by how much.
5. **Adjust one number, render, look again.** That loop is the calibration. It
   converges in a few passes and nothing is ever measured again.

Steps 1–3 are measurement and belong to the machine. Steps 4–5 are judgement and
belong to a person — which is exactly why the sizes live in a file of their own
rather than anywhere near the code.

## Line breaking

- Segment with `pythainlp` — `newmm` is fine. With the DP and the orphan penalty
  in place the engine stops mattering: `newmm` mis-segments `บอกว่า` as
  `บอ|กว่า` and the breaker declines that break anyway.
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
- **Attach punctuation to the word it leans on** — a closing mark to the word
  before, an opening mark to the word after. The segmenter returns `?`, `…` and
  `“` as tokens of their own, and a line will otherwise open with one.
- **Letter regions that share an utterance at one size.** One sentence at two
  sizes reads as two sentences.

## Fonts

- **No shaping engine is needed.** Thai marks stack above and below the base
  letter and every Thai comic face gives them zero advance, so basic layout puts
  them right. `skia-python` and `uharfbuzz` are for fonts that position marks
  through GPOS; such a font would draw wrongly rather than fail, so look at a new
  one before trusting it.
- **Check glyph coverage without a font library.** A missing character renders
  as `.notdef`, so compare its bitmap against a codepoint no font can have
  (`\U000F0000`). This caught `【】◯` drawing as empty boxes that still looked
  like lettering.
- **Letter dialogue in the regular cut.** A comic face's bold sits heavier than
  the lettering it replaces and reads as shouting; keep it for headings.

## Symptoms and causes

| What it looks like | What it is |
| --- | --- |
| Two long lines in every bubble | Something other than the region's box handed to the breaker |
| Sizes swinging across a page | Fitting each bubble to what it can hold instead of to its tag |
| One sentence at two sizes | Utterance grouping not applied to the size |
| A name split across lines | Not in `words.txt` |
| A line opening with `?` or a stray `“` | Punctuation attached to the wrong side |
| Empty boxes that look like letters | Font lacks the glyph; nothing checked |
| Heading no bigger than speech | Given a tag instead of filling its own box |
| A pause bubble lettered enormous | Its one character measured against its whole box |
| A loud page comes back ordinary | Sizes normalised against that page's own median |

Text placed off-centre or into a sliver of a bubble is a mask problem, not a
lettering one — see the `manga-text-removal` skill.
