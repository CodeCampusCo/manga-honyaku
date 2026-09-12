---
name: japanese-to-thai-manga
description: Use when translating Japanese manga dialogue into Thai — reading order and speaker attribution, composing an utterance whole before cutting it across balloons, matching the original's length against the room the bubble has, and what the work's own files settle.
---

# Translating manga into Thai

## Read the page before you translate any of it

Build a contact sheet of the annotated pages — the spread, or up to four — and settle
**reading order and speaker attribution first**.

`regions … --order` proposes that order from the boxes while you number a page,
and `regions … --todo` names every pair it and the file disagree about once the
page is numbered. **The second is the one that has to be answered** — the
proposal can be accepted wholesale and nothing would ever show it. Reading order
is the largest piece of hand work in a chapter and the one field `audit` cannot
catch: it checks the numbers run `1..N`, which a page numbered in entirely the
wrong sequence passes.

Print the working file beside the sheet: `uv run python -m manga_honyaku.regions series/<work> <chapter>` gives every
box with the size the Japanese was lettered at, the `room` that follows, and the
reading. The sheet says where a region is on the page; only the file says what is
in it and how much of it there is room for.

Where a region's own box cannot be painted out without taking artwork with it,
its line is drawn elsewhere on the page instead: `regions … --space` offers the
places, and [`working-a-chapter.md`](working-a-chapter.md) says how to choose.

Attribution is where the guessing goes wrong, and the check is cheap: read the
sequence back as a conversation. `それに…` following a line by the same speaker
means you have the order right; following a line by the other speaker means you
do not.

**The page is the unit of context.** One page per call, with the units numbered
in reading order and the image itself in front of you, beats both a smaller unit
and a larger one. Below the page a line is under-determined — Japanese drops
subjects, so a bubble alone has to guess, and the failure is a first-person line
coming out as *you*. Above the page, context dilutes.

So read the page, and do not reach for the chapter to translate from. The
chapter file is background — what the scene is and who is in it — and is not a
source: it holds no Japanese, and translating from a summary of the words
instead of the words is a loss no later pass recovers.

## The unit of translation is the utterance, not the bubble

A sentence split across two or three balloons is **one sentence**. Compose it
whole in Thai, then cut it across the regions, giving each piece its own
region's `room`. Mark the group with `utterance` so `render` letters them at one
size — one sentence at two sizes reads as two sentences.

**Do not close what the original left open.** A balloon that ends mid-clause in
Japanese ends mid-clause in Thai. Translating balloon by balloon quietly finishes
each one, and the rhythm goes: `最初はもっとそういうんじゃなくて` runs on into the
next balloon, but came out `ตอนแรกไม่ได้เป็นแบบนั้นเลย` — a closed sentence with
a full stop's worth of finality the original does not have.

This is also the lever the research measures. Numbering the units in reading
order is worth about as much as adding the page image at all, and what it buys
is exactly this: the sequence relation that lets a sentence split across two
bubbles be joined before it is translated.

**The risk it introduces is real and there is a check for it.** Composing whole
and then cutting makes it easier for a line to land in the wrong region.
`check` exists for it — run it.

## The work's own files are what binds

`voice.md` says how this work sounds in Thai and how far it goes toward Thai
idiom, `characters.md` what each person's first and second person are, and
`glossary.md` what a name suffix becomes. These three are what binds; do not
reach for a rule of your own over them.

## Match the original's length, not only its sense

The bubble was drawn to hold what the Japanese said. A version carrying the
meaning in half the words leaves it looking empty, and the reader sees the gap
before they read the line.

`room` on the region is how many characters the box holds at the size that region
asks for — counted as widths, so a mark above or below costs nothing and `ที่` is
one. Compose against it. A line coming in at half of `room` leaves the bubble
looking empty; one well past it gets lettered smaller to fit. Neither is a
failure, and neither is worth a second pass at the wording: the better sentence
wins, and where it has to miss, long misses better than short.

Where a line does come in short, the words to add are the ones a bare gloss
drops — `〜があって` is "it so happens that", `らしい` is "I hear that", `けっこう`
is "quite, as these things go", `なんか` hedges the report it introduces. Saying
those in full is both more faithful *and* better lettering.

A line the artist drew short stays short. And where the Thai runs much longer
than the Japanese, **shorten the line rather than the lettering** — a
four-character shout cannot be lettered large under a fifteen-character
translation of it.

**Going over `room` is the ordinary case, not the exception.** Four regions in
ten across a volume overflow and are lettered a step smaller, and of those the
median would have had to be a third shorter to fit. That is not a backlog to
work through. `room` is itself about 15% optimistic — the breaker leaves slack
on most lines and a word cannot be split — so a line written to exactly `room`
already costs its bubble a step.

**Pay the step.** The size step is cheap and the dropped nuance is not — an
aspect marker, a hedge, whose face is red. Nothing downstream puts those back.
This was measured over six pages and ruled on; the numbers are in
[`../thai-manga-lettering/SKILL.md`](../thai-manga-lettering/SKILL.md), which is
where a size argument belongs.

So when a line will not fit, **cut padding you added, never content the original
has.** A phrase repeated for emphasis in Japanese that Thai does not need, a
pronoun the Thai can drop, a transliteration that could be a translation — those
are yours to spend. The hedge that carries the speaker's hesitation is not.

## The record around the line

Composing the line is one half. The other is
[`working-a-chapter.md`](working-a-chapter.md), beside this file. Read it before
opening the chapter and again before closing it;
some of it is what you write while the page is still in front of you. A pass that
only reads and reports does not need it.
