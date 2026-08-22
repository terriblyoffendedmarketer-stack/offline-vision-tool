#!/usr/bin/env python3
# setup_models.py — Pre-download ML models so first queries aren't slow
# Usage: python setup_models.py
#
# Downloads CLIP ViT-B/32 (~340MB) and SmolVLM-500M-Instruct (~1GB) from
# HuggingFace Hub into the local cache. Run once after install.
#
# Gotchas:
# - SmolVLM requires num2words package (ImportError at processor init).
# - Downloads go to ~/.cache/huggingface/ by default.
# - On a slow connection, SmolVLM download can take 5-10 minutes.

import sys


def download_clip():
    print("   Downloading CLIP ViT-B/32...")
    try:
        import open_clip
        open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
        print("   CLIP ViT-B/32 ✓")
        return True
    except Exception as e:
        print(f"   CLIP download failed: {e}")
        return False


def download_smolvlm():
    print("   Downloading SmolVLM-500M-Instruct...")
    try:
        from transformers import AutoModelForImageTextToText, AutoProcessor
        model_id = "HuggingFaceTB/SmolVLM-500M-Instruct"
        AutoProcessor.from_pretrained(model_id)
        AutoModelForImageTextToText.from_pretrained(model_id)
        print("   SmolVLM-500M-Instruct ✓")
        return True
    except Exception as e:
        print(f"   SmolVLM download failed: {e}")
        return False


def main():
    ok = True
    ok = download_clip() and ok
    ok = download_smolvlm() and ok

    if ok:
        print("   All models downloaded ✓")
    else:
        print("   Some models failed to download. They'll download on first use instead.")
        sys.exit(1)


if __name__ == "__main__":
    main()
