# endpoints/check.py — Free-form visual Q&A via SmolVLM-500M
# Ask any question about an image, get a text answer.
# Model loads on first call (~600MB RAM, ~4s per query on M2 MPS).
#
# Gotchas:
# - Originally used moondream2, but it's incompatible with Python 3.14 +
#   transformers 5.x + MPS (NaN in probability tensors, missing attributes).
# - SmolVLM-500M-Instruct works reliably on all three.

import time

import torch
from PIL import Image


def run_check(registry, image_path, query):
    t0 = time.perf_counter()

    vlm = registry.get_smolvlm()
    model = vlm["model"]
    processor = vlm["processor"]
    device = vlm["device"]

    image = Image.open(image_path).convert("RGB")

    messages = [{"role": "user", "content": [
        {"type": "image"},
        {"type": "text", "text": query},
    ]}]
    prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(text=prompt, images=[image], return_tensors="pt").to(device)

    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=200)

    answer = processor.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

    elapsed = (time.perf_counter() - t0) * 1000

    return {
        "answer": answer.strip(),
        "detail": answer.strip(),
        "elapsed_ms": round(elapsed, 1),
    }
