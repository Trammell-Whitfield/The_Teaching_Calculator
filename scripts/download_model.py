#!/usr/bin/env python3
"""Download DeepSeek-Math-7B-Instruct model from Hugging Face"""

import os
from pathlib import Path
from huggingface_hub import snapshot_download

def download_model():
    model_id = "deepseek-ai/deepseek-math-7b-instruct"
    local_dir = Path(__file__).parent.parent / "models" / "base" / "deepseek-math-7b-instruct"

    print(f"Downloading {model_id}...")
    print(f"Target directory: {local_dir}")
    print(f"This will download ~13-15GB. Please be patient...")
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

    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return False

    return True

if __name__ == "__main__":
    download_model()
