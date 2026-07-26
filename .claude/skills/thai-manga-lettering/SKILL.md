---
name: thai-manga-lettering
description: Use when fitting Thai (or any alphabetic script) into manga speech bubbles — choosing lettering size, breaking lines, placing text inside a bubble's curve, or judging why rendered pages look wrong. Covers the geometry worth porting from MangaTranslator and the Thai-specific rules that differ from it.
---

# Lettering Thai into manga bubbles

## Where each decision lives

| | Owns | Test |
| --- | --- | --- |
| **Code** | Measuring and executing: safe box, collision test, line breaker, drawing, reporting what it could not do. | Could a person disagree about the answer? Then it is not code's. |
| **This skill** | Method and invariant. | Would it hold for another work in another genre? |
| **`series/lettering.md`** | Every number and name for one work: the steps, the clearance, the face's gaps, this work's departures. | Would another work need a different value? |
| **`work/<page>.agent.json`** | One region's exception where no measurement can reach it: `weight`, `lines`. Never size. | Is this about this bubble rather than this work? |

Numbers in this file are evidence for a method, not values to reuse — copying
one into a new work skips the measuring. And measure anything measurable: a
field in the working file that a program could derive will go stale, disagree
with the page, and be believed anyway.

## Port the geometry, don't reinvent it

From `/Users/tama/app/MangaTranslator` (Apache-2.0). Every attempt at writing
these from scratch was worse:

- **`calculate_centroid_expansion_box`** (`core/image/image_utils.py`) — the
  rectangle text may occupy. Distance-transform the mask, keep what is at least
  `padding` deep, take that region's centroid, ray-cast four ways, double the
  smaller of each opposing pair. **When the centroid's depth is under 0.70 of
  the deepest point, move the anchor to the pole of inaccessibility** — it is
  sitting in the waist between two conjoined lobes, and those are common.

- **`_check_collision`** (`core/text/layout_engine.py`) — test the four corners
  of every laid-out line against the mask. A line's box is the full extent of
  each axis, so its corners sit outside the curve of an oval.

- **`find_optimal_breaks_dp`** (`core/text/text_processing.py`) — Knuth-Plass in
  shape, minimising the sum of slack cubed, plus a penalty when a continuation
  line would start with a short Thai token.

Their shaping stack is not worth porting; see *Fonts*.

## Size comes from the original, in steps

A letterer works from a small set of sizes. **Give the translation the same set
and let the original choose which one each line gets.**

Recover the original's size as `sqrt(box_area / japanese_character_count)` —
Japanese sets on a square grid, so that holds whichever way the text ran.
Measure it across a chapter and the steps appear: on one, 154 of 212 bubbles
fell between 39 and 57px, a tail below, a tail above, six one-off panels far
above.

Write the steps in `series/lettering.md`: for each, the multiple of the base
size the translation is set at and the ceiling in the original's own pixels that
selects it. Then **write nothing per region** — choosing a step is measurement.

- **Keep the ceilings absolute, in the original's pixels.** Normalise against a
  page's own median and a page the artist lettered loud comes back ordinary.
- **Steps are for bubbles.** A free-floating region's box was drawn around the
  lettering itself, so it fills its box and needs no ladder. A chapter heading
  is this case.
- **Exclude a pause-only bubble from the measurement.** Its box is sized for a
  beat of silence; one character in a large box reads as enormous lettering.
- **A step that overflows brings that one region down; the step does not move.**
  On one chapter 190 of 202 regions landed exactly on their step.

`weight` is what is left in the working file, and it is not size. **Ink density
tells a display face from a body face** — dark pixels over the region's box
against the speech bubbles on the same page; a display face measures about twice.

## Set the Thai to the bubble, not to the line

This is the rule that differs from upstream and it matters most. It is an
invariant of Thai manga, so a series file should mention it only to record a
departure.

A bubble is a tall oval because Japanese ran down it. Hand the line breaker the
full box width and its objective — leave as little width unused as possible —
returns two long lines every time. **Thai lettering in manga is a stack of short
lines, and Thai readers have read it that way for as long as there has been Thai
manga.**

So: narrow the column a tenth at a time, keep every layout that fits without
colliding, and **choose the one that stands tallest**. Upstream stops at the
first that does not collide, which keeps the widest, shortest legal block.

`อ๋อ อันนี้เอง` reads no harder as `อ๋อ / อันนี้ / เอง`, and it fills the bubble.

### Break finer before you letter smaller

Three grains, tried in this order **inside** the size search, so the size only
comes down when the finest grain still overflows:

1. **words** — the segmenter's own breaks
2. **syllables** — pythainlp `subword_tokenize(engine="dict")`: `ติด|ต่อ|มา`,
   `ขอบ|คุณ`, `อะ|ไร|นะ`
3. **clusters** — `engine="tcc_p"`, for the word no syllable will fit either

`อะไรนะ` set as `อะ / ไร / นะ` and `โอ้โห` as `โอ้ / โห` are ordinary Thai manga
lettering, and they hold the size the original asked for. Put the grain loop
around the size search instead and every narrow bubble buys its word boundaries
by shrinking — which is the trade the wrong way round.

`ssg` and `han_solo` segment syllables too but each wants a package of its own;
`dict` needs nothing and splits the same way on this material.

## Line breaking

- Segment with `pythainlp` — `newmm` is fine. With the DP and the orphan penalty
  in place the engine stops mattering: `newmm` mis-segments `บอกว่า` as
  `บอ|กว่า` and the breaker declines that break anyway.
- **Feed the series glossary in as a custom dictionary.** A transliterated name
  is in no Thai dictionary: `ชิโนบุ` segments as `ชิ|โน|บุ` and a character's
  name lands across two lines.
- **Attach punctuation to the word it leans on** — a closing mark to the word
  before, an opening mark to the word after. The segmenter returns `?`, `…` and
  `“` as tokens of their own, and a breaker told to stand tall will start a line
  with one: `เอ๊ะ / ? อ่า…`, or leave `ว่า “` hanging.
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
| Two long lines in every bubble | Full box width handed to the breaker |
| Sizes swinging across a page | Fitting each bubble to what it can hold |
| One sentence at two sizes | Utterance grouping not applied to the size |
| Small text with tidy word breaks | Grain loop outside the size search |
| A name split across lines | Glossary not fed to the segmenter |
| A line opening with `?` or a stray `“` | Punctuation attached to the wrong side |
| Empty boxes that look like letters | Font lacks the glyph; nothing checked |
| Heading no bigger than speech | Sized from the ladder instead of filling its box |
| A pause bubble lettered enormous | Its one character measured against its whole box |
| A loud page comes back ordinary | Sizes normalised against that page's own median |

Text placed off-centre or into a sliver of a bubble is a mask problem, not a
lettering one — see the `manga-text-removal` skill.
