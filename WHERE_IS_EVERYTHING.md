# 📁 Holy Calculator - File Location Guide

**Project Location**: `/Users/elhoyabembe/Documents/GitHub/Holy-calc-pi/`

## 🎯 **THE MOST IMPORTANT FILES** (for Raspberry Pi)

**RECOMMENDED MODEL** (Best Performance):
```
/Users/elhoyabembe/Documents/GitHub/Holy-calc-pi/models/quantized/qwen2.5-math-7b-instruct-q5km.gguf
```
**Size**: 5.1 GB
**Purpose**: Qwen2.5-Math Q5_K_M quantized model - Superior accuracy for mathematical reasoning
**Status**: ✅ READY TO USE (PREFERRED)

**BACKUP MODEL** (Smaller, Faster):
```
/Users/elhoyabembe/Documents/GitHub/Holy-calc-pi/models/quantized/qwen2.5-math-7b-instruct-q4km.gguf
```
**Size**: 4.4 GB
**Purpose**: Qwen2.5-Math Q4_K_M quantized - Good balance of speed and accuracy
**Status**: ✅ READY TO USE

---

## 📂 Complete Directory Structure

```
/Users/elhoyabembe/Documents/GitHub/Holy-calc-pi/
│
├── 📋 README.md                    # Project overview
├── 📋 WHERE_IS_EVERYTHING.md       # This file!
├── 📋 requirements.txt             # Python dependencies
├── 📋 requirements_mqtt.txt        # MQTT/IoT dependencies
├── 📋 .gitignore                   # Git ignore rules
├── 📋 main.py                      # Main calculator application (10KB)
│
├── 📁 models/                      # AI Models (~86GB total)
│   ├── base/                       # Original downloaded models (HuggingFace format)
│   │   ├── deepseek-math-7b-instruct/     # DeepSeek-Math base model
│   │   └── Qwen2.5-Math-7B-Instruct/      # Qwen2.5-Math base model
│   │
│   └── quantized/                  # Quantized GGUF models for deployment
│       ├── deepseek-math-7b-f16.gguf      # 13 GB (full precision)
│       ├── deepseek-math-7b-q4km.gguf     # 3.9 GB
│       ├── deepseek-math-7b-q5km.gguf     # 4.6 GB
│       ├── qwen2.5-math-7b-instruct-f16.gguf   # 14 GB (full precision)
│       ├── qwen2.5-math-7b-instruct-q4km.gguf  # 4.4 GB
│       └── qwen2.5-math-7b-instruct-q5km.gguf  # 5.1 GB ⭐ BEST FOR PI!
│
├── 📁 llama.cpp/                   # LLM Inference Engine (~478MB)
│   ├── build/bin/
│   │   ├── llama-cli               # Run LLM inference
│   │   ├── llama-quantize          # Quantize models
│   │   ├── llama-bench             # Benchmark performance
│   │   └── llama-server            # API server
│   ├── convert_hf_to_gguf.py       # PyTorch → GGUF converter
│   └── [source code]
│
├── 📁 scripts/                     # Python Scripts (~612KB)
│   ├── download_model.py           # Downloads models from HuggingFace
│   ├── compare_llm_models.py       # LLM model comparison tool
│   ├── setup_mqtt.sh               # MQTT broker setup
│   ├── validate_dependencies.sh    # Dependency checker
│   ├── cascade/                    # Math solving cascade
│   │   ├── cascade_orchestrator.py # Main orchestrator
│   │   ├── llm_handler.py          # LLM integration
│   │   ├── sympy_handler.py        # SymPy solver
│   │   └── wolfram_handler.py      # Wolfram Alpha API
│   ├── cache/                      # Query caching system
│   │   └── query_cache.py          # Cache implementation
│   ├── hardware/                   # TI-84 integration
│   │   ├── ti84_interface.py       # TI-84 serial interface
│   │   └── ti84_protocol.py        # TI-84 protocol handler
│   ├── monitoring/                 # Performance monitoring
│   │   └── [monitoring scripts]
│   └── testing/                    # Test suites
│       └── [test files]
│
├── 📁 data/                        # Test Data & Configuration
│   ├── test-cases/                 # Test problem sets
│   └── config/                     # Configuration files
│
├── 📁 cache/                       # Query Cache Storage
│   └── [cached responses]
│
├── 📁 docs/                        # Documentation (~348KB)
│   ├── mac-system-baseline.txt     # Your Mac specs
│   ├── phase0-completion-summary.md
│   ├── phase1-summary.md
│   ├── phase2-completion-summary.md
│   ├── offline-pi-deployment-plan.md
│   ├── project-status-summary.md
│   └── [25+ other documentation files]
│
├── 📁 logs/                        # Build & Test Logs (~156KB)
│   ├── model-download.log          # Download log
│   ├── gguf-conversion.log         # GGUF conversion log
│   ├── quantize-q4km.log           # Quantization logs
│   └── [other logs]
│
├── 📁 pi-stats-app/                # Raspberry Pi monitoring app (~144KB)
│   ├── app.py                      # Flask web dashboard
│   └── [frontend files]
│
├── 📁 venv/                        # Python Virtual Environment (~162MB)
│   ├── bin/python3                 # Python interpreter
│   └── lib/python3.x/site-packages/
│       ├── sympy/                  # Symbolic mathematics
│       ├── numpy/                  # Numerical computing
│       └── [other packages]
│
└── 📁 CALC_env/                    # Alternative virtual environment (~874MB)
    └── [conda/alternative env]
```

---

## 🚀 How to Use This Project

### On Mac (Development)

**Activate Python environment:**
```bash
cd /Users/elhoyabembe/Documents/GitHub/Holy-calc-pi
source venv/bin/activate
```

**Test LLM locally (Qwen2.5-Math - RECOMMENDED):**
```bash
cd llama.cpp
./build/bin/llama-cli \
  -m ../models/quantized/qwen2.5-math-7b-instruct-q5km.gguf \
  -p "Solve for x: 2x + 5 = 13" \
  -n 100
```

**Run main calculator:**
```bash
python3 main.py
```

**Compare LLM models:**
```bash
python3 scripts/compare_llm_models.py
```

### Transfer to Raspberry Pi

**What to copy:**
1. **ESSENTIAL**: `models/quantized/qwen2.5-math-7b-instruct-q5km.gguf` (5.1 GB) ⭐
2. **BACKUP**: `models/quantized/qwen2.5-math-7b-instruct-q4km.gguf` (4.4 GB)
3. `main.py` - Main calculator application
4. `scripts/` folder - All Python code
5. `requirements.txt` & `requirements_mqtt.txt` - Dependencies
6. llama.cpp binaries (rebuild on Pi or cross-compile)

**Transfer methods:**
```bash
# Option 1: USB Drive
cp models/quantized/qwen2.5-math-7b-instruct-q5km.gguf /Volumes/USB_DRIVE/

# Option 2: SCP (one-time WiFi)
scp models/quantized/qwen2.5-math-7b-instruct-q5km.gguf pi@raspberrypi.local:~/

# Option 3: SD Card (before booting Pi)
# Mount SD card and copy directly to /boot or /home partition
```

**Quick deployment script:**
```bash
# See DEPLOY_CHEATSHEET.md and MODEL_TRANSFER_GUIDE.md for detailed instructions
```

---

## 📊 Storage Breakdown

| Location | Size | Keep on Mac? | Transfer to Pi? |
|----------|------|--------------|-----------------|
| `models/base/deepseek-math-7b-instruct/` | ~13 GB | ✅ Yes | ❌ No |
| `models/base/Qwen2.5-Math-7B-Instruct/` | ~14 GB | ✅ Yes | ❌ No |
| `models/quantized/deepseek-math-7b-f16.gguf` | 13 GB | ⚠️ Optional | ❌ No |
| `models/quantized/deepseek-math-7b-q4km.gguf` | 3.9 GB | ✅ Yes | ⚠️ Optional |
| `models/quantized/deepseek-math-7b-q5km.gguf` | 4.6 GB | ✅ Yes | ⚠️ Optional |
| `models/quantized/qwen2.5-math-7b-instruct-f16.gguf` | 14 GB | ⚠️ Optional | ❌ No |
| `models/quantized/qwen2.5-math-7b-instruct-q4km.gguf` | 4.4 GB | ✅ Yes | ✅ Backup |
| `models/quantized/qwen2.5-math-7b-instruct-q5km.gguf` | 5.1 GB | ✅ Yes | ✅ **PRIMARY!** |
| `llama.cpp/` | 478 MB | ✅ Yes | ✅ Yes (rebuild) |
| `scripts/` | 612 KB | ✅ Yes | ✅ Yes |
| `main.py` | 10 KB | ✅ Yes | ✅ Yes |
| `venv/` | 162 MB | ✅ Yes | ❌ No (rebuild on Pi) |
| `CALC_env/` | 874 MB | ⚠️ Optional | ❌ No |
| **TOTAL** | ~86 GB | | **~5-10 GB** |

---

## 🔑 Key Files Explained

### For Development (Mac)
- `main.py` - Main calculator orchestrator with cascade logic
- `llama.cpp/build/bin/llama-cli` - Test LLM inference
- `scripts/compare_llm_models.py` - Compare model performance
- `scripts/download_model.py` - Download models from HuggingFace
- `requirements.txt` - Python packages (`pip install -r requirements.txt`)
- `venv/` - Isolated Python environment

### For Deployment (Pi)
- `models/quantized/qwen2.5-math-7b-instruct-q5km.gguf` - **PRIMARY** model (best accuracy)
- `models/quantized/qwen2.5-math-7b-instruct-q4km.gguf` - Backup model (faster)
- `main.py` - Main calculator application
- `scripts/cascade/cascade_orchestrator.py` - SymPy → Wolfram → LLM cascade logic
- `scripts/cascade/sympy_handler.py` - Symbolic math solver
- `scripts/cascade/llm_handler.py` - LLM integration
- `scripts/hardware/ti84_interface.py` - TI-84 serial interface
- `scripts/cache/query_cache.py` - Response caching system

### Documentation
- `WHERE_IS_EVERYTHING.md` - This file (complete project map)
- `DEPLOY_CHEATSHEET.md` - Quick deployment reference
- `MODEL_TRANSFER_GUIDE.md` - How to transfer models to Pi
- `QUICK_REFERENCE.md` - Common commands and operations
- `QUICKSTART_PI.md` - Raspberry Pi setup guide
- `docs/offline-pi-deployment-plan.md` - Offline deployment strategy
- `docs/project-status-summary.md` - Current project status

---

## 🎓 Git Repository

Your project is a Git repository:

```bash
cd /Users/elhoyabembe/Documents/GitHub/Holy-calc-pi
git status
git log
```

**Recent commits:**
- Switch to Qwen2.5-Math models with Q5_K_M preferred quantization
- Create validate_dependencies.sh
- Create compare_llm_models.py
- Create setup_mqtt.sh
- Multiple phase completions and documentation updates

---

## ⚡ Quick Commands

### See what's taking up space:
```bash
cd /Users/elhoyabembe/Documents/GitHub/Holy-calc-pi
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
./build/bin/llama-cli -m ../models/quantized/qwen2.5-math-7b-instruct-q5km.gguf -p "2+2" -n 50
```

### Update Python requirements:
```bash
source venv/bin/activate
pip freeze > requirements.txt
```

### Run model comparison:
```bash
python3 scripts/compare_llm_models.py
```

### Validate dependencies before Pi transfer:
```bash
bash scripts/validate_dependencies.sh
```

---

## 🌟 Project Status & Next Steps

### ✅ Completed
- Phase 0: Environment setup (Mac + Python + llama.cpp)
- Phase 1: Model download (both DeepSeek-Math and Qwen2.5-Math)
- Phase 2: Model quantization (Q4_K_M and Q5_K_M variants)
- Phase 3: Model comparison testing (Qwen2.5 Q5_K_M is best)
- Phase 4: Cascade orchestrator (SymPy → Wolfram → LLM)
- Phase 5: Query caching system
- Phase 6: TI-84 interface implementation
- Phase 7: MQTT integration for IoT
- Phase 8: Pi monitoring dashboard

### 🔄 In Progress
- Final testing and optimization
- Documentation refinement

### 📋 Ready for Deployment
- Transfer Qwen2.5-Math Q5_K_M model to Raspberry Pi
- Set up offline calculator on Pi
- Test complete cascade system on Pi hardware

### 🎯 Optional Enhancements
- ESP32 integration for wireless display
- Enhanced caching strategies
- Additional model fine-tuning

---

**Last Updated**: December 17, 2025
**Project Status**: READY FOR RASPBERRY PI DEPLOYMENT
**Primary Model**: Qwen2.5-Math-7B Q5_K_M (5.1 GB)
**Total Project Size**: ~86 GB (Mac) → ~5-10 GB (Pi transfer)
