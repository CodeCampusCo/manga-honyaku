"""What can be tested without a manga.

`series/` is ignored and stays ignored, so nobody who clones this has a page to
run the pipeline on. What both sides can run is the arithmetic: the measurements,
the tags, the budget, the comparisons. Every bug these cover was a real one.

Run from the repository root, which is where the font path resolves from.
"""

from __future__ import annotations

import json
import unicodedata

import numpy as np

import pytest
from PIL import ImageFont

from manga_honyaku.chapters import chosen, entries
from manga_honyaku.detect import nearly
from manga_honyaku.ask import TOOLS
from manga_honyaku.fit import measure, terms, trie
from manga_honyaku.check import settle, says_something
from manga_honyaku.audit import split_words
from manga_honyaku.prepare import (cells, colliding, lettered_at, overlapping, tag,
                                   tag_page, uncovered)
from manga_honyaku.order import disagreements, propose
from manga_honyaku.page import Series
from manga_honyaku.regions import drifted, repeated, widest
from manga_honyaku.tally import chapter_of, polite_jp, polite_th
from manga_honyaku.render import (FONT, LINE_SPACING, SMALLEST, UNREADABLE,
                                  floor_for, lay_out, room_for, widths)
from manga_honyaku.sheet import around, build
from manga_honyaku.space import (BLOCK, blank, block, gap, margin, nearest,
                                 rectangles, share, spaces, where)


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


def test_one_line_written_with_two_kinds_of_pause_is_not_drift():
    """`08/09` against `05/02`: `อืมมม…` and `อืมมม...`. Flagged, it costs a
    re-read and teaches the reader to skim the flag."""
    rows = [
        ("08/09", {"status": "ok", "target": "อืมมม…"}),
        ("05/02", {"status": "ok", "target": "อืมมม..."}),
        ("05/14", {"status": "ok", "target": "อืมมม……"}),
    ]
    assert not drifted(rows)


def test_a_space_is_not_a_pause_and_still_counts():
    """Thai spaces are lettering decisions, so they are left alone."""
    rows = [
        ("a", {"status": "ok", "target": "คุณทามากาวะ"}),
        ("b", {"status": "ok", "target": "คุณทามา กาวะ"}),
    ]
    assert drifted(rows)


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


def test_the_space_thai_sets_before_the_repetition_mark_is_not_a_split():
    """`ต่าง ๆ` is one word written the conventional way. The mark is Thai
    script, so nothing else in the check tells it from a word cut in half."""
    assert not split_words("ต่าง ๆ กัน", None)
    assert not split_words("เร็ว ๆ นี้", None)


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


def test_every_tool_puts_the_question_in_its_argv():
    """The whole reason `ask` exists: each CLI takes a prompt differently.

    `agy`'s `-p` swallows the next word, so its prompt has to be attached to the
    flag — written apart it runs a turn against a flag name and says so.
    """
    question = "which Thai word carries this"
    for name, build in TOOLS.items():
        argv = build(question)
        assert argv[0] == name
        assert any(question in part for part in argv), name
    assert f"-p={question}" in TOOLS["agy"](question)


# --- the boxes the detector nearly drew --------------------------------------

def weak(box, score=0.2):
    return ("text_free", box, score)


def test_a_weak_box_on_text_already_boxed_is_not_a_loss():
    """Most near misses are the parts of a region the detector also found whole.

    Reported, they would bury the one case worth having: a drawn sound nothing
    covers at all.
    """
    regions = [{"box": [100, 100, 300, 400]}]
    assert nearly([weak([120, 120, 280, 380])], regions, 1180, 0.35) == []


def test_a_weak_box_nothing_covers_is_kept():
    """`07/19`: one ぽにょん scored 0.38 and its mirror 0.15, so the page was
    lettered with half a symmetrical gag and nothing could say so."""
    got = nearly([weak([113, 581, 249, 804], 0.17)], [{"box": [709, 567, 829, 760]}], 1180, 0.35)
    assert [c["score"] for c in got] == [0.17]


def test_a_sliver_is_not_lettering():
    """Under the threshold the model returns strokes and screentone, not text."""
    assert nearly([weak([500, 600, 508, 800])], [], 1180, 0.35) == []


def test_a_confident_detection_is_a_region_and_never_a_candidate():
    assert nearly([weak([0, 0, 200, 300], 0.9)], [], 1180, 0.35) == []


# --- the half of the budget room does not state ------------------------------

def test_the_longest_run_is_the_budget_for_one_line():
    """`room` is the whole box; a token wider than one line brings the size down
    however short the line is, which is what `room` alone cannot say."""
    region = {"box": [0, 0, 120, 300], "size": 30, "room": 24}
    assert widest(region, LINE_SPACING) == 24 // int(300 // (30 * LINE_SPACING))


def test_a_region_with_no_budget_has_no_run():
    assert widest({"box": [0, 0, 120, 300], "size": 30}, LINE_SPACING) is None
    assert widest({"box": [0, 0, 120, 300], "room": 24}, LINE_SPACING) is None


# --- which way round a sheet is read -----------------------------------------

def pages(tmp_path):
    from PIL import Image

    made = []
    for shade in (0, 255):
        path = tmp_path / f"{shade}.png"
        Image.new("RGB", (100, 140), (shade, shade, shade)).save(path)
        made.append(path)
    return made


def test_the_first_page_named_is_on_the_left_by_default(tmp_path):
    sheet, width = build(pages(tmp_path))
    assert sheet.getpixel((width // 2, 10)) == (0, 0, 0)


def test_rtl_puts_the_first_page_named_on_the_right(tmp_path):
    """A spread laid out the other way still reads panel by panel, so nothing
    about the sheet itself says it is mirrored."""
    sheet, width = build(pages(tmp_path), rtl=True)
    assert sheet.getpixel((width + width // 2, 10)) == (0, 0, 0)


# --- the order nothing else checks -------------------------------------------

def boxes(**named):
    return [{"id": rid, "box": box} for rid, box in named.items()]


def test_a_tier_is_read_right_to_left_and_tiers_top_to_bottom():
    page = boxes(
        A=[500, 0, 700, 200], B=[100, 0, 300, 200],
        C=[500, 300, 700, 500], D=[100, 300, 300, 500],
    )
    assert propose(page) == ["A", "B", "C", "D"]


def test_a_tall_panel_on_the_right_is_read_before_both_beside_it():
    """No horizontal line crosses the page, so the cut has to go the other way
    first — which is the layout a naive sort by row gets wrong."""
    page = boxes(
        tall=[500, 0, 700, 500],
        upper=[100, 0, 300, 200],
        lower=[100, 300, 300, 500],
    )
    assert propose(page) == ["tall", "upper", "lower"]


def test_boxes_no_line_can_separate_are_read_down_and_rightmost_first():
    page = boxes(A=[0, 0, 400, 300], B=[200, 100, 600, 400])
    assert propose(page) == ["A", "B"]


def test_a_pair_the_file_and_the_boxes_disagree_about_is_named():
    page = boxes(first=[500, 0, 700, 200], second=[100, 0, 300, 200])
    page[0]["order"], page[1]["order"] = 2, 1
    assert disagreements(page) == [("second", "first", False)]


def test_a_file_that_agrees_with_the_boxes_says_nothing():
    page = boxes(first=[500, 0, 700, 200], second=[100, 0, 300, 200])
    page[0]["order"], page[1]["order"] = 1, 2
    assert disagreements(page) == []


def test_a_pair_separable_both_ways_says_so_rather_than_settling_it():
    """`07/10`: a narrow panel beside a wide one, lettering high in one and low
    in the other, so a horizontal line passes between them as cleanly as the
    vertical one. The cut takes the horizontal and is wrong, and no rule over
    the boxes could have known — the ruled border is in the artwork."""
    page = boxes(low=[587, 734, 637, 881], high=[485, 336, 536, 579])
    page[0]["order"], page[1]["order"] = 1, 2
    (_, _, both), = disagreements(page)
    assert both


def test_a_pair_only_one_line_separates_is_a_real_disagreement():
    page = boxes(above=[100, 0, 700, 200], below=[100, 300, 700, 500])
    page[0]["order"], page[1]["order"] = 2, 1
    (_, _, both), = disagreements(page)
    assert not both


# --- naming a region instead of four numbers ---------------------------------

def work_with(tmp_path, regions, width=836, height=1180):
    (tmp_path / "pages").mkdir()
    (tmp_path / "pages" / "01.agent.json").write_text(json.dumps(
        {"img_width": width, "img_height": height, "regions": regions}
    ))
    return Series(tmp_path)


def test_a_region_crop_shows_what_the_region_sits_in(tmp_path):
    """A box on its own answers what it says; a crop is usually asked which
    panel it is in."""
    work = work_with(tmp_path, [{"id": "F8", "box": [400, 500, 500, 600]}])
    assert around(work, "01", "F8") == (300, 400, 600, 700)


def test_a_region_crop_stops_at_the_edge_of_the_page(tmp_path):
    work = work_with(tmp_path, [{"id": "B1", "box": [10, 10, 110, 110]}])
    assert around(work, "01", "B1") == (0, 0, 210, 210)


def test_naming_a_region_that_is_not_there_fails_loudly(tmp_path):
    work = work_with(tmp_path, [{"id": "B1", "box": [0, 0, 10, 10]}])
    with pytest.raises(SystemExit):
        around(work, "01", "B9")


# --- the smallest a work letters at ------------------------------------------

def test_a_work_sets_its_own_floor():
    assert floor_for({"floor": 7}, 1.0) == 7


def test_a_work_that_sets_none_gets_the_default():
    assert floor_for({}, 1.0) == SMALLEST


def test_the_page_scale_carries_the_floor_with_it():
    """A work scanned at twice the height letters at twice the size."""
    assert floor_for({"floor": 7}, 2.0) == 14


def test_nothing_goes_below_unreadable_however_small_it_is_asked_for():
    assert floor_for({"floor": 1}, 1.0) == UNREADABLE
    assert floor_for({"floor": 7}, 0.1) == UNREADABLE


def test_fit_measures_against_the_same_floor_render_draws_at():
    """Reported below it, a size is one the page will never be drawn at."""
    hair_thin = {"box": [0, 0, 40, 18]}
    assert measure(hair_thin, "ยินดีต้อนรับ", FONT, None, LINE_SPACING, 40) is None


# --- one sheet, boxes off several pages --------------------------------------

def test_each_cell_can_take_its_own_box(tmp_path):
    """Ten candidates off ten pages is one sheet, not ten runs and a combine."""
    from PIL import Image

    made = []
    for shade in (0, 255):
        path = tmp_path / f"{shade}.png"
        Image.new("RGB", (100, 100), (shade, shade, shade)).save(path)
        made.append(path)
    sheet, width = build(made, crop=[(0, 0, 50, 50), (0, 0, 100, 100)])
    assert sheet.width == 2 * width


def test_one_box_still_applies_to_every_cell(tmp_path):
    from PIL import Image

    made = []
    for shade in (0, 255):
        path = tmp_path / f"{shade}.png"
        Image.new("RGB", (100, 100), (shade, shade, shade)).save(path)
        made.append(path)
    sheet, width = build(made, crop=(0, 0, 50, 50))
    assert sheet.height == width


# --- two lines drawn onto the same piece of page -----------------------------

def plate(rid, box, role="caption", status="ok"):
    return {"id": rid, "box": box, "role": role, "status": status}


def test_a_plate_landing_on_a_line_is_reported():
    """`clean` paints the plate's box out and `render` draws into it, so the
    line underneath is gone and nothing measures what is missing."""
    (_, _, share), = colliding([plate("F5", [0, 0, 200, 200]),
                                plate("B1", [100, 100, 300, 300])])
    assert share > 0.2


def test_a_plate_landing_on_drawn_sound_is_reported():
    """The sound is artwork the page was meant to keep; the plate erases it."""
    got = colliding([plate("F2", [0, 0, 200, 200]),
                     plate("F3", [100, 100, 300, 300], role="sfx")])
    assert len(got) == 1


def test_regions_drawn_close_are_not_a_collision():
    assert colliding([plate("B1", [0, 0, 100, 100]),
                      plate("B2", [95, 95, 195, 195])]) == []


def test_two_regions_that_erase_nothing_cannot_collide():
    assert colliding([plate("F5", [0, 0, 200, 200], role="sfx"),
                      plate("F6", [0, 0, 200, 200], role="image_text")]) == []


def test_a_declined_region_erases_nothing_and_is_not_a_plate():
    assert colliding([plate("F5", [0, 0, 200, 200], status="declined"),
                      plate("B1", [0, 0, 200, 200])]) == []


# --- where a gloss goes -----------------------------------------------------

def paper(height=160, width=160):
    return np.full((height, width), 255, np.uint8)


def test_at_stands_in_for_the_box_everywhere_and_only_where_it_is_set():
    assert where({"box": [0, 0, 10, 10]}) == [0, 0, 10, 10]
    assert where({"box": [0, 0, 10, 10], "at": [5, 5, 9, 9]}) == [5, 5, 9, 9]


def test_a_glossed_region_is_measured_from_the_rectangle_it_is_drawn_into():
    """The whole of the `at` rule: `box` says where the Japanese sits and
    nothing else reads it for a size."""
    box = [0, 0, 100, 400]
    assert lettered_at(box, "ああああ") == pytest.approx(100.0)
    same = {"box": box, "at": [0, 0, 50, 200], "source": "ああああ"}
    tag_page([same], 1180, {"one": 0.5})
    assert same["size"] == 50


def test_a_budget_is_counted_against_the_at_when_there_is_one():
    style = {"k": 1.0, "line_spacing": LINE_SPACING, "one": 0.5}
    wide = {"box": [0, 0, 100, 100], "bubble": [0, 0, 100, 100], "source": "ああ"}
    narrow = dict(wide, at=[0, 0, 50, 100])
    tag(wide, 10, style)
    tag(narrow, 10, style)
    assert narrow["room"] < wide["room"]


def test_two_glosses_in_one_gutter_are_found_and_a_box_pair_is_not():
    regions = [
        {"id": "F1", "box": [0, 0, 10, 10], "at": [100, 100, 200, 200]},
        {"id": "F2", "box": [500, 500, 510, 510], "at": [150, 150, 250, 250]},
        {"id": "F3", "box": [900, 900, 910, 910]},
    ]
    assert not overlapping(regions)
    pairs = overlapping(regions, 0, field="at")
    assert [(a["id"], b["id"]) for a, b, _ in pairs] == [("F1", "F2")]


# --- the blank rectangles a page has ----------------------------------------

def test_a_speck_does_not_split_a_margin_and_a_stroke_does():
    """The bug this is for: one pixel of scan noise in a clean margin cuts it
    into two halves too narrow to use."""
    speckled = paper()
    speckled[80, 80] = 0
    assert blank(speckled, [], None).all()

    drawn = paper()
    drawn[76:84, 76:84] = 0
    assert not blank(drawn, [], None).all()


def test_dark_but_featureless_is_not_blank():
    """Black type has to read on it, and there is no white plate under a gloss."""
    shadowed = paper()
    shadowed[64:96] = 150
    grid = blank(shadowed, [], None)
    assert not grid[8:12].any()
    assert grid[:8].all()


def test_every_region_takes_its_own_box_out_of_the_page():
    region = {"box": [40, 40, 80, 80]}
    grid = blank(paper(), [region], region)
    assert not grid[6, 6]
    assert grid[0, 0]


def test_a_rectangle_is_reported_once_and_not_once_per_row_it_grew_through():
    grid = np.ones((4, 4), bool)
    assert rectangles(grid) == [(0, 0, 4, 4)]


def test_a_rectangle_is_maximal_in_both_directions():
    grid = np.ones((4, 4), bool)
    grid[0, 0] = False
    found = {(x1, y1, x2, y2) for x1, y1, x2, y2 in rectangles(grid)}
    assert found == {(1, 0, 4, 4), (0, 1, 4, 4)}


def test_distance_is_the_gap_and_not_the_centres():
    assert gap((0, 0, 10, 10), (0, 0, 10, 10)) == 0
    assert gap((20, 0, 30, 10), (0, 0, 10, 10)) == 10


def test_a_block_is_placed_as_near_the_lettering_as_its_rectangle_allows():
    assert nearest(10, 10, (0, 0, 100, 100), [200, 0, 210, 10]) == (90, 0, 100, 10)
    assert nearest(10, 10, (0, 0, 100, 100), [40, 40, 50, 50]) == (40, 40, 50, 50)


def test_the_page_edge_is_flagged_and_the_middle_of_the_drawing_is_not():
    assert margin((0, 40, 20, 60), 200, 200)
    assert margin((40, 180, 60, 200), 200, 200)
    assert not margin((40, 40, 60, 60), 200, 200)


def test_what_is_offered_is_trimmed_to_the_text_and_clear_of_the_lettering():
    """`render` centres a free block in its rectangle, so a rectangle larger
    than the text leaves the Thai floating in the middle of a strip."""
    region = {"id": "F1", "box": [0, 0, 40, 400], "target": "ที่เรียกว่ามือโปรไง"}
    found = spaces(
        paper(400, 400), [region], region, FONT, None, LINE_SPACING, 21, 60
    )
    assert found
    for box, size, _ in found:
        assert size >= 21
        assert box[0] >= region["box"][2]
        assert (box[2] - box[0]) * (box[3] - box[1]) < 300 * 400

