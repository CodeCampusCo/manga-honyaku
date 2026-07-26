---
name: thai-manga-lettering
description: Use when rendering Thai (or any alphabetic script) into manga speech bubbles — choosing lettering size, breaking lines, placing text inside a bubble's curve, or judging why rendered pages look wrong. Covers the geometry to port from MangaTranslator rather than reinvent, and the Thai-specific rules that differ from it.
---

# Lettering Thai into manga bubbles

Everything here was arrived at by getting it wrong first. The order of the
sections is the order the mistakes were made in.

## Where each decision lives

Four places, and a decision belongs in exactly one of them. When this file and a
series file appear to disagree, the series file is right about that work and this
file is wrong to have said it.

| | Owns | Test |
| --- | --- | --- |
| **Code** | Measurement and execution: the mask, the safe box, the collision test, the line breaker, drawing, and reporting what it could not do. | Could a person disagree about the answer? If yes it does not belong here. |
| **This skill** | Method and invariant. How to find a work's size steps; how to tell a display face from body lettering; that a stack of short lines is how Thai is set in manga at all. | Would it still hold for a different work in a different genre? |
| **`series/lettering.md`** | Every number and name for one work: the size steps, the clearance, what the face cannot draw, and any place this work departs from the invariants. | Would another work need a different value here? |
| **`work/<page>.agent.json`** | One region's exception, and only where measurement cannot reach it: `weight`, `lines`. Never size. | Is this about this bubble rather than this work, and could no measurement have found it? |

Two rules keep the boundary from eroding:

- **No value in this file is a value to reuse.** Numbers appear here only as the
  evidence for a method. Copying one into a new work skips the measuring.
- **Anything measurable is measured.** A field in the working file that a
  program could have derived is a field that will go stale, disagree with the
  page, and be believed anyway. Size went through three versions in the working
  file before it turned out the original had been saying it all along.

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

## Size comes from the original, in steps

A letterer works from a small set of sizes, not a continuum. **The translation
should have the same set, and the original chooses which one each line gets.**

Recover the original's size as `sqrt(box_area / japanese_character_count)` —
Japanese sets on a square grid, so that holds whichever way the text ran. Measure
it across a chapter and the steps appear: on one, 154 of 212 bubbles fell between
39 and 57 px, a tail below, a tail above, and a handful of one-off panels far
above.

Write the steps in `series/lettering.md`: for each, the multiple of the base size
the translation is set at, and the ceiling in the original's own pixels that
selects it. Then **nothing is written per region.** Choosing a step is
measurement, not judgement, so the code does it and the working file says
nothing about size at all.

Three rules keep it honest:

- **A step that overflows brings that one region down, and the step does not
  move.** Thai carries a sentence in more characters than Japanese, so this is
  the common case, not a failure. On one chapter 190 of 202 regions landed
  exactly on their step and twelve came down.
- **Steps are for bubbles only.** A bubble's box is larger than the lettering
  inside it, so something has to say how large that lettering should be. A
  free-floating region's box is the lettering's own extent, drawn around it —
  it fills its box, and needs no ladder. A chapter heading is this case.
- **A bubble holding only a pause is excluded from the measurement.** Its box is
  sized for a beat of silence, not for the dots; measured, one character in a
  large box reads as enormous lettering.

The ceilings are absolute, in the original's pixels. Normalising against a page's
own median instead throws away exactly the thing worth keeping: a page the artist
lettered loud throughout gets measured against itself and comes back ordinary.

What is left in the working file is `weight`, and it is not about size. A heading
is a display face, and **ink density tells it apart** — count dark pixels over
the region's box against the speech bubbles on the same page; a display face
measures roughly twice a body face.

## Thai in manga is set to the bubble, not to the line

This is the rule that differs from upstream and it is the one that matters most.
It is an invariant of Thai manga rather than a house style, so a series file
should only mention it to record a departure.

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
- A Thai comic face typically carries **no ♥ ♡ ★ ☆ ♪ 「」 ○** at all, and the
  original will use them. They are tone markers, so render them the way Thai
  marks tone — in the wording and a drawn-out vowel — rather than substituting a
  symbol the face happens to have. Which characters a face lacks belongs wherever
  the face is chosen — with the code if one face is standard across works, in
  `series/lettering.md` if it varies. What a particular work does about them is
  always per-work.
- **A comic face's regular cut is right for dialogue.** Its bold sits heavier
  than the lettering it replaces and reads as shouting; keep it for headings.

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
  hold what the Japanese said, and a version carrying the meaning in half the
  words leaves it looking empty. Measure it: Thai width per Japanese character,
  compared across the page. Where a line sits far below the rest it is usually
  rendering only the bare sense — `〜があって` is "it so happens that", `らしい`
  is "I hear that", `けっこう` is "quite, as these things go", `なんか` hedges the
  report it introduces. Saying those in full is more faithful *and* fills the
  bubble. A line the artist drew short stays short.

- **Where the Thai runs much longer than the Japanese, shorten the line rather
  than the lettering.** A four-character shout cannot be lettered large under a
  fifteen-character translation of it.

- **Lengthening a Thai syllable changes its vowel; it does not append a sign.**
  `ちゃ〜ん` drawn out is `จางงง` — the `ั` in `จัง` opens to `า`. Keeping the
  original vowel and adding a mark after it spells a different syllable, not a
  longer one.

## Symptoms and causes

| What it looks like | What it is |
| --- | --- |
| Two long lines in every bubble | Full box width handed to the breaker |
| Sizes swinging across a page | Fitting each bubble to what it can hold |
| One sentence at two sizes | Utterance grouping not applied to the size |
| Text off-centre in a conjoined bubble | Lobe masks cut on a box edge |
| A name split across lines | Glossary not fed to the segmenter |
| Empty boxes that look like letters | Font lacks the glyph; nothing checked |
| Heading no bigger than speech | Sized from the step ladder instead of filling its own box |
| A pause bubble lettered enormous | Its one character measured against its whole box |
| A loud page comes back ordinary | Sizes normalised against that page's own median |
