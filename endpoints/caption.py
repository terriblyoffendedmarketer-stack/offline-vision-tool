# endpoints/caption.py — Image captioning, OCR, and object detection via SmolVLM
# Supports three tasks: caption, ocr, detect.
# ~4s per image on M2 MPS (warm).
#
# Gotchas:
# - Originally used Florence-2-base, but it's incompatible with transformers 5.x
#   (Florence2LanguageConfig accesses forced_bos_token_id before super().__init__).
# - SmolVLM-500M handles all three tasks via appropriate prompting.

import time

import torch
from PIL import Image

TASK_PROMPTS = {
    "caption": "Describe this image in one detailed sentence.",
    "ocr": "Read and list all visible text in this image, exactly as shown.",
    "detect": "List every distinct object you can see in this image with its approximate position (left/right/center, top/bottom).",
}


def run_caption(registry, image_path, task):
    t0 = time.perf_counter()

    vlm = registry.get_smolvlm()
    model = vlm["model"]
    processor = vlm["processor"]
    device = vlm["device"]

    image = Image.open(image_path).convert("RGB")
    prompt_text = TASK_PROMPTS[task]

    messages = [{"role": "user", "content": [
        {"type": "image"},
        {"type": "text", "text": prompt_text},
    ]}]
    prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(text=prompt, images=[image], return_tensors="pt").to(device)

    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=500)

    answer = processor.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

    elapsed = (time.perf_counter() - t0) * 1000

    result = {}
    if task == "caption":
        result["caption"] = answer.strip()
    elif task == "ocr":
        result["text"] = answer.strip()
    elif task == "detect":
        result["objects"] = answer.strip()

    return {
        "result": result,
        "elapsed_ms": round(elapsed, 1),
    }
