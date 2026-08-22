# endpoints/score.py — CLIP similarity scoring
# Scores an image against text prompts. Fast (~20ms on M2).
# Returns which prompt best describes the image.

import time

import torch
from PIL import Image


def run_score(registry, image_path, prompts):
    t0 = time.perf_counter()

    clip = registry.get_clip()
    model = clip["model"]
    preprocess = clip["preprocess"]
    tokenizer = clip["tokenizer"]
    device = clip["device"]

    image = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(device)
    text = tokenizer(prompts).to(device)

    with torch.no_grad():
        image_features = model.encode_image(image)
        text_features = model.encode_text(text)

        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)

        similarity = (image_features @ text_features.T).squeeze(0)
        scores = similarity.cpu().tolist()

    best_idx = scores.index(max(scores))
    elapsed = (time.perf_counter() - t0) * 1000

    return {
        "scores": [round(s, 4) for s in scores],
        "best_match": prompts[best_idx],
        "elapsed_ms": round(elapsed, 1),
    }
