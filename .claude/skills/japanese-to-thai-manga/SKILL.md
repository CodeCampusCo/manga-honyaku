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

## The record, the roles, and reviewing

Composing the line is one half. The other is the record around it — which value a
region takes, which file a decision belongs in, what to write down page by page,
what to verify before rendering, and which chapters earn a review pass.

That is [`working-a-chapter.md`](working-a-chapter.md), beside this file. Read it
before filing a region or closing a chapter; you do not need it to translate a
sentence.
