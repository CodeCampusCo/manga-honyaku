"""Stage `prepare`: open the working file for a page.

Rewrites work/<page>.detector.json as work/<page>.agent.json — the same regions, with a
slot for everything the agent is about to work out. From here on the working
file is the agent's: it drops the regions it will not touch, adds the ones the
detector never saw, and accumulates the source and the translation.

This stage is mechanical on purpose. It carries 212 regions across a chapter
without a judgement being made about any of them, which is the part worth
automating; deciding which of them is speech is the part that is not.

OCR runs here rather than as a stage of its own. Its output is a `source` field
in the working file, and a stage that filled that field afterwards would be
writing into a file the agent had already edited — the failure the split between
the two files exists to prevent. Running it at creation means it can only ever
write into slots that are still empty.

Nothing here overwrites an existing working file. Redoing a page means redoing
the reading, so it has to be asked for.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from manga_honyaku.ocr import load_reader, read
from manga_honyaku.page import agent_path, detector_path

# Left present and empty rather than absent, so that a fresh working file shows
# what it is waiting for: what the text says, and what it is for. `clean` and
# `render` read absent and null alike.
SLOTS = {"source": None, "role": None}


def reading(detected: dict, image: Image.Image | None, reader) -> dict:
    regions = []
    for region in detected["regions"]:
        entry = {**region, **SLOTS}
        if reader is not None:
            entry["source"] = read(image, region["box"], reader)
        regions.append(entry)

    return {
        "version": detected["version"],
        "page": detected["page"],
        "img_width": detected["img_width"],
        "img_height": detected["img_height"],
        "detector": detected["detector"],
        "regions": regions,
        "questions": [],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pages", nargs="+", type=Path)
    ap.add_argument("--work", type=Path, default=Path("work"))
    ap.add_argument(
        "--force",
        action="store_true",
        help="rewrite working files that already exist, discarding the roles, "
        "reading order, speakers and translations in them",
    )
    ap.add_argument(
        "--no-ocr",
        action="store_true",
        help="leave every source empty for the agent to fill by reading the page",
    )
    args = ap.parse_args()

    reader = None if args.no_ocr else load_reader()

    for page in args.pages:
        out = agent_path(args.work, page.stem)
        if out.exists() and not args.force:
            print(f"{page.name}  {out.name} exists, skipping")
            continue

        detected = json.loads(detector_path(args.work, page.stem).read_text())
        image = None if reader is None else Image.open(page).convert("RGB")
        data = reading(detected, image, reader)
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(f"{page.name}  {out.name}  {len(data['regions'])} regions")


if __name__ == "__main__":
    main()
