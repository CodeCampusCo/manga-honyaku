"""A reading order proposed from the boxes, for a translator to correct.

`order` is the one field nothing checks: `audit` sorts the numbers and compares
them to `1..N`, which a page numbered completely and in the wrong sequence
passes. It is also the largest piece of hand work in a chapter.

The algorithm is the recursive cut, which needs no panel detection: split the
boxes wherever a straight line passes between them without crossing one,
horizontally first, then vertically with the rightmost group first. A gutter is
exactly such a line, so panels come out of it without being found.

Two failures, and the second is why a disagreement is reported rather than
settled. A balloon hanging across a panel border joins both sides into one
cluster. And two boxes can be separable **both** ways — a panel whose lettering
is high beside one whose lettering is low — where the cut takes the horizontal,
which is right for a stacked page and wrong for that tier. What decides it is the
ruled border in the artwork, which is not in this file.
"""

from __future__ import annotations


def split(boxes: list[tuple], axis: int) -> list[list[tuple]] | None:
    """The boxes grouped by every straight line that passes between them.

    `axis` 0 cuts vertically and 1 horizontally; None where no line fits.
    """
    low, high = axis, axis + 2
    groups: list[list[tuple]] = []
    edge = float("-inf")
    for box in sorted(boxes, key=lambda b: b[1][low]):
        if box[1][low] > edge:
            groups.append([])
        groups[-1].append(box)
        edge = max(edge, box[1][high])
    return groups if len(groups) > 1 else None


def cut(boxes: list[tuple]) -> list[tuple]:
    """These boxes in reading order, right to left and top to bottom."""
    if len(boxes) < 2:
        return list(boxes)
    for axis in (1, 0):
        groups = split(boxes, axis)
        if groups is None:
            continue
        if axis == 0:
            groups.reverse()
        return [box for group in groups for box in cut(group)]
    return sorted(boxes, key=lambda b: (b[1][1], -b[1][0]))


def propose(regions: list[dict]) -> list[str]:
    """Region ids in the order the geometry reads them."""
    return [rid for rid, _ in cut([(r["id"], r["box"]) for r in regions])]


def recorded(regions: list[dict]) -> list[str]:
    """Region ids in the order the working file records, unnumbered ones last."""
    numbered = [r for r in regions if r.get("order") is not None]
    return [r["id"] for r in sorted(numbered, key=lambda r: r["order"])]


def either_way(first: list[float], second: list[float]) -> bool:
    """Whether a horizontal and a vertical line both separate these two boxes.

    Asked of a pair, not of a page: of a page it is true of nearly every one that
    has more than a single panel.
    """
    return (
        (first[2] <= second[0] or second[2] <= first[0])
        and (first[3] <= second[1] or second[3] <= first[1])
    )


def disagreements(regions: list[dict]) -> list[tuple[str, str, bool]]:
    """Adjacent pairs the file reads one way round and the geometry the other.

    Each carries whether the boxes could be read either way, which separates a
    question for the artwork from an error in one of the two orders.
    """
    here = recorded(regions)
    there = propose(regions)
    rank = {rid: i for i, rid in enumerate(there)}
    box = {r["id"]: r["box"] for r in regions}
    return [
        (a, b, either_way(box[a], box[b]))
        for a, b in zip(here, here[1:])
        if a in rank and b in rank and rank[a] > rank[b]
    ]
