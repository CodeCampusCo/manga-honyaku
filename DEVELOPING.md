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
