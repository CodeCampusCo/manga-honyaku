# manga-honyaku

A manga translation workflow. Code handles geometry — detection, OCR, text removal,
rendering. You handle comprehension — reading order, speaker attribution, and the
translation itself.

The method is five files, and they are the same five whichever agent is reading
them. Read the one whose row matches before you do the thing, not after:

| Before you | Read |
| --- | --- |
| bring up a manga nobody has translated here | `.claude/skills/new-manga-work/SKILL.md` |
| translate a page | `.claude/skills/japanese-to-thai-manga/SKILL.md` |
| erase lettering, or judge a mask | `.claude/skills/manga-text-removal/SKILL.md` |
| choose a lettering size or a line break | `.claude/skills/thai-manga-lettering/SKILL.md` |
| say what is wrong with a rendered page | `.claude/skills/judging-a-thai-manga-page/SKILL.md` |

If your tool discovers skills on its own it has these already, and if it does not,
the paths above are the whole of it — nothing here has to fire by name. The
directory is named after the one tool that cannot be pointed anywhere else, which
is the whole reason it looks like it belongs to one agent; every tool that can be
pointed is pointed at it in a committed file.
[`docs/agents.md`](docs/agents.md) says which file is for which tool; none of it is
method, and none of it changes the table above.

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

**If your model cannot see the sheet, stop and ask. Do not route around it.**
Not every model that runs here has eyes, and a harness will quietly hand the
image to something that does: fourteen pages of one chapter were uploaded to a
third party's bucket before anybody knew images were leaving the machine at all.
[`docs/agents.md`](docs/agents.md) lists the readers that exist and what each one
costs. Which to use is the person's call, and one of the answers is to send the
page nowhere and have them read it to you.

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
    fit <work> --replace ก ข      # what changing a word costs, in every chapter at once

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
| `title` | display type that is nobody speaking — the work's own chapter titles and scene headers, and the magazine's masthead, promo strips, credits and logos | erases | draws Thai |
| `image_text` | writing inside the drawing — a sign, a badge, a screen, a spine | **leaves alone** | **draws nothing** |
| `sfx` | a sound drawn into the artwork | **leaves alone** | **draws nothing** |

**Most `title` is `declined`** — 37 of the 63 in this repository — because the
magazine's furniture is printed over the artwork rather than drawn into it, and
translating it would put a Thai masthead on somebody else's page. The role says
what a region is; `status` still decides what happens to it.

**`image_text` and `sfx` are recorded and not lettered.** Set `status: ok` with a
`target` on them anyway: the Thai reaches the reader through the working file,
and the drawing keeps its own lettering. A sound effect you *do* want drawn takes
`role: dialogue`, which is right when it sits in an ordinary balloon `clean` can
follow.

**`image_text` is a decision about the reader, not about where the writing sits.**
Nearly everything in a panel is writing inside the drawing, so that description
chooses nothing. Ask instead what the reader loses: it is right when the content
reaches them another way — a chyron whose story is in the lettered post beside it
— or when losing it costs nothing. **When the scene does not work without it, it
is not furniture. Draw it.** Filed wrongly it is the quiet failure: recorded, so
it looks handled, and Japanese on the page at the one place that mattered.

**`caption` against `dialogue` is not a formatting choice.** It is the difference
between what a character thinks and what they say, which is what `tally` counts
and what `characters.md` tracks across chapters. A chapter that files a
narrator's interior voice as `dialogue` reports them as having spoken every line
of it, and that number then joins a column counting something else.

## The four passes, and where each one goes

**The split is by what each is allowed to see.** A pass that can see everything
checks nothing, because whoever translated the page knows what it was meant to say
and reads their own error as correct. `audit` is the program above; the other
three are prompt files:

| Pass | Has | Never opens | Runs |
| --- | --- | --- | --- |
| `.claude/agents/translate-pages.md` | the Japanese and the notes; it writes | — | the translation |
| `.claude/agents/proofread-against-source.md` | the Japanese — **the scans included** — the Thai, and the notes | `out/` | **before `clean`** |
| `.claude/agents/page-look.md` | the rendered page | the Japanese, the notes | after `render` |

Run each in a session of its own. If your tool cannot take away the tools their
frontmatter names, the third column is yours to keep: a proofreader that has
opened `out/` has stopped being the one pass that catches a line which is fluent,
sits well, and says the opposite of the original.

The fourth column is a fact, not a preference. The proofreader needs no rendered
page, so running it before `clean` costs a finding instead of a re-render;
`page-look` judges the page that came out, so there has to be one.

**Run each pass once**, apply what it returns, and go on. Their own files say
why, and what each one is looking at.
