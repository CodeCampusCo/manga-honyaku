"""Tool `regions`: what the working file holds, and where a line was set before.

Not a stage — it reads `pages/<id>.agent.json` and prints, so it is safe to run
on a page that is being edited.

    uv run python -m manga_honyaku.regions series/<work> 03        # a chapter
    uv run python -m manga_honyaku.regions series/<work> 03/05     # one page
    uv run python -m manga_honyaku.regions series/<work> --match 聞け
    uv run python -m manga_honyaku.regions series/<work> 03 --overlaps
    uv run python -m manga_honyaku.regions series/<work> 03 --todo
    uv run python -m manga_honyaku.regions series/<work> 03 --repeats
    uv run python -m manga_honyaku.regions series/<work> 03/05 --order

The default view is the one a chapter cannot be read without: every region with
its box, the size the Japanese was lettered at, the `room` that follows from it,
and the reading beside them. **Nothing else prints it.** `fit` speaks only about
regions that already carry a target, `chapters` reads the notes written *about*
a page rather than the file being worked on, and `check` reports only the lines
that moved. Two translators on two different chapters each wrote the same
throwaway script for this before opening a single page, which is what a missing
tool looks like.

`--match` answers the question that arrives mid-sentence: *what did this work do
with this Japanese before?* `glossary.md` holds the terms somebody decided to
write down; the working files hold every line that was ever set, and searching
their `source`, `target` and `reason` is the sweep the `japanese-to-thai-manga`
skill describes as grep-shaped. It searches the whole work, not the pages named.

`--repeats` is what has to be settled before a chapter is split between more than
one translator, and it can be asked **before anybody has read a page** — the OCR
is already in the working files the moment `prepare` has run. A line the chapter
says twice has to come out the same twice, and a line an earlier chapter already
said has already been answered. Run on chapter 2 of the first work here it
returned `私はいつも穿いてますよ` and `Tバック` at three pages each, which is that
chapter's entire hook, from no reading at all.

The output comes in two parts, because they are read at two different moments.
**What an earlier chapter already answered** is a list to read *before* the first
page of a new one — it is the work saying *this is decided, do not think about it
again*, and the translator who asked for this said the confirmations saved more
of their time than the disagreements did. **What these pages say twice and the
work has not answered** is the list to settle once and apply everywhere, and it
is what has to be pinned before a chapter is split between two translators.

Two boxes standing on one piece of lettering count as one occurrence. Counted as
two, every duplicate the detector leaves behind arrives here as a line the
chapter says twice, which is noise and is also false — that is `--overlaps`'s
question, not this one.

**What it compares is OCR, not Japanese.** `source` is what the reader made of a
box, so two regions the artist drew identically can differ in the file, and two
it drew differently can match. A `DRIFTED` line is therefore *a place to open the
scan*, never a translation error on its own: one such pair here was `失敗!!` and
`失敗!!!`, reported upward as a mistranslation and then found on the page to be
the original counting 1→2→3→4, with the Thai right all along and the reading
wrong. Open the page before believing the tool.

It finds strings, so it finds neither a pun nor a paraphrase: `ティーバッグ` and
`Tバック` are the joke of that same chapter and are two different strings. What it
is for is the repeat that must not drift, not the reading.

`--overlaps` is a worklist, not a check: see `prepare.overlapping`.

`--order` proposes a reading order from the boxes and says nothing about whether
the file agrees; `--todo` says where it does not, pair by pair. Which of the two
to reach for depends on whether the page has been numbered yet, and neither is
an authority — see `order.py` for what the proposal is and is not.

`--todo` is `audit`'s bookkeeping asked early, plus the two checks the skill asks
for *before* a page is rendered rather than after. One is the characters this face
cannot draw: `render` warns about those too, and asking the font is the only way
to know — the list in a work's `style.md` was written by hand and will drift from
the font it describes.

The other is the boxes the detector nearly drew and nothing has covered since.
**It is the only report in the pipeline that can see text which is not in the
working file**, because every other one walks the regions and a sound that was
never boxed has no region to walk. Most of them are nothing. Look at each once —
but only a region over one takes it off the list, so a chapter answered by
judgement alone hands the next reader the same lines.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from PIL import ImageFont

from manga_honyaku.audit import record, spacing, spelling
from manga_honyaku.clean import KEEP
from manga_honyaku.detect import ALREADY, covered
from manga_honyaku.order import disagreements, propose
from manga_honyaku.check import settle, says_something, unpaused
from manga_honyaku.ocr import SURE
from manga_honyaku.page import Series
from manga_honyaku.prepare import colliding, overlapping, uncovered
from manga_honyaku.render import FONT, LINE_SPACING, lexicon, missing_glyphs, settings


def widest(region: dict, spacing: float) -> int | None:
    """The longest unbreakable run the box holds on one line, in characters.

    The size is set by the longest token, so a wording proposed against `room`
    alone is a guess. `room` was already this number times the lines.
    """
    size = region.get("size")
    room = region.get("room")
    if not size or not room:
        return None
    _, y1, _, y2 = region["box"]
    lines = int((y2 - y1) // (size * spacing))
    return round(room / lines) if lines else None


def summarise(region: dict, spacing: float = LINE_SPACING) -> str:
    """One region as one line: where it is, how big, and what it is for."""
    x1, y1, x2, y2 = region["box"]
    who = "/".join(
        part for part in (region.get("role"), region.get("speaker")) if part
    )
    run = widest(region, spacing)
    score = region.get("source_score")
    fields = [
        f"{region.get('order') or '-':>3}",
        f"{region['id']:<4}",
        f"{region['placement']:<6}",
        f"{x2 - x1:.0f}x{y2 - y1:.0f}".rjust(9),
        f"size={region.get('size')}".ljust(9),
        f"room={region['room']}".ljust(9) if region.get("room") else " " * 9,
        f"line={run}".ljust(8) if run else " " * 8,
        (who or "—").ljust(22),
        (region.get("status") or "—").ljust(9),
    ]
    doubt = "? " if score is not None and score < SURE else ""
    return "  ".join(fields).rstrip() + "  " + doubt + (region.get("source") or "")


def unclaimed(work: Series, page: str, data: dict) -> list[dict]:
    """The detector's near misses that no region in the working file covers.

    Re-checked rather than taken as written: one is answered by adding a region
    over it, and a worklist that does not clear stops being read. A page prepared
    before `prepare` copied them still has them on the detector's file, unread.
    """
    candidates = data.get("candidates")
    if candidates is None:
        found = work.derived(page, "detector.json")
        candidates = (
            json.loads(found.read_text()).get("candidates", [])
            if found.exists() else []
        )
    return [
        candidate
        for candidate in candidates
        if covered(candidate["box"], data["regions"]) <= ALREADY
    ]


def hits(region: dict, needle: str) -> list[str]:
    """Which of a region's written fields contain this text."""
    return [
        name
        for name in ("source", "target", "reason")
        if needle in (region.get(name) or "")
    ]


def show(work: Series, ids: list[str], spacing: float = LINE_SPACING) -> None:
    for page in ids:
        data = json.loads(work.agent(page).read_text())
        print(f"{page}  {data['img_width']}x{data['img_height']}"
              f"  {len(data['regions'])} regions")
        for region in sorted(
            data["regions"], key=lambda r: (r.get("order") is None, r.get("order") or 0)
        ):
            print("  " + summarise(region, spacing))
            if region.get("target"):
                print(f"       → {region['target']}")
            if region.get("reason"):
                print(f"       ✗ {region['reason']}")


def repeated(work: Series, ids: list[str]) -> list[tuple]:
    """Lines the chosen pages say more than once, and where else the work says them.

    Normalised the way `check` normalises, so that a pause written three ways is
    one line and a reading that could not identify anything is not counted.
    """
    here = set(ids)
    chosen, everywhere = defaultdict(list), defaultdict(list)
    for page in work.ids([]):
        regions = json.loads(work.agent(page).read_text())["regions"]
        # Two boxes on one piece of lettering are one occurrence of it, not two.
        # Counted as two, every duplicate the detector left behind arrives here
        # as a line the chapter says twice, which is both noise and false.
        twice = {b["id"] for _, b, _ in overlapping(regions)}
        for region in regions:
            said = settle(region.get("source"))
            if region["id"] in twice or not says_something(said):
                continue
            everywhere[said].append((page, region))
            if page in here:
                chosen[said].append((page, region))
    return sorted(
        (
            (said, rows, [e for e in everywhere[said] if e not in rows])
            for said, rows in chosen.items()
            if len(rows) > 1 or len(everywhere[said]) > 1
        ),
        key=lambda group: -len(group[1]) - len(group[2]),
    )


def drifted(rows: list[tuple]) -> bool:
    """Whether one Japanese line has come out as more than one Thai one.

    The failure this is for cannot be seen from inside a page: a line the chapter
    says three times, translated three times, in three sittings or by three
    translators. Each one reads correctly where it sits. Only the set disagrees,
    and a work whose joke is that two characters said the identical sentence
    loses the joke without anything else reporting it.

    A region that was declined has no target and is not a disagreement.

    Pauses are settled first. `เอ่อ…` against `เอ่อ……` is one line written twice,
    and flagged as drift it costs a re-read and teaches the reader to skim the
    flag — which is the expensive failure, not the false positive.
    """
    said = {
        unpaused(r["target"])
        for _, r in rows
        if r.get("status") == "ok" and r.get("target")
    }
    return len(said) > 1


def search(work: Series, needle: str) -> None:
    found = 0
    for page in work.ids([]):
        data = json.loads(work.agent(page).read_text())
        for region in data["regions"]:
            where = hits(region, needle)
            if not where:
                continue
            found += 1
            print(f"{page} {region['id']}  {region.get('status')}  [{','.join(where)}]")
            for name in ("source", "target", "reason"):
                if region.get(name):
                    print(f"    {name:<7} {region[name]}")
    print(f"\n{found} region(s) mention {needle!r}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", type=Path, help="a work's directory under series/")
    ap.add_argument("pages", nargs="*", help="page ids; a directory; none for all")
    ap.add_argument("--match", help="print every region of the work mentioning this")
    ap.add_argument(
        "--overlaps", action="store_true", help="region pairs whose boxes collide"
    )
    ap.add_argument(
        "--todo", action="store_true", help="regions the working file leaves unfinished"
    )
    ap.add_argument(
        "--order",
        action="store_true",
        help="a reading order proposed from the boxes, for you to correct",
    )
    ap.add_argument(
        "--repeats",
        action="store_true",
        help="lines these pages say twice, and what the rest of the work said",
    )
    args = ap.parse_args()

    work = Series(args.series)
    if args.match:
        search(work, args.match)
        return

    ids = work.ids(args.pages)
    if args.order:
        for page in ids:
            data = json.loads(work.agent(page).read_text())
            regions = {r["id"]: r for r in data["regions"]}
            print(f"{page}  {len(data['regions'])} regions")
            for at, rid in enumerate(propose(data["regions"]), 1):
                region = regions[rid]
                was = region.get("order")
                moved = "" if was == at else f"  (file says {was or '-'})"
                print(f"  {at:>3}  {rid:<4}{moved}  {(region.get('source') or '')[:44]}")
        return

    probe = ImageFont.truetype(
        settings(args.series).get("font") or FONT, 40
    ) if args.todo else None
    custom = lexicon(args.series) if args.todo else None
    if args.repeats:
        groups = repeated(work, ids)
        for heading, picked in (
            ("already answered elsewhere in the work — say it the same way",
             [g for g in groups if g[2]]),
            ("said more than once here, and nowhere else yet — settle it once",
             [g for g in groups if not g[2]]),
        ):
            print(f"\n{heading}\n")
            for said, rows, elsewhere in picked:
                flag = (
                    "  ← DRIFTED, these do not say the same thing"
                    if drifted(rows + elsewhere) else ""
                )
                print(f"  {said}{flag}")
                for page, region in rows + elsewhere:
                    answer = region.get("target") or f"({region.get('status') or 'not set'})"
                    print(f"      {page} {region['id']:<4} → {answer}")
            if not picked:
                print("  nothing")
        return

    if args.overlaps or args.todo:
        for page in ids:
            data = json.loads(work.agent(page).read_text())
            said = []
            if args.overlaps:
                said += [
                    f"{a['id']} and {b['id']} cover the same text"
                    f" ({cover:.0%}) — keep one, decline the other"
                    for a, b, cover in overlapping(data["regions"])
                ]
            if args.todo:
                said += record(data) + spelling(data) + spacing(data, custom)
                said += [
                    f"nothing covers {[int(v) for v in c['box']]}, which the "
                    f"detector nearly drew" + (
                        f" and the reader makes {c['source']!r} of"
                        if c.get("source") else ""
                    ) + " — look at it once"
                    for c in unclaimed(work, page, data)
                ]
                said += [
                    f"{big['id']} is declined and holds "
                    f"{', '.join(r['id'] for r in inside)}, which cover "
                    f"{share:.0%} of it — is the rest meant to stay Japanese?"
                    for big, inside, share in uncovered(data["regions"])
                    if share < 0.85
                ]
                # Not reported twice: `--overlaps` owns the pair, and a list
                # repeating another one is where skipping is learned.
                twinned = {
                    frozenset((a["id"], b["id"]))
                    for a, b, _ in overlapping(data["regions"])
                }
                said += [
                    f"{a['id']} and {b['id']} will be drawn over each other — "
                    f"{share:.0%} of a box is shared, and both hold a line"
                    for a, b, share in colliding(
                        data["regions"],
                        lambda r: r.get("role") and r["role"] not in KEEP
                        and r.get("status") == "ok",
                    )
                ]
                said += [
                    f"{a} is read before {b} and the boxes say the other way "
                    f"round — " + (
                        "a line separates them either way, so the boxes cannot "
                        "say which; the border in the artwork decides"
                        if both else
                        "the boxes separate them one way only, so this is a "
                        "real disagreement unless a balloon here hangs across a "
                        "panel border"
                    )
                    for a, b, both in disagreements(data["regions"])
                    if frozenset((a, b)) not in twinned
                ]
                absent = missing_glyphs(
                    probe, "".join(r.get("target") or "" for r in data["regions"])
                )
                if absent:
                    said.append(f"font has no glyph for {''.join(sorted(absent))}")
            for line in said:
                print(f"{page}  {line}")
        return

    show(work, ids, settings(args.series).get("line_spacing", LINE_SPACING))


if __name__ == "__main__":
    main()
