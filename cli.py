#!/usr/bin/env python3
# cli.py — Command-line interface for quick vision queries
# Usage:
#   python cli.py check image.png "is there an error message?"
#   python cli.py score image.png "a clean page" "a broken page"
#   python cli.py compare before.png after.png
#   python cli.py caption image.png [--task caption|ocr|detect]
#   python cli.py health
#
# Talks to the running server at localhost:9090.
# If server is not running, prints an error.

import argparse
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
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"Error: Cannot reach server at {BASE_URL}. Is it running?", file=sys.stderr)
        print(f"Start it with: python server.py", file=sys.stderr)
        sys.exit(1)


def _get(endpoint):
    try:
        with urllib.request.urlopen(f"{BASE_URL}{endpoint}", timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError:
        print(f"Error: Cannot reach server at {BASE_URL}. Is it running?", file=sys.stderr)
        sys.exit(1)


def cmd_health(args):
    result = _get("/health")
    print(json.dumps(result, indent=2))


def cmd_check(args):
    result = _post("/check", {"image": args.image, "query": args.query})
    print(result["answer"])
    if args.json:
        print(json.dumps(result, indent=2))


def cmd_score(args):
    result = _post("/score", {"image": args.image, "prompts": args.prompts})
    for prompt, score in zip(args.prompts, result["scores"]):
        print(f"  {score:.3f}  {prompt}")
    print(f"Best: {result['best_match']}")
    if args.json:
        print(json.dumps(result, indent=2))


def cmd_compare(args):
    result = _post("/compare", {"before": args.before, "after": args.after})
    print(f"SSIM: {result['ssim']:.4f}")
    if result["changed_regions"]:
        print(f"Changed regions: {len(result['changed_regions'])}")
        for r in result["changed_regions"][:5]:
            print(f"  ({r['x']},{r['y']}) {r['width']}x{r['height']} diff={r['mean_diff']:.3f}")
    else:
        print("No significant changes detected")
    if args.json:
        print(json.dumps(result, indent=2))


def cmd_caption(args):
    result = _post("/caption", {"image": args.image, "task": args.task})
    r = result["result"]
    if "caption" in r:
        print(r["caption"])
    elif "text" in r:
        print(r["text"])
    elif "objects" in r:
        print(r["objects"])
    if args.json:
        print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Offline Vision Tool CLI")
    parser.add_argument("--json", action="store_true", help="Print full JSON response")
    sub = parser.add_subparsers(dest="command", required=True)

    p_health = sub.add_parser("health", help="Check server status")
    p_health.set_defaults(func=cmd_health)

    p_check = sub.add_parser("check", help="Ask a question about an image")
    p_check.add_argument("image", help="Path to image file")
    p_check.add_argument("query", help="Question to ask")
    p_check.set_defaults(func=cmd_check)

    p_score = sub.add_parser("score", help="Score image against text prompts")
    p_score.add_argument("image", help="Path to image file")
    p_score.add_argument("prompts", nargs="+", help="Text prompts to score against")
    p_score.set_defaults(func=cmd_score)

    p_compare = sub.add_parser("compare", help="Compare two images")
    p_compare.add_argument("before", help="Before image path")
    p_compare.add_argument("after", help="After image path")
    p_compare.set_defaults(func=cmd_compare)

    p_caption = sub.add_parser("caption", help="Caption/OCR/detect an image")
    p_caption.add_argument("image", help="Path to image file")
    p_caption.add_argument("--task", default="caption", choices=["caption", "ocr", "detect"])
    p_caption.set_defaults(func=cmd_caption)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
