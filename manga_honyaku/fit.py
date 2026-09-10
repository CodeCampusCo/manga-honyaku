"""Tool `fit`: what size a candidate line would be lettered at, before it is set.

Not a stage — it draws nothing and writes nothing, so it is safe to run on a page
mid-edit.

Each line reports the box, the size the Japanese was lettered at, the size the
Thai would be drawn at, how much of the box that fills, and the lines the breaker
produced. `--replace` and `--word` report instead every region a change touches,
worst first, and end with the pages whose rendering would differ.

When to reach for which, and what the numbers mean, is
`.claude/skills/running-the-manga-pipeline/`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pythainlp.corpus.common import thai_words
from pythainlp.util import Trie

from manga_honyaku.page import Series
from manga_honyaku.render import FONT, LINE_SPACING, lay_out, lexicon, settings

# Below the floor nothing is readable, and the tool has to agree with `render`
# about that or it answers a question nobody asked.
SMALLEST = 7


def measure(region: dict, text: str, font: str, custom, spacing: float):
    """The size, the fill and the lines, or None where nothing fits."""
    x1, y1, x2, y2 = region["box"]
    width, height = x2 - x1, y2 - y1
    laid = lay_out(
        text, (x1, y1, width, height), font, SMALLEST, max(SMALLEST, int(height)),
        custom, spacing,
    )
    if laid is None:
        return None
    font_used, lines, line_height = laid
    return font_used.size, line_height * len(lines) / height, lines


def terms(series: Path) -> set[str]:
    """What `words.txt` lists, as a set. Absent or empty is an empty set."""
    path = series / "words.txt"
    if not path.exists():
        return set()
    return {word.strip() for word in path.read_text().splitlines() if word.strip()}


def trie(words: set[str]):
    """A segmenter dictionary for a `words.txt` that is not on disk yet."""
    return Trie(set(thai_words()) | words) if words else None


def sweep(work: Series, word: str, swap, after_terms: set[str], font, spacing) -> None:
    """Every region the change touches, what it costs, and what to re-render."""
    before = trie(terms(work.root))
    after = trie(after_terms)
    rows, pages = [], []

    for page in work.ids([]):
        data = json.loads(work.agent(page).read_text())
        for region in data["regions"]:
            text = region.get("target") or ""
            if word not in text:
                continue
            was = measure(region, text, font, before, spacing)
            now = measure(region, swap(text), font, after, spacing)
            rows.append((page, region, text, was, now))
            if (was and was[0]) != (now and now[0]):
                pages.append(page)

    if not rows:
        print(f"no target holds {word!r} — nothing to re-render")
        return

    def step(row) -> int:
        _, _, _, was, now = row
        if was is None or now is None:
            return -99
        return now[0] - was[0]

    for page, region, text, was, now in sorted(rows, key=step):
        x1, y1, x2, y2 = region["box"]
        shape = f"{x2 - x1:.0f}x{y2 - y1:.0f}"
        head = f"{page} {region['id']:>4}  {shape}  jp={region.get('size')}"
        if was is None or now is None:
            gone = "does not fit" if now is None else "fits again"
            print(f"{head}  {gone}  {text}")
            continue
        move = now[0] - was[0]
        arrow = f"{was[0]} → {now[0]}" if move else f"{now[0]} unchanged"
        print(f"{head}  {arrow:>16}  fills {now[1]:.0%}  {now[2]}")

    touched = sorted(set(pages))
    held = f"{len(rows)} region{' holds' if len(rows) == 1 else 's hold'} it"
    moved = f"{len(touched)} page{'' if len(touched) == 1 else 's'} would render differently"
    print(f"\n{held}; {moved}")
    if touched:
        print("re-render: " + " ".join(touched))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", type=Path, help="a work's directory under series/")
    ap.add_argument("page", nargs="?", help="one page id")
    ap.add_argument("--replace", nargs=2, metavar=("OLD", "NEW"), help="price a wording change")
    ap.add_argument("--word", help="a term in words.txt to price adding or dropping")
    ap.add_argument("--add", action="store_true", help="with --word: price listing it")
    ap.add_argument("--drop", action="store_true", help="with --word: price unlisting it")
    ap.add_argument(
        "pairs",
        nargs="*",
        metavar="ID TEXT",
        help="region id and candidate line, repeated; none for what is already set",
    )
    args = ap.parse_args()

    if len(args.pairs) % 2:
        raise SystemExit("pairs are a region id and a line: F1 'เธอนำแสง'")

    work = Series(args.series)
    values = settings(args.series)
    font = values.get("font") or FONT
    spacing = values.get("line_spacing", LINE_SPACING)
    custom = lexicon(args.series)

    if args.replace or args.word:
        listed = terms(args.series)
        if args.replace:
            old, new = args.replace
            after = (listed - {old}) | {new} if old in listed else listed
            sweep(work, old, lambda t: t.replace(old, new), after, font, spacing)
        else:
            if args.add == args.drop:
                raise SystemExit("--word takes one of --add or --drop")
            after = listed | {args.word} if args.add else listed - {args.word}
            sweep(work, args.word, lambda t: t, after, font, spacing)
        return

    if not args.page:
        raise SystemExit("name a page, or price a change with --replace or --word")

    data = json.loads(work.agent(args.page).read_text())
    regions = {r["id"]: r for r in data["regions"]}

    pairs = list(zip(args.pairs[::2], args.pairs[1::2]))
    if not pairs:
        pairs = [(r["id"], r["target"]) for r in data["regions"] if r.get("target")]

    for rid, text in pairs:
        region = regions.get(rid)
        if region is None:
            raise SystemExit(f"{args.page} has no region {rid}")
        x1, y1, x2, y2 = region["box"]
        shape = f"{x2 - x1:.0f}x{y2 - y1:.0f}"
        got = measure(region, text, font, custom, spacing)
        if got is None:
            print(f"{rid:>4}  {shape}  jp={region.get('size')}  does not fit  {text}")
            continue
        size, fill, lines = got
        print(
            f"{rid:>4}  {shape}  jp={region.get('size')}  thai={size}"
            f"  fills {fill:.0%}  {lines}"
        )


if __name__ == "__main__":
    main()
