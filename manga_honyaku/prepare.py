"""Stage `prepare`: open the working file for a page.

Rewrites work/<page>.json as work/<page>.read.json — the same regions, with a
slot for everything the agent is about to work out. From here on the working
file is the agent's: it drops the regions it will not touch, adds the ones the
detector never saw, and accumulates the source and the translation.

This stage is mechanical on purpose. It carries 212 regions across a chapter
without a judgement being made about any of them, which is the part worth
automating; deciding which of them is speech is the part that is not.

Nothing here overwrites an existing working file. Redoing a page means redoing
the reading, so it has to be asked for.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from manga_honyaku.page import detected_path, reading_path

# Left present and empty rather than absent, so that a fresh working file shows
# what it is waiting for. `clean` and `render` read absent and null alike.
SLOTS = {"source": None, "class": None}


def reading(detected: dict) -> dict:
    return {
        "version": detected["version"],
        "page": detected["page"],
        "img_width": detected["img_width"],
        "img_height": detected["img_height"],
        "detector": detected["detector"],
        "regions": [{**region, **SLOTS} for region in detected["regions"]],
        "utterances": [],
        "questions": [],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pages", nargs="+", type=Path)
    ap.add_argument("--work", type=Path, default=Path("work"))
    ap.add_argument(
        "--force",
        action="store_true",
        help="rewrite working files that already exist, discarding the classes, "
        "reading order, speakers and translations in them",
    )
    args = ap.parse_args()

    for page in args.pages:
        out = reading_path(args.work, page.stem)
        if out.exists() and not args.force:
            print(f"{page.name}  {out.name} exists, skipping")
            continue

        detected = json.loads(detected_path(args.work, page.stem).read_text())
        data = reading(detected)
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(f"{page.name}  {out.name}  {len(data['regions'])} regions")


if __name__ == "__main__":
    main()
