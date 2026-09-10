# Agents

Nothing in this file is method. The method is [`AGENTS.md`](../AGENTS.md) and the
files it names; this is only how each tool finds them, and what this
repository commits so that nobody has to wire it up again.

| Tool | Reads instructions from | Finds the method through | Committed for it |
| --- | --- | --- | --- |
| Claude Code | `CLAUDE.md`, which imports `AGENTS.md` | `.claude/skills/`, discovered | `CLAUDE.md` |
| Codex CLI (`codex`) | `AGENTS.md`, at the root and beside changed files | the paths in the `AGENTS.md` table | nothing |
| opencode | `AGENTS.md`, searched upward from where it starts | `.claude/skills/`, discovered | `opencode.json`, for the passes only |
| goose | `AGENTS.md`, or `.goosehints` | `.claude/skills/`, discovered | nothing |
| Antigravity CLI (`agy`) | `AGENTS.md`, or `.agents/rules/*.md` | the entries in `.agents/skills.json` | `.agents/skills.json` |

Codex and goose need nothing said to them at all, and opencode needs nothing to
find the method either — its file buys something else, two sections down. Nothing
in the last column is a copy: `CLAUDE.md` imports `AGENTS.md`, and the rest name
it, or the directory beside it, or the pass files. **A tool is added by naming a
file that already exists, or it is added by doing nothing.**

**Ask the tool, and prefer the question it can answer without a model.** Three of
the rows cost nothing to re-check, and those three are the ones to trust:

- **Codex**: `codex debug prompt-input` renders exactly what it would send. This
  repository's `AGENTS.md` is in it, whole, and the skill roots it lists are
  `~/.codex/skills`, that directory's `.system`, and the plugin caches — no root
  inside the repository. `codex doctor` names one config file, `~/.codex/config.toml`;
  a `.codex/config.toml` committed here changes nothing, which was tried.
- **goose**: `goose skills list` prints every one of this repository's skills, by
  path. Asked what instructions it had it answered `AGENTS.md`, but the provider
  configured on this machine is `claude-acp`, which brings context files of its
  own, so that half is not settled.
- **opencode**: `opencode agent list` prints every agent it has, with its merged
  permission rules in evaluation order, and no model runs. The three passes are
  there, at `mode: all`, with the rules below them. Its two neighbours,
  `opencode debug config` and `opencode debug skill`, both die in 1.1.28 with
  `fn3 is not a function`, so `agent list` is the whole of what can be asked;
  the instructions column is from an earlier session's answer.

Claude Code's row it answered itself. `agy`'s is from Antigravity's own
documentation, for the reason two sections down.

## Codex has no repository skills, and that is why the table names paths

Codex loads skills from `~/.codex/skills` only. A repository cannot register one,
and nothing committed here will make `japanese-to-thai-manga` fire by name. That
is why the index in `AGENTS.md` gives a file path per row rather than a skill
name: a name means something only to a tool that has already scanned the
directory, and a path means the same thing to all of them.

Anyone who wants them to load on their own can copy or link the directory into
`~/.codex/skills`. That is a decision about one machine and does not belong here.

## `agy` ignores a workspace it has not been trusted with

Antigravity loads no rules and no skills from a folder that is not trusted —
`AGENTS.md` included. Asked in a fresh clone what instructions it has, it answers
that it has none, which looks exactly like the wiring being wrong. The first
interactive run in the directory offers the trust; until somebody accepts it,
nothing in that row is in effect.

That much was read rather than watched, but the refusal itself was seen here:
Google's other CLI, which shares the `~/.gemini` home `agy` keeps its state
under, printed `Skipping project agents due to untrusted folder` in this
repository and listed nothing from it. The gate belongs to the family, not to one
binary.

## Running the review passes outside Claude Code

Each file in `.claude/agents/` is a prompt with a header. Any tool that takes a
prompt can run one — give it the work and the pages, and nothing else:

```sh
codex exec   "$(cat .claude/agents/page-look.md)

series/<work>, pages X0006-X0012."

opencode run "$(cat .claude/agents/page-look.md)

series/<work>, pages X0006-X0012."

agy --dangerously-skip-permissions -p="$(cat .claude/agents/page-look.md)

series/<work>, pages X0006-X0012."

goose run --no-session -t "$(cat .claude/agents/page-look.md)

series/<work>, pages X0006-X0012."

opencode run --agent page-look "series/<work>, pages X0006-X0012."
```

The last one reads nothing off the command line because opencode already has the
prompt; that is the next section.

**The `tools:` line in that header is Claude Code taking tools away, and no other
tool reads it.** Run from a bare prompt like this, a pass can open everything, so
the `Never opens` column of the table in `AGENTS.md` becomes yours to keep. Run
each in a session of its own, for the same reason. opencode is the one exception,
two sections down.

**`-p` takes the next word as the prompt, so the flag has to carry it.**
Written `agy -p --dangerously-skip-permissions "<prompt>"`, agy runs a turn whose
whole prompt is the word `--dangerously-skip-permissions` and tells you it has
done so; `-p="<prompt>"` with the other flags elsewhere is the form that works.

**`agy -p` cannot ask for a permission, so it denies one**, and the run ends with
a line naming what it wanted instead of doing the work. All three passes need
`command`, because each reaches a page through `sheet`.

Grant it narrowly and not with `--dangerously-skip-permissions`, which approves
every tool the pass calls for — survivable for the two that change nothing, a
poor trade for `translate-pages`, which writes. An allow-rule of `command(uv)` in
`~/.gemini/antigravity-cli/settings.json` is the whole of what the passes need.
That file is one machine's, and `.agents/` has no permissions file, so there is
nothing this repository can commit that grants it: the machine's owner adds the
line.

Print mode also gives up after five minutes; a span worth batching wants
`--print-timeout 20m`.

## opencode is the one tool that can be handed the split

`opencode.json` registers the three passes as agents of its own. Each names its
prompt as `{file:./.claude/agents/<pass>.md}`, which opencode resolves when it
loads the config — a reference and not a copy, and it fails loudly rather than
quietly: point one at a file that is not there and the config is refused with
`bad file reference`. What the file adds is the part a prompt cannot enforce:

    "permission": { "edit": "deny",
                    "read": { "series/*/out/**": "deny" } }

That is `proofread-against-source`, which may not open the rendered pages.
`page-look` is the pair of rules that leaves it only those — `series/**` denied,
then `series/*/out/**` allowed again.

**The order is general first, and the last match wins.** opencode evaluates with
`findLast`, so a rule written later beats a rule written earlier, and a trailing
`"*": "allow"` would undo everything above it — including opencode's own default
that asks before reading a `.env`. Written this way round, the defaults stay in
force and these rules only carve out of them. It was written the other way round
first, which loaded without complaint and enforced nothing; `opencode agent list`
prints the merged ruleset in evaluation order, and is how that was found.

`mode: "all"` is what makes each one both `--agent` on the command line and a
subagent the main one can call.

**It is a guard rail, not a sandbox.** `bash` is not restricted — a pass that
shells out to `cat` reads what the read rules deny, and it has to be able to
shell out, because `page-look` views pages through `sheet`. The rules stop the
accidental `read`, which is how the split actually gets broken; the prompt is
still where the discipline lives.

## Adding a tool

One rule: **its instruction file points at `AGENTS.md` and never holds a copy of
it.** A second copy is a second set of rules, and the two will disagree inside a
chapter. A tool that reads `AGENTS.md` already needs no file; one that reads a
name of its own gets a file that points there; one that reads nothing on its own
gets a config line naming `AGENTS.md`. If the tool has a skills root that can be
configured, point it at `.claude/skills` and add the row. If it has neither, it needs nothing — the table in `AGENTS.md` is
the fallback, and it is the part that has to keep working.

If it can be told what a named agent may read, it can also be handed the pass
prompts and their limits, the way `opencode.json` is. That is worth doing and it
is never the fallback: the passes have to work in a tool that offers none of it.

**A model that cannot see a page cannot do this work**, and no arrangement of
readers fixes that — it was tried, and what came back was a chapter translated
from somebody else's description of the artwork. Reading the page is the
translator's own job. Give the work to a tool whose model has eyes.
