# Working a chapter: the record, the roles, and when to review

Tool names here are written short — `regions --todo`, `check`, `fit`. Nothing
installs a command, so each is `uv run python -m manga_honyaku.<tool>
series/<work> …`; the full forms are in
[`../running-the-manga-pipeline/SKILL.md`](../running-the-manga-pipeline/SKILL.md).

Everything here is about the chapter rather than the line. The craft of composing
the Thai is in [`SKILL.md`](SKILL.md); this is what surrounds it — which value a
region takes, which file a decision belongs in, what to write down as you read,
what to check before rendering, and which chapters are worth a review pass.

## Choosing a region's role

`AGENTS.md` gives the five values and what `clean` and `render` do with each.
Which one a region *is* is a reading decision, and these are the four that are
got wrong.

**Most `title` is `declined`**, because the
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
is not furniture. Draw it**, which means moving the role: `caption` for writing
in the artwork, `dialogue` for a sound in a balloon `clean` can follow. There is
no third value; a region either erases and is drawn into or it does neither. Filed wrongly it is the quiet failure: recorded, so
it looks handled, and Japanese on the page at the one place that mattered.

**`caption` against `dialogue` is not a formatting choice.** It is the difference
between what a character thinks and what they say, which is what `tally` counts
and what `characters.md` tracks across chapters. A chapter that files a
narrator's interior voice as `dialogue` reports them as having spoken every line
of it, and that number then joins a column counting something else.

## What goes here, and what goes in the work's own files

The test when something new is learned: *would this still be true of a different
manga by a different artist?* If yes it belongs in a skill. If a page, a face or
a measurement told you, it belongs to the work that told you.

## Keep the series files current as you go

- **`characters.md`** — identify by costume and props first; faces and
  proportions are deformed for effect and are not evidence. Record each
  character's speech habits, because those are what make chapter 8 sound like
  chapter 1. Name a voice group (`passerby`, `commenter`) rather than inventing
  a character, and give it its own entry the moment it is named.
- **`glossary.md`** — every agreed transliteration and term, with the reason.
  Nothing reads it but you; it is what makes a later chapter say what the first
  one said. Per work, always: two works that both need the same term write it
  down twice, and that is cheaper than a shared list that grows with every work,
  serves none of them particularly, and puts each work's vocabulary somewhere
  anyone with the repository can read it.
- **`words.txt`** — one Thai word per line, and the line breaker's whole
  dictionary. A different list for a different reason: it holds what stops
  meaning anything when cut in half, which is names and transliterations. Not
  phrases — see the `thai-manga-lettering` skill for what a phrase in there
  costs. Per work, for the same reason as the glossary.
- **`style.md`** — only if this work departs from a convention above. Most works
  never need the file; a general rule written down per work is a copy that will
  drift from the one it was copied from.
- **`summary.md`** — capped length, rewritten rather than appended.
- **`handoff.md`** — what the *next translator* has to pick up, and nothing about
  the work itself. Where the chapters stand, anything left undone, anything
  decided late that earlier chapters predate, and whatever operational fact about
  this work would otherwise have to be rediscovered. **Rewritten, never appended**
  — it describes the situation as it stands, not how it got there. An item leaves
  when someone does it, which is a different clock from `questions.md`, which is
  why it is a different file. Say "nothing outstanding" rather than deleting the
  heading; silence and unchecked look identical.

  **Everything it points at has to still be there when it is read.** It is picked
  up by someone with none of the context that wrote it, so it cannot refer to a
  pull request or an issue number, to a file in a scratch directory, or to
  anything else that was true of the session rather than of the work. A rule that
  has landed is named where it now lives; a rule still in flight does not belong
  in the file at all. The test: could this line be acted on a month from now by
  someone who was not there?
- **`questions.md`** — what the work has not answered yet, and nothing else.
  **Update it at the end of a chapter, not while translating.** An item leaves
  the moment the work answers it, and the answer goes to `characters.md`. Keeping
  a list of answers here instead is how a work ends up carrying, for three
  chapters, a question it settled in the first — which happened. A per-page
  `questions` field is a different thing: it is about one page's output, and
  stays there.

## When the chapter is rendered, read your own chapter back

**One pass, after the pages are out, over the finished working files rather than
the art.** It is a separate step from translating because what it looks for
cannot be seen from inside a page: counts, firsts, and comparisons against the
chapters before. Its output goes to `characters.md`, and that file is the only
reason chapter 8 sounds like chapter 1.

Four questions, and they all have answers that are numbers or page ids:

- **Count the register, do not remember it.** How many of a character's lines
  took the polite particle, out of how many. `tally <work>` prints this for
  every speaker and every chapter at once, the Japanese `ですます` beside the
  Thai particle, so the row can be read rather than assembled. A ratio that
  has moved since last chapter is characterisation and goes in the file. One
  that has not moved is worth a line saying so, because *confirmed* and
  *never checked* look identical a chapter later.
- **Find the onlys and the firsts.** Something a character did exactly once in a
  chapter is the chapter's own hinge — the artist spent it deliberately. Once is
  a decision; twice is a habit; the file should say which. This is invisible
  while translating, where every line is the only one in front of you.
- **Answer the gauges the file already set.** `characters.md` names things to
  watch — a suffix that has not dropped, a pronoun that has not moved. Say
  outright whether each moved this chapter. **"Three chapters in, neither has
  moved" is worth writing**, because without it a later session finds an
  unanswered gauge and decides it must have happened offscreen.
- **Say what the chapter proved or broke.** A rule that survived a page built to
  fool it is stronger and should record the page that tested it. A rule the
  chapter contradicted is simply wrong: fix the rule, do not annotate it. Two
  rules that disagree are worse than one rule that is out of date.

**A count extends the series, it does not restart it.** The previous chapters'
numbers are already in the work's file; add this chapter's to them and read the
row. A count taken against one chapter alone answers nothing — the question is
always *has it moved*, and one number cannot move.

Then the discipline that keeps the file usable:

- **Cite page ids for everything.** An observation a later session cannot check
  is one it has to either trust blindly or re-derive, and both are worse than a
  number and an id.
- **Do not restate what is already there.** The file grows every chapter, and a
  paraphrase of an existing paragraph is drift with a delay on it. Add, sharpen,
  or delete; never re-say.
- **Cut what has stopped earning its place, and expect to.** The test is the
  file's own job: *would someone starting at the next chapter need this line?* An
  observation a later chapter superseded is rewritten, not annotated with an
  exception. Two entries saying one thing become one entry. A gauge the work has
  answered leaves, and its answer goes where answers go. **These are working
  briefs, not logs — a good pass often makes them shorter.** A file nobody can
  read to the end protects nothing.
- **Sort by which file it belongs to.** How a character speaks is
  `characters.md`. What happened is `summary.md`. What the work has not answered
  is `questions.md`. What the next translator has to pick up is `handoff.md`. A
  fact about the two languages is this file, not any of them.

**`summary.md` cannot hold a section per chapter.** A long series would end with
a file nobody reads, duplicating `chapters/NN.md` at lower resolution. Keep the
premise and the recent chapters at length, and compress older ones toward a line
each as they recede. The detail already exists per chapter; this file is for the
shape of the work.

## How much of the record to read before starting a chapter

Reading everything defeats the point of a record. Reading nothing repeats work
already done and contradicts decisions already made.

- **The work's own files, always, in full** — `characters.md`, `glossary.md`,
  `style.md` if it exists, `questions.md`, `handoff.md`, `summary.md`. These are
  short by design and they are the whole handover.
- **The previous chapter's `chapters/NN.md`, always.** Scenes and states run
  across the break, and a chapter that opens mid-situation will not tell you so.
- **Any other chapter, only when a question actually arises**, and then through
  `chapters.py` for the specific pages rather than by opening the file. That is
  what the tool is for.

## Applying a chapter's translation

**One throwaway script per batch of pages, never one edit per region.** A chapter
is 150–250 regions; editing them one at a time is slow, and the diff it produces
is unreviewable. Write the batch as data — page, region id, and the fields to set
— run it, and let it report which regions fell outside their `room` band so the
misses are a list rather than a discovery at render.

Delete the script afterwards. It described one batch and is wrong for the next.

## Write down what you saw, page by page

You have no memory of an image. It is in front of you while you look and gone
when the session ends, and **what you wrote down is all that survives** — so a
page you read and did not record is a page nobody read.

Keep `chapters/<n>.md` in the work's directory, one entry per page, written from
the raw scan and not from the rendered output. Four things per page:

The review passes read this file and reason from it, so **mark anything you did
not verify as a guess** — a size you did not ask `fit` for, a claim about part of
a page you did not frame.

```markdown
## <page id>
Art — the panels: how many, how they read, which are cuts to somewhere else.
  Then what is in them: place, who is present and what makes each recognisable
  here, props the page gives room to. Detail in proportion to the space the
  artist gave it — a full-page panel earns a paragraph, a row of talking heads
  earns a line. Say what changed from the last page; unchanged needs no words.
What happens — the action.
Who speaks — who says each line, and what settled it: tail direction, where a
  tail crosses a panel border, who is off-panel.
? — what you could not read, and why you could not. Resolved later, in place,
  saying where the answer came from.
```

Quote a line to refer to it — the Japanese, **never the translation.** A
translation written here becomes the answer your translation pass was supposed to
reach on its own.

Name a region id where the note is about that region's handling — which box the
detector missed, which of a pair to keep. `regions <work> <page>` prints the file
in one command, so an id costs nothing now and makes the note checkable instead
of merely readable. Do not use one as a substitute for saying what the line is.

Head every one of these files with the rule that makes them safe:

> This is what was seen while reading, not a substitute for the page. If you need
> something that is not written here, open the scan. Never guess from an
> incomplete note.

Because that is the failure this exists to stop. A page with two bubbles and no
entry got both speakers wrong — assigned from the Japanese alone, `わたし` being
feminine, without looking at the tails, which were round and both pointed at a
third character. The Thai was identical either way, so nothing downstream caught
it. **Structure is what gets misread, not content**: a cut between two places
read as two people in one place.

Read as a reader does. Where you already know something the page has not said
yet, write that the page does not say it and where it arrives — not the answer
folded in, which makes the record look more certain than the page is.

**When you open a scan because the file did not say, write what you found into
that page's entry.** A file that says nothing about something and a page that
does not have it look identical, and that is the one gap the header rule sends
you back to the scan for. Sending every session back for the same gap is the
waste: pay it once and the entry stops being silent. This is what makes an entry
worth trusting later — not that it was written carefully the first time, but
that every session that had to go past it left what it found behind.

Where a page is content you will not describe, still record its panels, who is
in it, and what it does to the story. Those are the parts a later chapter needs,
and they are not the part being declined.

## Verify the record before rendering

**Run `uv run python -m manga_honyaku.check series/<work> <pages>`.** It reads every region
again and reports any holding a line that belongs to another region on the same
page — the one failure that re-reading the page will not show. Three bubbles on
one page held each other's lines and read perfectly as a conversation; only this
found them. Readings you corrected by hand are counted and not listed, because
that list is the same every run.

**Then `regions --todo`**, which reports what the file still
leaves unfinished and the characters this face cannot draw. Ask the font, never
a list somebody typed: `render` warns about the same thing, and two sessions in
a row wrote their own regex against a work's `style.md` before finding that out.

## Going back over a chapter that is already rendered

Two jobs, easy to confuse because they fall at the same moment. **One protects
the chapters that come after it. The other repairs chapters already out.** Only
the second wants to be batched.

### Review a chapter when what it settles will be inherited

**Always a work's first chapter, before the second one starts.** It is where the
register, the pronouns, the glossary and the character file are invented, and
every chapter after it copies them. Held to the end of a volume, it is reviewed
after six chapters have already inherited whatever it got wrong.

One first chapter, read back against its source, returned **eleven real findings
in 238 regions** — among them a potential negative rendered as a plain one,
`聞けず` as *did not ask* rather than *could not ask*, on the line the work's
whole premise rests on; and two terms that had already drifted from the work's
own glossary. Six chapters would have carried all of it.

After that, review a chapter that **establishes** rather than one that continues:
a character who will recur, a term that had to be decided, a register that moved.
A chapter spending only what earlier ones settled has little to give a pass that
`audit` has not already given it.

**This is not "review every chapter."** A restricted pass costs what translating
a chapter costs, and spent on a chapter that established nothing it buys noise.
Where a work has no volume boundary at all — a web serial that simply runs — this
is the rule that stands in for one, and it needs no calendar.

### Sweep a span when a decision has settled

A correction that arrives in chapter 4 does not justify stopping to repaint
chapters 1–3: **the error costs less than the interruption, and a decision made
late is usually still settling.** Collect them and pay them off together, once
the decision has stopped moving, over whatever span it reaches — a volume where a
work has volumes, and simply a span where it does not.

The sweeps are grep-shaped: the decision names the Japanese it applies to, so
search the recorded `source` fields for it rather than re-reading —
`regions --match <japanese>` is that search, over `source`, `target` and
`reason` across every chapter. **A sweep that cannot be expressed as a search
is usually a rule that has not been stated clearly enough yet.**

Rewrite the notes files at the sweep, **whole and once** — not once per chapter.
Seven partial edits to one file produce a file with seven voices in it. A single
chapter's review adds to `questions.md` and to `handoff.md` and leaves the rest
alone.

### When two passes disagree, the answer is usually a third thing

They see different halves on purpose, so a finding from one can cost what the
other is there to protect — a term made consistent across a chapter can arrive as
a token too wide for the box it lands in, and the pass that judges the page will
then call that region the worst thing on it. Neither is wrong, and because they
run in sequence the later one reads as overruling the earlier.

**Take neither.** Find the wording that satisfies both, price it, and record that
it came from the pair. It is usually there: a root kept visible with a shorter
tail, a compound split into the two ordinary words it is made of.

### What a review looks at, in this order, because each narrows the next

**1. `audit`, because it is free and it does not get tired.** This one runs on
every chapter as it lands, review or no review. It reads every finished page
against the artwork actually produced and reports what no other
stage can: a region that was erased and drew nothing back, Japanese that
survived `clean`, a broken reading order, a decline with no reason. Every one of
those has reached a rendered page in silence at least once. Fix all of it.

Two of its findings are notes rather than defects, and over-fixing them costs
more than leaving them:

- **Fit.** A line well under its `room` is usually a one-character reaction
  bubble that is correct; a line well over it is usually the better sentence,
  lettered smaller. Look at each, change few.
- **Surviving ink.** How much is left is not the question — *where* is. Original
  lettering runs past its own box routinely, and residue at a margin is
  invisible. Open the rendered page: fix it only where it shows under the Thai.
  Chasing the rest means hand-editing boxes or masks, which breaks more than it
  repairs.

**2. The read — a person, or a session with no restriction on it.** No pass can
do this one: `proofread-against-source` never opens `out/` and `page-look` never
opens the Japanese, and this step wants both at once. That is why it is here and
not in the passes table.

**It is the only part that needs a person.** Open the rendered
pages and the originals together and ask of each line: does this read like
something a Thai speaker would say, in this character's voice, at this moment?

**The bar for changing a line is that it is wrong or it stumbles — not that you
would have written it differently.** A review that rewrites everything it touches
has destroyed the consistency the notes files exist to protect, and nobody can
tell afterwards which changes were fixes. Count the lines you change; if it is
most of them, the problem is the bar, not the chapter.

## Record uncertainty where it changes the output

`questions` is for the case where being wrong would change what gets drawn — not
for everything you were unsure of. A note that a comment is lettered level while
the original is skewed with a phone screen is worth keeping; a note that you
considered two synonyms is not.

**When you decline a region, mark it `declined` with a reason, and say what the
reader loses.** Never silently skip and never quietly soften — a page that is
missing four lines should say so in its own file.
