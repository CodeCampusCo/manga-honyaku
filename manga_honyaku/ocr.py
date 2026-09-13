"""Read the Japanese out of a region, for `prepare`.

Weights from `kha-white/manga-ocr-base` (Apache-2.0), referenced and never
vendored, like the detector. The `manga_ocr` package around them is not used:
it is a thin wrapper, and its tokenizer needs mecab and a fast-tokenizer
conversion that recent transformers will not do without extra dependencies.

None of that is needed to *decode*. The vocabulary is one character per line
with no word pieces, so turning generated ids back into text is a lookup and a
join. mecab only ever mattered for splitting input text, which nothing here does.
"""

from __future__ import annotations

import os

import torch
from huggingface_hub import hf_hub_download
from PIL import Image
from transformers import VisionEncoderDecoderModel, ViTImageProcessor

READER = os.environ.get("MANGA_HONYAKU_OCR", "kha-white/manga-ocr-base")

# Kept on CPU with the detector, for the reason in detect.py. Both models are
# small and run once per page.
DEVICE = torch.device("cpu")

SPECIAL = {"[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"}

# The crop is grown before reading: free-floating boxes are tight enough to clip
# the first glyph. Unlike erasing, where any margin cuts into artwork, a wider
# crop costs nothing here.
MARGIN = 0.05

# Below this, open the box on the scan. Measured over one chapter: 65 of the 66
# regions at or above it needed no correction, and 52 of the 96 below did.
SURE = 0.8


def load_reader():
    model = VisionEncoderDecoderModel.from_pretrained(READER).to(DEVICE).eval()
    processor = ViTImageProcessor.from_pretrained(READER)
    vocab = open(hf_hub_download(READER, "vocab.txt")).read().splitlines()
    return model, processor, vocab


def read(image: Image.Image, box: list[float], reader) -> tuple[str, float]:
    """The Japanese in this box, and how sure the reader was of its worst character.

    The worst rather than the mean: the failure is one character read as another,
    and a mean over a dozen confident ones buries it.
    """
    model, processor, vocab = reader
    x1, y1, x2, y2 = box
    pad = MARGIN * min(x2 - x1, y2 - y1)
    crop = image.crop(
        (
            max(x1 - pad, 0),
            max(y1 - pad, 0),
            min(x2 + pad, image.width),
            min(y2 + pad, image.height),
        )
    )
    pixels = processor(crop, return_tensors="pt").pixel_values.to(DEVICE)
    with torch.inference_mode():
        got = model.generate(
            pixels, max_length=64, output_scores=True, return_dict_in_generate=True
        )
    ids = got.sequences[0].tolist()
    # `scores[i]` is the distribution `ids[i + 1]` was drawn from: the first id is
    # the decoder's start token and was never chosen.
    chosen = [
        torch.softmax(step[0], -1)[token].item()
        for step, token in zip(got.scores, ids[1:])
        if vocab[token] not in SPECIAL
    ]
    text = "".join(vocab[i] for i in ids if vocab[i] not in SPECIAL)
    return text, round(min(chosen), 3) if chosen else 0.0
