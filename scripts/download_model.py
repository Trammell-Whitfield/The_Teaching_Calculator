#!/usr/bin/env python3
"""
Download Qwen2.5-Math-7B-Instruct model from Hugging Face

This downloads the base FP16 model which can then be quantized to Q5_K_M or Q4_K_M.
Qwen2.5-Math is the preferred model for Holy Calculator (Phase 7.5+).
"""

import argparse
from pathlib import Path
from huggingface_hub import snapshot_download


def download_model(model_choice: str = "qwen"):
    """
    Download a math model from Hugging Face.

    Args:
        model_choice: Either 'qwen' (default) or 'deepseek' (legacy)
    """
    # Model configurations
    models = {
        "qwen": {
            "id": "Qwen/Qwen2.5-Math-7B-Instruct",
            "dir": "Qwen2.5-Math-7B-Instruct",
            "size": "~14GB",
            "description": "Qwen2.5-Math-7B-Instruct (recommended - superior accuracy)"
        },
        "deepseek": {
            "id": "deepseek-ai/deepseek-math-7b-instruct",
            "dir": "deepseek-math-7b-instruct",
            "size": "~13-15GB",
            "description": "DeepSeek-Math-7B-Instruct (legacy)"
        }
    }

    if model_choice not in models:
        print(f"❌ Unknown model choice: {model_choice}")
        print(f"Available options: {', '.join(models.keys())}")
        return False

    config = models[model_choice]
    model_id = config["id"]
    local_dir = Path(__file__).parent.parent / "models" / "base" / config["dir"]

    print(f"Downloading: {config['description']}")
    print(f"Model ID: {model_id}")
    print(f"Target directory: {local_dir}")
    print(f"This will download {config['size']}. Please be patient...")
    print()

    try:
        snapshot_download(
            repo_id=model_id,
            local_dir=str(local_dir),
            local_dir_use_symlinks=False,
            resume_download=True,
        )
        print(f"\n✓ Download complete!")
        print(f"Model saved to: {local_dir}")

        # List downloaded files
        print("\nDownloaded files:")
        for file in sorted(local_dir.glob("*")):
            size = file.stat().st_size / (1024**3)  # Convert to GB
            print(f"  {file.name}: {size:.2f} GB")

        print(f"\n📋 Next steps:")
        print(f"1. Convert to GGUF format (if not already done)")
        print(f"2. Quantize to Q5_K_M or Q4_K_M")
        print(f"   - Q5_K_M: Better quality, needs 16GB RAM")
        print(f"   - Q4_K_M: Faster, works with 8GB RAM")

    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return False

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download math models for Holy Calculator"
    )
    parser.add_argument(
        "--model",
        choices=["qwen", "deepseek"],
        default="qwen",
        help="Model to download (default: qwen)"
    )

    args = parser.parse_args()
    download_model(args.model)
