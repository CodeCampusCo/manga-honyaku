# Working a chapter: the record and the roles

Composing the line itself is [`SKILL.md`](SKILL.md); this is the record around
it, for whoever translates.
Tool names here are short — `regions --todo`, `check`, `fit`, `chapters`,
`tally`, `audit`, `prepare --retag`. The full forms are in
[`../running-the-manga-pipeline/SKILL.md`](../running-the-manga-pipeline/SKILL.md).

## Read this much of the record before starting

- **The work's own files, always, in full** — `voice.md`, `characters.md`,
  `glossary.md`, `style.md`, `questions.md`, `handoff.md`,
  `summary.md`.
- **The previous chapter's `chapters/NN.md`, always.**
- **Any other chapter only when a question actually arises**, and then through
  `chapters` for the specific pages rather than by opening the file.

## Where a decision goes

Route it before writing it down: *would this still be true of a different manga
by a different artist?* If yes, it belongs in a skill. If a page, a face or a
measurement told you, it belongs to the work that told you. A fact about the two
languages is never the work's.

Within the work:

| The finding | The file |
| --- | --- |
| how a character speaks | `characters.md` |
| what happened | `summary.md` |
| what the work has not answered | `questions.md` |
| what the next translator has to pick up | `handoff.md` |

## Keep the work's files current as you go

**`characters.md`**

- Identify by costume and props first. Faces and proportions are deformed for
  effect; do not take them as evidence.
- Record each character's speech habits.
- Give someone the file does not name yet the base of whoever in it they are
  most like.
- Give a bit part — someone who turns up twice, usually without a name — what
  the moment calls for, and a row only where they may come back. Do not build a
  persona for one.
- Enter a recurring anonymous voice as a group (`passerby`, `commenter`), never
  as an invented character.

**`glossary.md`** — every agreed transliteration and term, with the reason. A
คู่คำ you had to think about goes in too — `เปียโนหลังนี้` over `เปียโนอันนี้`.
Per work, even where another work needed the same word.

**`words.txt`** — one Thai word per line: names and transliterations, whatever
stops meaning anything when cut in half. Not phrases; see
[`../thai-manga-lettering/SKILL.md`](../thai-manga-lettering/SKILL.md) for what a
phrase in there costs. Per work, like the glossary.

**`style.md`** — a ruling that will not expire, under one of two headings.

- *Where this work departs from the skills* — which general rule, and what this
  work does instead.
- *What this artist does normally* — what `audit` or `page-look` reports every
  run and was ruled correct, with the number that settled it.

**`summary.md`** — rewrite it; never append. Keep the premise and
the recent chapters at length and compress older ones toward a line each as they
recede. No section per chapter.

**`questions.md`** — what the work has not answered yet, and nothing else.

- Update it at the end of a chapter, not while translating.
- Remove an item the moment the work answers it, and put the answer in
  `characters.md`. Do not keep a list of answers here.
- A page's own `questions` field is a different thing and stays on the page.

**`handoff.md`** — written by whoever ran the chapter, not by you. Report into
it; what belongs in it is below.

- Put in it: where the chapters stand, anything left undone, anything decided
  late that earlier chapters predate, and whatever operational fact about this
  work would otherwise have to be rediscovered. Nothing about the work itself.
- Remove an item when someone does it. An item nobody will ever do is
  `style.md`'s.
- Write "nothing outstanding" rather than deleting the heading.
- Point only at what will still be there when it is read: no pull request or
  issue number, no file in a scratch directory, nothing that was true of the
  session rather than of the work. Name a rule that has landed where it now
  lives; leave a rule still in flight out of the file entirely.
- Test every line: could someone who was not there act on it a month from now?

## Write down what you saw, page by page

Keep one file per chapter in `chapters/`, named with the same segment the
pages carry — `chapters/02.md` for pages `02/…`, two digits where the pages are
flat — one entry per page, however
little is on the page. Write it from the raw scan, never from the rendered
output.

Head every one of these files with:

> This is what was seen while reading, not a substitute for the page. If you need
> something that is not written here, open the scan. Never guess from an
> incomplete note.

Four things per page:

```markdown
## <page id>
Art — the panels: how many, how they read, which are cuts to somewhere else.
  Then what is in them: place, who is present and what makes each recognisable
  here, props the page gives room to. Detail in proportion to the space the
  artist gave it — a full-page panel earns a paragraph, a row of talking heads
  earns a line. Say what changed from the last page; unchanged needs no words.
What happens — the action.
Who speaks — who says each line, and what settled it.
? — what you could not read, and why you could not. Resolved later, in place,
  saying where the answer came from.
```

While you write the entry:

- Quote a line to refer to it — the Japanese, **never the translation**.
- Name a region id where the note is about that region's handling: which box the
  detector missed, which of a pair to keep. `regions <work> <page>` prints the
  page's ids. Never use an id in place of saying what the line is.
- Mark anything you did not verify as a guess — a size you did not ask `fit`
  for, a claim about part of a page you did not frame.
- Attribute each speaker from the page around the line, not from the Japanese
  alone: `わたし` is not evidence of who is speaking. Structure is what gets
  misread — settle which panel a line sits in, and which panels are cuts to
  somewhere else, before the words in them.
- Read as a reader does. Where you already know something the page has not said
  yet, write that the page does not say it and where it arrives; do not fold the
  answer in.
- Where a page is content you will not describe, still record its panels, who is
  in it, and what it does to the story.
- Correct a region's `source` in the same breath as reading its crop. Where the
  box is what is wrong, fix the box in the same pass, then `prepare --retag`.
- When you open a scan because the entry did not say, write what you found back
  into that entry.

## Choose a region's role

`AGENTS.md` gives the five values.

- **Most `title` is `declined`** — the magazine's furniture: masthead, promo
  strips, credits, logos, printed over the artwork rather than drawn into it.
  The role still says what the region is; `status` decides whether it is acted
  on.
- **`image_text` and `sfx` are recorded and not lettered.** Set `status: ok` and
  write a `target` on them anyway.
- **Decide `image_text` by what the reader loses, not by where the writing
  sits.** It is `image_text` when the content reaches the reader another way — a
  chyron whose story is in the lettered post beside it — or when losing it costs
  nothing. **When the scene does not work without it, draw it**: move the role to
  `caption` for writing in the artwork, `dialogue` for a sound in a balloon
  `clean` can follow. There is no third value — a region either erases and is
  drawn into, or it does neither.
- **`caption` against `dialogue` is thinking against saying aloud**, not
  formatting. File a narrator's interior voice as `caption`.

## Record uncertainty, and decline out loud

- Write a page's `questions` only where being wrong would change what gets
  drawn. Worth a note: a comment lettered level while the original is skewed
  with a phone screen. Not worth one: that you considered two synonyms.
- When you decline a region, mark it `declined`, give the `reason`, and say what
  the reader loses. Never silently skip and never quietly soften: a page that is
  missing four lines says so in its own file.

## Apply a chapter's translation in batches

1. Write **one throwaway script per batch of pages**, never one edit per region.
2. Write the batch as data — page, region id, and the fields to set.
3. Run it, and have it report each region's length against its `room`.
4. Delete the script afterwards.

## Verify the record before rendering

1. **`check <work> <pages>`**, and fix every region it reports as holding a line
   that belongs to another region on the same page.
2. **`regions --todo`**, and fix what the file still leaves unfinished and the
   characters this face cannot draw. Ask the font — `regions --todo` and
   `render`'s own warning both do. Never write a list or a regex of undrawable
   characters against a work's `style.md`.
Then hand the chapter back. The passes after this, the stages that draw, and the
read-back into the work's notes are
[`../running-a-chapter/SKILL.md`](../running-a-chapter/SKILL.md), and not yours.
