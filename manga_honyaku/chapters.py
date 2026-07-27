"""Print what the reading found on particular pages.

`chapters/<n>.md` is written a page at a time and read a chapter at a time, and
for translating a chapter that is right: the whole file costs less than looking
at the pages it describes. Asking about three pages is where it stops being
right, and the file that holds them is not always the one you would guess.

So: page ids, or a range, and this finds them wherever they live. The file's
opening rule comes with them — an entry lifted out on its own loses the sentence
that says it is not a substitute for the page, and that sentence is the whole
reason the file is trustworthy.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def entries(directory: Path) -> tuple[str, dict[str, str]]:
    """The rule at the top of the files, and every entry by page id."""
    rule, found = [], {}
    for path in sorted(directory.glob("*.md")):
        page, lines = None, []
        for line in path.read_text().splitlines():
            if line.startswith("## "):
                if page:
                    found[page] = "\n".join(lines).rstrip()
                page, lines = line[3:].strip(), [line]
            elif page:
                lines.append(line)
            elif rule and not rule[-1]:
                pass                          # the rule ended at its blank line
            elif rule or line.startswith("What follows"):
                rule.append(line)
        if page:
            found[page] = "\n".join(lines).rstrip()
    return "\n".join(rule).strip(), found


def chosen(names: list[str], found: dict[str, str]) -> list[str]:
    if not names:
        return list(found)
    picked = []
    for name in names:
        first, sep, last = name.partition("-")
        if sep:
            picked += [p for p in found if first <= p <= last]
        elif name in found:
            picked.append(name)
        else:
            raise SystemExit(f"nothing written about {name}")
    return picked


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", type=Path, help="a work's directory under series/")
    ap.add_argument("pages", nargs="*", help="page ids, or FIRST-LAST; none for all")
    args = ap.parse_args()

    rule, found = entries(args.series / "chapters")
    if not found:
        raise SystemExit(f"no chapter files under {args.series / 'chapters'}")

    wanted = chosen(args.pages, found)
    print(rule + "\n")
    for page in wanted:
        print(found[page] + "\n")


if __name__ == "__main__":
    main()
