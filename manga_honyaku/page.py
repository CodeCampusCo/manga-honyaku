"""Where a page's two files live.

The pipeline runs one way: raw -> .json -> .read.json -> clean -> render. Each
stage reads the artifact before it and writes the one after, and nothing reads
backwards.

`<page>.json` is what the detector found. It is derived from raw and can be
rebuilt in under a second, so any stage may overwrite it.

`<page>.read.json` is the working file: the detector's regions rewritten, with
what will not be touched dropped, what the detector missed added, and the source
and the translation accumulated in it. Nothing rebuilds it but reading the page
again, so no stage overwrites it without being told to.

To change detection after a page has been read, start again from raw — there is
no merge, and a half-updated working file would be worse than either.
"""

from __future__ import annotations

from pathlib import Path


def detected_path(work: Path, stem: str) -> Path:
    return work / f"{stem}.json"


def reading_path(work: Path, stem: str) -> Path:
    return work / f"{stem}.read.json"
