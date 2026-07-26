---
name: thai-manga-lettering
description: Use when rendering Thai (or any alphabetic script) into manga speech bubbles — choosing lettering size, breaking lines, placing text inside a bubble's curve, or judging why rendered pages look wrong. Covers the geometry to port from MangaTranslator rather than reinvent, and the Thai-specific rules that differ from it.
---

# Lettering Thai into manga bubbles

Everything here was arrived at by getting it wrong first. The order of the
sections is the order the mistakes were made in.

## Take the geometry from MangaTranslator

`/Users/tama/app/MangaTranslator` (Apache-2.0). Three pieces are worth porting
verbatim, and every attempt at writing them from scratch was worse:

- **`calculate_centroid_expansion_box`** (`core/image/image_utils.py`) — the
  rectangle text may occupy. Distance-transform the mask, keep what is at least
  `padding` deep, take that region's centroid, then ray-cast four ways and
  double the smaller of each opposing pair.

  The step that matters: **when the centroid's depth is under 0.70 of the
  deepest point it is in the waist between two conjoined lobes, so the anchor
  moves to the pole of inaccessibility.** Conjoined bubbles are common, not an
  edge case.

- **`_check_collision`** (`core/text/layout_engine.py`) — test the four corners
  of every laid-out line against the mask. That box is the full extent of each
  axis, so its corners sit outside the curve; a block filling its width
  collides there as a matter of course.

- **`find_optimal_breaks_dp`** (`core/text/text_processing.py`) — Knuth-Plass in
  shape, minimising the sum of slack cubed, plus a penalty when a continuation
  line would start with a short Thai token. That penalty is what stops a break
  inside a compound leaving a stub at the head of the next line.

What is *not* worth porting: their shaping stack. See below.

## Size is chosen before anything is wrapped

Fitting the largest size that happens to go in lets the shape of each box decide
the size. Measured on one page, ten bubbles the artist lettered identically came
out anywhere from 25 px to 45 px.

Instead: a **narrow band**, quoted for a one-megapixel page and scaled by
`sqrt(area / 1e6)` so one setting holds at any scan resolution. Upstream's
defaults are 8–16; against a comic face those letter at about half what the
Japanese did, and **11–22 puts Thai near two thirds of the original**, which is
where upstream's own renders sit. Binary-search within the band.

Then per region, from the working file:

- **`scale`** — the original's own lettering size relative to that page's median.
  Recover it as `sqrt(box_area / japanese_character_count)`: on a real page that
  read every ordinary bubble at 41–46 px and picked out the emphatic ones at
  1.8×, a shout at 1.96×, and inner monologue at 0.58×. Write it into the
  working file; do not leave it to the renderer to guess.

  **The estimate does not work on a single horizontal line** — it reads a
  chapter heading spanning the page as ordinary lettering. Set those by hand
  from the measured ink height.

- **`weight`** — a heading is a display face. Ink density measures it: 0.23 for
  the heading against 0.11 for the bubbles on the same page.

Where the Thai is longer than the Japanese it replaces, coming down in size is
correct and expected. Where it is *much* longer, shorten the line instead — a
four-character Japanese shout cannot be lettered large under a fifteen-character
Thai one.

## Thai in manga is set to the bubble, not to the line

This is the rule that differs from upstream and it is the one that matters most.

Thai is written horizontally, so the obvious thing is to hand the line breaker
the full box width. Its objective is to leave as little of that width unused as
possible, so it returns two long lines every time. **A bubble is taller than it
is wide.** Thai lettering in manga is a stack of short lines, and Thai readers
have read it that way for as long as manga has been translated into Thai.

So: narrow the column a tenth at a time, keep every layout that fits without
colliding, and **choose the one that stands tallest**. Upstream stops at the
first that does not collide, which keeps the widest and shortest block that is
merely legal.

`อ๋อ อันนี้เอง` reads no harder as `อ๋อ / อันนี้ / เอง`, and it fills the bubble.

## Line breaking

- Segment with `pythainlp` — `newmm` is fine. With the DP and the orphan penalty
  in place the engine choice stops mattering: `newmm` mis-segments `บอกว่า` as
  `บอ|กว่า` and the breaker declines that break anyway.
- **Feed the series glossary in as a custom dictionary.** A transliterated name
  is in no Thai dictionary: `ชิโนบุ` segments as `ชิ|โน|บุ` and a character's
  name gets split across lines.
- **Merge punctuation into the token before it.** The segmenter returns `?` and
  `…` as tokens of their own, and a breaker told to stand as tall as it can will
  start a line with one: `เอ๊ะ / ? อ่า…`
- Fall back to TCC clusters only when no size will wrap at word boundaries.
  Reversing that order keeps the text large and splits `ติดต่อมา` as
  `ติดต่|อมา`, which reads as a typo rather than a line break.
- Regions sharing an utterance letter at one size. One sentence at two sizes
  reads as two sentences.

## Fonts

- **No shaping engine is needed.** Thai marks stack above and below the base
  letter, and every Thai comic face gives them zero advance, so Pillow's own
  layout puts them right. `skia-python` and `uharfbuzz` are for fonts that
  position marks through GPOS. A font that did would draw wrongly rather than
  fail, so check a new one by eye before trusting it.
- **Check glyph coverage without a font library.** A missing character renders
  as `.notdef`, so compare its bitmap against a codepoint no font can have
  (`\U000F0000`). This caught `【】◯` drawing as empty boxes that still looked
  like lettering.
- A Thai comic face typically has **no ♥ ♡ ★ ☆ ♪ 「」 ○** at all. A flirtatious
  `♥` is a tone marker: render it in the wording and a drawn-out vowel, which is
  how Thai marks tone anyway.
- `iannnnnJPG` regular is right for dialogue; its bold sits heavier than the
  lettering it replaces. Keep the bold for headings.

## Masks

- **Each lobe of a conjoined bubble needs its own interior.** Cropping each lobe
  to its own outline box cuts the shared interior along a box edge, one lobe
  takes a slice of the other, and text centred in what is left sits off-centre
  in the bubble a reader sees. Find the interior once for the group of
  overlapping outlines and give each lobe what its own outline encloses, with
  the overlap going to the nearer one.

  Two other splits were tried and are worse: nearest-text-centre draws a
  straight bisector across both lobes, and a watershed on the interior's depth
  follows its medial axis and returns the lobes interleaved in stripes.

- **Clearance is for a drawn outline.** A free-floating region's mask is the
  text's own extent; holding letters off the edge of that cost a chapter heading
  a third of its size for nothing.

## Translation feeds the rendering

- **Match the original's length, not only its sense.** The bubble was drawn to
  hold what the Japanese said. Measured as Thai width per Japanese character,
  one page ran from 0.36 to 1.45 — the low end was rendering only the bare
  sense. `〜があって` is "it so happens that", `らしい` is "I hear that",
  `けっこう` is "quite, as these things go", `なんか` hedges the report it
  introduces. Saying those in full is more faithful *and* fills the bubble.
  A line the artist drew short stays short.

## Symptoms and causes

| What it looks like | What it is |
| --- | --- |
| Two long lines in every bubble | Full box width handed to the breaker |
| Sizes swinging across a page | Fitting each bubble to what it can hold |
| One sentence at two sizes | Utterance grouping not applied to the size |
| Text off-centre in a conjoined bubble | Lobe masks cut on a box edge |
| A name split across lines | Glossary not fed to the segmenter |
| Empty boxes that look like letters | Font lacks the glyph; nothing checked |
| Heading no bigger than speech | `weight`/`scale` never set for it |
