---
name: asking-a-second-opinion
description: Use when one line or one term is stuck mid-translation — you want something looked up (what a slang term means now, whether a phrase has dated, what a reference is) or another model's read on a rendering (which Thai holds the register, whether the joke survives). Asks somebody who does not know the work, weighs the answer, and does not have to take it.
---

# Asking a second opinion

Turning to the desk next to you. Not a review pass, not a check, and not
somebody who will look at the page for you.

## What it is for

One question at a time, and the question is about **language**, not about this
manga:

- a line whose sense you have and whose register you do not
- slang, a set phrase, a joke that turns on a word — what Thai does in the same
  place, if it does anything
- a term you are about to settle in `glossary.md` and will be stuck with
- two renderings you cannot choose between

## What it is not for

**Not for looking.** It cannot see the page, and neither can the person you are
asking. Reading the artwork is yours and cannot be delegated — `AGENTS.md` is
explicit and the reason is expensive.

**Not for a chapter.** A whole chapter read against its source is
`proofread-against-source`, which is a pass with rules about what it may see.
This is a question, not a pass.

**Not for deciding.** See below; it is the whole of why this file exists.

## You asked. You decide.

**An answer here is evidence, not an instruction.** Weigh it against the work,
and put it down if it does not fit. Choosing against a second opinion is a normal
outcome and needs no justification beyond knowing the work better than the
answerer does.

This matters more than it sounds. Whoever you ask does not know the character,
has not read the chapter, and does not know what the page is doing — so what
comes back is **fluent, confident and context-free**, which is exactly the shape
of a wrong answer nobody catches. This repository has met that shape before, in
two directions: a term invented on a misreading and written into `glossary.md` as
fact, and a transliteration adopted because it looked like a word. Both read
perfectly well.

Warning signs that you are being led rather than helped: the answer changes the
character's register and you accept the new one; you find yourself justifying
your own line rather than judging theirs; you take a suggestion you would not
have written yourself and cannot say why it is better.

## Asking well

**Give the situation, not the story.** The person answering is more use knowing
nothing about the plot. Say who is speaking in terms of *how they speak* — their
standing relative to the listener, how formally they talk, whether they hedge.
Say what the line is doing: landing a joke, conceding, deflecting, giving an
order they expect to be obeyed. Quote the Japanese. Say what you have so far and
what is wrong with it.

**Ask for options with the difference named**, not for the answer. Three
renderings and what separates them beats one confident line, because the choosing
is yours and you need the axis to choose along.

**Never send the artwork, and never send the chapter.** The question travels; the
work does not.

## Two different asks, and they go to different places

**"Find this out" — a subagent.** When the question has an answer somebody could
look up: what a slang term currently means and to whom, whether a phrase has
dated, what a product or a reference is, how a convention is usually handled.
Send it with search and let it go looking; what comes back is information, and
you judge it the way you would judge anything you read.

**"What do you think" — another CLI, on a different model.** When the question is
judgement rather than fact: which of two renderings holds the register, whether
the joke survives, what a Thai speaker hears first. A different model is a
different set of priors, and that is the only thing that makes this worth more
than talking to yourself. It will go and look things up on its own if it needs
to; you do not have to arrange that. The invocations are in
[`../../../docs/agents.md`](../../../docs/agents.md).

Asking the same model you are already running is close to asking yourself twice —
it will usually hand back the answer you already have, and agreement obtained
that way is not evidence of anything.

**Disagreement is the useful outcome.** It says the line has an axis you had not
noticed, and it is worth the question even when you keep what you had.

## Afterwards

If the answer changed a term, it belongs in `glossary.md` with the reason — and
the reason is *why the Thai is right*, never *because it was suggested*. A row
that records who said so instead of what makes it true is a row nobody can
overturn later.

If it changed nothing, that is a result too and does not need writing down.
