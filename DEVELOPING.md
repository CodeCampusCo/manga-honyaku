# Developing the tool

**If you are here to translate a chapter, this file is not for you.** Nothing in
it is method, and one thing in it will mislead you: it says the translated pages
are disposable, which is true of the project and not of your chapter. Go back to
`AGENTS.md` and the work's `handoff.md`.

This is for whoever is changing the tool itself. `CONTRIBUTING.md` is how to
change the code; this is how the change gets decided, written down because most
of it was learned by getting it wrong.

**The pages are not the product.** This is a general manga translation tool that
happens to have chapters of one work lying around it. Everything under
`series/*/pages`, `build/` and `out/` can be deleted at any time and will be, and
the whole work re-run from the first chapter once the tooling settles. Correctness
comes from re-running a better tool, never from repairing an output by hand.

## The loop

1. **Find and gather.** Read the code, run the tools, measure. Bring back what is
   there, not what to do about it.
2. **Put it up for a decision** — ranked, with the evidence, and with a
   recommendation. One list, not a running commentary.
3. **The direction comes from the person, not from the finding.** A defect that is
   real can still be out of scope, and scope is not yours to decide.
4. **Then change it**, and rebuild rather than preserve. Nothing here is owed its
   current shape.
5. **Then audit with a fresh context.** A subagent that has never seen the
   conversation reads what you wrote and reports what it understood, what was
   ambiguous, and what two files say differently. Sit it an exam: *if you had to
   do this, would you know how?* Answering well from memory of the discussion is
   the failure this catches.

**Do not turn every remark into a commit.** A question is usually a question.
Collect, and change once the decision stops moving.

## Three places a thing can go, and they are not interchangeable

- **The conversation** is where the system gets designed. Most of what is said
  here is thinking, not specification, and belongs in neither of the other two.
- **`AGENTS.md`** is the always-loaded index: the skills table, the `role` and
  `status` contracts, the working file's fields, where the passes go. It is the
  first thing that grows when something is unclear, and growing it is almost
  always the wrong fix — there is a skill or an agent whose job that already is.
- **A skill** is read by a model about to do one thing. Invocation detail lives
  here, never in `AGENTS.md`.

Deciding which of the three a new paragraph belongs to is the judgement this
project asks for most often.

## Writing a skill

**State what is, not why it was written that way.** The reasoning that produced a
rule is not the rule, and leaving it in costs length now and contradicts a future
edit later. This alone shortens a file by a third without losing anything.

**Hand the model only the decisions it actually has to make.** Every extra
alternative is a chance to pick wrong.

**No page citations.** A skill that names `06/14` of one work points at nothing
the next time it is used, and this is a generic tool.

**No number that cannot be reproduced.** A measurement doing argumentative work
with no path back to how it was taken is a defect in its own right, whether or not
it is true — this repository has already carried a justification that was invented
once and then copied forward through several whole-file rewrites, because
rewriting a file re-copies it rather than re-checking it. Cite it or cut it and
keep the rule.

## Guard in the code, report to the model

Rules written in prose produce compliance you cannot distinguish from luck. Put
the guard where it can be observed instead: let the tool notice what went wrong
and **say so in its output**, and let the run continue.

**Do not pre-empt.** Forbidding a mistake in advance buys a silent result — you
never learn whether it would have happened, or whether the model simply obeyed
that day. Every check in this repository earned its place by a failure reaching a
rendered page while nothing said so.

A worklist has to be able to clear, or it stops being read. If the only way to
answer a line is to do the work, the list is load-bearing; if it can be discharged
by accepting it, it is a convenience and something else must carry the weight.

## Before choosing a constant, measure

Sweep it, find the knee, and write down what was measured and on what. A threshold
picked by argument is a threshold nobody can revisit. Where a value has an obvious
name, check whether that name is already taken — two constants called the same
thing in one codebase will be confused, and one of them will be set in the wrong
file by someone who read the other's documentation.

## Verify before relaying

Other sessions and subagents report confidently and are sometimes wrong, in both
directions: a real finding described backwards, or a precedent that turns out to
be one case counted twice. **Check every claim against the code or the file before
passing it on**, and say plainly which parts did not survive the check. This
applies to your own earlier statements with more force, not less.

Never supply a reason you have not confirmed. Inventing a plausible justification
for a conclusion is the failure mode this project is least able to detect, because
the justification then reads like a decision somebody made.

## Working with a translating session

Each chapter is translated by a session that has not translated the one before it.
That is the test: whether the repository carries the method on its own.

**Brief it thinly.** Name the chapter, point at `AGENTS.md` and the work's
`handoff.md`, and stop. Repeating the method in the message makes the run prove
nothing.

**Ask for friction as it happens**, not at the end: what stalled, what two
instructions pulled against each other, what had to be guessed, and any script
improvised — especially a second time, which is a tool that has not been written.

Three questions have been worth more than the rest:

- *What did you find by reading, versus what did you wish existed?* A tool that
  did the job but was found late is a documentation defect, counted the same as a
  missing feature.
- *What felt like the job rather than like an obstacle?* The largest piece of hand
  work in a chapter went unreported twice because it did not feel like friction.
- *Where was a file wrong about the tools?* A command that does not do what the
  file says is a first-class finding, not a nuisance to route around.

**Keep it to the current chapter.** A finding that only affects a chapter already
translated changes nothing and crowds out the ones that change the next.

## What not to do

- Repair a rendered page by hand instead of fixing what produced it.
- Add to `AGENTS.md` because something was unclear.
- Patch what another session produced, unless it will mislead the next one.
- Explain, in a file, why the file says what it says.
- Report a subagent's finding without checking it.

## How each tool finds the method

Nothing in this section is method. The method is `AGENTS.md` and the five files
it names; this is only how each tool finds them, and what this repository commits
so that nobody has to wire it up again.

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
- **goose**: `goose skills list` prints all five of this repository's skills, by
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

### Codex has no repository skills, and that is why the table names paths

Codex loads skills from `~/.codex/skills` only. A repository cannot register one,
and nothing committed here will make `japanese-to-thai-manga` fire by name. That
is why the index in `AGENTS.md` gives a file path per row rather than a skill
name: a name means something only to a tool that has already scanned the
directory, and a path means the same thing to all of them.

Anyone who wants them to load on their own can copy or link the directory into
`~/.codex/skills`. That is a decision about one machine and does not belong here.

### `agy` ignores a workspace it has not been trusted with

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

### Running the review passes outside Claude Code

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
tool reads it.** Run from a bare prompt like this, a pass can open everything, and
what each pass cannot see is the whole value of the split — so it becomes yours to
keep: `page-look` must not open the Japanese or the notes, and
`proofread-against-source` must not open `out/`. A proofreader that has seen the
rendered page has stopped being the one pass that catches a line which is fluent,
sits well, and says the opposite of the original.

Run each in a session of its own, for the same reason. opencode is the one
exception to the paragraph above, and the section after next says what it can do
instead.

**`-p` takes the next word as the prompt, so the flag has to carry it.**
Written `agy -p --dangerously-skip-permissions "<prompt>"`, agy runs a turn whose
whole prompt is the word `--dangerously-skip-permissions` and tells you it has
done so; `-p="<prompt>"` with the other flags elsewhere is the form that works.

**`agy -p` cannot ask, so it denies**, and a run that needs a permission ends
with a line naming the one it wanted instead of doing the work. All three passes
need `command`, because every one of them reaches a page through `sheet`. What
agy runs without asking is a list of allow-rules in
`~/.gemini/antigravity-cli/settings.json`, which is one person's machine and does
not travel; `.agents/` registers skills, plugins, rules and hooks and has no
permissions file, so there is nothing this repository can commit that grants it.

**Name the permission rather than reaching for the flag.** `--dangerously-skip-permissions`
approves every tool the pass calls for, and then the prompt is the only thing
holding it back — survivable for `page-look` and `proofread-against-source`, which
report and change nothing, and a poor trade for `translate-pages`, which writes,
and run that way writes unwatched. An allow-rule of `command(uv)` is the whole of
what the passes actually need, and it is the machine owner's line to add.

**A prompt that stays inside agy's own tools needs no permission at all.** Asked
to view one image with its file-viewing tool and told not to shell out, agy 1.1.28
answered correctly on `gemini-3.8-flash-medium`, unprivileged, with clean text on
stdout. Asked the same question in a way that let it reach for a shell, it stopped
on `command`. Which way a prompt sends it is a property of the prompt, and worth
knowing before granting anything.

Print mode also gives up after five minutes; a span long enough to be worth
batching wants `--print-timeout 20m`.

### opencode is the one tool that can be handed the split

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

### Reading a page on a model that cannot see

`AGENTS.md` says to stop and ask rather than route around it. This is what to
offer. Two readers were measured on the same spread, with the same prompt, and
both transcribed all ten balloons correctly:

```sh
# A — Antigravity CLI, so the page goes to Google
agy --print-timeout 4m --model gemini-3.8-flash-medium \
    -p="Using your own file-viewing tool and no shell commands, open <sheet> and ..."

# B — a one-shot Claude session, so the page goes to Anthropic
claude -p "Read the image at <sheet> and ..."
```

**Neither needs a permission granted**, and neither needs the page prepared any
differently — build the sheet with `sheet` first and hand over the path. `claude
-p` reported that it had no Bash and so could not crop, which is the shape to
aim for: the caller does the geometry, the reader only looks. A reader with no
tools cannot wander.

One difference looked decisive and was not. Asked the same question, Claude
returned the ruby on `嘘だろオイ` as `嘘(うそ)` and Gemini dropped it — but asked
again with the word *furigana* in the prompt, Gemini returned it too. **Neither
reader volunteers ruby; one of them happened to.** So name it, every sheet, as
its own line item, whichever reader is being used. Furigana is what OCR loses and
the reason a page is looked at at all, and a name that arrives without it goes
into `characters.md` wrong and stays wrong for the series.

`agy` answered in about a minute, `claude -p` in forty seconds, and `agy`'s `-p`
needs the form two sections up or it runs the wrong prompt entirely.

**Ask for what the OCR could not give.** `prepare` has already transcribed every
box, so a reader asked to transcribe returns what the working file holds and
proves nothing. Ask instead for **who speaks which region id**, **the order the
panels and the boxes in them are read**, and **any lettering outside a box** —
furigana on a name above all, which is what puts a character's name into Thai
wrongly for a whole series.

And say plainly what each option costs the person, including the third one: a
page not sent anywhere, read aloud to you by whoever asked for the chapter.

### Adding a tool

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
