# Manual redraw — design note for a tool that is not built yet

Status: a plan, agreed 2026-09-15, growing out of issue #20 and the testing
behind it. Nothing here is implemented. When the tool exists, this file shrinks
to whatever the code cannot say and the rest is deleted.

## The decision the plan rests on

Model-based repair of artwork is **for manual work only**. The automated
pipeline is untouched: `clean` keeps painting free-placement regions white and
glossing what it must, and no stage calls anything off this machine. In a manual
round the person reads the finished pages, names the panels that hurt, and the
agent fixes those spots — one at a time or in a short batch, at the person's
instruction, never on the agent's own initiative.

## What the testing chose

- **Service: Gemini direct API, `gemini-3-pro-image` at `image_size: "1K"`.**
  Not through Replicate (it upscales to 2K+ and charges the higher tier), not
  through an agent CLI (the agent rewrites the prompt and wanders the
  filesystem), not OpenAI (its mask is a soft hint, it redraws the whole frame,
  and its moderation refused manga artwork on the drawing, not the text), not
  xAI (equal at best, one moderation refusal).
- **Resolution does not change the bill.** The usage block reports 1120 image
  output tokens whether the request asks for 1K or 512, so `image_size` only
  changes the returned file. Pro also spends fewer total tokens than Flash.
  The Batch API halves the price if a 24-hour wait is acceptable.
- **The prompt that won is the short one**, and the word that matters is
  *lettering*, not *Japanese characters* — every service asked to erase
  "Japanese characters" dutifully left the Latin behind.

  > Erase the lettering. Replace each erased pixel with a continuation of what
  > is directly adjacent to it. Where what is adjacent is empty, leave it empty.
  > Invent nothing. Everything outside the lettering is unchanged.

## The method, as proven on six pages

1. **Send a crop, never a page.** Context band of 70 px around the region,
   scaled up first so the short side is at least 512 (one service refuses
   smaller; all get the same rule so the comparison stays honest).
2. **No mask.** On these instruction-edit APIs a mask does not bound anything.
3. **Fit the answer back by search, not by resizing and hoping:** scale within
   ±6 % in 13 steps, offset within ±12 px in steps of 3, scored on how well the
   parts nobody asked to change line up. Only then is anything written.
4. **Composite only the region's pixels** — the box grown by 6 px — into the
   page. The crop's edges never enter the page, so a seam at a crop edge is
   impossible by construction.
5. **A refusal is a per-region result, not a failure of the run.** Report it
   and keep going. In the six-page test one region of 27 was refused
   (`E005`, "flagged as sensitive") on artwork that had no lettering left in it.

## Interface

`tools/send_to_model.py` — outside `manga_honyaku/`, run by path, so it is not
a stage and `python -m manga_honyaku.<anything>` can never reach it.

```
uv run python tools/send_to_model.py series/<work> 05/08:F2            # plan only
uv run python tools/send_to_model.py series/<work> 05/08:F2 --send     # fire
uv run python tools/send_to_model.py series/<work> 05/08:F2 01/10:F11 --send
uv run python tools/send_to_model.py series/<work> 05/08               # one page
uv run python tools/send_to_model.py series/<work> --apply 05/08 ...   # offline
```

- **Patches are permanent:** `series/<work>/redraw/<page>/<id>.png`, full-page
  size with alpha outside the region. They cost money and survive no
  re-derivation, so they live beside the working file, not in `build/`.
- **`--apply` paints stored patches onto `build/<page>.clean.png`** and touches
  no network. It is what runs after `clean` has been re-run.
- **`--force` is required to overwrite an existing patch.**
- Every run writes a before/after pair of the page for the person to read.

## Guardrails, and the paths they close

The question asked of this design was *which steps an LLM could call by
accident*. Six paths were found; each guardrail below closes at least one.

| Path | Closed by |
| --- | --- |
| it sits in `manga_honyaku/`, so it reads as a stage | it lives in `tools/`, run by path |
| it appears in the stage table of `running-the-manga-pipeline` | it gets no row there; it gets its own row in `AGENTS.md` saying: manual tool, sends artwork off this machine |
| `running-a-chapter` runs it as part of a chapter | it refuses a directory argument; named regions or one page only |
| `audit`/`page-look` reports a list and the agent "fixes" all of it | a ceiling on regions per `--send` (10); beyond that an explicit `--yes` |
| `--apply` succeeding teaches it the command is safe | without `--send` nothing leaves the machine — the command prints what it *would* send and stops |
| it sees `clean` leave a white box and reaches for the tool | same as above: the first call anyone makes has no effect |

The filename says what it does: calling `send_to_model.py` is admitting that
artwork is about to leave the machine.

Also: the key is read from `.env` (gitignored), never printed, and scrubbed
from any error before display; the HTTP call is `urllib.request` from the
stdlib so no dependency is added; nothing reads the key or the network at
import time, so `uv run pytest` stays green and the pure parts — which regions
qualify, how nested boxes collapse, where a patch is written — are testable
offline.

## Open problems

- **Latin and symbols survive the erase.** `SP`, `in`, `☆` stayed even when a
  per-image prompt named them explicitly ("the letters S and P, the word in").
  Unsolved.
- **The regions that most need the cloud are the ones most likely to be
  refused.** The failure mode over figures is the same content filters guard.
  Expect refusals on exactly the hard cases; the fallback is what the pipeline
  already does.
- **Per-image price is unverified against a bill.** Published tiers disagree
  with each other; the usage block says the tiers do not differ. Read the
  invoice after the first real batch before believing any number here.
- Judging a redraw is a person looking at the page at reading size. Every
  automated verdict tried in issue #20's testing measured the ground, not the
  failure; do not build one into this tool.
