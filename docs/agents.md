# Calling another tool

How to put a prompt in front of a CLI other than the one you are in. Nothing
here is method — `AGENTS.md` is that.

Two things get asked of another tool: a question, when a line is stuck and a
different model's read is worth having (`.claude/skills/asking-a-second-opinion/`),
and a whole review pass, when you want one run somewhere else. Both are the same
invocation with a different prompt in it.

## A question

    codex exec "<question>"
    opencode run "<question>"
    goose run --no-session -t "<question>"
    agy --print-timeout 4m --model <model> -p="<question>"

`agy models` lists what that one can run.

## A review pass

Each file in `.claude/agents/` is a prompt with a header. Give it the work and
the pages and nothing else:

    codex exec "$(cat .claude/agents/page-look.md)

    series/<work>, pages X0006-X0012."

    opencode run --agent page-look "series/<work>, pages X0006-X0012."

opencode is the exception: `opencode.json` already holds the three passes as
agents of its own, so it takes the name rather than the file.

## What trips each one

**`agy`'s `-p` takes the next word as its prompt.** Written `agy -p --flag
"<prompt>"` it runs a turn whose whole prompt is `--flag`, and says so. The
prompt attaches to the flag — `-p="<prompt>"` — with other flags elsewhere.

**`agy` in print mode cannot ask for a permission, so it denies one** and ends
with a line naming what it wanted. A pass needs `command`, because each reaches a
page through `sheet`. Grant it narrowly — an allow-rule of `command(uv)` in
`~/.gemini/antigravity-cli/settings.json` — rather than with
`--dangerously-skip-permissions`, which approves every tool the pass calls for:
survivable for the two passes that change nothing, a poor trade for
`translate-pages`, which writes. That settings file belongs to one machine and
`.agents/` has no permissions file, so nothing this repository commits can grant
it; the machine's owner adds the line.

Print mode also gives up after five minutes. A span worth batching wants
`--print-timeout 20m`.

**`agy` loads nothing at all from a folder it has not been trusted with** —
`AGENTS.md` included. Asked in a fresh clone what instructions it has, it answers
that it has none, which looks exactly like the wiring being wrong. The first
interactive run in the directory offers the trust.

**Codex has no repository skills.** It loads them from `~/.codex/skills` only, so
nothing committed here makes a skill fire by name in it. That is why the table in
`AGENTS.md` gives a path per row rather than a skill name: a name means something
only to a tool that has already scanned the directory, a path means the same
thing to all of them.

**A pass run from a bare prompt has no tools taken away.** The `tools:` line in
its header is Claude Code doing that and no other tool reads it, so the
`Never opens` column of the passes table in `AGENTS.md` becomes yours to keep.
opencode is the exception, below.

## The three files this repository commits for other tools

Delete one and the tool it belongs to quietly stops working.

| File | For | What it does |
| --- | --- | --- |
| `CLAUDE.md` | Claude Code | imports `AGENTS.md`, which is the name it looks for |
| `.agents/skills.json` | `agy` | points it at `.claude/skills` — the one skills root that can be pointed |
| `opencode.json` | opencode | registers the three passes as its own agents, with what each may read |

`opencode.json` is the only one that does more than point. Each pass names its
prompt as `{file:./.claude/agents/<pass>.md}`, which opencode resolves at load —
a reference and not a copy, and it refuses the config if the file is missing.
`permission.read` then writes the passes table's third column as rules it
enforces: `proofread-against-source` denied `series/*/out/**`, `page-look` denied
`series/**` and allowed `series/*/out/**` back.

**General first, and the last match wins** — opencode evaluates with `findLast`,
so a trailing `"*": "allow"` undoes every deny above it, including opencode's own
default that asks before reading a `.env`. Written the other way round it loads
without complaint and enforces nothing.

It is a guard rail and not a sandbox: `bash` stays open because `page-look` views
pages through `sheet`, so a pass that shells out reads what the read rules deny.
It stops the accidental read, which is how the split actually gets broken.

## Adding a tool

**Its instruction file points at `AGENTS.md` and never holds a copy of it.** A
second copy is a second set of rules and the two will disagree inside a chapter.
A tool that reads `AGENTS.md` already needs no file; one that reads a name of its
own gets a file that points there; one that reads nothing on its own gets a
config line naming it. If it has a skills root that can be configured, point it
at `.claude/skills`. If it has neither it needs nothing — the table in
`AGENTS.md` is the fallback, and it is the part that has to keep working.

**A model that cannot see a page cannot do this work**, and no arrangement of
readers fixes that — it was tried, and what came back was a chapter translated
from somebody else's description of the artwork. Give the work to a tool whose
model has eyes.
