#!/usr/bin/env python3
# mcp_server.py — MCP (Model Context Protocol) server wrapper
# Exposes the vision tool as MCP tools that Claude Code can call directly.
# Uses stdio transport (Claude Code launches this as a subprocess).
#
# Usage: python mcp_server.py
# Registered via: claude mcp add vision-tool python3 /path/to/mcp_server.py
#
# Gotchas:
# - Talks to the HTTP server at localhost:9090. Server must be running.
# - If server is down, tools return a clear error message, not a crash.

import json
import sys
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:9090"


def _post(endpoint, data):
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def _get(endpoint):
    with urllib.request.urlopen(f"{BASE_URL}{endpoint}", timeout=10) as resp:
        return json.loads(resp.read())


def _server_available():
    try:
        _get("/health")
        return True
    except (urllib.error.URLError, OSError):
        return False


TOOLS = [
    {
        "name": "vision_check",
        "description": "Ask a question about an image and get a text answer. Use this instead of taking screenshots when you need to verify UI state, check for errors, or understand what's in an image. Runs locally for free — no API tokens consumed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image": {"type": "string", "description": "Absolute path to the image file"},
                "query": {"type": "string", "description": "Question to ask about the image, e.g. 'Is there an error message visible?' or 'How many input fields are there?'"},
            },
            "required": ["image", "query"],
        },
    },
    {
        "name": "vision_score",
        "description": "Score an image against text descriptions using CLIP. Returns similarity scores showing which description best matches. Great for UI verification: score against 'a properly laid out page' vs 'a broken page with errors'. Runs locally, ~20ms per image.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image": {"type": "string", "description": "Absolute path to the image file"},
                "prompts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Text descriptions to score the image against",
                },
            },
            "required": ["image", "prompts"],
        },
    },
    {
        "name": "vision_compare",
        "description": "Compare two images using SSIM (structural similarity). Returns a similarity score and bounding boxes of changed regions. Perfect for visual regression testing after code changes. Pure math, ~5ms, no model needed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "before": {"type": "string", "description": "Absolute path to the before image"},
                "after": {"type": "string", "description": "Absolute path to the after image"},
            },
            "required": ["before", "after"],
        },
    },
    {
        "name": "vision_caption",
        "description": "Get a caption, OCR text, or object list from an image. Use task='caption' for a description, 'ocr' to read text, 'detect' to list objects. Runs locally via SmolVLM.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image": {"type": "string", "description": "Absolute path to the image file"},
                "task": {
                    "type": "string",
                    "enum": ["caption", "ocr", "detect"],
                    "description": "What to extract: caption (description), ocr (text), or detect (objects)",
                    "default": "caption",
                },
            },
            "required": ["image"],
        },
    },
]


def handle_request(request):
    method = request.get("method")
    req_id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "vision-tool", "version": "0.1.0"},
            },
        }

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS},
        }

    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if not _server_available():
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": "Error: Vision tool server is not running at localhost:9090. Start it with: cd '/Users/apple/Documents/Claude Code/Offline Vision Tool' && source venv/bin/activate && python server.py"}],
                    "isError": True,
                },
            }

        try:
            if tool_name == "vision_check":
                result = _post("/check", {"image": args["image"], "query": args["query"]})
                text = f"Answer: {result['answer']}\n({result['elapsed_ms']:.0f}ms)"

            elif tool_name == "vision_score":
                result = _post("/score", {"image": args["image"], "prompts": args["prompts"]})
                lines = [f"  {s:.3f}  {p}" for s, p in zip(result["scores"], args["prompts"])]
                lines.append(f"Best match: {result['best_match']}")
                text = "\n".join(lines) + f"\n({result['elapsed_ms']:.0f}ms)"

            elif tool_name == "vision_compare":
                result = _post("/compare", {"before": args["before"], "after": args["after"]})
                text = f"SSIM: {result['ssim']:.4f}\n"
                if result["changed_regions"]:
                    text += f"Changed regions: {len(result['changed_regions'])}\n"
                    for r in result["changed_regions"][:5]:
                        text += f"  ({r['x']},{r['y']}) {r['width']}x{r['height']} diff={r['mean_diff']:.3f}\n"
                else:
                    text += "No significant changes detected\n"
                text += f"({result['elapsed_ms']:.0f}ms)"

            elif tool_name == "vision_caption":
                task = args.get("task", "caption")
                result = _post("/caption", {"image": args["image"], "task": task})
                r = result["result"]
                if "caption" in r:
                    text = r["caption"]
                elif "text" in r:
                    text = r["text"]
                elif "objects" in r:
                    text = str(r["objects"])
                else:
                    text = json.dumps(r)
                text += f"\n({result['elapsed_ms']:.0f}ms)"

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                        "isError": True,
                    },
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": text}],
                },
            }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"Error: {e}"}],
                    "isError": True,
                },
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        response = handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
