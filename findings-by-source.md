# Where a chapter's findings come from

**If you are here to translate a chapter, this file is not for you** — nothing in
it is method. It is a tally kept while deciding where to spend effort on the
tool, and it lives beside [`DEVELOPING.md`](DEVELOPING.md) for that reason.

Artwork, lettering size, which regions get translated and text placement reached
an accepted level at chapter 10, and effort moved to **wording**. The question
this answers is where wording defects are actually caught, so that the next
investment goes where they are caught rather than where it is easy to build.

## How a row is classified

**Class** — what was wrong:

| | |
| --- | --- |
| `wording` | the Thai says the wrong thing, or says it in the wrong voice |
| `lettering` | size, line break, or where the Thai sits |
| `artwork` | erasure, a box, or Japanese left standing |
| `record` | a note, glossary row or handoff line that was wrong |

**Source** — what caught it: a review pass (`proofread`, `page-look`), a program
(`audit`, `check`, `--todo`), a question asked of the file (`--repeats`, `fit`,
`--order`), or `looking` — the translator's own eye on a page, with nothing
pointing them at it.

Counts come from what each chapter's session reported, which was not written for
this, so treat small differences as noise and the shape as the finding.

## The tally

| chapter | source | class | what |
| --- | --- | --- | --- |
| 9 | proofread | wording | `お疲れ` at clock-off rendered as *brace yourself* — inverts a farewell |
| 9 | proofread | wording | `仲良くやっていきましょう` as an invitation to be personally close, from a character the notes call terrified of seeming lecherous |
| 9 | proofread | lettering | `歓迎会を台無しにして` breaking so the first line reads *workplace* |
| 9 | proofread | wording | five further findings, applied, not itemised in the report |
| 9 | page-look | lettering | a caption at two-thirds the size of its neighbour an inch away |
| 9 | page-look | lettering | one further real finding |
| 9 | --repeats | wording | `09/08` = `06/11` word for word, before a page was opened — prevented a defect rather than caught one |
| 9 | --order | artwork | 2 disputes, translator wrong both times |
| 9 | fit | lettering | three wordings overturned, twice against a note that had eyeballed the box |
| 10 | proofread | wording | `かもしれない` dropped — he is floating the theory the back half takes away |
| 10 | proofread | wording | two speaker errors |
| 10 | proofread | record | a glossary row locking a counter the majority of pages do not use |
| 10 | proofread | wording | three further findings, applied, not itemised |
| 10 | page-look | lettering | a `คO|ย!` break `fit` had printed and the translator read past |
| 10 | page-look | lettering | `ผู้ จัดการ` split, which `fit` had endorsed and the page overruled |
| 10 | page-look | artwork | a plate cutting a poster in half |
| 10 | looking | artwork | a box clipping its own last glyph, leaving a kana on the page |
| 10 | looking | artwork | a caption plate drawn across a balloon |
| 10 | looking | artwork | a widened plate cutting a background figure |
| 10 | audit | artwork | 3 findings, the known residue class |

## What it says so far

Two chapters is not enough to act on, and this is what to weigh at the next one.

- **Every `wording` finding so far came from `proofread-against-source`**, except
  one prevented by `--repeats` before a page was read. No program has ever caught
  one, and nothing suggests one could.
- **`page-look` catches `lettering`, and it caught the one case where the
  arithmetic was wrong about a wording** — a split `fit` endorsed that the page
  overruled. It is the only thing that compares a region to its neighbours.
- **`looking` catches `artwork` and only `artwork`**, and all three instances are
  the same shape: a region's box against what is next to it. `--todo` now reports
  the collision case, so that third should shrink.
- So if the open front is wording, the next investment is in
  `proofread-against-source` and in what reaches it — the accuracy of `source`,
  and the notes it reasons from — rather than in another check.
