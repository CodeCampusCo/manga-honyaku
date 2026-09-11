---
name: running-the-manga-pipeline
description: Use when running any stage of the manga pipeline or asking a work what its files hold — detect, annotate, prepare, clean, render, audit, and the tools that answer a question without changing anything (regions, chapters, tally, fit, check, sheet). Invocations, what each one reports, and the flag that answers each question.
---

# Running the pipeline, and asking a work what it holds

`AGENTS.md` says which of these to run and when. This file is how.

## Every stage takes the work first

    uv run python -m manga_honyaku.render series/<work>            # every page
    uv run python -m manga_honyaku.render series/<work> X0006      # one page
    uv run python -m manga_honyaku.render series/<work> 01/ch02    # a directory

`detect`, `annotate`, `prepare`, `clean`, `render` and `audit` all read their
arguments that way. **`annotate` depends on `detect` and on nothing else**, so it
runs any time after it — before `prepare` or after, whichever a work's handoff
says. What it draws is what makes a page readable region by region, so it has to
have run before anybody opens one. Nothing named is every page; a name that is a page is that
page; a name that is a directory is every page under it, so a chapter is asked
for the way it is stored.

## Reading an image

    uv run python -m manga_honyaku.sheet a.png b.png -o /tmp/look.png
    uv run python -m manga_honyaku.sheet 16.png 17.png --rtl -o /tmp/spread.png
    uv run python -m manga_honyaku.sheet page.png --crop 640,280,1060,760 -o /tmp/one.png

It caps each image at the width past which reading stops getting easier and cost
goes on rising, and `--crop X1,Y1,X2,Y2` takes a box out first. A spread costs
about 2300 tokens and one bubble about 1000 — **one page and two pages cost the
same**, so read the spread. There is never a reason to write a resize by hand.

**`--rtl` for a spread in a right-to-left work**, which puts the first page named
on the right, where the reader starts. Without it the two halves are swapped and
nothing about the sheet says so: each panel still reads, and the page that came
after appears to come before. It prints which way round it built every sheet of
more than one image — that line is the only thing that will tell you.

## The two that check

    uv run python -m manga_honyaku.check series/<work> <pages>
    uv run python -m manga_honyaku.audit series/<work> <pages>

Both read their pages the way a stage does: nothing named is the whole work, a
page id is that page, a directory is every page under it.

`check` reads every region again and reports any holding a line that belongs to
another region on the same page — the Thai is plausible where it sits and only
the boxes disagree, which is why a re-read of the page will not find it. Three
bubbles on X0048 held each other's lines and nothing else found them.

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
    …manga_honyaku.regions series/<work> 01/05 --order # a reading order proposed from the boxes
    …manga_honyaku.chapters series/<work> X0006-X0008 # what the reading found on those pages
    …manga_honyaku.tally    series/<work>             # the counts a chapter is read back against
    …manga_honyaku.fit      series/<work> 01/05 F1 "…" # what size a candidate line draws at
    …manga_honyaku.fit      series/<work> --replace ก ข # what changing a word costs, everywhere

**`--repeats` and `--overlaps` are asked before a page is read**, not after.
`--repeats` answers in two parts, read at two different moments: what an earlier
chapter already settled, with the wording it used, and what these pages
themselves say twice. `--overlaps` lists the pairs standing on one piece of
lettering, half of which the eye does not find. Their output lives only in the session that ran
them — nothing writes it to disk, so a compaction loses it.

**`--todo` is every check `audit` makes that does not need a rendered page** —
a region with no role, an `ok` with nothing to draw, a decline with no reason, a
reading order that is not `1..N` — **so the completeness sweep before `clean` is
this command and not a script.** One translator here wrote that sweep by hand
twice, once before `clean` and once at the end, because this line did not say so.

It is otherwise a worklist rather than a defect list. It asks about boxes standing
inside other boxes, which is a decision, not a fault, and about **the boxes the
detector nearly drew and nothing has covered since** — the one report in the
pipeline that can see text which is not in the working file. Each line carries
what the reader made of the box, which is what makes it a decision rather than a
crop to build: a line reading `ん` beside a page that draws ぽにょん twice answers
itself. Most are nothing. Adding a region over one or deciding it is artwork
clears it either way, and a list that clears is a list that goes on being read.
Drawn sounds are what it is for: `07/19` of the first work here draws one twice,
once over each woman, and the detector found one of them.

**`--todo`'s disagreements are what a chapter is not finished without. `--order`
is what you consult while numbering**, the way `fit` is consulted while wording.
The asymmetry is the whole design: eight lines you have to answer cannot be
discharged by accepting them, because answering one leaves a trace in the file
and not answering leaves the line there next run — whereas a hundred and sixty-two
proposed numbers can be taken with one keystroke, and a page numbered that way
and a page numbered by reading are the same file.

`order` is the one field that changes what the reader gets while every check
stays green: `audit` sorts the numbers and compares them to `1..N`, which a page
numbered completely and in the wrong sequence passes. **Neither the file nor the
proposal is an authority.** On one chapter here the file was wrong once — a
thought cloud sorted before the shop sign above it, from sorting a panel by x and
forgetting the top-down half — and the geometry was wrong three times. The
dispute list is the only place either of them was checked.

A pair it calls separable **either way** is a question for the artwork: a
horizontal line passes between the two boxes as cleanly as a vertical one, which
happens whenever a panel with high lettering sits beside one with low, and only
the ruled border decides. A pair separated **one way only** is a real
disagreement — unless a balloon there hangs across a panel border, which is the
other way the geometry gets it wrong.

**Two numbers in the default view are a budget, and they answer different
questions.** `room=` is how many characters the box holds altogether; `line=` is
the longest run it holds without a break. A word longer than `line=` brings the
whole region's size down however short the sentence is, so a wording proposed
against `room=` alone is a guess — `fit` has contradicted one twice here. A `?`
before the Japanese means the reader was unsure of at least one character of it:
open that box on the scan before translating it. **What it buys is the other
direction.** The mark is common — about three in five regions — so it narrows a
page rather than naming its errors; what is worth trusting is the unmarked
remainder, where 65 of 66 regions of one chapter needed no correction at all.

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

`fit` prints the lines the breaker produced, and **a Thai word broken in the
wrong place is a real defect** — one chapter shipped `ที|แบ็ค` and another nearly
shipped `คุณชิ|กุระ` in five places. Only the line list shows them. Fix a bad
break by putting the word in `words.txt` or by choosing a different word, not by
re-rendering.

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
