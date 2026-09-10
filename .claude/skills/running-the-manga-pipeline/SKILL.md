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
    uv run python -m manga_honyaku.sheet page.png --crop 640,280,1060,760 -o /tmp/one.png

It caps each image at the width past which reading stops getting easier and cost
goes on rising, and `--crop X1,Y1,X2,Y2` takes a box out first. A spread costs
about 2300 tokens and one bubble about 1000 — **one page and two pages cost the
same**, so read the spread. There is never a reason to write a resize by hand.

## The two that check

    uv run python -m manga_honyaku.check series/<work> <pages>
    uv run python -m manga_honyaku.audit series/<work> <pages>

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
piece of lettering the detector missed is invisible to them.

## Asking a work a question

None of these is a stage. None of them writes.

Every one of them is `uv run python -m manga_honyaku.<tool> series/<work> …` —
nothing here installs a command, so a bare `regions` is not on anyone's PATH.

    …manga_honyaku.regions series/<work> 01/ch02      # the working file: boxes, sizes, room, source
    …manga_honyaku.regions series/<work> --match 聞け  # every line of the work that ever said this
    …manga_honyaku.regions series/<work> 01 --overlaps # region pairs on the same lettering
    …manga_honyaku.regions series/<work> 01 --todo    # what the file still leaves unfinished
    …manga_honyaku.regions series/<work> 01 --repeats # lines an earlier chapter already said
    …manga_honyaku.chapters series/<work> X0006-X0008 # what the reading found on those pages
    …manga_honyaku.tally    series/<work>             # the counts a chapter is read back against
    …manga_honyaku.fit      series/<work> 01/05 F1 "…" # what size a candidate line draws at
    …manga_honyaku.fit      series/<work> --replace ก ข # what changing a word costs, everywhere

**`--repeats` and `--overlaps` are asked before a page is read**, not after.
`--repeats` lists what an earlier chapter already settled, with the wording it
used; `--overlaps` lists the pairs standing on one piece of lettering, half of
which the eye does not find. Their output lives only in the session that ran
them — nothing writes it to disk, so a compaction loses it.

**`--todo` is a worklist, not a defect list.** It asks about boxes standing
inside other boxes, which is a decision, not a fault.

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
