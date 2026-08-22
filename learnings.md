# Learnings Log

Bugs, fixes, and non-obvious discoveries. Format: `what broke | why | what fixed it`

## 2026-08-22 — Initial setup

- Python 3.14.6 on this machine | Very new, may cause compatibility issues with torch/transformers | Monitoring — core deps (fastapi, scikit-image, numpy) all installed fine
- skimage SSIM with float arrays needs explicit `data_range=255.0` | np.mean() converts uint8 to float, skimage refuses without data_range on floats | Added data_range=255.0 to ssim() call
- FastAPI TestClient now requires `httpx2` not `httpx` (starlette change) | starlette.testclient imports httpx2 in newer versions | pip install httpx2
- First SSIM call takes ~9.4s (scikit-image import overhead), subsequent calls ~5ms | Module import is lazy but heavy | Expected, not a bug — just cold-start cost
- CLIP ViT-B/32 first download is ~340MB, takes ~57s | Downloads from HuggingFace Hub | Cached after first run, subsequent loads ~2-3s
- PyTorch 2.13.0 MPS works fine on M2 MacBook Air | No compatibility issues with Python 3.14 | MPS acceleration available for all models
- moondream2 totally broken on Python 3.14 + transformers 5.x + MPS | Three separate issues: (1) `all_tied_weights_keys` missing in custom model code, (2) NaN in probability tensors on MPS, (3) hardcoded MPS ops even when device is CPU | Replaced with SmolVLM-500M-Instruct
- moondream dedicated package (`pip install moondream`) uses kestrel runtime | kestrel-mps-torch-ext doesn't support PyTorch 2.13 yet | Not usable until kestrel updates
- Florence-2-base also broken with transformers 5.x | `Florence2LanguageConfig` accesses `forced_bos_token_id` before `super().__init__()` is called | Replaced with SmolVLM for caption/OCR/detect tasks
- SmolVLM-500M-Instruct requires `num2words` package | ImportError at processor init | `pip install num2words`
- SmolVLM-500M-Instruct works reliably on Python 3.14 + transformers 5.x + MPS | ~600MB RAM, ~4s/query warm, handles Q&A, caption, OCR | Best small VLM for this stack
- Simplified from 4 models to 2 (CLIP + SmolVLM) + SSIM math | Total RAM ~1.1GB vs original 3GB estimate | Fewer compatibility headaches, still covers all use cases
