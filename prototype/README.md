# Prototype

Throwaway scripts kept for reference, not part of the package.

## `annotate.py`

Runs RT-DETR alone and draws numbered boxes on a copy of a page. This is the
`detect` + `annotate` pair from the design, before either was factored into the
project.

It does **not** run standalone yet — it imports `core.ml` and `core.image` from an
upstream MangaTranslator checkout and must be run from that checkout's virtualenv
with its root on `PYTHONPATH`. Making it standalone is the first task of the spike.

```
PYTHONPATH=<upstream> <upstream>/.venv/bin/python annotate.py <page.jpg> <out.png> [conf]
```

Two behaviours in it were arrived at by trial and are deliberate:

- Region labels are drawn **outside** the box. Inside, the label covers the first
  character of the text the annotation exists to make readable, and the error is
  silent — the page still looks fine, the text just reads wrong.
- Only text-carrying classes are drawn. Drawing the enclosing bubble as well roughly
  doubles the box count and makes a dense page unreadable.

On Apple Silicon the model is pinned to CPU; the MPS backend fails on a float64
operation inside RT-DETR.
