# manga-honyaku

A manga translation workflow. Code handles geometry — detection, OCR, text removal,
rendering. You handle comprehension — reading order, speaker attribution, and the
translation itself.

The skills under `.claude/skills/` hold the method: `new-manga-work` for bringing
up a manga that has not been translated here before, then `japanese-to-thai-manga`,
`manga-text-removal` and `thai-manga-lettering`.

`docs/specs/2026-07-26-design.md` is the original design — read it for why the work
is split this way, not for how anything currently works.

## Working here

One directory per work, and every stage takes it as its first argument:

    uv run python -m manga_honyaku.render series/<work>            # every page
    uv run python -m manga_honyaku.render series/<work> X0006      # one page
    uv run python -m manga_honyaku.render series/<work> 01/ch02    # a directory

`detect`, `annotate`, `prepare`, `clean` and `render` all read that way. Inside:
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

`python -m manga_honyaku.chapters <work> X0006-X0008` prints what the reading
found on particular pages, so asking about three of them does not mean loading
the chapter they are in.

When you decline a region, mark it `declined` with a reason. Never silently skip or
soften.
