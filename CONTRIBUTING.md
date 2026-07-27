# Contributing

Code handles geometry — detection, OCR, text removal, rendering. An LLM agent
handles comprehension — reading order, speaker attribution, and the translation
itself. Most of what looks like a missing feature is comprehension, and belongs
in a skill under `.claude/skills/` rather than in Python.

## You cannot run the pipeline, and that is deliberate

`series/` is ignored and stays ignored. No manga is in this repository and none
ever will be, so a fresh clone has nothing to detect, clean or render. To use it
you point `raw.txt` at scans you have the right to use; to *develop* it you
mostly do not need to.

What both you and this project can run is the arithmetic:

```sh
uv sync
uv run pytest        # 28 assertions, about four seconds
```

Every test there covers a bug that was real. If you change how a size is
measured, how long a line may be, or how a reading file is parsed, the test that
fails is the one to read first.

### If a test fails and your change looks right

It might be your Pillow build. Whether `libraqm` is compiled in changes how a
lone combining mark measures — zero without it, a full character width with it —
and Thai marks are the whole reason this project can letter without a shaping
engine. `uv.lock` pins Pillow's version but cannot pin which wheel your platform
gets, so this varies by machine and not by version.

The tests are written to assert what holds either way, and are verified on macOS
arm64 without raqm and on Linux x86_64 with it. Windows is not verified. The
tolerances in `widths` and in `tests/test_units.py` were chosen from those two
data points; a third build could sit outside them. **If that is what you are
seeing, say so in the issue rather than adjusting a tolerance to fit** — a
number that moves whenever someone new turns up is not measuring anything.

## Rules the code will not tell you

- **Nothing under `series/` is ever committed.** Not a page, not a translation,
  not a sample. If a test needs a fixture, build it in `tmp_path`.
- **Skills stay general.** The test is *would this still be true of a different
  manga by a different artist?* Facts about one work live in that work's own
  files. A pronoun rule belongs in the skill; a character's name does not.
- **The least code that does the job.** No dependency, abstraction or config
  that is not needed yet. Several things here were deleted for being unread, and
  a smaller change with the same effect wins.
- **Artefacts and code are in English**, including comments, commit messages,
  and the notes a work accumulates.
- **The stages stay separate.** Editing a translation and re-rendering must not
  re-run detection or OCR. That split is what makes adjusting a line cost
  seconds instead of minutes, and it is easy to break by accident.
- **Read the image through `python -m manga_honyaku.sheet`**, never by resizing
  by hand. It caps width at the point past which reading stops getting easier
  and cost goes on rising.

## Sending a change

`master` takes pull requests only — direct pushes are refused for everyone,
including whoever owns the repository. CI runs the tests on your branch and on
your fork.

```sh
git switch -c what-it-does
uv run pytest
gh pr create
```

Commit messages here say what changed and why it was wrong before, in prose. The
log is the closest thing this project has to a design history, so a message that
only names the file is a message that will be read once.

## Reporting something

Issues are open. A rendered page that looks wrong is hard to act on without the
region's `size`, its `room`, and what the Japanese was — all three are in that
page's working file, and none of them require sending the artwork.
