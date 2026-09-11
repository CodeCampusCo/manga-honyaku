"""Tool `tally`: the counts a chapter has to be read back against.

Not a stage — it reads the working files and prints.

    uv run python -m manga_honyaku.tally series/<work>
    uv run python -m manga_honyaku.tally series/<work> --lines tamagawa

The `japanese-to-thai-manga` skill asks for one pass after a chapter is
rendered, and its first question is the one nobody can answer from memory:
**how many of a character's lines took the polite particle, out of how many, and
has that moved since last chapter.** A count taken against one chapter answers
nothing — the question is always whether it moved — so this reads every chapter
of the work and prints them as rows, which is the shape the answer has.

Two columns, not one, because they are different facts:

- **`ですます`** is what the *original* did. It is the character's register and
  the thing `characters.md` is tracking.
- **`ค่ะ/ครับ`** is what the *translation* did. It sits *above* the Japanese
  column and is expected to: `はい` answering a question is itself `ค่ะ`, and a
  name called out to someone senior takes one, and neither leaves a `ですます`
  behind on the Japanese side. **What is worth watching is the gap, and only
  whether it widens** — a chapter where the Thai column pulls away from a steady
  Japanese one is a chapter where the particle is being written per bubble
  rather than per utterance, which is the error the skill names and which no
  other check looks for.

**Both columns are matched on substrings and are therefore approximate.** They
are here to be compared across chapters, where a consistent bias cancels; a
single number off this tool is not evidence of anything. `--lines` prints the
lines behind a speaker's counts so a ratio that moved can be checked rather than
believed.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from manga_honyaku.page import Series

# The **stems of the two polite auxiliaries**, not a list of their endings.
# Written as endings this misses a whole row of the conjugation and looks like it
# works: `ます` and `です` alone let `ましょうか`, `でしょう` and `でした` through,
# which is the し-row of both verbs, and the ratio comes out a chapter too low
# without anything looking wrong. `まし` covers ました・ましょう・まして and
# `でし` covers でした・でしょう, so the table is closed rather than sampled.
#
# `ござい` needs no entry: ございます ends in ます and ございません in ませ. `ます`
# also catches `ますた`, board slang misspelling the polite form on purpose, and
# counting that as polite is right.
POLITE_JP = ("です", "でし", "ます", "ませ", "まし", "ください")

# What a character puts inside quotation marks is not their register — most of
# all in this work, whose running joke is one man repeating a polite question he
# never manages to ask. Stripped before matching, so 「玉川さんAV出てました?」って
# counts as the plain `って…` it actually is.
QUOTED = re.compile(r"[「『“][^」』”]*[」』”]?")

# The Thai politeness slot. The stretched forms are here because this artist
# holds vowels — `ค่าาา` is `ค่ะ` drawn out, and dropping it undercounts exactly
# the lines that are most obviously polite.
POLITE_TH = ("ค่ะ", "คะ", "ครับ", "คับ", "ค่า", "คร้าบ")


def polite_jp(source: str) -> bool:
    said = QUOTED.sub("", source or "")
    return any(mark in said for mark in POLITE_JP)


def polite_th(target: str) -> bool:
    return any(mark in (target or "") for mark in POLITE_TH)


def chapter_of(page: str) -> str:
    """The chapter a page id belongs to, or `—` where a work is flat."""
    head, sep, _ = page.rpartition("/")
    return head if sep else "—"


def gather(work: Series) -> dict:
    """Every lettered region of the work, by chapter and by speaker."""
    found: dict = {}
    for page in work.ids([]):
        data = json.loads(work.agent(page).read_text())
        book = found.setdefault(
            chapter_of(page),
            {"roles": Counter(), "status": Counter(), "who": {}, "vocab": Counter()},
        )
        for region in data["regions"]:
            book["status"][region.get("status")] += 1
            for field in ("role", "speaker", "weight"):
                if region.get(field):
                    book["vocab"][(field, region[field])] += 1
            if region.get("status") != "ok":
                continue
            book["roles"][region.get("role")] += 1
            speaker = region.get("speaker")
            if not speaker:
                continue
            rows = book["who"].setdefault(speaker, [])
            rows.append((page, region))
    return found


def counts(rows: list[tuple], role: str) -> tuple[int, int, int]:
    """Lines of this role, and how many are polite on each side."""
    picked = [r for _, r in rows if r.get("role") == role]
    return (
        len(picked),
        sum(polite_jp(r.get("source")) for r in picked),
        sum(polite_th(r.get("target")) for r in picked),
    )


def share(part: int, whole: int) -> str:
    return f"{part:>3} ({part / whole:>3.0%})" if whole else "  —      "


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", type=Path, help="a work's directory under series/")
    ap.add_argument("--lines", metavar="SPEAKER", help="print this speaker's lines")
    args = ap.parse_args()

    work = Series(args.series)
    found = gather(work)
    books = sorted(found)

    if args.lines:
        for book in books:
            for page, region in found[book]["who"].get(args.lines, []):
                marks = "".join(
                    (
                        "J" if polite_jp(region.get("source")) else "·",
                        "T" if polite_th(region.get("target")) else "·",
                    )
                )
                print(f"{page} {region['id']:<4} {region.get('role'):<9} {marks}  "
                      f"{region.get('source')}")
                print(f"{'':>22}   → {region.get('target')}")
        return

    # `role` and `speaker` are free strings that nothing validates. `narration`
    # for `caption` letters the same and reads the same; `image-text` for
    # `image_text` is erased and drawn over when it should have been left alone,
    # and no stage says a word. The only defence is being able to see, before the
    # first batch, which values the work already uses — and a count of 1 next to
    # a value is either a character who has just arrived or a typo.
    print("values this work uses — nothing validates these, so read them")
    vocab = Counter()
    for book in found.values():
        vocab += book["vocab"]
    for field in ("role", "speaker", "weight"):
        used = sorted(
            ((v, n) for (f, v), n in vocab.items() if f == field), key=lambda kv: -kv[1]
        )
        if used:
            print(f"  {field:<9}" + "  ".join(f"{v} {n}" for v, n in used))

    # A role every other chapter uses heavily and this one does not use at all
    # is not a style: it is a chapter whose regions were tagged wrong. Chapter 4
    # of the first work here carried 129 `dialogue` and no `caption`, so a man
    # whose interior voice is most of the book was recorded as having said all of
    # it out loud — and the count went from here into `characters.md`, beside
    # three chapters that had counted a different thing.
    for role in sorted({r for b in found.values() for r in b["roles"]}, key=str):
        elsewhere = [b for k, b in found.items() if b["roles"][role]]
        for book in books:
            if found[book]["roles"][role] or len(elsewhere) < 2:
                continue
            usual = sorted(b["roles"][role] for b in elsewhere)[len(elsewhere) // 2]
            print(f"  ** chapter {book} has no `{role}` at all, where the others "
                  f"average about {usual}. Check how its regions were tagged.")

    print("\nregions lettered, by role")
    roles = sorted({r for b in found.values() for r in b["roles"]}, key=str)
    print("  " + "chapter".ljust(9) + "".join(str(r).rjust(12) for r in roles))
    for book in books:
        row = found[book]["roles"]
        print("  " + book.ljust(9) + "".join(str(row[r]).rjust(12) for r in roles))

    print("\ndeclined, of every region on the page")
    for book in books:
        row = found[book]["status"]
        print(f"  {book.ljust(9)}{row['declined']:>5} of {sum(row.values()):>5}")

    speakers = sorted({s for b in found.values() for s in b["who"]})
    for speaker in speakers:
        print(f"\n{speaker}")
        print("  " + "chapter".ljust(9) + "spoken".rjust(7) + "ですます".rjust(13)
              + "ค่ะ/ครับ".rjust(15) + "thought".rjust(10))
        for book in books:
            rows = found[book]["who"].get(speaker, [])
            spoken, jp, th = counts(rows, "dialogue")
            thought, _, _ = counts(rows, "caption")
            print("  " + book.ljust(9) + f"{spoken:>7}" + share(jp, spoken).rjust(13)
                  + share(th, spoken).rjust(15) + f"{thought:>10}")


if __name__ == "__main__":
    main()
