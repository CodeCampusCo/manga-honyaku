---
name: japanese-to-thai-manga
description: Use when translating Japanese manga dialogue into Thai — reading order and speaker attribution, composing an utterance whole before cutting it across balloons, choosing pronouns and register, and why an accurate line still reads stiff. Covers keeping a series consistent across chapters and what to check before the pages are lettered.
---

# Translating manga into Thai

## Read the page before you translate any of it

Build a contact sheet of the annotated pages, two to four at a time, and settle
**reading order and speaker attribution first**. Right-to-left within a row of
panels, right-to-left and top-down within a panel. A bubble drawn across a panel
border belongs to the panel its tail comes from.

Print the working file beside the sheet: `regions <work> <chapter>` gives every
box with the size the Japanese was lettered at, the `room` that follows, and the
reading. The sheet says where a region is on the page; only the file says what is
in it and how much of it there is room for.

Attribution is where the guessing goes wrong, and the check is cheap: read the
sequence back as a conversation. `それに…` following a line by the same speaker
means you have the order right; following a line by the other speaker means you
do not.

**The page is the unit of context, and it is measured, not a preference.** For
text embedded in an image, one page per call with the units numbered in reading
order beats every alternative tried: line-by-line loses on every metric, and *so
does more* — three pages, and a whole volume, both score below a single page
(Lippmann et al., COLING 2025, JP→EN ChrF: line-by-line < 36.0 page text < 36.6
+ page image < **36.8** + numbered units in order; 3-page 35.9, whole volume
35.7). Below the page a line is under-determined — Japanese drops subjects, so a
bubble alone has to guess, and the documented failure is a first-person line
coming out as *you*. Above the page, context dilutes.

So read the page, and do not reach for the chapter to translate from. The
chapter file is background — what the scene is and who is in it — and is not a
source: it holds no Japanese, and translating from a summary of the words
instead of the words is a loss no later pass recovers.

## The unit of translation is the utterance, not the bubble

A sentence split across two or three balloons is **one sentence**. Compose it
whole in Thai, then cut it across the regions, giving each piece its own
region's `room`. Mark the group with `utterance` so `render` letters them at one
size — one sentence at two sizes reads as two sentences.

**Do not close what the original left open.** A balloon that ends mid-clause in
Japanese ends mid-clause in Thai. Translating balloon by balloon quietly finishes
each one, and the rhythm goes: `最初はもっとそういうんじゃなくて` runs on into the
next balloon, but came out `ตอนแรกไม่ได้เป็นแบบนั้นเลย` — a closed sentence with
a full stop's worth of finality the original does not have.

This is also the lever the research measures. Numbering the units in reading
order is worth about as much as adding the page image at all, and what it buys
is exactly this: the sequence relation that lets a sentence split across two
bubbles be joined before it is translated.

**The risk it introduces is real and there is a check for it.** Composing whole
and then cutting makes it easier for a line to land in the wrong region, and that
is the one failure re-reading will not show, because the Thai reads plausibly in
both places. `check` exists for it — run it.

## Pronouns are not translated, they are re-chosen

This is a rule for manga in general, not a house style for one work. Japanese
marks age, gender and self-image in the first person; Thai marks *politeness and
distance*, and the two grids do not line up. **Pick the Thai pronoun the
character would have in a Thai edition of a Japanese comic** — not the one that
matches the Japanese word, and not the one the situation would call for if the
scene were Thai.

### The pair, by speaker and by distance

Read each cell as *first person → second person*. The axis is **distance and
power, not affection** — a character can be fond of someone they stay formal
with, and that gap is often the scene.

| Speaker | Stranger | Knows by sight | Friend, familiar | Very close | Someone above them |
| --- | --- | --- | --- | --- | --- |
| Young woman | ฉัน → คุณ | ฉัน → คุณ | ฉัน → เธอ, name | ฉัน → เธอ, name | ฉัน → คุณ (+ค่ะ) |
| Girl, a child | **หนู** → คุณ | **หนู** → คุณ | ฉัน → เธอ, name | ฉัน → เธอ, name | **หนู** → คุณ (+ค่ะ) |
| Young man, boy | ผม → คุณ | ผม → คุณ, name | ฉัน → นาย, name | ฉัน → แก, นาย | ผม → คุณ (+ครับ) |
| Adult woman | ฉัน → คุณ | ฉัน → คุณ, name | ฉัน → เธอ | ฉัน → เธอ or แก | ฉัน, ดิฉัน → คุณ (+ค่ะ) |
| Adult man | ผม → คุณ | ผม → คุณ, name | ฉัน → นาย | ฉัน → แก | ผม → คุณ, ท่าน |
| An elder, speaking down | ฉัน → เธอ | ฉัน → เธอ, name | ฉัน → name, เธอ | ฉัน → แก | ผม, ดิฉัน → ท่าน |
| Thug, villain | ฉัน → แก | ฉัน → แก | ฉัน → แก, พวกแก | **กู → มึง**, only past control | ผม → คุณ, ท่าน |

What the grid is actually saying:

- **`หนู` is a child's word.** It marks the speaker as a child talking to an
  adult, and that is the whole of its range. A teenager or a young woman is
  `ฉัน` in every column, including to someone above her — the deference is on
  the particle, not on the pronoun. Reaching for `หนู` because a woman is young
  or junior or being polite is the single most common way to make a translated
  page read as Thai television rather than as manga.
- **Even a child drops it among friends.** `หนู` is for the gap in rank, so it
  disappears the moment there is not one.
- **It is never a second person.** Japanese already has ちゃん and くん for
  addressing a child, and Thai manga transliterates those — see the honorifics
  below. An elder addresses a junior as `เธอ` or by name.
- **The male side has no counterpart.** Boys and men are both `ผม`, moving to
  `ฉัน` when close. There is no child form to reach for and none is needed.
- **`เรา` is not used as first person.** Closeness is carried by the second
  person — `เธอ`, `นาย`, `แก` — while the first person stays `ฉัน`.
- **A name works as either person**, which is what the Japanese is already doing
  with `ハルカちゃんは…`. It is the safest choice while a relationship is still
  being established.
- **The `very close` cell of the adult rows is character, not rule.** `เธอ` or
  `แก` depending on who the person is.

A register that escalates reads better than one that starts at the ceiling. Give
a character `ฉัน` while he is still arguing and `กู` only in the panel where he
stops arguing, and the shift does work the vocabulary alone cannot. The grid is a
starting position, not a lookup table.

The grid covers the cases a work would otherwise write down for itself: a
working adult woman is `ฉัน` however deferential the line, and a villain reaches
`กู` at the moment he stops choosing words. Nothing about either belongs in a
work's own file — what the character actually says is already in the working
file, page by page.

## Honorifics carry the same information — read them

Japanese name suffixes do work Thai has its own forms for, so the original is
telling you which Thai word to reach for.

| Japanese | Thai | How |
| --- | --- | --- |
| さん | **คุณ** | Fits nearly everywhere. Thai readers also read `ซัง`, but `คุณ` is the one to use, so that it is the same in every work and never a thing to decide. |
| ちゃん | **จัง** — transliterate | Adult to a girl, and to boys too. The role Thai fills with `หนู`, but manga Thai does not use `หนู` here. |
| くん | **คุง** — transliterate | Adult to a child; a senior to a junior they are close to — a student, a junior at work. |
| 様 | **ท่าน** | Never transliterate. |
| 先生 | **อาจารย์**, **หมอ**, **ทนาย** — from context | Closer to *master* than to *teacher*: any credentialed expert, including a mangaka. Thai defaults to "อาจารย์ = schoolteacher" but does accept `อาจารย์` for a mangaka. Read the panel before choosing. |
| 先輩 / 後輩 | **พี่** / **น้อง** | Kinship words work as pronouns in Thai and land this better than a literal translation. |

**A bare name stays bare.** Where the Japanese drops the suffix, so does the
Thai: `忍って` is the name as a vocative, with nothing in front of it.

**A suffix on a role rather than a name takes the Thai kinship or title form** —
`バイト君` is `น้องพาร์ทไทม์`, `店長さん` is `คุณผู้จัดการร้าน`. Transliterating a
role produces nonsense.

## Politeness lands once per utterance

A three-bubble sentence takes one `ค่ะ` / `ครับ`, on the last bubble — the
particle belongs to the utterance, which is the unit everything else here is
composed in too.

Who gets one at all follows the same distance the pronouns do. A woman speaking
politely ends with `ค่ะ`. **Men among themselves take no particle**: `ครับ`
between peers reads as sarcasm, and is for speaking to someone above them.
`はい` answering a question is itself `ค่ะ` or `ครับ`, and does not count as the
sentence-final particle.

Give the same treatment to a pronoun split across bubbles: `私 / 頑張ります!`
is `ฉัน` then `จะตั้งใจทำให้เต็มที่ค่ะ!`, not `ฉัน` then `ฉันจะ…`.

### `นะ` takes `คะ`, `น่ะ` takes `ค่ะ` — the tone mark matches or it is wrong

Four spellings are in circulation and two of them are misspellings:

| | |
| --- | --- |
| **`นะคะ`** | correct |
| **`น่ะค่ะ`** | correct |
| `นะค่ะ` | **wrong** |
| `น่ะคะ` | **wrong** |

The particles agree: no tone mark on both, or a mái èk on both. Mixed across the
pair is an error, and **Thai writers make it constantly**, so it cannot be judged
by whether a line looks like ordinary writing — that instinct is what produces
it. It is a rule, and it is deterministic, so `audit` checks it.

Where the particle is doing no work, drop it and let the bare `ค่ะ` or `คะ`
carry the politeness on its own.

## Match the original's length, not only its sense

The bubble was drawn to hold what the Japanese said. A version carrying the
meaning in half the words leaves it looking empty, and the reader sees the gap
before they read the line.

`room` on the region is how many characters the box holds at the size that region
asks for — counted as widths, so a mark above or below costs nothing and `ที่` is
one. Compose against it. A line coming in at half of `room` leaves the bubble
looking empty; one well past it gets lettered smaller to fit. Neither is a
failure, and neither is worth a second pass at the wording: the better sentence
wins, and where it has to miss, long misses better than short.

Where a line does come in short, the words to add are the ones a bare gloss
drops — `〜があって` is "it so happens that", `らしい` is "I hear that", `けっこう`
is "quite, as these things go", `なんか` hedges the report it introduces. Saying
those in full is both more faithful *and* better lettering.

A line the artist drew short stays short. And where the Thai runs much longer
than the Japanese, **shorten the line rather than the lettering** — a
four-character shout cannot be lettered large under a fifteen-character
translation of it.

**Going over `room` is the ordinary case, not the exception.** Four regions in
ten across a volume overflow and are lettered a step smaller, and of those the
median would have had to be a third shorter to fit. That is not a backlog to
work through. `room` is itself about 15% optimistic — the breaker leaves slack
on most lines and a word cannot be split — so a line written to exactly `room`
already costs its bubble a step.

**Pay the step.** A six-page rerun composed 31% longer, dropped the share of
bubbles keeping their asked-for size from 71% to 59%, and was the better
translation: it was ruled *"อ่านลื่นขึ้นและดูเป็นการพูดคุยที่เป็นธรรมชาติขึ้น"*,
with the single longest line on the page named as the best one on it. The size
step is cheap and the dropped nuance is not — an aspect marker, a hedge, whose
face is red. Nothing downstream puts those back.

So when a line will not fit, **cut padding you added, never content the original
has.** A phrase repeated for emphasis in Japanese that Thai does not need, a
pronoun the Thai can drop, a transliteration that could be a translation — those
are yours to spend. The hedge that carries the speaker's hesitation is not.

## Why an accurate line still reads stiff

Every fault below produces Thai in which **no word is wrong**. Checking the
translation for accuracy cannot find any of them, which is why they survive a
whole volume.

The governing rule, from Thai translation teaching: carry the original's
structure and word order across *as far as it holds* — and **the moment the Thai
sounds ขัดหู, abandon the structure, not the wording.** Nudging words inside a
Japanese-shaped sentence never repairs it. `Not until I filled my glass did I
notice that it was broken` has three Thai renderings; the first two keep the
shape and *do not communicate*, and only the third — which rebuilds the sentence
as Thai — does. The failure here is stopping at the first two.

### A noun in Japanese is usually a verb in Thai

Japanese builds compound nouns freely and Thai does not. `コーティング量がズバ抜
けてる` came out `ปริมาณที่เคลือบมามันเหนือชั้นกว่าใครเพื่อน` — a noun phrase
built to the Japanese's shape. Thai says it with a verb: `เคลือบมาเยอะกว่าเจ้า
อื่นเยอะเลย`.

The same finding comes back from the other direction. A study of 214 Japanese
sound and manner words in published Thai manga and novel translations found five
methods, and in order of frequency they are **adverb, verb, left untranslated,
noun, result phrase** — the two commonest are both predicates and the noun is
next to last. **When a Japanese noun is doing the work of a verb, translate it
as a verb.**

### Words that are each correct and wrong together

Thai calls this คู่คำ; the error is a *collocational clash*, and it is the exact
shape of "accurate but reads wrong":

| wrong | right |
| --- | --- |
| เปียโน**อันนี้** | เปียโน**หลังนี้** |
| อากาศร้อน**แรง** | อากาศร้อน**ระอุ** |
| น้ำตา**ตกหล่น** | น้ำตา**ร่วงหล่น** |
| ปรบมือ**เร็วๆ** | ปรบมือ**รัวๆ** |
| พระสงฆ์ 3 **องค์** | พระสงฆ์ 3 **รูป** |

A pair you had to think about is a pair worth recording in the work's
`glossary.md`, the same as a term.

### The final particle is information, not decoration

Japanese marks stance on the sentence end — `よ ね ぞ わ の さ ぜ` — and **Thai has
its own system in the same slot**, so the information is in the source and
dropping it is a choice. Thai's particles split into stance (`นะ` `สิ` `ล่ะ`
`หรอก` `เลย` `ไง` `แหละ` `เนี่ย` `ว่ะ`) and politeness (`ค่ะ` `ครับ`), and the
vowel's length carries the feeling: **short is curt or serious** — `ซิ` `นะ`
`เถอะ` `ละ` — **long is coaxing** — `ซี่` `น่า` `น้า`.

`小口が落ちたぞ!!` came out `โคงุจิตกลงไปแล้ว!!`, which drops `ぞ` — and `ぞ` was
the whole of the line's voice. Over one volume, **56% of dialogue lines ended
with no particle at all**, against 33% with a stance particle and 11% with a
polite one. Some of those are right — an exclamation, a fragment running into
the next balloon — but a bare majority is worth suspecting.

Aspect and reason markers go the same way. `まざっちゃうから...` became
`มันจะปนกันค่ะ…`, which keeps the fact and loses both the `ちゃう` that says *and
that would be a shame* and the `から` that says *that's why*.

### An idiom translated by its parts inverts

`覚悟を決める` is *to steel yourself*, and came out `ทำใจ`, which is *to resign
yourself* — the opposite stance. When a phrase is idiomatic, ask what it is for
before what it says; an accurate rendering of the parts can invert the speaker.

## Thai lengthens by opening the vowel

A syllable held is a syllable whose vowel opens: `ちゃ〜ん` is `จางงง`, where the
`ั` of `จัง` becomes `า` and the final consonant runs on.

The same move carries the symbols a Thai comic face has no glyph for — **♥ ♡ ★
☆ ♪ 「」 ○**. They are tone markers, so render them the way Thai marks tone: in
the wording and the drawn-out vowel. Where a character ends most of her lines
with `♥`, she reads as herself in Thai through the vowels and the word choice,
never through a particle she would not otherwise use.

Where the original uses a CJK bracket or a censoring circle, take the shape:
`【】` becomes `[]` and `◯◯◯` becomes `OOO`. What `◯◯◯` says is that a word has
been withheld, and three circles say that in either script.

## Conventions that hold across works

These need no deciding per work; a work's own file records only where it departs.

- **Sound effects are artwork.** Not translated, not painted over. They were
  drawn into the page.
- **Text inside the drawing is translated and recorded, and the drawing is left
  alone** — signs, phone screens, flyers, product labels. The Thai reaches the
  reader through the working file rather than by overwriting the picture.
- **`…` at the end of a line is a character trailing off,** not an ellipsis of
  omitted words. Thai keeps the `…` and lets the sentence stay unfinished.
- **Keep the question mark wherever the Japanese has one.** Thai does not need it
  — `เหรอ` and `ปะ` already mark the question — but in a bubble it is part of the
  lettering's rhythm rather than grammar, and dropping it flattens a beat the
  artist drew. A question the Japanese wrote without one gets none.
- **Text drawn on a slant is lettered level.** Nothing rotates text, and level
  Thai beside a skewed phone screen reads fine at print size.

## What goes here, and what goes in the work's own files

This file holds **method, and facts about the language pair** — that Thai marks
politeness where Japanese marks self-image, that `หนู` is a child's word, that
`さん` is `คุณ`. Those are true of the next manga too, and re-deriving them per
work would mean deciding the same thing again and having the two decisions drift.

A work's own directory holds **what reading that work produced**: who its
characters are and how each one speaks, its terms, its unbreakable words, what it
has not answered yet. The grid above says what a register becomes in Thai;
`characters.md` says which register a given character has. Neither can do the
other's job.

The test when something new is learned: *would this still be true of a different
manga?* If yes it belongs here. If it is something a page told you, it belongs to
the work that told you.

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

Quote a line to refer to it — the Japanese, no region id and no translation. An
id means opening another file; **a translation written here becomes the answer
your translation pass was supposed to reach on its own.**

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

**Run `python -m manga_honyaku.check <work> <pages>`.** It reads every region
again and reports any holding a line that belongs to another region on the same
page — the one failure that re-reading the page will not show. Three bubbles on
one page held each other's lines and read perfectly as a conversation; only this
found them. Readings you corrected by hand are counted and not listed, because
that list is the same every run.

Then check the targets for characters the face cannot draw, before a page is
rendered rather than after.

## Reviewing pages that are already rendered

Two different jobs are easy to bundle here, because on the first work they fell
at the same moment — the end of a volume. **One protects the chapters that come
after it. The other repairs chapters already out.** Their triggers are not the
same, and only the second one wants to be batched.

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
`regions <work> --match <japanese>` is that search, over `source`, `target` and
`reason` across every chapter. **A sweep that cannot be expressed as a search
is usually a rule that has not been stated clearly enough yet.**

Rewrite the notes files at the sweep, **whole and once** — not once per chapter.
Seven partial edits to one file produce a file with seven voices in it. A single
chapter's review adds to `questions.md` and to `handoff.md` and leaves the rest
alone.

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

**2. The read, which is the only part that needs a person.** Open the rendered
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
