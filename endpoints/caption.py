# endpoints/caption.py — Florence-2 captioning, OCR, and object detection
# Supports three tasks: caption, ocr, detect.
# ~100ms per image on M2.

import time

import torch
from PIL import Image

TASK_MAP = {
    "caption": "<CAPTION>",
    "ocr": "<OCR>",
    "detect": "<OD>",
}


def run_caption(registry, image_path, task):
    t0 = time.perf_counter()

    fl = registry.get_florence2()
    model = fl["model"]
    processor = fl["processor"]
    device = fl["device"]

    image = Image.open(image_path).convert("RGB")
    prompt = TASK_MAP[task]

    inputs = processor(text=prompt, images=image, return_tensors="pt").to(device)

    with torch.no_grad():
        generated = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=1024,
            num_beams=3,
        )

    decoded = processor.batch_decode(generated, skip_special_tokens=False)[0]
    parsed = processor.post_process_generation(decoded, task=prompt, image_size=image.size)

    elapsed = (time.perf_counter() - t0) * 1000

    result = {}
    if task == "caption":
        result["caption"] = parsed.get("<CAPTION>", decoded)
    elif task == "ocr":
        result["text"] = parsed.get("<OCR>", decoded)
    elif task == "detect":
        od = parsed.get("<OD>", {})
        result["objects"] = []
        if "bboxes" in od and "labels" in od:
            for bbox, label in zip(od["bboxes"], od["labels"]):
                result["objects"].append({"label": label, "bbox": bbox})

    return {
        "result": result,
        "elapsed_ms": round(elapsed, 1),
    }
