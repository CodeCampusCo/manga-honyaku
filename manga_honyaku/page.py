"""The page file, split in two.

`work/<page>.json` is what the detector found: boxes, classes, scores. It costs
a second to rebuild and nothing in it is worth protecting.

`work/<page>.read.json` is what the agent worked out: which region is speech and
which is a sound effect, the reading order, who is speaking to whom, and the
translation. Nothing regenerates it.

They were one file until a second `detect` run over a chapter overwrote the
reading of every page already translated, printing the same line it prints on
success. Later stages still want the two merged, which is what `load_page` does.

Region ids are positions in a sorted list of detections, so re-running detect at
a different threshold renumbers them and `B3` stops meaning the bubble the agent
read. Each reading therefore records the box it was written against, and a
reading whose box has moved is reported and dropped rather than applied to
whichever region inherited its id.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Written by the agent; everything else in the reading file is per-region.
PAGE_KEYS = ("utterances", "image_text", "questions")


def detected_path(work: Path, stem: str) -> Path:
    return work / f"{stem}.json"


def reading_path(work: Path, stem: str) -> Path:
    return work / f"{stem}.read.json"


def load_page(work: Path, stem: str) -> dict:
    """Detection output with the agent's reading merged into it."""
    data = json.loads(detected_path(work, stem).read_text())

    path = reading_path(work, stem)
    reading = json.loads(path.read_text()) if path.exists() else {}
    entries = reading.get("regions", {})

    for region in data["regions"]:
        entry = entries.get(region["id"])
        if entry is None:
            continue
        if entry.get("box") != region["box"]:
            print(
                f"{path.name}: {region['id']} was read at {entry.get('box')} but "
                f"detect now puts it at {region['box']} — reading dropped",
                file=sys.stderr,
            )
            continue
        region.update({k: v for k, v in entry.items() if k != "box"})

    for key in PAGE_KEYS:
        data[key] = reading.get(key, [])
    return data


def save_reading(work: Path, stem: str, data: dict) -> Path:
    """Write back only the agent's half of a merged page."""
    by_id = {}
    for region in data["regions"]:
        entry = {
            k: v
            for k, v in region.items()
            if k not in ("id", "box", "detector_class", "score")
        }
        if entry:
            by_id[region["id"]] = {"box": region["box"], **entry}

    reading = {"version": data.get("version", 1), "page": data["page"], "regions": by_id}
    reading.update({k: data[k] for k in PAGE_KEYS if data.get(k)})

    path = reading_path(work, stem)
    path.write_text(json.dumps(reading, ensure_ascii=False, indent=2) + "\n")
    return path
