"""What can be tested without a manga.

`series/` is ignored and stays ignored, so nobody who clones this has a page to
run the pipeline on. What both sides can run is the arithmetic: the measurements,
the tags, the budget, the comparisons. Every bug these cover was a real one.

Run from the repository root, which is where the font path resolves from.
"""

from __future__ import annotations

import json
import unicodedata

import pytest
from PIL import ImageFont

from manga_honyaku.chapters import chosen, entries
from manga_honyaku.fit import measure, terms, trie
from manga_honyaku.check import settle, says_something
from manga_honyaku.audit import split_words
from manga_honyaku.prepare import (cells, lettered_at, overlapping, tag,
                                   tag_page, uncovered)
from manga_honyaku.page import Series
from manga_honyaku.regions import drifted, repeated
from manga_honyaku.tally import chapter_of, polite_jp, polite_th
from manga_honyaku.render import FONT, LINE_SPACING, lay_out, room_for, widths


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

def test_a_pause_recorded_twice_over_is_one_pause_on_the_page():
    """The bug: `・・・...` is three dots read twice, in two scripts.

    Twenty-eight regions in volume one carry a pause written both ways, from two
    readings of one box being merged. Counted as six characters the region
    measures a sixth smaller than it is — and small lettering is the fault this
    measurement exists to find.
    """
    assert cells("じゃあさ・・・...") == cells("じゃあさ・・・") == 7
    assert cells("あ...") == 4                       # a pause written once stands
    assert cells("あ い") == 2                       # whitespace is not a cell


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


# --- the two fields prepare writes ------------------------------------------

def style(**over):
    return {"k": 1.45, "line_spacing": 1.32, "one": 0.46, **over}


def bubble(box, **over):
    return {"box": box, "bubble": box, **over}


def test_a_region_that_cannot_be_measured_takes_the_rest_of_its_page():
    """The bug: --retag overwrote sizes it could not measure with a constant.

    A burst bubble reading `!?` still has to be lettered, and what the page it
    sits on was set at is a better answer than a number carried in from another
    book.
    """
    regions = [
        bubble([0, 0, 100, 100], source="あいうえ"),
        bubble([100, 0, 200, 100], source="あいうえ"),
        bubble([200, 0, 300, 100], source="!?"),
    ]
    tag_page(regions, 200, style())
    assert regions[0]["size"] == regions[1]["size"] == regions[2]["size"]


def test_a_fallback_does_not_displace_a_size_set_by_eye():
    regions = [bubble([200, 0, 300, 100], source="!?", size=99)]
    tag_page(regions, 200, style())
    assert regions[0]["size"] == 99


def test_a_measurable_region_is_always_re_measured():
    regions = [bubble([0, 0, 100, 100], source="あいうえ", size=99)]
    tag_page(regions, 200, style())
    assert regions[0]["size"] != 99


def test_free_floating_text_gets_no_budget():
    """It is lettered to its own extent rather than to a size."""
    region = {"box": [0, 0, 400, 200], "room": 99}
    tag(region, 30, style())
    assert "room" not in region


def test_a_bubble_too_small_for_one_line_gets_no_budget():
    region = bubble([0, 0, 200, 10])
    tag(region, 30, style())
    assert "room" not in region


def test_a_bubble_that_holds_something_states_how_much():
    region = bubble([0, 0, 400, 200])
    tag(region, 20, style())
    assert region["room"] > 0


def test_one_multiplier_moves_every_region_together():
    """What survives translation is the ratio between the regions on a page, so
    the budget answers to `k` the same way wherever the region sits."""
    small, large = bubble([0, 0, 400, 200]), bubble([0, 0, 400, 200])
    tag(small, 20, style())
    tag(large, 20, style(k=2.9))
    assert small["room"] > large["room"]


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


# --- the size a candidate line would be drawn at ----------------------------

def test_the_longest_word_sets_the_size_not_the_length():
    """The bug: a caption lettered half-size was read as a line that ran long.

    A word cannot be broken, so in a column this narrow the binding constraint is
    the widest single token. These two lines are the same thirteen letters and
    differ only in how they tokenise, and the one whose longest token is shorter
    is set nearly twice as large. That is why the fix for a small caption is a
    different word rather than a shorter sentence.
    """
    column = {"box": [0, 0, 84, 309]}
    one_long_token = measure(column, "เธอนำแสงสว่าง", FONT, None, LINE_SPACING)
    four_short_ones = measure(column, "เธอ นำ แสง สว่าง", FONT, None, LINE_SPACING)
    assert four_short_ones[0] > one_long_token[0]

    # And this is the mechanism, rather than a ratio between two builds' numbers:
    # at the larger size the undivided word is wider than the column, so the line
    # holding it has to come down until it is not.
    larger = ImageFont.truetype(FONT, four_short_ones[0])
    assert larger.getlength("แสงสว่าง") > 84


def test_a_longer_line_of_short_words_still_beats_a_short_line_of_long_ones():
    column = {"box": [0, 0, 84, 309]}
    shorter = measure(column, "เธอนำแสงสว่าง", FONT, None, LINE_SPACING)
    longer = measure(column, "เธอ นำ แสง มา ให้ ผม", FONT, None, LINE_SPACING)
    assert len("เธอ นำ แสง มา ให้ ผม".replace(" ", "")) > len("เธอนำแสงสว่าง")
    assert longer[0] > shorter[0]


def test_a_line_that_cannot_be_broken_small_enough_reports_rather_than_guesses():
    hair_thin = {"box": [0, 0, 12, 300]}
    assert measure(hair_thin, "ยินดีต้อนรับ", FONT, None, LINE_SPACING) is None


def test_fill_is_the_share_of_the_box_the_stack_covers():
    size, fill, lines = measure({"box": [0, 0, 400, 200]}, "สวัสดี", FONT, None, 1.32)
    assert 0 < fill <= 1
    assert fill == pytest.approx(int(size * 1.32) * len(lines) / 200)


# --- regions standing on the same lettering ---------------------------------

def box(x1, y1, x2, y2, rid="R"):
    return {"id": rid, "box": [x1, y1, x2, y2]}


def test_the_same_text_found_twice_is_one_pair():
    pair = overlapping([box(10, 10, 60, 200, "B1"), box(10, 10, 60, 200, "F1")])
    assert [(a["id"], b["id"]) for a, b, _ in pair] == [("B1", "F1")]


def test_a_column_inside_a_phrase_counts_even_though_the_union_barely_overlaps():
    """The shape this exists for: one box round a whole phrase, one round a
    column of it. As a share of the pair they overlap a third; as a share of the
    smaller they overlap entirely, and it is the smaller that is redundant."""
    phrase, column = box(0, 0, 300, 100, "F5"), box(0, 0, 100, 100, "F8")
    assert overlapping([phrase, column])
    union = 100 * 100 / (300 * 100)
    assert union < 0.85


def test_boxes_that_only_touch_at_a_margin_are_not_a_pair():
    assert not overlapping([box(0, 0, 100, 100, "A"), box(90, 90, 200, 200, "B")])


def test_regions_that_do_not_meet_at_all_are_not_a_pair():
    assert not overlapping([box(0, 0, 50, 50, "A"), box(60, 60, 100, 100, "B")])


def test_the_worst_pair_is_reported_first():
    found = overlapping(
        [box(0, 0, 100, 100, "A"), box(0, 0, 100, 100, "B"), box(0, 0, 92, 100, "C")]
    )
    assert [(a["id"], b["id"]) for a, b, _ in found][0] == ("A", "B")


# --- counting a register rather than remembering it -------------------------

def test_politeness_is_read_off_the_verb_ending():
    assert polite_jp("靴紐ほどけてますよっ")
    assert polite_jp("お待たせしました...")
    assert not polite_jp("やっぱ店長面白い人だなぁ")


def test_board_slang_misspelling_the_polite_form_still_counts_as_polite():
    assert polite_jp("特定しますた。")


def test_a_held_vowel_is_still_the_politeness_slot():
    """This artist draws out final vowels, and `ค่าาา` is `ค่ะ` held. Matching
    only the dictionary spelling undercounts exactly the most obviously polite
    lines."""
    assert polite_th("ล้อเล่นน่ะ โกหกค่าาา——")
    assert polite_th("ฉันใส่ตลอดเลยค่ะ")
    assert not polite_th("ทีแบ็ค")


def test_a_page_id_carries_the_chapter_it_belongs_to():
    assert chapter_of("02/05") == "02"
    assert chapter_of("01/ch02/003") == "01/ch02"


def test_a_flat_work_is_one_chapter_rather_than_none():
    assert chapter_of("X0006") == "—"


# --- what a chapter says twice ----------------------------------------------

def work_of(pages: dict, root):
    """A series on disk holding nothing but sources, which is all `repeats` reads."""
    for page, sources in pages.items():
        path = root / "pages" / f"{page}.agent.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "regions": [
                {"id": f"B{i}", "box": [0, 0, 10, 10], "placement": "bubble",
                 "source": s, "target": t}
                for i, (s, t) in enumerate(sources, 1)
            ]
        }, ensure_ascii=False))
    return Series(root)


def test_a_line_the_chapter_says_twice_is_found_before_anyone_reads_a_page(tmp_path):
    work = work_of({
        "02/09": [("私はいつも穿いてますよ", None)],
        "02/16": [("私はいつも穿いてますよ", None)],
        "02/21": [("よいしょ", None)],
    }, tmp_path)
    found = {said: len(rows) for said, rows, _ in repeated(work, work.ids(["02"]))}
    assert found == {"私はいつも穿いてますよ": 2}


def test_an_earlier_chapter_that_already_answered_it_comes_with_its_answer(tmp_path):
    work = work_of({
        "01/21": [("あ...ありじゃす", "ข…ขอบคุงคับ")],
        "02/14": [("あ・・・ありじゃす", None)],
    }, tmp_path)
    (said, rows, elsewhere), = repeated(work, work.ids(["02"]))
    assert len(rows) == 1 and [p for p, _ in elsewhere] == ["01/21"]
    assert elsewhere[0][1]["target"] == "ข…ขอบคุงคับ"


def test_a_pause_identifies_no_line_and_is_not_a_repeat(tmp_path):
    work = work_of({"02/09": [("...", None)], "02/15": [("・・・", None)]}, tmp_path)
    assert repeated(work, work.ids(["02"])) == []


def test_one_japanese_line_answered_two_ways_is_drift():
    rows = [
        ("01/16", {"status": "ok", "target": "ยังไม่รู้เลย…"}),
        ("02/20", {"status": "ok", "target": "ยังไม่รู้อยู่ดี…"}),
    ]
    assert drifted(rows)
    assert not drifted([(p, {**r, "target": "เหมือนกัน"}) for p, r in rows])


def test_a_region_nobody_lettered_is_not_a_disagreement():
    """A duplicate box has one region declined and no target on it. That is the
    ordinary case, not two answers to one line."""
    rows = [
        ("02/06", {"status": "ok", "target": "กำลังเติมของ"}),
        ("02/06", {"status": "declined", "target": None}),
    ]
    assert not drifted(rows)


def test_one_piece_of_lettering_found_twice_is_not_a_line_said_twice(tmp_path):
    """The detector returns some text once as bubble text and once as free text.
    Both boxes stand on the same drawn phrase, so the chapter said it once."""
    root = tmp_path / "w"
    (root / "pages" / "03").mkdir(parents=True)
    (root / "pages" / "03" / "01.agent.json").write_text(json.dumps({
        "regions": [
            {"id": "B3", "box": [0, 0, 60, 200], "placement": "bubble", "source": "ぼー"},
            {"id": "F1", "box": [0, 0, 60, 200], "placement": "free", "source": "ぼー"},
        ]
    }, ensure_ascii=False))
    work = Series(root)
    assert repeated(work, work.ids(["03"])) == []


def test_the_shi_row_of_both_polite_auxiliaries_counts():
    """Written as a list of endings rather than of stems, this matcher let
    ましょう, でしょう and でした through and read a chapter as a register lower
    than it was."""
    assert polite_jp("ではお客さん相手で実践してみましょうか")
    assert polite_jp("そうでしょうね")
    assert polite_jp("大変でした")
    assert polite_jp("数え切れません")
    assert not polite_jp("やっぱ店長面白い人だなぁ")


def test_a_line_a_character_quotes_is_not_their_own_register():
    """This work's whole joke is a man repeating a polite question he cannot
    ask. Counting the quotation as his register reads him as polite in the panel
    where he is talking to himself."""
    assert not polite_jp("「玉川さんAV出てました?」って…")
    assert polite_jp("「AV出てた?」なんて聞けませんよ")


# --- a space inside a word ---------------------------------------------------

def test_a_space_between_two_words_is_not_a_split():
    assert not split_words("ผมจะไป สั่งของ", None)
    assert not split_words("เขา ไป", None)


def test_a_space_forced_into_a_dictionary_word_is_reported_and_should_be():
    """`ยินดีต้อนรับ` is one word, so `ยินดี ต้อนรับค่ะ!` splits it — which a work
    may still want, and `style.md` names that line as a deliberate exception.
    The check reports it; the exception is recorded where the decision was made,
    not suppressed in the code."""
    assert split_words("ยินดี ต้อนรับค่ะ!", None)


def test_a_space_inside_a_word_is_caught():
    """`ล้ม เหลว` reached a rendered page twelve times in one chapter: the line
    breaker is free to break at a space, so the word comes apart on the page."""
    assert split_words("ล้ม เหลว", None)
    assert split_words("เสียง คราง", None)


def test_a_space_beside_latin_or_digits_is_ordinary_typesetting():
    """Only Thai on both sides makes a space a word-splitter. Without this the
    check reports every price, every `AV`, every bracket — three of its four
    false positives across four chapters were exactly that."""
    assert not split_words("ราคา 2,180 เยน", None)
    assert not split_words("ดู AV มาแล้ว", None)


# --- a declined box holding a lettered one -----------------------------------

def test_a_declined_box_whose_parts_cover_it_is_not_reported():
    whole = {"id": "F3", "box": [0, 0, 100, 400], "status": "declined"}
    parts = [{"id": "F4", "box": [0, 0, 100, 200], "status": "ok"},
             {"id": "F5", "box": [0, 200, 100, 400], "status": "ok"}]
    (_, _, share), = uncovered([whole] + parts)
    assert share > 0.85


def test_a_declined_box_a_lettered_part_barely_covers_is_reported():
    """`04/09`: the whole phrase declined as "partial", one column lettered, and
    the rest of the Japanese left standing under the Thai."""
    whole = {"id": "F3", "box": [0, 0, 100, 500], "status": "declined"}
    part = {"id": "F4", "box": [0, 0, 100, 150], "status": "ok"}
    (_, inside, share), = uncovered([whole, part])
    assert [r["id"] for r in inside] == ["F4"] and share < 0.4


def test_terms_reads_words_txt(tmp_path):
    """`words.txt` is one term per line, and blank lines are not terms."""
    (tmp_path / "words.txt").write_text("ฮารุกะ\n\n  ชิกุระ  \n")
    assert terms(tmp_path) == {"ฮารุกะ", "ชิกุระ"}


def test_terms_without_the_file(tmp_path):
    """A work that has settled no term of its own is not an error."""
    assert terms(tmp_path) == set()


def test_trie_of_nothing_is_nothing():
    """`render` takes None for "no custom dictionary", so this must agree."""
    assert trie(set()) is None
    assert trie({"ฮารุกะ"}) is not None


def test_a_listed_term_stops_the_segmenter_splitting_it():
    """Why `words.txt` exists: unlisted, a transliteration falls apart.

    This is also why listing one costs something — an unsplittable token cannot
    wrap, so it is the token that overflows a narrow box.
    """
    from manga_honyaku.render import tokenise

    loose = [token for token, _ in tokenise("ฮารุกะ", trie(set()))]
    held = [token for token, _ in tokenise("ฮารุกะ", trie({"ฮารุกะ"}))]
    assert len(loose) > 1
    assert held == ["ฮารุกะ"]
