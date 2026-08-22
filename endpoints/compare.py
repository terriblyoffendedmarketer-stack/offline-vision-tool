# endpoints/compare.py — SSIM comparison with changed region detection
# No ML model needed — pure math using scikit-image.
# ~5ms per comparison on M2.

import time

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim


def run_compare(before_path, after_path, resize=True):
    t0 = time.perf_counter()

    img_before = Image.open(before_path).convert("RGB")
    img_after = Image.open(after_path).convert("RGB")

    if resize and img_before.size != img_after.size:
        img_after = img_after.resize(img_before.size, Image.LANCZOS)

    arr_before = np.array(img_before)
    arr_after = np.array(img_after)

    gray_before = np.mean(arr_before, axis=2)
    gray_after = np.mean(arr_after, axis=2)

    score, diff_map = ssim(gray_before, gray_after, full=True, data_range=255.0)

    changed_regions = _find_changed_regions(diff_map, threshold=0.5)

    elapsed = (time.perf_counter() - t0) * 1000

    return {
        "ssim": round(float(score), 4),
        "changed_regions": changed_regions,
        "elapsed_ms": round(elapsed, 1),
    }


def _find_changed_regions(diff_map, threshold=0.5, min_area=100):
    """Find bounding boxes of regions where SSIM dropped below threshold."""
    from skimage.measure import label, regionprops

    binary = diff_map < threshold
    labeled = label(binary)
    regions = []

    for prop in regionprops(labeled):
        if prop.area < min_area:
            continue
        y0, x0, y1, x1 = prop.bbox
        regions.append({
            "x": int(x0),
            "y": int(y0),
            "width": int(x1 - x0),
            "height": int(y1 - y0),
            "area": int(prop.area),
            "mean_diff": round(1.0 - float(diff_map[y0:y1, x0:x1].mean()), 3),
        })

    regions.sort(key=lambda r: r["area"], reverse=True)
    return regions[:20]
