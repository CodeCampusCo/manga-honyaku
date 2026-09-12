---
name: running-a-chapter
description: Use when running a chapter end to end rather than translating one — the order the stages and the three passes go in, reading the finished chapter back into the work's notes, and deciding whether a chapter earns a review or a span earns a sweep. The job above the page.
---

# Running a chapter

You are not translating. You dispatch the passes, run the stages between them,
and decide what the chapter leaves behind. Tool names here are short; the full
forms are in
[`../running-the-manga-pipeline/SKILL.md`](../running-the-manga-pipeline/SKILL.md).

## The order

1. **`regions --repeats`** and **`regions --overlaps`** over the chapter, before
   any page is read. Their output lives only in the session that ran them, so
   hand it to the translator with the range.
2. **`translate-pages`**, in its own session, over the range. It ends at `check`.
3. **`proofread-against-source`**, in its own session. Apply what it returns
   yourself — it has no `Edit`, and an editor who fixes as it reads stops
   reading. It needs no rendered page, so a finding here costs an edit instead of
   a re-render.
4. **`clean`**, then **`render`**, then **`audit`**. Fix what `audit` reports.
5. **`page-look`**, in its own session, over the rendered pages. Apply, and
   re-render the pages it names. **Where you rule one of its reports fine
   because of how this artist draws, write the number into `style.md`** — the one
   file that pass may read.
6. The read-back below, then `handoff.md`.

Each pass runs once per rendering of the chapter. What each one may see is in
`AGENTS.md`; if your tool cannot take away the tools their frontmatter names,
that column is yours to keep.

**`handoff.md` is yours to write** — rewritten, never appended. What goes in it
is in
[`../japanese-to-thai-manga/working-a-chapter.md`](../japanese-to-thai-manga/working-a-chapter.md).

## When the chapter is rendered, read your own chapter back

One pass over the finished working files rather than the art.

Answer four questions, each with numbers or page ids:

- **Count the register, do not remember it.** How many of a character's lines
  took the polite particle, out of how many. `tally <work>` prints this for every
  speaker and every chapter at once, the Japanese `ですます` beside the Thai
  particle. Put a ratio that has moved since last chapter in the file as
  characterisation. Write a line saying so where it has not moved.
- **Find the onlys and the firsts.** Something a character did exactly once in a
  chapter is the chapter's hinge. Once is a decision, twice is a habit: say which.
- **Answer the gauges the file already set** — a suffix that has not dropped, a
  pronoun that has not moved. Say outright whether each moved this chapter.
  Write "three chapters in, neither has moved".
- **Say what the chapter proved or broke.** Record the page that tested a rule
  and did not break it. Fix a rule the chapter contradicted; do not annotate it
  with an exception.

**Add this chapter's counts to the previous chapters' and read the row.** Never
take a count against one chapter alone.

Then, editing the files:

- **Cite page ids for everything.**
- **Add, sharpen, or delete; never re-say** what is already there.
- **Cut what has stopped earning its place**, and expect to. The test: *would
  someone starting at the next chapter need this line?* Rewrite an observation a
  later chapter superseded rather than annotating it. Make two entries saying one
  thing into one. Remove a gauge the work has answered and put the answer where
  answers go. A good pass often makes these files shorter.
- **Sort each finding into its file** by the table above.

## Going back over a chapter that is already rendered

Two jobs that fall at the same moment: a review protects the chapters that come after, a
sweep repairs chapters already out. Only the sweep is batched.

### Review a chapter when what it settles will be inherited

- **Always a work's first chapter, before the second one starts.**
- After that, review a chapter that **establishes** rather than one that
  continues: a character who will recur, a term that had to be decided, a
  register that moved. Skip a chapter that only spends what earlier ones settled.
- **Do not review every chapter.**
- A work with no volume boundary — a web serial that simply runs — reviews on
  this rule alone.

### Sweep a span when a decision has settled

- Do not stop to repaint earlier chapters when a correction arrives mid-work.
  Collect corrections and pay them off together, once the decision has stopped
  moving, over whatever span it reaches — a volume where a work has volumes, a
  span where it does not.
- **Search, do not re-read.** The decision names the Japanese it applies to:
  `regions --match <japanese>` searches `source`, `target` and `reason` across
  every chapter.
- Where a sweep cannot be expressed as a search, state the rule better until it
  can.
- **Rewrite the notes files at the sweep, whole and once** — not once per
  chapter. A single chapter's review adds to `questions.md` and `handoff.md` and
  leaves the rest alone.

### When two passes disagree, take neither

Find the wording that satisfies both, price it, and record that it came from the
pair: a root kept visible with a shorter tail, a compound split into the two
ordinary words it is made of.

### What a review looks at, in this order

**1. `audit`.** Run it on every chapter as it lands, review or no review. Fix
everything it reports — a region that was erased and drew nothing back, Japanese
that survived `clean`, a broken reading order, a decline with no reason — except
two findings that are notes rather than defects:

- **Fit.** Look at each, change few. A line well under its `room` is usually a
  one-character reaction bubble that is correct; a line well over it is usually
  the better sentence, lettered smaller.
- **Surviving ink.** Ask *where* it is, not how much. Open the rendered page and
  fix it only where it shows under the Thai. Do not hand-edit boxes or masks to
  chase the rest.

**2. The read — a person, or a session with no restriction on it.** Open the
rendered pages and the originals together and ask of each line: does this read
like something a Thai speaker would say, in this character's voice, at this
moment? Do not hand this step to `proofread-against-source` or `page-look`; it
needs the rendered page and the Japanese at once.

**Change a line only where it is wrong or it stumbles** — never because you would
have written it differently. Count the lines you change; where it is most of
them, raise the bar.
