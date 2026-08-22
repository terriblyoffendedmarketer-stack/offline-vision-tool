# models.py — Lazy-loading model registry
# Tracks which models are loaded and loads them on first use.
# Keeps idle RAM at ~50MB; full suite is ~2GB.
#
# Gotchas:
# - moondream2 is incompatible with Python 3.14 + transformers 5.x + MPS.
#   Replaced with SmolVLM-500M-Instruct which works on all three.
# - Florence-2 uses trust_remote_code=True (custom architecture).
# - CLIP uses open_clip, not HuggingFace transformers.

import threading


class ModelRegistry:
    """Thread-safe lazy loader for ML models."""

    def __init__(self):
        self._models = {}
        self._locks = {
            "clip": threading.Lock(),
            "smolvlm": threading.Lock(),
        }

    def status(self) -> dict[str, str]:
        return {
            "clip": "loaded" if "clip" in self._models else "not loaded",
            "smolvlm": "loaded" if "smolvlm" in self._models else "not loaded",
            "ssim": "always available (no model needed)",
        }

    def get_clip(self):
        if "clip" not in self._models:
            with self._locks["clip"]:
                if "clip" not in self._models:
                    self._models["clip"] = _load_clip()
        return self._models["clip"]

    def get_smolvlm(self):
        if "smolvlm" not in self._models:
            with self._locks["smolvlm"]:
                if "smolvlm" not in self._models:
                    self._models["smolvlm"] = _load_smolvlm()
        return self._models["smolvlm"]


def _load_clip():
    import open_clip
    import torch

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k"
    )
    model = model.to(device).eval()
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    print(f"[models] CLIP ViT-B/32 loaded on {device}")
    return {"model": model, "preprocess": preprocess, "tokenizer": tokenizer, "device": device}


def _load_smolvlm():
    from transformers import AutoModelForImageTextToText, AutoProcessor
    import torch

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model_id = "HuggingFaceTB/SmolVLM-500M-Instruct"
    processor = AutoProcessor.from_pretrained(model_id)
    model = AutoModelForImageTextToText.from_pretrained(
        model_id, dtype=torch.float32
    ).to(device).eval()
    print(f"[models] SmolVLM-500M-Instruct loaded on {device}")
    return {"model": model, "processor": processor, "device": device}
