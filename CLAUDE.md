# Offline Vision Tool

Local Python service providing image analysis and UI verification without API costs. Runs as a background HTTP service on localhost, uses offline models that fit in 16GB unified memory (M2 MacBook Air).

## Status

**Phase:** Not started — project spec ready, needs implementation.
**Target machine:** M2 MacBook Air, 16GB unified memory.

## Goal

Replace expensive API-based vision (browser MCP screenshots cost 2,000-3,000 tokens each) with local models that run for free. Two use cases:
1. **General:** UI verification, visual regression testing, screenshot analysis for any project
2. **Specific:** Image quality scoring for the Comic Book Converter's benchmark (dithered output quality, text readability, contrast assessment)

## Architecture

Background HTTP service on `localhost:9090` with these endpoints:

### Endpoints

- `POST /compare` — Before/after SSIM comparison with changed region detection
  - Input: `{ "before": "path.png", "after": "path.png" }`
  - Output: `{ "ssim": 0.94, "changed_regions": [...] }`

- `POST /check` — Answer a question about an image (moondream)
  - Input: `{ "image": "path.png", "query": "is there an error message?" }`
  - Output: `{ "answer": "yes", "confidence": 0.92, "detail": "red text saying 'Failed to load'" }`

- `POST /score` — CLIP similarity scoring against text descriptions
  - Input: `{ "image": "path.png", "prompts": ["a blue button with white text", "a broken layout"] }`
  - Output: `{ "scores": [0.87, 0.12] }`

- `POST /caption` — Florence-2 image captioning and OCR
  - Input: `{ "image": "path.png", "task": "caption" | "ocr" | "detect" }`
  - Output: `{ "caption": "...", "objects": [...] }`

- `GET /health` — Check which models are loaded and ready

## Models

| Model | Size on disk | RAM when loaded | Speed (M2) | Purpose |
|-------|-------------|----------------|------------|---------|
| CLIP ViT-B/32 | 340 MB | ~400 MB | 20ms/image | Image-text similarity scoring |
| Florence-2-base | 450 MB | ~600 MB | 100ms/image | Captioning, OCR, object detection |
| moondream 2B | 1.7 GB | ~2 GB | 1-2s/image | Answer any question about an image |
| SSIM/LPIPS | ~50 MB | ~100 MB | 5ms/image | Perceptual quality comparison |

Total: ~3GB RAM when all loaded. Fits comfortably in 16GB.

## Use Cases

### General (any project)
- **UI verification:** Score a screenshot against "a properly laid out web page" vs "a broken page with overlapping elements"
- **Visual regression:** SSIM compare before/after code changes, flag regions that changed
- **Content check:** "Is there an error message visible?" "Does this form have 3 fields?"
- **Replace browser MCP screenshots:** Call localhost instead of burning 2-3k tokens per screenshot

### Comic Book Converter (Pass 2 of benchmark)
- Score dithered output: CLIP similarity to "sharp readable manga page" vs "muddy unreadable page"
- OCR check: Is text in speech bubbles still readable after dithering?
- Florence-2 detail detection: Are fine lines preserved or lost?
- Compare parameter combos with perceptual metrics beyond pure math

## Roadmap

1. [ ] Project setup — venv, requirements, basic Flask/FastAPI server
2. [ ] SSIM/LPIPS endpoint — pure math, no model download needed
3. [ ] CLIP integration — download model, load on startup, /score endpoint
4. [ ] Florence-2 integration — /caption and /ocr endpoints
5. [ ] moondream integration — /check endpoint for free-form questions
6. [ ] Lazy loading — only load models on first use to save RAM
7. [ ] CLI mode — `vision check image.png "is there an error?"` for quick one-offs
8. [ ] Auto-start (launchd) — always available at localhost:9090
9. [ ] MCP server wrapper — so Claude Code can call it directly as a tool

## Setup & Run

```bash
cd "Offline Vision Tool"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
# Service available at http://localhost:9090
```

## File Map

- `CLAUDE.md` — this file
- (files to be created during implementation)
