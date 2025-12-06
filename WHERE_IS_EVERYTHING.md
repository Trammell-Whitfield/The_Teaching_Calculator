# 📁 Holy Calculator - File Location Guide

**Project Location**: `/Users/elhoyabembe/Documents/GitHub/Holy_Calculator/`

## 🎯 **THE MOST IMPORTANT FILE** (for Raspberry Pi)

This is what you'll transfer to your Pi:

```
/Users/elhoyabembe/Documents/GitHub/Holy_Calculator/models/quantized/deepseek-math-7b-q4km.gguf
```
**Size**: 3.9 GB
**Purpose**: Quantized LLM model for offline mathematical reasoning
**Status**: ✅ READY TO USE

---

## 📂 Complete Directory Structure

```
/Users/elhoyabembe/Documents/GitHub/Holy_Calculator/
│
├── 📋 README.md                    # Project overview
├── 📋 WHERE_IS_EVERYTHING.md       # This file!
├── 📋 requirements.txt             # Python dependencies
├── 📋 .gitignore                   # Git ignore rules
│
├── 📁 models/                      # AI Models (26GB total)
│   ├── base/                       # Original downloaded model
│   │   └── deepseek-math-7b-instruct/    # 12.9 GB (PyTorch format)
│   │       ├── pytorch_model-00001-of-00002.bin  (9.3GB)
│   │       ├── pytorch_model-00002-of-00002.bin  (3.6GB)
│   │       ├── config.json
│   │       ├── tokenizer.json
│   │       └── [other config files]
│   │
│   └── quantized/                  # Quantized models for deployment
│       ├── deepseek-math-7b-f16.gguf      # 13 GB (intermediate)
│       ├── deepseek-math-7b-q4km.gguf     # 3.9 GB ⭐ USE THIS ON PI!
│       └── deepseek-math-7b-q5km.gguf     # ~4.8 GB (backup, creating...)
│
├── 📁 llama.cpp/                   # LLM Inference Engine
│   ├── build/bin/
│   │   ├── llama-cli               # Run LLM inference
│   │   ├── llama-quantize          # Quantize models
│   │   ├── llama-bench             # Benchmark performance
│   │   └── llama-server            # API server
│   ├── convert_hf_to_gguf.py       # PyTorch → GGUF converter
│   └── [source code]
│
├── 📁 scripts/                     # Python Scripts
│   ├── download_model.py           # Downloads models from HuggingFace
│   ├── cascade/                    # (Empty - Phase 7)
│   │   └── [future: SymPy, Wolfram, LLM handlers]
│   ├── monitoring/                 # (Empty - Phase 3)
│   │   └── [future: performance monitoring]
│   └── testing/                    # (Empty - Phase 4)
│       └── [future: test suites]
│
├── 📁 data/                        # Test Data
│   └── test-cases/                 # (Empty - Phase 3)
│       └── [future: math-problems.yaml]
│
├── 📁 docs/                        # Documentation
│   ├── mac-system-baseline.txt     # Your Mac specs
│   ├── llamacpp-version.txt        # llama.cpp version
│   ├── build-config.txt            # Build configuration
│   ├── base-model-manifest.txt     # List of model files
│   ├── phase0-completion-summary.md
│   ├── phase1-summary.md
│   ├── offline-pi-deployment-plan.md  # ⭐ Important!
│   ├── project-status-summary.md
│   └── WHERE_IS_EVERYTHING.md      # This file
│
├── 📁 logs/                        # Build & Test Logs
│   ├── model-download.log          # Download log
│   ├── gguf-conversion.log         # GGUF conversion log
│   ├── quantize-q4km.log           # Q4 quantization log
│   └── quantize-q5km.log           # Q5 quantization log (creating...)
│
└── 📁 venv/                        # Python Virtual Environment
    ├── bin/
    │   └── python3                 # Python interpreter
    └── lib/python3.9/site-packages/
        ├── sympy/                  # Symbolic mathematics
        ├── numpy/                  # Numerical computing
        ├── torch/                  # PyTorch
        ├── transformers/           # HuggingFace transformers
        └── [other packages]
```

---

## 🚀 How to Use This Project

### On Mac (Development)

**Activate Python environment:**
```bash
cd /Users/elhoyabembe/Documents/GitHub/Holy_Calculator
source venv/bin/activate
```

**Test LLM locally:**
```bash
cd llama.cpp
./build/bin/llama-cli \
  -m ../models/quantized/deepseek-math-7b-q4km.gguf \
  -p "Solve for x: 2x + 5 = 13" \
  -n 100
```

**Run Python scripts:**
```bash
python3 scripts/download_model.py
```

### Transfer to Raspberry Pi

**What to copy:**
1. `models/quantized/deepseek-math-7b-q4km.gguf` (3.9 GB) ⭐ ESSENTIAL
2. `scripts/` folder (all Python code)
3. `requirements.txt` (Python dependencies)
4. llama.cpp binaries (rebuild on Pi or cross-compile)

**Transfer methods:**
```bash
# Option 1: USB Drive
cp models/quantized/deepseek-math-7b-q4km.gguf /Volumes/USB_DRIVE/

# Option 2: SCP (one-time WiFi)
scp models/quantized/deepseek-math-7b-q4km.gguf pi@raspberrypi.local:~/

# Option 3: SD Card (before booting Pi)
# Mount SD card and copy directly
```

---

## 📊 Storage Breakdown

| Location | Size | Keep on Mac? | Transfer to Pi? |
|----------|------|--------------|-----------------|
| `models/base/` | 12.9 GB | ✅ Yes (for re-quantization) | ❌ No |
| `models/quantized/deepseek-math-7b-f16.gguf` | 13 GB | ⚠️ Optional | ❌ No |
| `models/quantized/deepseek-math-7b-q4km.gguf` | 3.9 GB | ✅ Yes | ✅ **YES!** |
| `models/quantized/deepseek-math-7b-q5km.gguf` | ~4.8 GB | ✅ Yes (backup) | ⚠️ Optional |
| `llama.cpp/` | ~500 MB | ✅ Yes | ✅ Yes (rebuild) |
| `scripts/` | ~5 MB | ✅ Yes | ✅ Yes |
| `venv/` | ~1 GB | ✅ Yes | ❌ No (rebuild on Pi) |
| **TOTAL** | ~31 GB | | **~4.5 GB** |

---

## 🔑 Key Files Explained

### For Development (Mac)
- `llama.cpp/build/bin/llama-cli` - Test LLM inference
- `scripts/download_model.py` - Download models from HuggingFace
- `requirements.txt` - Install Python packages (`pip install -r requirements.txt`)
- `venv/` - Isolated Python environment

### For Deployment (Pi)
- `models/quantized/deepseek-math-7b-q4km.gguf` - THE quantized model
- `scripts/cascade/` - (Future) SymPy → Wolfram → LLM logic
- `scripts/hardware/` - (Future) TI-84 interface

### Documentation
- `docs/offline-pi-deployment-plan.md` - How to deploy without WiFi
- `docs/project-status-summary.md` - Current project status
- `docs/phase1-summary.md` - What we've completed

---

## 🎓 Git Repository

Your project is a Git repository:

```bash
cd /Users/elhoyabembe/Documents/GitHub/Holy_Calculator
git status
git log
```

**Recent commits:**
1. Phase 0: Environment setup
2. Phase 1: Model download complete

---

## ⚡ Quick Commands

### See what's taking up space:
```bash
cd /Users/elhoyabembe/Documents/GitHub/Holy_Calculator
du -sh *
```

### Check model file sizes:
```bash
ls -lh models/quantized/
```

### Test if LLM works:
```bash
cd llama.cpp
./build/bin/llama-cli --version
```

### Update Python requirements:
```bash
source venv/bin/activate
pip freeze > requirements.txt
```

---

## 🌟 Next Steps

1. **Phase 2 Complete**: Wait for Q5_K_M to finish quantizing (~5 min)
2. **Phase 3-4**: Set up monitoring and testing
3. **Phase 5**: Build SymPy integration (offline math solver)
4. **Phase 6**: Wolfram Alpha integration (optional, needs internet)
5. **Phase 7**: Cascade orchestrator (SymPy → Wolfram → LLM)
6. **Phase 8**: Transfer to Raspberry Pi and test offline!

---

**Last Updated**: November 28, 2025
**Project Status**: Phase 2 nearly complete (90%)
**Ready for Pi?**: Almost! (need to build cascade logic first)
