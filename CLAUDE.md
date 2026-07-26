# manga-honyaku

A manga translation workflow. Code handles geometry — detection, OCR, text removal,
rendering. You handle comprehension — reading order, speaker attribution, and the
translation itself.

Design: `docs/specs/2026-07-26-design.md`. Read it before changing the pipeline or
the page-file schema.

## Working here

`raw/` is read-only. Everything derived goes to `work/` or `out/`.

Keep the stages separate: editing a translation and re-rendering must not re-run
detection or OCR.

Artifacts and code are written in English.

## Translating

Read the whole page before translating any of it, and keep `series/` current as you
go — the character and style files are what make later chapters consistent.

Record uncertainty in `questions` only when being wrong would change the output.

Before rendering a batch, diff every recorded `source` against a fresh OCR read of
its own box. It is cheap and it catches the one failure a re-read of the page will
not: lines written onto the wrong region ids. Three bubbles on X0048 held each
other's lines, and nothing else showed it.

When you decline a region, mark it `declined` with a reason. Never silently skip or
soften.
