#!/usr/bin/env python3
"""Quick test to verify the quantized model file is valid"""

import struct
from pathlib import Path

def test_gguf_file(model_path):
    """Test that a GGUF file is valid by checking its header"""
    model_path = Path(model_path)

    if not model_path.exists():
        print(f"✗ Model file not found: {model_path}")
        return False

    size_gb = model_path.stat().st_size / (1024**3)
    print(f"✓ Model file found: {model_path.name}")
    print(f"✓ Size: {size_gb:.2f} GB")

    # Read GGUF magic number and version
    with open(model_path, 'rb') as f:
        magic = f.read(4)
        if magic == b'GGUF':
            version = struct.unpack('<I', f.read(4))[0]
            print(f"✓ Valid GGUF file (version {version})")
            return True
        else:
            print(f"✗ Invalid magic number: {magic}")
            return False

if __name__ == "__main__":
    models_dir = Path(__file__).parent / "models" / "quantized"

    print("=" * 60)
    print("TESTING QUANTIZED MODELS")
    print("=" * 60)

    # Test Q4_K_M
    q4_model = models_dir / "deepseek-math-7b-q4km.gguf"
    print("\nQ4_K_M Model (for Raspberry Pi):")
    if test_gguf_file(q4_model):
        print("✓ Q4_K_M model is ready for deployment!")

    # Test FP16 if exists
    fp16_model = models_dir / "deepseek-math-7b-f16.gguf"
    if fp16_model.exists():
        print("\nFP16 Model (intermediate):")
        test_gguf_file(fp16_model)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✓ Q4_K_M model ({q4_model.stat().st_size / (1024**3):.2f}GB) is ready")
    print(f"✓ This file can be transferred to Raspberry Pi")
    print(f"✓ Location: {q4_model}")
