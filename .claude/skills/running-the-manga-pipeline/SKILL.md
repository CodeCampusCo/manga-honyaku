---
name: running-the-manga-pipeline
description: Use when running any stage of the manga pipeline or asking a work what its files hold — detect, annotate, prepare, clean, render, audit, and the tools that answer a question without changing anything (regions, chapters, tally, fit, check, sheet). Invocations, what each one reports, and the flag that answers each question.
---

# Running the pipeline, and asking a work what it holds

`AGENTS.md` says which of these to run and when. This file is how.

## Every stage takes the work first

    uv run python -m manga_honyaku.render series/<work>            # every page
    uv run python -m manga_honyaku.render series/<work> <page>     # one page
    uv run python -m manga_honyaku.render series/<work> 01/ch02    # a directory

`detect`, `annotate`, `prepare`, `clean`, `render` and `audit` all read their
arguments that way. **`annotate` depends on `detect` and on nothing else**, so it
runs any time after it — before `prepare` or after, whichever a work's handoff
says. What it draws is what makes a page readable region by region, so it has to
have run before anybody opens one. Nothing named is every page; a name that is a page is that
page; a name that is a directory is every page under it, so a chapter is asked
for the way it is stored.

**A box the detector got wrong is not permanent, and `prepare --retag` is why.**
`prepare` will not overwrite a working file, which reads as *the geometry is
settled* and is not what it means. Edit a region's `box` — widen it over a glyph
the detector clipped, trim it off a balloon it landed on — correct its `source`
in the same breath, then `prepare --retag series/<work> <page>`: it re-measures
`size` and the `room` that follows and touches nothing else, so the roles,
reading order, speakers and translations all stand. **Run `clean` again as well
where the box was a free-placement one** — its box is the mask, so a re-render
alone leaves the old erasure exactly where it was. It prints how many regions
it changed, which is how you check it did what you meant. `--force` is the other
switch and is the destructive one: it rewrites the working file from scratch.

## Reading an image

    uv run python -m manga_honyaku.sheet series/<work> <page> <page> --rtl -o /tmp/spread.png
    uv run python -m manga_honyaku.sheet series/<work> <page> --region B3 -o /tmp/one.png
    uv run python -m manga_honyaku.sheet series/<work> --region 01/05:F1 02/11:B3 -o /tmp/few.png
    uv run python -m manga_honyaku.sheet series/<work> <page> --show out -o /tmp/done.png
    uv run python -m manga_honyaku.sheet a.png b.png --crop 640,280,1060,760 -o /tmp/any.png

**Name a work and page ids, the way every other tool here is named.** A page id
gives the annotated page; `--show raw` gives the scan, `--show out` the rendered
one. **`--region` crops named regions and their surrounds**, one to a cell, and
each may name its own page — a worklist spread over ten pages is one sheet.
Reading one box never means taking coordinates off the sheet and converting them
back. Bare image paths still work, for anything that is not a page of a work.

Cells are all as tall as the tallest, so crops of very different shapes waste the
budget and the sheet comes back too small to read. The line says so when it
happens; build those in two runs, by shape.

It caps each image at the width past which reading stops getting easier and cost
goes on rising, and `--crop X1,Y1,X2,Y2` takes a box out first. A spread costs
about 2300 tokens and one bubble about 1000 — **one page and two pages cost the
same**, so read the spread. There is never a reason to write a resize by hand.

The output line ends with the scale it drew at and the crop's origin, so a
position read off a sheet converts back without the arithmetic.

**`--rtl` for a spread in a right-to-left work**: the first page named goes on
the right. Without it the halves are swapped and each panel still reads, so
nothing about the sheet itself says so — which way round it was built is printed
for every sheet of more than one image.

## The two that check

    uv run python -m manga_honyaku.check series/<work> <pages>
    uv run python -m manga_honyaku.audit series/<work> <pages>

Both read their pages the way a stage does: nothing named is the whole work, a
page id is that page, a directory is every page under it.

`check` reads every region again and reports any holding a line that belongs to
another region on the same page. The Thai is plausible where it sits and only the
boxes disagree, so a re-read of the page will not find it.

`audit` checks a finished page against the artwork it actually produced: a region
erased and never drawn back into, Japanese left under the Thai by `clean`, a
broken reading order, a decline with no reason, a space inside a Thai word. Every
check in it is there because that failure reached a rendered page once and
nothing said so.

They do not overlap — one re-reads the Japanese, the other looks at what came
out. Neither reports what a region has no box for: both walk the regions, so a
piece of lettering the detector missed is invisible to them. That is what
`regions --todo` answers, and nothing else does.

## Asking a work a question

None of these is a stage. None of them writes.

Every one of them is `uv run python -m manga_honyaku.<tool> series/<work> …` —
nothing here installs a command, so a bare `regions` is not on anyone's PATH.

    …manga_honyaku.regions series/<work> 01/ch02      # the working file: boxes, sizes, budgets, source
    …manga_honyaku.regions series/<work> --match 聞け  # every line of the work that ever said this
    …manga_honyaku.regions series/<work> 01 --overlaps # region pairs on the same lettering
    …manga_honyaku.regions series/<work> 01 --todo    # what the file still leaves unfinished
    …manga_honyaku.regions series/<work> 01 --repeats # what is already answered, in two lists
    …manga_honyaku.regions series/<work> 01 --order   # a reading order proposed from the boxes
    …manga_honyaku.regions series/<work> 01/05 --space F1 # where this region's Thai could go instead
    …manga_honyaku.regions series/<work> 01/05 --space F1 --take c # writes that spot into `at`
    …manga_honyaku.regions series/<work> --bar        # the smallest size this work glosses at
    …manga_honyaku.chapters series/<work> <page>-<page> # what the reading found on those pages
    …manga_honyaku.tally    series/<work>             # the counts a chapter is read back against
    …manga_honyaku.fit      series/<work> 01/05 F1 "…" # what size a candidate line draws at
    …manga_honyaku.fit      series/<work> --replace ก ข # what changing a word costs, everywhere

**`--repeats` and `--overlaps` are asked before a page is read**, not after.
`--repeats` answers in two parts, read at two different moments: what an earlier
chapter already settled, with the wording it used, and what these pages
themselves say twice. `--overlaps` lists the pairs standing on one piece of
lettering, half of which the eye does not find. Their output lives only in the session that ran
them — nothing writes it to disk, so a compaction loses it.

**`--space` is for a region whose artwork cannot be painted out.** It lists the
rectangles this page has where that region's Thai would fit and read, nearest
first, and writes `build/<page>.space.png` with them lettered a, b, c. A spot
flagged *in the drawing* passes the same brightness test as paper and may be
skin, cloth or sky; a spot in the page edge is paper by construction. **The
four corner strips come last and are not blank at all** — they punch, and are
set at the bar rather than at the region's own weight because a hole is paid for
in artwork. Take one with `--take <letter>`, which writes the rectangle into `at`
and the status to `glossed`; **no coordinate is ever typed**, which is the point
of the flag. Nothing separates a gutter from the next panel, so the picture is
the only thing that will tell you a spot sits inside a neighbour.

**`--bar` is the number `--space` measures against**, and it goes in
`lettering.json` as `gloss`. It is the smallest size the artist letters a free
caption at, times `k`, so it needs `role` and a settled `k` and is read off the
work rather than chosen.

**`--todo` is every check `audit` makes that needs no rendered page** — a region
with no role, an `ok` with nothing to draw, an `erase` with one, a decline with no
reason, a reading order that is not `1..N`, a misspelled polite ending, a space
inside a Thai word. **The completeness sweep before `clean` is this command.**

It is otherwise a worklist rather than a defect list: boxes standing inside other
boxes, which is a decision and not a fault, and **the boxes the detector nearly
drew that nothing has covered since** — the one report that can see text which is
not in the working file. Each line carries what the reader made of the box. Most
are nothing. **Only a region over it takes one off the list** — judging it artwork
leaves the line there for whoever reads the chapter next. Drawn sound is most of
what it finds, because the same sound drawn twice in a panel can clear the
detector's threshold over one character and not the other.

**`--todo`'s disagreements are what a chapter is not finished without; `--order`
is what you consult while numbering**, the way `fit` is consulted while wording.
A disagreement you answer leaves a trace in the file and one you ignore is there
again next run. A proposed order can be taken whole, and a page numbered that way
cannot be told from one numbered by reading.

`order` is the one field that changes what the reader gets while every check
stays green: `audit` compares the numbers to `1..N`, which a page numbered
completely and in the wrong sequence passes. **Neither the file nor the proposal
is an authority.**

A pair called separable **either way** is a question for the artwork: a horizontal
line passes between the two boxes as cleanly as a vertical one, which happens
wherever a panel with high lettering sits beside one with low, and only the ruled
border decides. A pair separated **one way only** is a real disagreement, unless a
balloon there hangs across a panel border.

**Two numbers in the default view are a budget and they answer different
questions.** `room=` is how many characters the box holds altogether; `line=` is
the longest run it holds without a break. A word longer than `line=` brings the
whole region's size down however short the sentence is, so a wording proposed
against `room=` alone is a guess.

A `?` before the Japanese means the reader was unsure of at least one character
of it: open that box on the scan before translating it. It marks a good share of
a page rather than naming its errors — **what it buys is the unmarked
remainder**, which is almost always right. A page prepared before the score
existed carries no marks at all, so on an old chapter the silence means
unmeasured, not confident.

`ask` is beside them and is not about the work at all — it puts one question to a
CLI running a different model, and knows how each of them takes a prompt.
`…manga_honyaku.ask --list` says which are installed, `--all` asks every one.

**`chapters` holds what somebody wrote *about* a page; `regions` holds the file
being worked on.** On a fresh chapter `regions` is the only one of the two that
exists, which is why it is what to open a chapter with.

## `fit`, and why it is asked before applying rather than after rendering

In a box drawn for vertical Japanese the size is set by the **longest token**,
not by the length of the line, so a caption lettered half-size is usually fixed
by a different word of the same meaning rather than a shorter sentence.

**`fit` takes one page and not a chapter**, unlike every stage above it. Given a
chapter it raises `FileNotFoundError` on a path it built itself, so read the
traceback as the argument being wrong rather than the work being broken, and
loop over the pages.

`fit` prints the lines the breaker produced, and **a Thai word broken in the
wrong place is a real defect** — one chapter shipped `ที|แบ็ค` and another nearly
shipped `คุณชิ|กุระ` in five places. Only the line list shows them. Fix a bad
break by choosing a different word, or by putting the word in `words.txt` — but
those answer different faults. **An entry stops a word being broken *across
lines*; it does nothing about the breaker cutting mid-word** when the column
cannot hold the token whole at any usable size. For that the answer is another
word, or a deliberate space the work records. Never re-rendering.

Its `thai=` is an upper bound for a bubble: `render` caps a bubble at `k × jp`,
which `fit` does not apply, so a bubble reported far above its Japanese size will
simply be drawn at the cap.

`--replace OLD NEW` prices a wording change across every chapter at once and ends
with the pages whose rendering would change — that list is the set to re-render
and nothing more. `--word W --add` / `--drop` prices the other kind of change:
the text does not move, only what the segmenter refuses to split. A word in
`words.txt` cannot be broken across lines, so listing one is how a long token
comes to overflow a narrow box.

**`fit` cannot see the page.** Two of one chapter's three worst-looking balloons
fitted perfectly: a line can sit astride a balloon's outline because the box is
rectangular and the balloon is an oval, and two caption plates can share a
baseline and merge into one shape. Only looking at the rendered page finds those.
