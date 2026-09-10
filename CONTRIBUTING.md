# Contributing

Code handles geometry — detection, OCR, text removal, rendering. An LLM agent
handles comprehension — reading order, speaker attribution, and the translation
itself. Most of what looks like a missing feature is comprehension, and belongs
in a skill under `.claude/skills/` rather than in Python. That directory is the
method for every agent that works here, not for one of them.

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
- **Instructions live in `AGENTS.md`.** `CLAUDE.md` imports it and holds nothing
  of its own, and any file a tool needs points at `AGENTS.md` or at the pass
  prompts rather than repeating either. Never a copy: two copies of a rule are two
  rules, and they will disagree inside a chapter.
- **Artefacts and code are in English**, including comments, commit messages,
  and the notes a work accumulates.
- **The stages stay separate.** Editing a translation and re-rendering must not
  re-run detection or OCR. That split is what makes adjusting a line cost
  seconds instead of minutes, and it is easy to break by accident.
- **Read the image through `python -m manga_honyaku.sheet`**, never by resizing
  by hand. It caps width at the point past which reading stops getting easier
  and cost goes on rising.

## Other tools

Five CLIs can work in this repository and each finds the same instructions its
own way. Three files are committed so that nobody has to wire it up twice, and
**deleting one makes a tool quietly stop working**:

| File | For | What it does |
| --- | --- | --- |
| `CLAUDE.md` | Claude Code | imports `AGENTS.md`, which is the name it looks for |
| `.agents/skills.json` | `agy` | points it at `.claude/skills` — the one skills root that can be pointed |
| `opencode.json` | opencode | registers the three review passes as its own agents, with what each may read |

Codex and goose need nothing: they read `AGENTS.md` themselves and find
`.claude/skills` on their own, except that **Codex loads skills from
`~/.codex/skills` only**, so nothing committed here makes one fire by name in it.
That is why the table in `AGENTS.md` gives a path per row rather than a skill
name — a name means something only to a tool that has already scanned the
directory.

`opencode.json` is the only one that does more than point. Each pass names its
prompt as `{file:./.claude/agents/<pass>.md}`, resolved at load, so there is one
copy; `permission.read` then writes the passes table's third column as rules
opencode enforces. **General first, and the last match wins** — it evaluates with
`findLast`, so a trailing `"*": "allow"` undoes every deny above it and the config
loads without complaint enforcing nothing. It is a guard rail and not a sandbox:
`bash` stays open because `page-look` reaches a page through `sheet`.

**Asking another tool a question** is `uv run python -m manga_honyaku.ask`, which
knows how each one takes a prompt. Two things it cannot fix for you: `agy` loads
nothing at all from a folder it has not been trusted with — in a fresh clone it
answers that it has no instructions, which looks exactly like the wiring being
broken, and the first interactive run in the directory offers the trust — and in
print mode it cannot ask for a permission, so it denies one. A review pass needs
`command`, because each reaches a page through `sheet`; an allow-rule of
`command(uv)` in `~/.gemini/antigravity-cli/settings.json` is the whole of it, and
better than `--dangerously-skip-permissions`, which approves every tool a pass
calls for.

**Running a whole review pass elsewhere** is the same shape: each file in
`.claude/agents/` is a prompt with a header, so `codex exec "$(cat
.claude/agents/page-look.md)\n\nseries/<work>, pages X0006-X0012."` runs one.
opencode takes `--agent page-look` instead, because its config already holds them.
A pass run from a bare prompt keeps none of the tool restrictions its header
names — the `tools:` line is Claude Code doing that and no other tool reads it.

**Adding a tool.** Its instruction file points at `AGENTS.md` and never holds a
copy of it; a second copy is a second set of rules and the two will disagree
inside a chapter. A tool that reads `AGENTS.md` needs no file; one that reads a
name of its own gets a file that points there; one that reads nothing on its own
gets a config line naming it. If it has a skills root that can be configured,
point it at `.claude/skills`. If it has neither it needs nothing.

**A model that cannot see a page cannot do this work**, and no arrangement of
readers fixes that — it was tried, and what came back was a chapter translated
from somebody else's description of the artwork.

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
