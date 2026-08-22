# Offline Vision Tool

Local Python service providing image analysis and UI verification without API costs. Runs as a background HTTP service on localhost, uses offline models that fit in 16GB unified memory (M2 MacBook Air).

## Status

**Phase:** Core implementation complete — all 4 endpoints working, CLI and MCP server built.
**Target machine:** M2 MacBook Air, 16GB unified memory.
**Models:** CLIP ViT-B/32 + SmolVLM-500M-Instruct + SSIM math. Total ~1.1GB RAM when loaded.

## Architecture

Background HTTP service on `localhost:9090` with lazy-loaded ML models.

### Models (simplified from original spec)

| Model | RAM when loaded | Speed (M2 MPS) | Purpose |
|-------|----------------|-----------------|---------|
| CLIP ViT-B/32 | ~400 MB | ~20ms/image | Image-text similarity scoring |
| SmolVLM-500M | ~600 MB | ~4s/query | Q&A, captioning, OCR, object detection |
| SSIM | ~0 MB | ~5ms/pair | Perceptual image comparison |

Original plan included Florence-2 and moondream2, but both are incompatible with
Python 3.14 + transformers 5.x. SmolVLM handles all their tasks. See learnings.md.

### Endpoints

- `POST /compare` — SSIM comparison with changed region detection
- `POST /check` — Free-form visual Q&A (SmolVLM)
- `POST /score` — CLIP similarity scoring against text prompts
- `POST /caption` — Captioning, OCR, object detection (SmolVLM)
- `GET /health` — Model status and uptime

## Roadmap

1. [x] Project setup — venv, requirements, FastAPI server
2. [x] SSIM/compare endpoint — pure math, ~5ms per comparison
3. [x] CLIP /score endpoint — similarity scoring, ~20ms warm
4. [x] SmolVLM /check endpoint — visual Q&A, ~4s warm
5. [x] SmolVLM /caption endpoint — captioning/OCR/detect
6. [x] Lazy loading — models load on first use, idle RAM ~50MB
7. [x] CLI mode — `python cli.py check image.png "is there an error?"`
8. [x] MCP server wrapper — Claude Code can call vision tools directly
9. [x] Auto-start (launchd) — run `bash install.sh`
10. [x] Global CLAUDE.md integration — tell Claude to prefer local vision tools
11. [x] Permission rules — auto-allow curl to localhost:9090
12. [x] Portability — dynamic paths, setup_models.py, no hardcoded user dirs

## Setup & Run

```bash
cd "Offline Vision Tool"
source venv/bin/activate
python server.py
# Server at http://localhost:9090
```

### Full install (auto-start + Claude integration)

```bash
bash install.sh
```

## File Map

- `CLAUDE.md` — this file
- `server.py` — FastAPI HTTP server, all endpoint routing
- `models.py` — Lazy-loading model registry (CLIP, SmolVLM)
- `endpoints/compare.py` — SSIM comparison with region detection
- `endpoints/check.py` — SmolVLM visual Q&A
- `endpoints/score.py` — CLIP similarity scoring
- `endpoints/caption.py` — SmolVLM captioning/OCR/detect
- `cli.py` — Command-line interface for quick queries
- `mcp_server.py` — MCP server for Claude Code integration
- `install.sh` — One-step installer (venv, models, launchd, MCP registration)
- `setup_models.py` — Pre-downloads CLIP and SmolVLM models (~1GB)
- `requirements.txt` — Python dependencies
- `learnings.md` — Bug fixes and compatibility discoveries
