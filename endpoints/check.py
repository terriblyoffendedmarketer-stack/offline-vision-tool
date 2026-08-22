# endpoints/check.py — Free-form visual Q&A via moondream2
# Ask any question about an image, get a text answer.
# Model loads on first call (~2GB RAM, 1-2s per query on M2).

import time

from PIL import Image


def run_check(registry, image_path, query):
    t0 = time.perf_counter()

    md = registry.get_moondream()
    model = md["model"]
    tokenizer = md["tokenizer"]

    image = Image.open(image_path).convert("RGB")

    enc_image = model.encode_image(image)
    answer = model.answer_question(enc_image, query, tokenizer)

    elapsed = (time.perf_counter() - t0) * 1000

    return {
        "answer": answer.strip(),
        "detail": answer.strip(),
        "elapsed_ms": round(elapsed, 1),
    }
