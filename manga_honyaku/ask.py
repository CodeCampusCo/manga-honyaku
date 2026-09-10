"""Tool `ask`: put one question to a CLI running a different model, and print what it says.

Not a stage — it writes nothing and reads nothing of the work. It exists because
a second opinion on a line is worth having from a model that is not the one you
are already running, and every CLI that can give you one takes its prompt
differently:

    uv run python -m manga_honyaku.ask "…question…"
    uv run python -m manga_honyaku.ask --tool codex "…"
    uv run python -m manga_honyaku.ask --all "…"

`--all` asks every tool installed, which is the shape the answer is worth most in:
agreement between models says little, and where they part is where the line has an
axis you had not noticed.

**What comes back is evidence, not an instruction** — the skill beside this,
`asking-a-second-opinion`, is about what to do with it. Nothing here knows the
work, and nothing here should be sent the artwork.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys

# Each entry builds a whole argv from the question. They differ in ways that are
# easy to get wrong by hand, which is the reason this file exists:
#
# `agy`'s `-p` takes the next word as its prompt, so the prompt has to be
# attached to the flag or the run is made against a flag name. It also gives up
# after five minutes unless told otherwise, and it needs a model named.
#
# `goose` starts a session and keeps it unless told not to.
TOOLS = {
    "codex": lambda q: ["codex", "exec", q],
    "opencode": lambda q: ["opencode", "run", q],
    "goose": lambda q: ["goose", "run", "--no-session", "-t", q],
    "agy": lambda q: [
        "agy", "--print-timeout", "10m", "--model", "gemini-3.8-flash-medium", f"-p={q}"
    ],
}

# Long enough for a considered answer, short enough that a hung CLI does not hold
# a translation up. Each tool's own timeout, where it has one, is set under this.
TIMEOUT = 720


def installed() -> list[str]:
    return [name for name in TOOLS if shutil.which(name)]


def ask(tool: str, question: str) -> tuple[bool, str]:
    """What the tool said, or why it said nothing."""
    try:
        done = subprocess.run(
            TOOLS[tool](question), capture_output=True, text=True, timeout=TIMEOUT
        )
    except subprocess.TimeoutExpired:
        return False, f"gave up after {TIMEOUT // 60} minutes"
    answer = done.stdout.strip()
    if answer:
        return True, answer
    # A CLI that exits cleanly with nothing on stdout has usually refused
    # something — a permission it could not ask for, a workspace it does not
    # trust — and says so on stderr.
    return False, done.stderr.strip() or f"exited {done.returncode} with nothing to say"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("question", nargs="?", help="one question, in quotes")
    ap.add_argument("--tool", choices=sorted(TOOLS), help="which CLI to ask")
    ap.add_argument("--all", action="store_true", help="ask every CLI installed")
    ap.add_argument("--list", action="store_true", help="print which are installed and stop")
    args = ap.parse_args()

    here = installed()
    if args.list:
        for name in sorted(TOOLS):
            print(f"{name:10} {'installed' if name in here else '-'}")
        return
    if not args.question:
        raise SystemExit("ask what? give one question, in quotes")
    if not here:
        raise SystemExit(
            "none of " + ", ".join(sorted(TOOLS)) + " is on PATH — install one, or "
            "ask a person"
        )

    if args.tool and args.tool not in here:
        raise SystemExit(f"{args.tool} is not on PATH; installed: {', '.join(here)}")

    asked = here if args.all else [args.tool or here[0]]
    failed = 0
    for name in asked:
        got, said = ask(name, args.question)
        print(f"\n=== {name}\n{said}")
        failed += not got
    if failed == len(asked):
        sys.exit(1)


if __name__ == "__main__":
    main()
