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

Each of these was built, shipped and deleted, and each looked necessary at the
time. They are named so that they are not built again — every one was a way of
recovering a column the box had already given:

- **a computed column from the mask.** The box *is* the column, and the computed
  one came out wider than the original's own lettering, so short phrases never
  stacked.
- **a corner collision test against the curve** — needed only because that column
  was not inside it.
- **narrowing the column a step at a time and keeping the tallest layout** — a
  search for what the box gives for free, with a tuned constant of its own.
- **a ladder of finer break points**, word to syllable to cluster, and the two
  patches it then needed: rejoining splits inside a run of repeated letters, and
  marking word-list terms unsplittable.

**When a fix needs a fix, the thing being fixed is usually the wrong mechanism.**
Half of that list exists only to repair the other half.

The one thing worth porting from MangaTranslator is
**`find_optimal_breaks_dp`** (`core/text/text_processing.py`) — Knuth-Plass in
shape, minimising the sum of slack cubed, plus a penalty when a continuation line
would start with a short Thai token. That is the line breaker doing its own job,
not a search around it. Their geometry and shaping stack are not.

## Size comes from the original: one number, one multiplier

**Measure what each region has to be lettered at, write the number down, and
multiply by one number for the whole work.** That is the entire model.

- **`size` is `sqrt(box area / japanese cells)`**, in the page's own pixels,
  measured once when the page is prepared. Japanese sets on a square grid, so it
  holds whichever way the text ran. It never changes again, so deriving it at
  every render is work repeated to reach the same answer.
- **Thai pixels = `k` × `size`.** One `k` per work, in the stylesheet, set by eye
  on a rendered page. Both numbers are measured on the same page, so `k` needs no
  scaling for a rescan and neither does `size`.
- **A run of pause marks counts once.** A pause is often recorded twice over,
  once in each script — `・・・...` where the page has three dots, from two
  readings of one box being merged. Count both and the region measures a sixth
  smaller than it is, which is the exact fault this measurement is for.
- **A region that cannot be measured takes the median of its page.** A burst
  bubble reading `!?` still has to be lettered, and what the rest of that page
  was set at beats a constant carried in from another book.
- **Free-floating text takes no size.** It is lettered to its own extent — it
  fills the box it was drawn into. A chapter heading is this case, and what makes
  it a heading is the face, so it takes `weight`.

### Do not give the number a name

`quiet`, `normal`, `loud`, `shout` was the model here for seven chapters and it
is a mistake. **Why the artist set a line large cannot be read back off the
page.** A shout from across the street is lettered small; a whisper close to the
reader can be lettered large. Size is one input to loudness among several — the
balloon's outline, the distance in the drawing, the words themselves — and
loudness cannot be recovered from it alone.

So the name is a guess, and a region labelled `quiet` that holds a shout sends
the translator after the wrong words. **A wrong label is worse than no label.**
The emotion is in the source sentence, where the translator can read it.

Nothing needs the name anyway: rendering needs `k` × the number, budget needs
`room`, which follows from the number. Names bought nothing and cost accuracy.

### What `k` cannot do

**Above a certain `k` the page stops getting bigger.** `render` sets each region
at `k` × `size` and steps down while it overflows, so once most regions are
already overflowing, raising `k` only converts regions that fitted into regions
that get shrunk — and shrinking is arbitrary, so it is the ratios between regions
that pay. On one volume, the share of regions drawn at the size asked for fell
from about four in five at `k = 0.8` to one in ten at `k = 1.2`, while the size
actually drawn stopped rising after 0.9 and the ratios between regions went on
falling the whole way.

**Calibrate to the knee, not by eye alone** — on a page the rows past the knee
look alike, and the first column says they are not.

### The measurement that looks right and is not

Measuring the **ink inside the box** instead of the box was tried, and the
argument for it is convincing and wrong. Write it down or it will be tried again.

The detector's box is loose — its padding runs from 4% to six times the ink — so
it plainly does not measure the original's letters. But the padding varies with
the region's *shape*, not with its scale, which makes the box a tilted ruler that
holds steady, against an ink extent that swings with whichever glyphs a region
happens to contain.

**A work carries its own proof, and it is worth re-running before believing
either ruler.** Regions sharing an utterance were one sentence in the original
and were lettered alike, so their spread is the ruler's own error. Measured that
way the box came out the steadier of the two, and by enough to resolve more
distinct sizes than the ink does.

And the tilt is not a defect. **This number does not have to describe the
Japanese — it has to letter the Thai**, which is set horizontally into boxes
drawn for vertical Japanese and has to fill them. Carrying some of the space
available into the answer is what makes it fill them. A caption measuring 20 from
its ink and 45 from its box is one where 45 fits the line exactly.

### When it will not fit

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

### In a narrow box the size is set by the longest token, not by the length

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

## Starting a new work

The method transfers; the numbers do not. Every work has its own hand and every
scan its own resolution, so **every number below is an output of the steps, not
an input to them.**

```json
{
  "font": "fonts/iannnnnJPG/2005_iannnnnJPG.ttf",
  "page_height": 1200,
  "line_spacing": 1.32,
  "floor": 7,
  "k": 0.90
}
```

| | is | found how |
| --- | --- | --- |
| `font` | the face this work is lettered in | chosen once, then everything else is quoted for it |
| `k` | Thai pixels per pixel of the original's lettering | the loop below |
| `line_spacing` | a property of the face, not the work | changes only with the face |
| `floor` | below this the lettering stops being readable at print size | one look at a printed page |
| `page_height` | the height `floor` is quoted for | read off a scan |

The face belongs in this file rather than on the command line because the rest of
the file is quoted for it: `room` on each region counts how many of that face's
characters the box holds, and `line_spacing` is the face's own. Rendering in
another face letters to a budget nothing measured.

`floor` is the one number left that counts absolute pixels rather than a ratio,
which is why `page_height` is still here: a volume scanned larger needs it scaled
or the smallest lettering allowed comes out half as big on the page.

Calibrating `k`, once per work:

1. **Detect and prepare a chapter, and translate it.** `k` is judged on set Thai,
   so there is nothing to calibrate against until there is a translation.
2. **Render at `k = 1` and look.** One page tells you which way to go.
3. **Plot the knee** — `render <work> --calibrate` draws nothing and prints a row
   per candidate `k`. Take the largest at which `drew` is still rising; past it
   the page is no bigger and only the ratios suffer.
4. **Look again at the knee, and at one step either side.** The numbers narrow it
   to two or three candidates; a person picks between them.

Step 3 is arithmetic and belongs to the machine. Steps 2 and 4 are judgement.
Nothing is measured again afterwards.

## Line breaking

- **Where the original divides one utterance between boxes, each piece has to
  read alone.** It divides where its own script lets it, and a kana reads alone;
  a Thai syllable does not. Kept division for division, every box fits and a size
  probe confirms it, while the reader gets a fragment where the original gave a
  word. Move the cuts between whole words and pay the size step. Fitting is not
  reading, and nothing measures the difference — only the rendered page shows it.
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
- **`ๆ` is one of those marks and does not look like one.** It is Unicode
  category `Lm`, so `isalnum()` calls it a letter and a rule written as "a token
  with no alphanumerics is punctuation" lets it through. It then breaks off the
  word it repeats and sits alone at the head of a line, meaning nothing —
  `สาวๆ` comes back as `สาว / ๆ`. Name it alongside the closing marks, because
  the test that finds them will not.
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

## What goes here, and what goes in the work's own files

This file holds **method, and facts about the two scripts** — that Thai marks
stack with zero advance, that a name means nothing cut in half, that the size a
region asks for cannot be named without guessing. Those hold for the next manga
too.

A work's own directory holds **what measuring that work produced**: its `k`, its
page height, its word list, and how its characters speak. Every
one of those is re-derived for the next work by running the same method, which
is why none of them is written down here.

The test when something new is learned: *would this still be true of a different
manga by a different artist?* If yes it belongs here. If a page, a face or a
measurement told you, it belongs to the work that told you.

## Symptoms and causes

| What it looks like | What it is |
| --- | --- |
| Two long lines in every bubble | Something other than the region's box handed to the breaker |
| Sizes swinging across a page | Fitting each bubble to what it can hold instead of to its tag |
| One sentence at two sizes | Utterance grouping not applied to the size |
| A name split across lines | Not in `words.txt` |
| A line opening with `?` or a stray `“` | Punctuation attached to the wrong side |
| A line opening with a lone `ๆ` | The same, for a mark `isalnum()` calls a letter |
| Empty boxes that look like letters | Font lacks the glyph; nothing checked |
| Heading no bigger than speech | Given a tag instead of filling its own box |
| A pause bubble lettered enormous | Its one character measured against its whole box |
| A cry lettered at conversation size, its column left empty | A held vowel or a long transliteration with no break point in it, in a box drawn for vertical Japanese |
| One caption half the size of its neighbours, for no reason you can see | One long token in it, in a box too narrow for that token at the size the rest of the page is set at |
| A whole sentence's worth of captions lettered small, one of them tiny | Free-floating regions grouped into an `utterance`: they letter at what the narrowest of them holds, and free text has no common size to protect |
| A loud page comes back ordinary | Sizes normalised against that page's own median |

Text placed off-centre or into a sliver of a bubble is a mask problem, not a
lettering one — see the `manga-text-removal` skill.
