# manga-honyaku

The instructions for working here are in [`AGENTS.md`](AGENTS.md), which every
agent that touches this repository reads. This file adds nothing of its own; it
imports that one, because Claude Code looks for this name and not that one.

@AGENTS.md

The five method files that `AGENTS.md` names are skills here and are discovered
without being asked for, and so are the review passes in `.claude/agents/`. Both
directories are read by the other agents too — [`docs/agents.md`](docs/agents.md)
says how. Keep instructions out of this file: two copies of a rule are two rules
that will disagree.
