---
name: manga-text-removal
description: Use when erasing lettering from manga artwork and recovering the space a translation goes into — finding a bubble's interior without a segmentation model, splitting conjoined bubbles, handling screentone or free-floating text, deciding what to leave alone. The stage between detection and lettering.
---

# Clearing a manga page for translation

The output of this stage is two things: artwork with the Japanese gone, and one
mask per region saying where the Thai may go. The masks are the contract with
the lettering stage — text placed badly is usually a mask that was recovered
badly.

## Recover the interior from the artwork

Detectors return boxes. A box is not where text may go: the bubble is an oval
inside it, and letters centred in the box sit outside the curve. Rather than add
a segmentation model back, read the interior off the artwork.

**Inside a detected bubble box, the interior is the paper the text sits on.**
Threshold at a fixed value — the split between paper and ink is nowhere near
marginal, and an adaptive threshold chases the screentone behind the bubble —
then take the connected component with the **largest overlap with the text box**.

Three other rules were tried and each fails on real pages:

| Rule | How it fails |
| --- | --- |
| Flood from the box's centre | The centre is where the lettering is; the seed lands in the counter of `あ` |
| Largest component | Picks the paper *outside* the bubble whenever the box is loose |
| The component not touching the box edge | Fails on conjoined lobes, which reach both edges |

Then **fill the holes**: the lettering sits inside that component as enclosed
complement regions. A hole is any part of the complement that does not reach the
edge of the crop — flooding inward from a corner fails on a bubble that reaches
one.

## Conjoined lobes share one interior

Two lobes of a conjoined bubble are detected separately and their boxes overlap.
Crop each lobe to its own box and the shared interior is cut along a box edge —
a straight line nowhere near the waist where the lobes actually meet. One lobe
takes a slice of the other, and text centred in what is left sits visibly
off-centre in the bubble a reader sees.

**Group the regions whose outline boxes overlap, find the interior once for the
group, then give each lobe what its own outline encloses and hand the overlap to
the nearer lobe.** The only pixels in dispute are the ones in the waist.

Two other splits are worse: nearest-text-centre draws a straight bisector across
both lobes, and a watershed on the interior's depth follows its medial axis and
returns the lobes interleaved in stripes.

## A toned bubble is paper with ink ruled through it

Threshold a screentoned bubble and the tone's gaps come back as separate
stripes; one stripe wins the overlap and the text is set into a sliver.

**Close the mask to join the stripes, then erode by the same amount to give back
the outline the close ate.**

**Do it as a fallback, not as the rule.** Applied to every bubble the same close
bridges thin outlines and floods the artwork around them — on one chapter it
moved 334 of 500 masks and stripped whole bubbles of their outlines, to fix two.
Trigger it on a symptom only the fault produces: **a lone bubble whose interior
fills under half its outline box.** A conjoined group's box has corners no lobe
occupies and is legitimately that empty, so leave groups out.

## Repaint with the bubble's own paper

Fill with the median of the paper pixels inside the mask rather than with white,
so a bubble that is toned or tinted does not come back as a white hole in a grey
panel.

## Free-floating text gets its box, exactly

There is no outline to follow and no way to know what was behind it, so it is a
white rectangle unless you add an inpainting model. On a page margin that is
invisible; over artwork it is a patch, and that is the trade.

**Fill the box and not a pixel more.** These boxes are cropped tight — a chapter
title's box ends on the very row where the panel rule begins, so any margin cuts
the rule. Clearance for a drawn outline is a different question: a free region's
mask is the text's own extent, and holding letters off the edge of it cost one
chapter heading a third of its size for nothing.

A margin *before OCR* is worth having, where reading a clipped glyph costs
nothing but a wider crop.

## Leave the artwork alone

A sound effect drawn as lettering is artwork. So is a sign, a product label, a
phone screen. What they say reaches the reader through the translation record,
not by overwriting the drawing — so mark them and skip them, and let the
lettering stage find no mask and draw nothing.

**Only a reader can tell a sound effect from a line of unbubbled speech**, so
that call belongs to whoever translated the page, not to this stage. A region
with no role yet is left alone. A declined region is left for a different
reason: erasing it leaves a hole with nothing to put in it.

## Watch for the silent failure

This stage is full of operations that no-op rather than raise:

- **Pillow's `ImageDraw.floodfill` silently does nothing** on an array from
  `Image.fromarray()` — the image is `readonly=1` and the `ValueError` is
  swallowed. Use OpenCV.
- **Torch on MPS** fails on a float64 op inside some models and swallows it.
  Pin these small models to CPU; they run once per page.

Both look like a clean run that produced nothing. Check an output, not a
return code.

## Symptoms and causes

| What it looks like | What it is |
| --- | --- |
| Text off-centre in a conjoined bubble | Lobe masks cut on a box edge |
| Text crammed into a sliver of a bubble | Toned interior; stripes labelled apart |
| A white hole where a grey bubble was | Repainted with white instead of its own paper |
| A panel rule cut at a caption's edge | Margin added to a free region's box |
| The Japanese still showing under the Thai | Region kept as artwork but given a target |
| A blank page and a zero exit code | A silently-swallowed failure; look at the image |
