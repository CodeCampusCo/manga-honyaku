---
name: japanese-to-thai-manga
description: Use when translating Japanese manga dialogue into Thai — choosing pronouns and register, matching a line's length to the bubble it was drawn for, establishing reading order and speaker attribution, and keeping a series consistent across chapters. Covers what to check before the pages are lettered.
---

# Translating manga into Thai

## Pronouns are not translated, they are re-chosen

This is a rule for manga in general, not a house style for one work. Japanese
marks age, gender and self-image in the first person; Thai marks *politeness and
distance*, and the two grids do not line up. **Pick the Thai pronoun the
character would have in a Thai edition of a Japanese comic** — not the one that
matches the Japanese word, and not the one the situation would call for if the
scene were Thai.

| Japanese | Thai | Why |
| --- | --- | --- |
| 私 / あたし, a young woman | **ฉัน** | `หนู` is what the situation looks like it wants, and it is what a Thai girl really would say — which is the problem. In manga it reads as a Thai schoolgirl and pulls the scene out of Japan. |
| 僕 / 俺, an ordinary man | **ผม** — `ฉัน` where he is rough or talking to himself | `ผม` is unmarked in Thai and carries neither the politeness of 僕 nor the swagger of 俺; let the sentence carry those. |
| 俺 / 俺様 from a thug or a villain | **ฉัน** | `กู` is coarser in Thai than 俺 ever is in Japanese. Hold it back for someone past the point of choosing words — screaming, swinging — and it lands when it finally comes. |
| お前 / てめえ / あんた | **แก**, **พวกแก** | Same reason: `มึง` overshoots. `แก` is already dismissive, and it leaves somewhere to go. |

A register that escalates reads better than one that starts at the ceiling. One
stalker says `ฉัน` while he is arguing and `กู` in the panel where he pulls a
knife, and that shift does work the vocabulary alone cannot.

What belongs in `series/style.md` is only the exception: which character, on
which page, is allowed past the default.

### The pair by speaker and distance

Read as *first person → second person*. Distance, not affection: a character can
be fond of someone they are formal with.

| Speaker | Stranger | Knows by sight | Friend | Very close | Someone above them |
| --- | --- | --- | --- | --- | --- |
| Young woman, girl | ฉัน → คุณ | ฉัน → เธอ | ฉัน → เธอ, name | เรา → แก | ฉัน → คุณ (+ค่ะ) |
| Young man, boy | ผม → คุณ | ผม → นาย, name | ฉัน → นาย, name | ฉัน → แก | ผม → คุณ (+ครับ) |
| Adult woman | ฉัน → คุณ | ฉัน → คุณ | ฉัน → เธอ | เรา → แก | ฉัน → คุณ (+ค่ะ) |
| Adult man | ผม → คุณ | ผม → คุณ, name | ฉัน → นาย | ฉัน → แก | ผม → คุณ, ท่าน |
| An elder, speaking down | ฉัน → หนู, เธอ | ฉัน → หนู, name | ฉัน → name, เธอ | ฉัน → แก | ผม, ดิฉัน → ท่าน |
| Thug, villain | ฉัน → แก | ฉัน → แก | ฉัน → แก, พวกแก | **กู → มึง**, only past control | ผม → คุณ, ท่าน |

Four things the grid is really saying:

- **`หนู` is asymmetric.** As second person, from an adult down to a child, it is
  warm and correct. As *first* person for a young woman it is what a Thai girl
  would really say — and that is the problem: it relocates the scene to Thailand.
- **`เรา → แก` is the ordinary close-friend pair**, especially among women and
  the young. It carries the intimacy `กู → มึง` is usually reached for, at none
  of the cost.
- **A name works as either person**, which is exactly what Japanese is already
  doing with `さくらちゃんは…`. It is the safest choice when the relationship is
  still being established.
- **`ค่ะ` / `ครับ` carries the deference**, so the pronoun does not have to climb
  to meet it. `ฉัน` with `ค่ะ` is polite; `หนู` on top of it is a costume.

The grid is a starting position, not a lookup table — a single scene moves along
it as the temperature changes, and that movement is usually the translation's
best tool.

## Politeness lands once per utterance

`ค่ะ` / `ครับ` at the end of every bubble in a three-bubble sentence reads as
three sentences. Put the particle on the utterance, not on the bubble — usually
the last one — and let the rest carry the register through word choice.

Give the same treatment to a pronoun split across bubbles: `私 / グラビア頑張ります!`
is `ฉัน` then `จะตั้งใจทำกราเวียค่ะ!`, not `ฉัน` then `ฉันจะ…`.

## Match the original's length, not only its sense

The bubble was drawn to hold what the Japanese said. A version carrying the
meaning in half the words leaves it looking empty, and the reader sees the gap
before they read the line.

Measure it: Thai width per Japanese character, compared across the page. Where a
line sits far below the rest it is usually rendering only the bare sense —
`〜があって` is "it so happens that", `らしい` is "I hear that", `けっこう` is
"quite, as these things go", `なんか` hedges the report it introduces. Saying
those in full is both more faithful *and* better lettering.

A line the artist drew short stays short. And where the Thai runs much longer
than the Japanese, **shorten the line rather than the lettering** — a
four-character shout cannot be lettered large under a fifteen-character
translation of it.

## Thai lengthens by opening the vowel

`ちゃ〜ん` drawn out is `จางงง`: the `ั` in `จัง` opens to `า`. Keeping the
original vowel and adding a mark after it spells a different syllable, not a
longer one.

The same instinct handles the symbols a Thai comic face does not carry — **♥ ♡
★ ☆ ♪ 「」 ○** are tone markers, so render them the way Thai marks tone: in the
wording and a drawn-out vowel, not by substituting a symbol the face happens to
have. What a particular work does about them belongs in `series/lettering.md`.

## Keep the series files current as you go

- **`series/characters.md`** — identify by costume and props first; faces and
  proportions are deformed for effect and are not evidence. Record each
  character's speech habits, because those are what make chapter 8 sound like
  chapter 1. Name a voice group (`passerby`, `commenter`) rather than inventing
  a character, and give it its own entry the moment it is named.
- **`series/glossary.md`** — every agreed transliteration and term. It doubles
  as the line breaker's custom dictionary, so anything that must not split
  across lines belongs in it: names, loanwords, coined terms.
- **`series/summary.md`** — capped length, rewritten rather than appended.
- **`series/style.md`** — the conventions this work settled on.

## Read the page before you translate any of it

Build a contact sheet of the annotated pages, two to four at a time, and settle
**reading order and speaker attribution first**. Right-to-left within a row of
panels, right-to-left and top-down within a panel. A bubble drawn across a panel
border belongs to the panel its tail comes from.

Attribution is where the guessing goes wrong, and the check is cheap: read the
sequence back as a conversation. `それに…` following a line by the same speaker
means you have the order right; following a line by the other speaker means you
do not.

## Verify the record before rendering

**Diff every recorded `source` against a fresh OCR read of its own box.** It
catches the one failure that re-reading the page will not: lines written onto
the wrong region ids. Three bubbles on one page held each other's lines and read
perfectly as a conversation; only the diff showed it.

Then check the targets for characters the face cannot draw, before a page is
rendered rather than after.

## Record uncertainty where it changes the output

`questions` is for the case where being wrong would change what gets drawn — not
for everything you were unsure of. A note that a comment is lettered level while
the original is skewed with a phone screen is worth keeping; a note that you
considered two synonyms is not.

**When you decline a region, mark it `declined` with a reason, and say what the
reader loses.** Never silently skip and never quietly soften — a page that is
missing four lines should say so in its own file.
