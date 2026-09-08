"""A series on disk, and where each page's files live in it.

    series/<work>/
        raw.txt         one line: where the scans are
        lettering.json  words.txt                            read by code
        characters.md   glossary.md  summary.md              read by the translator

        pages/          <id>.agent.json — the translation
        build/          <id>.detector.json .boxes.png .clean.png .masks.png
        out/            <id>.png

A page is identified by its path under the raw directory, without the suffix:
`X0006`, or `01/ch02/003` where a work ships as volume and chapter directories.
`pages/`, `build/` and `out/` mirror whatever shape raw has, so a flat work and a
chaptered one are not two cases anything has to handle.

`pages/` is kept apart from `build/` because everything in `build/` rebuilds from
raw in seconds and nothing in `pages/` rebuilds at all — it is hours of reading
the page.

The pipeline runs one way:

    raw -> build/<id>.detector.json -> pages/<id>.agent.json -> build -> out

Each stage reads the artifact before it and writes the one after, and nothing
reads backwards. The detector's file is derived, so any stage may overwrite it;
the working file is not, so no stage overwrites it without being told to. To
change detection after a page has been read, start again from raw — there is no
merge, and a half-updated working file would be worse than either.
"""

from __future__ import annotations

from pathlib import Path

SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")
AGENT = ".agent.json"


class Series:
    """One work's directories, and the pages in it."""

    def __init__(self, root: Path):
        self.root = root
        self.pages = root / "pages"
        self.build = root / "build"
        self.out = root / "out"

    @property
    def raw(self) -> Path:
        """Where the scans are: `raw.txt` says, or `raw/` beside the rest."""
        pointer = self.root / "raw.txt"
        if pointer.exists():
            return Path(pointer.read_text().strip()).expanduser()
        return self.root / "raw"

    def scan(self, page: str) -> Path:
        for suffix in SUFFIXES:
            found = self.raw / f"{page}{suffix}"
            if found.exists():
                return found
        raise SystemExit(f"no scan for {page} under {self.raw}")

    def agent(self, page: str) -> Path:
        return self._at(self.pages, f"{page}{AGENT}")

    def derived(self, page: str, kind: str) -> Path:
        return self._at(self.build, f"{page}.{kind}")

    def rendered(self, page: str) -> Path:
        return self._at(self.out, f"{page}.png")

    def _at(self, directory: Path, name: str) -> Path:
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def ids(self, chosen: list[str], *, prepared: bool = True) -> list[str]:
        """Page ids, from what was named on the command line.

        Nothing named is every page. A name that is a page is that page; a name
        that is a directory is every page under it, so a chapter is asked for the
        way it is stored. `prepared` chooses which side to look at: the pages
        that have been read, or the scans that exist.
        """
        if prepared:
            root, tails = self.pages, (AGENT,)
        else:
            root, tails = self.raw, SUFFIXES

        def below(directory: Path) -> list[str]:
            return sorted(
                str(p.parent / p.name[: -len(t)])[len(str(root)) + 1 :]
                for p in directory.rglob("*")
                if p.is_file()
                for t in tails
                if p.name.endswith(t)
            )

        if not chosen:
            return below(root)

        ids: list[str] = []
        for name in chosen:
            if any((root / f"{name}{t}").exists() for t in tails):
                ids.append(name)
            elif (root / name).is_dir():
                ids.extend(below(root / name))
            else:
                raise SystemExit(f"no page or directory {name} under {root}")
        return ids
