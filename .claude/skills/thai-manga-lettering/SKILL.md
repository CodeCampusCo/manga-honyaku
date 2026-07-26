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
| Marking glossary terms unsplittable | `ซากุระ` coming back as `ซา / กุ / ระ` | A patch on the ladder, and it had to be threaded through four functions. |

The pattern is worth naming: **when a fix needs a fix, the thing being fixed is
usually the wrong mechanism.** Three of the six above exist only to repair the
two above them.

The one thing worth porting from MangaTranslator is
**`find_optimal_breaks_dp`** (`core/text/text_processing.py`) — Knuth-Plass in
shape, minimising the sum of slack cubed, plus a penalty when a continuation line
would start with a short Thai token. That is the line breaker doing its own job,
not a search around it. Their geometry and shaping stack are not worth porting.

## Size comes from the original, in steps

A letterer works from a small set of sizes. **Give the translation the same set
and let the original choose which one each line gets.**

Recover the original's size as `sqrt(box_area / japanese_character_count)` —
Japanese sets on a square grid, so that holds whichever way the text ran.
Measure it across a chapter and the steps appear: on one, 154 of 212 bubbles
fell between 39 and 57px, a tail below, a tail above, six one-off panels far
above.

Write the steps in `series/lettering.md`: for each, the multiple of the base size
the translation is set at and the ceiling in the original's own pixels that
selects it. Then **write nothing per region** — choosing a step is measurement.

- **Keep the ceilings absolute, in the original's pixels.** Normalise against a
  page's own median and a page the artist lettered loud comes back ordinary.
- **Steps are for bubbles.** Free-floating text is not speech and belongs to no
  set; it fills the box it was drawn into. A chapter heading is this case.
- **Exclude a pause-only bubble from the measurement.** Its box is sized for a
  beat of silence; one character in a large box reads as enormous lettering.
- **A step that overflows brings that one region down; the step does not move.**

`weight` is the one thing left in the working file, and it is not size. **Ink
density tells a display face from a body face** — dark pixels over the region's
box against the speech bubbles on the same page; a display face measures about
twice.

## Line breaking

- Segment with `pythainlp` — `newmm` is fine. With the DP and the orphan penalty
  in place the engine stops mattering: `newmm` mis-segments `บอกว่า` as
  `บอ|กว่า` and the breaker declines that break anyway.
- **Feed the series glossary in as a custom dictionary.** A transliterated name
  is in no Thai dictionary: `ชิโนบุ` segments as `ชิ|โน|บุ` and a character's
  name lands across two lines.
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
| Sizes swinging across a page | Fitting each bubble to what it can hold instead of to a step |
| One sentence at two sizes | Utterance grouping not applied to the size |
| A name split across lines | Glossary not fed to the segmenter |
| A line opening with `?` or a stray `“` | Punctuation attached to the wrong side |
| Empty boxes that look like letters | Font lacks the glyph; nothing checked |
| Heading no bigger than speech | Sized from the step ladder instead of filling its box |
| A pause bubble lettered enormous | Its one character measured against its whole box |
| A loud page comes back ordinary | Sizes normalised against that page's own median |

Text placed off-centre or into a sliver of a bubble is a mask problem, not a
lettering one — see the `manga-text-removal` skill.
