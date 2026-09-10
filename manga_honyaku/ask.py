"""Tool `ask`: put one question to a CLI running a different model, and print what it says.

Not a stage — it writes nothing and reads nothing of the work. Each CLI takes its
prompt differently; the differences are in `TOOLS` and guarded by a test.

What to ask, and what to do with the answer, is
`.claude/skills/asking-a-second-opinion/`.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys

TOOLS = {
    "codex": lambda q: ["codex", "exec", q],
    "opencode": lambda q: ["opencode", "run", q],
    "goose": lambda q: ["goose", "run", "--no-session", "-t", q],
    "agy": lambda q: [
        "agy", "--print-timeout", "10m", "--model", "gemini-3.8-flash-medium", f"-p={q}"
    ],
}

# Above any tool's own print-mode timeout, so theirs reports first.
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
    # Exiting clean with nothing said is how these refuse; the reason is on stderr.
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
