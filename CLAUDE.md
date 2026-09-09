# manga-honyaku

A manga translation workflow. Code handles geometry — detection, OCR, text removal,
rendering. You handle comprehension — reading order, speaker attribution, and the
translation itself.

The skills under `.claude/skills/` hold the method: `new-manga-work` for bringing
up a manga that has not been translated here before, then `japanese-to-thai-manga`,
`manga-text-removal` and `thai-manga-lettering`.

`docs/specs/2026-07-26-design.md` is the original design — read it for why the work
is split this way, not for how anything currently works.

**Start at the work's `handoff.md`.** A work is translated a chapter at a time by
someone who did not translate the one before it, so that file — not this one —
says where the chapters stand, what was decided late, and what not to re-run.
Read it before anything else in `series/<work>/`.

## Working here

One directory per work, and every stage takes it as its first argument:

    uv run python -m manga_honyaku.render series/<work>            # every page
    uv run python -m manga_honyaku.render series/<work> X0006      # one page
    uv run python -m manga_honyaku.render series/<work> 01/ch02    # a directory

`detect`, `annotate`, `prepare`, `clean`, `render` and `audit` all read that way. Inside:
`pages/` is the translation and rebuilds from nothing, `build/` rebuilds from the
scans in seconds, `out/` is the finished pages, and the scans themselves are
read-only wherever `raw.txt` points.

Keep the stages separate: editing a translation and re-rendering must not re-run
detection or OCR.

Artifacts and code are written in English.

**Read every image through `python -m manga_honyaku.sheet`** — pages, crops, all
of it. It caps each image at the width past which reading stops getting easier
and cost goes on rising, and `--crop X1,Y1,X2,Y2` takes a box out first, so
there is never a reason to write a resize by hand.

    sheet a.png b.png -o /tmp/look.png              # two pages, ~2300 tokens
    sheet page.jpg --crop 640,280,1060,760 -o ...   # one bubble, ~1000

One page and two pages cost the same, so read the spread.

## Translating

Read the whole page before translating any of it, and keep the work's own notes
current as you go — `characters.md` and `glossary.md` are what make later
chapters consistent.

Record uncertainty in `questions` only when being wrong would change the output.

Before rendering a batch, run `python -m manga_honyaku.check <work> <pages>`. It
reads every region again and reports any holding a line that belongs to another
region on the same page. That is the one failure a re-read of the page will not
show — the Thai is plausible where it sits, and only the boxes disagree. Three
bubbles on X0048 held each other's lines, and nothing else found them.

After rendering, run `python -m manga_honyaku.audit <work> <pages>`. It checks a
finished page against the artwork it actually produced, and every check in it is
there because that failure reached a rendered page once and nothing said so — a
region erased and never drawn back into, Japanese left under the Thai by `clean`,
a broken reading order, a decline with no reason. `check` and `audit` do not
overlap: one re-reads the Japanese, the other looks at what came out.

`python -m manga_honyaku.chapters <work> X0006-X0008` prints what the reading
found on particular pages, so asking about three of them does not mean loading
the chapter they are in.

Three more tools answer questions about a work without changing anything in
it, and none of them is a stage:

    regions <work> 01/ch02        # the working file: boxes, sizes, room, source
    regions <work> --match 聞け    # every line of the work that ever said this
    regions <work> 01 --overlaps  # region pairs standing on the same lettering
    regions <work> 01 --todo      # what the file still leaves unfinished
    regions <work> 01 --repeats   # lines this chapter says twice, before reading any
    tally <work>                  # the counts a finished chapter is read back against
    fit <work> 01/05 F1 "…"       # what size a candidate line would be drawn at

**`regions` is what to open a chapter with.** `chapters` holds what somebody
wrote *about* a page; `regions` holds the file being worked on, which on a fresh
chapter is the only one of the two that exists.

A region's `status` says what happens to it, and the three values answer
different questions: **`ok`** takes the Japanese out and puts Thai in its place,
**`declined`** leaves the artwork alone and says why in `reason`, **`erase`**
takes the Japanese out and puts nothing back — furigana the detector boxed on
its own, a glyph the interior fill could not reach.

Never silently skip or soften. `ok` with nothing to draw cannot be told from a
line somebody forgot, and `declined` is never erased at all, so the page keeps
the Japanese while the record says it was handled. Both mistakes have been made
here; that is why the third value exists.

**`role` says what the region *is*, and the stages read it before they read
`status`.** These five are the whole vocabulary. Nothing validates the field, so
a sixth value invented in good faith fails quietly — `tally <work>` prints every
value a work is using, and a count of 1 beside one is either something new or a
typo.

| `role` | What it is | `clean` | `render` |
| --- | --- | --- | --- |
| `dialogue` | said aloud, in a balloon | erases | draws Thai |
| `caption` | thought, narrated, or a plate the artist set over the art | erases | draws Thai |
| `title` | a chapter title or a display line belonging to the work | erases | draws Thai |
| `image_text` | writing inside the drawing — a sign, a badge, a screen, a spine | **leaves alone** | **draws nothing** |
| `sfx` | a sound drawn into the artwork | **leaves alone** | **draws nothing** |

**`image_text` and `sfx` are recorded and not lettered.** Set `status: ok` with a
`target` on them anyway: the Thai reaches the reader through the working file,
and the drawing keeps its own lettering. A sound effect you *do* want drawn takes
`role: dialogue`, which is right when it sits in an ordinary balloon `clean` can
follow. Putting a line the reader needs under `image_text` is the quiet failure —
it is recorded, it looks handled, and the page still shows Japanese.

**`caption` against `dialogue` is not a formatting choice.** It is the difference
between what a character thinks and what they say, which is what `tally` counts
and what `characters.md` tracks across chapters. A chapter that files a
narrator's interior voice as `dialogue` reports them as having spoken every line
of it, and that number then joins a column counting something else.
