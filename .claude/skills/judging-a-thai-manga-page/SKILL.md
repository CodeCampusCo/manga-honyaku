---
name: judging-a-thai-manga-page
description: Use when looking at finished translated manga pages and judging only how they look — lettering out of proportion to the box holding it, balloons that sit wrong, line breaks that stop the eye. Knows what this face and this format do normally, so the things that look like faults but are not do not get reported. Not for judging a translation.
---

# Judging a Thai manga page

You are looking at printed pages and saying where the **page** goes wrong. Not
the translation — you cannot check that and must not try. Somebody judging a book
from across a table, who has never seen the original and does not need to.

**Read the pages right to left**, the way the book is read: rightmost panel
first, and within a panel, right to left and top down. View them through
`manga_honyaku.sheet`, two at a time — that is about the size the page is
printed at.

**Judge at that size.** Cropping in to check a detail is fine, but decide from
the page as a whole: everything is legible if you look closely enough, so a
verdict reached while zoomed in is a verdict about your zoom.

## Most of what looks wrong here is not

This is the important half of this file. A first pass written without it reported
fourteen things and **thirteen were normal**. Learn these before looking.

**Every exception below was put here by a Thai reader ruling on a real report,
and the list is meant to keep growing that way.** Nobody can write it from
memory — the entries arrived one at a time, each because a pass flagged something
and a reader said *that is fine, and here is why*. When a future pass reports
something and the ruling is that it reads fine, the ruling belongs here. A pass
whose false positives are not fed back will keep making the same ones.

### The face draws tone marks high and detached

Thai tone marks in this lettering face float well above the letter they belong
to, clearly separated from it. **`๋` (ไม้จัตวา) is a small cross, so detached and
high it reads as a stray `+` sitting above the line.** `็`, `์` and `๊` float the
same way.

This is how the face is drawn, it is the same on every page, and a Thai reader
reads straight through it. **Never report it.** Vowels above and below the letter
sit correctly — only the tone marks ride high.

### Text with no balloon around it is normal

Manga prints dialogue straight onto the white of the page all the time, with no
outline at all — the page white *is* the balloon. Lines running out of a balloon
and continuing on bare paper are the same device. **Never report missing or
broken balloon outlines**; the artist drew it that way and the original does the
same thing in the same place.

### A balloon can be mostly empty and still be right

Thai is set horizontally into balloons drawn for vertical Japanese, so the shapes
do not fill the way they did. **Empty space is the expected cost of the format,
not a fault.** In particular these are all correct:

- a large balloon holding one short word — often a name — drawn big for emphasis
- a tall narrow caption box now holding one or two words per line with space left
- text sitting below or off the centre of its balloon
- a balloon lettered smaller than the one beside it: sizes are inherited from
  what the original was lettered at, so a quiet line beside a shout is *meant* to
  be half its size. Its box is smaller too — that is what tells it apart from
  type that has simply been shrunk

### A white erase plate does not end where it looks like it ends

Free-floating text is erased as a white rectangle, and on a light ground its
edges are invisible: the plate and the artwork are the same white. Two things
then read as an edge that is not one — **a panel border whited out where it
passes behind the plate**, and the bottom of the type itself. Both put the
apparent edge above the real one, and the last line or two of a centred block
then look as though they have fallen out onto the drawing.

**They have not.** One chapter reported this way six times on six pages; measured
against the mask, the whole chapter had 83 pixels of ink outside a plate — a few
glyph edges by one or two pixels, out of 28 pages. **A plate is a rectangle and
the text is centred in it, so text cannot land outside it.** Do not report text
running off its plate, in any direction. If something genuinely looks wrong
there, describe what you see without claiming the type has left its box.

What *is* worth reporting about a plate: one that **erases drawn detail the page
needs** — an arrow the caption was pointing along, the outline of a tilted card
or a screen the text sat inside, a panel border a reader uses to follow the row.
That is a reason to re-cut the region, and it is a different observation from the
plate merely being visible.

### A drawn-out vowel broken across lines is accepted

A held cry sets a run of repeated vowels, and the line breaker splits it, so a
line can begin with bare vowel characters carrying no consonant. It has been
looked at and accepted as readable. **Do not report it.**

## What to report

Three things, and the bar for each is that **you would notice it while reading**,
not that it is measurably imperfect.

1. **Lettering out of proportion to the box it sits in.** A large box holding
   tiny type reads as a mistake however legible that type is. **This is not a
   legibility test** — do not ask whether you can read it, ask whether the size
   suits the space it was given. Legibility is the wrong question because it
   passes anything you can make out, and because it changes with how close you
   look, which is under your control and therefore no test at all.

   The box is the anchor, not the neighbours. A quiet line beside a shout is
   smaller *and sits in a smaller box*, so its proportion holds and it is
   correct. Proportion has broken when the type is small and the box is not.

   Second, weaker reading: type that does not sit with the rest of the lettering
   on its page. Use it to confirm, never on its own.

2. **A balloon that reads wrong some other way** — text crowded hard against the
   outline with nowhere to breathe, or text drifting onto artwork dark enough to
   swallow it.
3. **A line break that stops the eye** — a word split where it should not be, a
   last line holding one stray fragment, text so narrow it comes out one or two
   characters per line.

Report nothing you would not defend with the page in front of you. A pass that
finds two hundred things has said nothing.

## What to send back

Per point: **the page**, **where on the page** — describe the position and what
the balloon looks like well enough that someone with the page open finds it in
one go, since you have no region ids — and **what is wrong**.

**Do not diagnose the cause and do not propose new wording.** Both need the
translation and the working files, which you do not have. Three different causes
produce small lettering — a term that cannot be broken, a size inherited from the
original, and a sentence longer than its box — and code downstream tells them
apart from data you cannot see. Your job is to say *this one is out of
proportion*; saying why is somebody else's, and guessing at it makes your report
harder to use.

End with three numbers: pages looked at, points reported, and roughly how many
balloons a page carries — so the count can be read as a proportion.
