# manga-honyaku

A manga translation workflow. Code handles geometry — detection, OCR, text removal,
rendering. You handle comprehension — reading order, speaker attribution, and the
translation itself.

The method is six files, and they are the same six whichever agent is reading
them. Read the one whose row matches before you do the thing, not after:

| Before you | Read |
| --- | --- |
| bring up a manga nobody has translated here | `.claude/skills/new-manga-work/SKILL.md` |
| translate a page | `.claude/skills/japanese-to-thai-manga/SKILL.md` |
| erase lettering, or judge a mask | `.claude/skills/manga-text-removal/SKILL.md` |
| choose a lettering size or a line break | `.claude/skills/thai-manga-lettering/SKILL.md` |
| say what is wrong with a rendered page | `.claude/skills/judging-a-thai-manga-page/SKILL.md` |
| run a stage, or ask a work what its files hold | `.claude/skills/running-the-manga-pipeline/SKILL.md` |

If your tool discovers skills on its own it has these already, and if it does not,
the paths above are the whole of it — nothing here has to fire by name. The
directory is named after the one tool that cannot be pointed anywhere else, which
is the whole reason it looks like it belongs to one agent; every tool that can be
pointed is pointed at it in a committed file.

**Start at the work's `handoff.md`.** A work is translated a chapter at a time by
someone who did not translate the one before it, so that file — not this one —
says where the chapters stand, what was decided late, and what not to re-run.
Read it before anything else in `series/<work>/`.

## Working here

One directory per work, and every stage — `detect`, `annotate`, `prepare`,
`clean`, `render`, `audit` — takes it as its first argument, then the pages.
Inside: `pages/` is the translation and rebuilds from nothing, `build/` rebuilds
from the scans in seconds, `out/` is the finished pages, and the scans themselves
are read-only wherever `raw.txt` points.

Keep the stages separate: editing a translation and re-rendering must not re-run
detection or OCR.

Artifacts and code are written in English.

**Read every image through `manga_honyaku.sheet`** — pages, crops, all of it. It caps an image
at the width past which reading stops getting easier and cost goes on rising, and
it crops, so there is never a reason to write a resize by hand. One page and two
pages cost the same, so read the spread.

**If you cannot see the sheet, stop. You cannot do this work.** Reading the page
is not a step that can be handed to something else and reported back — it was
tried, and the chapter that came out had been translated from a description of
the artwork. A harness will quietly send the image somewhere that can look, so
the first sign of it is often a page you never saw. Say so and stop.

## Translating

Read the whole page before translating any of it, and keep the work's own notes
current as you go — `characters.md` and `glossary.md` are what make later
chapters consistent.

Record uncertainty in `questions` only when being wrong would change the output.

**Before rendering, `check`. After rendering, `audit`.** They do not overlap: one
re-reads the Japanese and finds a line sitting in a region it does not belong to,
which is the failure a re-read of the page will not show; the other looks at what
came out. Both are worth running because every check in them is there for a
failure that reached a page once and nothing said so.

**`regions` is what to open a chapter with**, and what a chapter is opened with
before any page is read: what an earlier chapter already settled, and which boxes
stand on the same lettering.

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

**Either of the last two can be moved when the scene needs it drawn**, and the
value it moves to is the one whose shape `clean` can follow: `dialogue` for a
sound in an ordinary balloon, `caption` for writing in the artwork — which erases
as a white plate over the drawing, and is accepted here. There is no third
option: a region either erases and is drawn into, or it does neither.

## The working file

`pages/<page>.agent.json` is the only artifact that rebuilds from nothing. Each
region in it carries:

| Field | Written by | What it is |
| --- | --- | --- |
| `id` `box` `placement` `score` `bubble` | `detect` | the region and where it sits |
| `source` | `prepare` | the Japanese, OCR'd |
| `size` `room` | `prepare` | the size the Japanese was lettered at, and the budget |
| `role` `status` `reason` | you | above |
| `order` | you | reading order, `1..N` over every region on the page, declined ones included |
| `speaker` | you | who says it, by the key `characters.md` uses |
| `target` | you | the Thai |
| `utterance` | you | a tag shared by the regions one sentence is cut across |
| `weight` | you | a named font face, where the work has more than one |

The page itself carries `version`, `page`, `img_width`, `img_height`, `detector`
and `questions`. Nothing validates any of it.

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
