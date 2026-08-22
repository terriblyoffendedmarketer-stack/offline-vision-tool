# Offline Vision Tool

**Understand images on your Mac without sending them to the cloud.** No API keys, no per-image charges, no data leaving your machine.

This is a local service that runs in the background on your Mac. It uses small AI models (~1GB total) to answer questions about images, compare screenshots, read text, and score how well an image matches a description. Everything runs on your hardware using Apple's Metal GPU acceleration.

## Why this exists

AI assistants like Claude burn thousands of tokens every time they look at a screenshot. That costs money and fills up the conversation context. This tool gives them a local alternative — instead of encoding a full image into the conversation, they call this service and get a short text answer back. Same information, ~95% fewer tokens.

It was built for [Claude Code](https://docs.anthropic.com/en/docs/claude-code), but the HTTP API works with anything.

## What it can do

| Tool | What it does | Speed | Example |
|------|-------------|-------|---------|
| **check** | Answer any question about an image | ~4s | "Is there an error message on this page?" |
| **score** | Rate how well an image matches text descriptions | ~140ms | Score against "clean layout" vs "broken layout" |
| **compare** | Find differences between two images | ~5ms | Before/after screenshots of a UI change |
| **caption** | Describe an image, read text (OCR), or list objects | ~4s | "Read all visible text in this screenshot" |

## Setup (one command)

```bash
git clone https://github.com/terriblyoffendedmarketer-stack/offline-vision-tool.git
cd offline-vision-tool
bash install.sh
```

That's it. The installer:
- Creates a Python environment and installs everything
- Downloads the AI models (~1GB, one-time)
- Sets up the service to start automatically when you log in
- Registers with Claude Code so the tools show up in every session

**Requirements:** macOS with Apple Silicon (M1/M2/M3/M4), Python 3.10+, ~2GB free disk space.

## How to use it

### With Claude Code (automatic)

Once installed, Claude Code sees four new tools: `vision_check`, `vision_score`, `vision_compare`, `vision_caption`. It uses them automatically instead of taking expensive screenshots. You don't need to do anything different — the savings happen in the background.

### From the command line

```bash
# Ask a question about an image
python cli.py check screenshot.png "Is there an error message visible?"

# Score an image against descriptions
python cli.py score page.png "a clean, well-laid-out page" "a broken page with overlapping elements"

# Compare two screenshots
python cli.py compare before.png after.png

# Read text from an image
python cli.py caption screenshot.png --task ocr

# Check if the server is running
python cli.py health
```

### From any app (HTTP API)

The service runs at `http://localhost:9090`. Send JSON requests:

```bash
# Ask about an image
curl -X POST http://localhost:9090/check \
  -H "Content-Type: application/json" \
  -d '{"image": "/path/to/screenshot.png", "query": "Is there an error?"}'

# Compare two images
curl -X POST http://localhost:9090/compare \
  -H "Content-Type: application/json" \
  -d '{"before": "/path/to/before.png", "after": "/path/to/after.png"}'
```

Full API docs at `http://localhost:9090/docs` when the server is running.

## The models

Two small models handle everything:

- **CLIP ViT-B/32** (~400MB RAM) — Scores how similar an image is to a text description. Very fast.
- **SmolVLM-500M-Instruct** (~600MB RAM) — Answers questions, writes captions, reads text. A small but capable vision-language model.
- **SSIM** (no model needed) — Mathematical image comparison. Finds exactly which regions changed between two images.

Models load on demand. The service idles at ~50MB and only loads a model when you first use it.

## What we tried and what broke

We originally planned to use moondream2 and Florence-2, but both are incompatible with the current Python + PyTorch stack:

- **moondream2**: NaN errors on Apple Silicon, missing attributes in transformers 5.x, hardcoded GPU ops
- **Florence-2**: Config initialization bug in transformers 5.x

SmolVLM-500M turned out to handle all their tasks reliably. Full details in [learnings.md](learnings.md).

## Known limitations

- **Small text**: OCR misses fine print and small labels. For precise text reading, ask a specific question via `/check` instead of using `/caption --task ocr`.
- **Counting**: The model approximates when counting objects ("about five" when there are three). Don't rely on exact counts.
- **Cold start**: First query after a model loads takes 4-8 seconds. After that, queries are fast.
- **Not Claude-level vision**: These are small local models. For complex visual reasoning (subtle CSS bugs, intricate layouts), Claude's built-in vision is still better. This tool handles the 80% of cases where you just need a quick answer.

## Uninstall

```bash
launchctl unload ~/Library/LaunchAgents/com.local.vision-tool.plist
rm ~/Library/LaunchAgents/com.local.vision-tool.plist
claude mcp remove vision-tool
```

## Project structure

```
server.py          — HTTP server (FastAPI on port 9090)
models.py          — Lazy-loads CLIP and SmolVLM on first use
endpoints/         — One file per endpoint (check, score, compare, caption)
cli.py             — Command-line interface
mcp_server.py      — Makes tools available in Claude Code
install.sh         — One-step setup (venv, models, launchd, MCP)
setup_models.py    — Pre-downloads models so first queries aren't slow
learnings.md       — Every bug hit and how it was fixed
CLAUDE.md          — AI-facing project docs (architecture, roadmap, file map)
```
