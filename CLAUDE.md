# manga-honyaku

A manga translation workflow. Code handles geometry — detection, OCR, text removal,
rendering. You handle comprehension — reading order, speaker attribution, and the
translation itself.

Design: `docs/specs/2026-07-26-design.md`. Read it before changing the pipeline or
the page-file schema.

## Working here

One directory per work, and every stage takes it as its first argument:

    uv run python -m manga_honyaku.render series/<work>            # every page
    uv run python -m manga_honyaku.render series/<work> X0006      # one page
    uv run python -m manga_honyaku.render series/<work> 01/ch02    # a directory

`detect`, `annotate`, `prepare`, `clean` and `render` all read that way. Inside:
`pages/` is the translation and rebuilds from nothing, `build/` rebuilds from the
scans in seconds, `out/` is the finished pages, and the scans themselves are
read-only wherever `raw.txt` points.

Keep the stages separate: editing a translation and re-rendering must not re-run
detection or OCR.

Artifacts and code are written in English.

Look at pages through `python -m manga_honyaku.sheet` rather than opening them at
full size. It scales a batch to the largest size a reader actually keeps, so four
pages cost what one full-resolution page costs.

## Translating

Read the whole page before translating any of it, and keep the work's own notes
current as you go — `characters.md` and `style.md` are what make later chapters
consistent.

Record uncertainty in `questions` only when being wrong would change the output.

Before rendering a batch, diff every recorded `source` against a fresh OCR read of
its own box. It is cheap and it catches the one failure a re-read of the page will
not: lines written onto the wrong region ids. Three bubbles on X0048 held each
other's lines, and nothing else showed it.

When you decline a region, mark it `declined` with a reason. Never silently skip or
soften.
