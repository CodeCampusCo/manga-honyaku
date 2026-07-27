"""What can be tested without a manga.

`series/` is ignored and stays ignored, so nobody who clones this has a page to
run the pipeline on. What both sides can run is the arithmetic: the measurements,
the tags, the budget, the comparisons. Every bug these cover was a real one.

Run from the repository root, which is where the font path resolves from.
"""

from __future__ import annotations

import unicodedata

import pytest

from manga_honyaku.chapters import chosen, entries
from manga_honyaku.check import settle, says_something
from manga_honyaku.prepare import lettered_at, size_of, tag
from manga_honyaku.render import FONT, lay_out, room_for, widths

BANDS = {"quiet": 35, "normal": 47, "loud": 60, "shout": 88}
SIZES = {"quiet": 24, "normal": 34, "loud": 50, "shout": 67, "display": 101}


# --- what a character costs -------------------------------------------------

def test_marks_are_free_even_where_unicode_says_otherwise():
    """The bug: `unicodedata.combining` is about collation, not typesetting.

    It returns 0 for Thai's above-vowels, so counting by it overstates a line by
    about a tenth. The face is the authority on what it draws.
    """
    _, free = widths(FONT)
    lied_about = "ัิีึื็์ํ๎"
    assert all(unicodedata.combining(c) == 0 for c in lied_about)
    assert set(lied_about) <= free


def test_a_consonant_costs_about_half_its_size():
    one, free = widths(FONT)
    assert 0.3 < one < 0.7
    assert "ก" not in free


@pytest.mark.parametrize(
    "word", ["สวัสดีครับ", "ที่", "เนี่ย", "ขอบคุณมากค่ะ", "ไอดอลกราเวีย"]
)
def test_free_marks_never_cost_a_character(word):
    """What counting by `free` is allowed to be wrong by, on any Pillow build.

    Pillow answers for a *lone* mark differently depending on whether libraqm is
    in the build — zero without it, a full width with it — which is why `widths`
    measures a mark on a base. Even then the two do not agree exactly: shaping
    through HarfBuzz sets `เนี่ย`, where an above-vowel and a tone mark stack,
    about eight per cent narrower than summing the parts does. Both machines
    letter correctly, because `lay_out` measures with the face it draws with;
    what neither may do is let a mark cost a character.
    """
    from PIL import ImageFont

    one, free = widths(FONT)
    face = ImageFont.truetype(FONT, 100)
    bare = "".join(c for c in word if c not in free)
    assert abs(face.getlength(bare) - face.getlength(word)) < one * 100


def test_room_is_an_estimate_and_says_so():
    """`one` is a median, so counting by it converges over a line and is loose
    over a word. `room` is a guide and not a bar, which is the same fact."""
    from PIL import ImageFont

    one, free = widths(FONT)
    line = "ขอบคุณมากค่ะ ไม่หรอกครับ ช่วยผมได้เยอะเลย"
    counted = sum(1 for c in line if c not in free) * one * 100
    assert counted == pytest.approx(ImageFont.truetype(FONT, 100).getlength(line), rel=0.2)


# --- how much fits ----------------------------------------------------------

def test_room_is_zero_when_not_one_line_fits():
    """A stated zero would read as `write nothing`, so prepare drops the key."""
    assert room_for([0, 0, 200, 10], size=40, spacing=1.32, one=0.46) == 0


def test_room_grows_with_the_box_and_shrinks_with_the_size():
    wide = room_for([0, 0, 400, 200], 20, 1.32, 0.46)
    narrow = room_for([0, 0, 200, 200], 20, 1.32, 0.46)
    bigger = room_for([0, 0, 400, 200], 40, 1.32, 0.46)
    assert wide == pytest.approx(2 * narrow, rel=0.05)
    assert bigger < wide / 2


# --- what the Japanese was lettered at --------------------------------------

def test_punctuation_alone_cannot_be_measured():
    """`!?` in a burst bubble and `…` in a pause are both unmeasurable.

    One character in a box sized for a beat measures as enormous lettering, so
    the measurement declines rather than answering.
    """
    assert lettered_at([0, 0, 100, 100], "!?") is None
    assert lettered_at([0, 0, 100, 100], "…") is None
    assert lettered_at([0, 0, 100, 100], "あ") is not None


def test_more_characters_in_the_same_box_measure_smaller():
    big = lettered_at([0, 0, 100, 100], "あい")
    small = lettered_at([0, 0, 100, 100], "あいうえおかきくけこ")
    assert big > small


def test_whitespace_is_not_a_character():
    assert lettered_at([0, 0, 100, 100], "あ い") == lettered_at([0, 0, 100, 100], "あい")


def test_size_of_reads_the_bands_against_the_scale():
    """A larger scan measures larger throughout, so the bands are quoted for a
    stated page height and scaled to the page in hand."""
    box = [0, 0, 100, 100]                   # ten characters measure at 31.6
    ten = "あいうえおかきくけこ"
    assert size_of(box, ten, BANDS, scale=1) == "quiet"
    assert size_of(box, ten, BANDS, scale=0.6) == "loud"
    assert size_of(box, ten, BANDS, scale=0.2) == "display"   # past every band
    assert size_of(box, "!?", BANDS, scale=1) == "normal"     # the fallback


# --- the two fields prepare writes ------------------------------------------

def style(**over):
    return {"sizes": SIZES, "line_spacing": 1.32, "one": 0.46, **over}


def test_a_fallback_does_not_displace_a_size_set_by_eye():
    """The bug: --retag overwrote sizes it could not measure.

    A burst bubble reading `!?` had been set to `display` by hand and came back
    as `normal`, which is what the measurement says when it has nothing to say.
    """
    region = {"box": [0, 0, 100, 100], "bubble": [0, 0, 100, 100],
              "source": "!?", "size": "display"}
    tag(region, region, BANDS, style(), scale=1)
    assert region["size"] == "display"


def test_an_unmeasurable_region_with_no_size_yet_still_gets_one():
    region = {"box": [0, 0, 100, 100], "bubble": [0, 0, 100, 100], "source": "!?"}
    tag(region, region, BANDS, style(), scale=1)
    assert region["size"] == "normal"


def test_a_measurable_region_is_always_re_measured():
    region = {"box": [0, 0, 100, 100], "bubble": [0, 0, 100, 100],
              "source": "あいうえおかきくけこ", "size": "display"}
    tag(region, region, BANDS, style(), scale=1)
    assert region["size"] == "quiet"


def test_free_floating_text_gets_no_budget():
    """It is lettered to its own extent rather than to a step."""
    region = {"box": [0, 0, 400, 200], "source": "あい", "room": 99}
    tag(region, region, BANDS, style(), scale=1)
    assert "room" not in region


def test_a_bubble_too_small_for_one_line_gets_no_budget():
    region = {"box": [0, 0, 200, 10], "bubble": [0, 0, 200, 10], "source": "あい"}
    tag(region, region, BANDS, style(), scale=1)
    assert "room" not in region


def test_a_bubble_that_holds_something_states_how_much():
    region = {"box": [0, 0, 400, 200], "bubble": [0, 0, 400, 200], "source": "あい"}
    tag(region, region, BANDS, style(), scale=1)
    assert region["room"] > 0


# --- comparing a reading against what was recorded --------------------------

def test_a_pause_is_written_a_dozen_ways_and_they_are_all_the_same():
    assert settle("…") == settle("...") == settle("・・・") == settle(":")
    assert settle("ま…って") == settle("ま...って")


def test_a_pause_identifies_no_line():
    """Thirty-two regions in one volume record nothing but `…`.

    Any box that reads as a pause would match one of them and mean nothing by
    it, so a reading with no letters is not evidence a line moved.
    """
    assert not says_something(settle("…"))
    assert not says_something(settle("・・・"))
    assert says_something(settle("あ…"))


# --- reading the record back ------------------------------------------------

RULE = ("What follows is what was seen while reading, not a substitute for the\n"
        "page. Never guess from an incomplete note.")


@pytest.fixture
def written(tmp_path):
    directory = tmp_path / "chapters"
    directory.mkdir()
    (directory / "01.md").write_text(
        f"# One\n\n{RULE}\n\n## X0001\nArt — a room.\n\n## X0002\nArt — a street.\n")
    (directory / "02.md").write_text(
        f"# Two\n\n{RULE}\n\n## X0003\nArt — a door.\n")
    return directory


def test_the_rule_comes_back_whole(written):
    """The bug: only its first line was captured, so it stopped being a rule."""
    rule, _ = entries(written)
    assert rule == RULE
    assert "incomplete note" in rule


def test_entries_are_found_across_files(written):
    _, found = entries(written)
    assert sorted(found) == ["X0001", "X0002", "X0003"]
    assert found["X0002"].startswith("## X0002")


def test_a_range_selects_inclusively_across_files(written):
    _, found = entries(written)
    assert chosen(["X0002-X0003"], found) == ["X0002", "X0003"]
    assert chosen(["X0001"], found) == ["X0001"]
    assert chosen([], found) == ["X0001", "X0002", "X0003"]


def test_asking_for_a_page_nobody_wrote_about_fails_loudly(written):
    _, found = entries(written)
    with pytest.raises(SystemExit):
        chosen(["X9999"], found)


# --- laying a line into a box -----------------------------------------------

def test_a_line_that_fits_keeps_the_size_it_asked_for():
    laid = lay_out("สวัสดี", (0, 0, 400, 200), FONT, 9, 40)
    assert laid is not None
    assert laid[0].size == 40


def test_a_line_too_long_is_brought_down_rather_than_overflowing():
    box = (0, 0, 120, 60)
    short = lay_out("สวัสดี", box, FONT, 9, 40)
    long = lay_out("สวัสดีครับผมมาจากที่ไกลมากเลยนะครับ", box, FONT, 9, 40)
    assert long[0].size < short[0].size
    assert long[2] * len(long[1]) <= 60      # line height times lines fits the box
