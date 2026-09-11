# Maintaining the letterer

For whoever changes `render`, brings up a new work, or is about to build
something here. A translator needs none of it —
[`SKILL.md`](SKILL.md) beside this file is what a chapter is translated with.

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

## Line breaking, the engine's own rules

- Segment with `pythainlp` — `newmm` is fine. With the DP and the orphan penalty
  in place the engine stops mattering: `newmm` mis-segments `บอกว่า` as
  `บอ|กว่า` and the breaker declines that break anyway.

- **Attach punctuation to the word it leans on** — a closing mark to the word
  before, an opening mark to the word after. The segmenter returns `?`, `…` and
  `“` as tokens of their own, and a line will otherwise open with one.

- **`ๆ` is one of those marks and does not look like one.** It is Unicode
  category `Lm`, so `isalnum()` calls it a letter and a rule written as "a token
  with no alphanumerics is punctuation" lets it through. It then breaks off the
  word it repeats and sits alone at the head of a line, meaning nothing —
  `สาวๆ` comes back as `สาว / ๆ`. Name it alongside the closing marks, because
  the test that finds them will not.
