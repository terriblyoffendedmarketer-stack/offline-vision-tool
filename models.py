# models.py — Lazy-loading model registry
# Tracks which models are loaded and loads them on first use.
# Keeps idle RAM at ~50MB; full suite is ~3GB.

import threading


class ModelRegistry:
    """Thread-safe lazy loader for ML models."""

    def __init__(self):
        self._models = {}
        self._locks = {
            "clip": threading.Lock(),
            "florence2": threading.Lock(),
            "moondream": threading.Lock(),
        }

    def status(self) -> dict[str, str]:
        return {
            "clip": "loaded" if "clip" in self._models else "not loaded",
            "florence2": "loaded" if "florence2" in self._models else "not loaded",
            "moondream": "loaded" if "moondream" in self._models else "not loaded",
            "ssim": "always available (no model needed)",
        }

    def get_clip(self):
        if "clip" not in self._models:
            with self._locks["clip"]:
                if "clip" not in self._models:
                    self._models["clip"] = _load_clip()
        return self._models["clip"]

    def get_florence2(self):
        if "florence2" not in self._models:
            with self._locks["florence2"]:
                if "florence2" not in self._models:
                    self._models["florence2"] = _load_florence2()
        return self._models["florence2"]

    def get_moondream(self):
        if "moondream" not in self._models:
            with self._locks["moondream"]:
                if "moondream" not in self._models:
                    self._models["moondream"] = _load_moondream()
        return self._models["moondream"]


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


def _load_florence2():
    from transformers import AutoModelForCausalLM, AutoProcessor
    import torch

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model_id = "microsoft/Florence-2-base"
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, trust_remote_code=True, torch_dtype=torch.float32
    ).to(device).eval()
    print(f"[models] Florence-2-base loaded on {device}")
    return {"model": model, "processor": processor, "device": device}


def _load_moondream():
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model_id = "vikhyatk/moondream2"
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, trust_remote_code=True, torch_dtype=torch.float32
    ).to(device).eval()
    print(f"[models] moondream2 loaded on {device}")
    return {"model": model, "tokenizer": tokenizer, "device": device}
