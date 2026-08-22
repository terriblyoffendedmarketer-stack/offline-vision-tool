# server.py — Main HTTP server for the Offline Vision Tool
# Usage: python server.py [--port 9090] [--host 127.0.0.1]
# Requires: fastapi, uvicorn, Pillow, numpy, scikit-image
#
# Lazy-loads ML models on first use to keep idle RAM low (~50MB).
# Full model suite uses ~3GB when all loaded.

import argparse
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from models import ModelRegistry

app = FastAPI(
    title="Offline Vision Tool",
    description="Local image analysis without API costs",
    version="0.1.0",
)

registry = ModelRegistry()


# --- Request/Response schemas ---

class CompareRequest(BaseModel):
    before: str
    after: str
    resize: bool = True

class CompareResponse(BaseModel):
    ssim: float
    changed_regions: list[dict]
    elapsed_ms: float

class CheckRequest(BaseModel):
    image: str
    query: str

class CheckResponse(BaseModel):
    answer: str
    detail: str
    elapsed_ms: float

class ScoreRequest(BaseModel):
    image: str
    prompts: list[str]

class ScoreResponse(BaseModel):
    scores: list[float]
    best_match: str
    elapsed_ms: float

class CaptionRequest(BaseModel):
    image: str
    task: str = "caption"

class CaptionResponse(BaseModel):
    result: dict
    elapsed_ms: float

class HealthResponse(BaseModel):
    status: str
    models: dict[str, str]
    uptime_seconds: float


# --- Startup tracking ---

_start_time = time.time()


# --- Endpoints ---

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        models=registry.status(),
        uptime_seconds=round(time.time() - _start_time, 1),
    )


@app.post("/compare", response_model=CompareResponse)
async def compare(req: CompareRequest):
    before_path = Path(req.before).expanduser()
    after_path = Path(req.after).expanduser()

    if not before_path.exists():
        raise HTTPException(404, f"Before image not found: {req.before}")
    if not after_path.exists():
        raise HTTPException(404, f"After image not found: {req.after}")

    from endpoints.compare import run_compare
    return run_compare(before_path, after_path, resize=req.resize)


@app.post("/check", response_model=CheckResponse)
async def check(req: CheckRequest):
    image_path = Path(req.image).expanduser()
    if not image_path.exists():
        raise HTTPException(404, f"Image not found: {req.image}")

    from endpoints.check import run_check
    return run_check(registry, image_path, req.query)


@app.post("/score", response_model=ScoreResponse)
async def score(req: ScoreRequest):
    image_path = Path(req.image).expanduser()
    if not image_path.exists():
        raise HTTPException(404, f"Image not found: {req.image}")
    if not req.prompts:
        raise HTTPException(400, "At least one prompt required")

    from endpoints.score import run_score
    return run_score(registry, image_path, req.prompts)


@app.post("/caption", response_model=CaptionResponse)
async def caption(req: CaptionRequest):
    image_path = Path(req.image).expanduser()
    if not image_path.exists():
        raise HTTPException(404, f"Image not found: {req.image}")
    if req.task not in ("caption", "ocr", "detect"):
        raise HTTPException(400, f"Invalid task: {req.task}. Use caption, ocr, or detect")

    from endpoints.caption import run_caption
    return run_caption(registry, image_path, req.task)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Offline Vision Tool server")
    parser.add_argument("--port", type=int, default=9090)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    args = parser.parse_args()

    print(f"Starting Offline Vision Tool on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
