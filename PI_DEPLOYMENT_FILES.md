# Raspberry Pi Deployment - File Manifest

All files created for Raspberry Pi 5 deployment.

## 🔧 Deployment Scripts

### `scripts/deployment/prepare_for_pi.sh`
**Purpose:** Pre-deployment validation (run on Mac/dev machine)

**What it does:**
- ✅ Verifies Q4_K_M and Q5_K_M models exist
- ✅ Warns about F16 models (too large for Pi)
- ✅ Calculates transfer size
- ✅ Generates SHA256 checksums
- ✅ Freezes Python dependencies
- ✅ Shows transfer commands

**Usage:**
```bash
./scripts/deployment/prepare_for_pi.sh
```

**Output:** `models/quantized/SHA256SUMS`

---

### `scripts/deployment/transfer_to_pi.sh`
**Purpose:** Automated transfer to Raspberry Pi

**What it does:**
- ✅ Tests Pi connectivity (ping)
- ✅ Creates destination directories via SSH
- ✅ Transfers models with progress bars
- ✅ Transfers code (excludes venv, build artifacts)
- ✅ Supports resume on interruption

**Usage:**
```bash
export PI_HOST=raspberrypi.local  # or IP address
export PI_USER=pi
./scripts/deployment/transfer_to_pi.sh
```

**Time:** 10-30 minutes (for ~18GB models)

---

### `scripts/deployment/pi_setup.sh`
**Purpose:** Automated Pi setup (run ON the Pi)

**What it does:**
- ✅ Verifies ARM64 architecture
- ✅ Updates system packages (`apt update && upgrade`)
- ✅ Installs build dependencies (OpenBLAS, CMake, etc.)
- ✅ Configures 4GB swap space
- ✅ Sets CPU governor to "performance"
- ✅ Creates Python virtual environment
- ✅ Installs Python dependencies (with ARM fallbacks)
- ✅ Builds llama.cpp with OpenBLAS acceleration
- ✅ Verifies model checksums
- ✅ Runs smoke tests (SymPy, LLM loading)

**Usage:**
```bash
# On the Pi:
cd ~/Holy_Calculator
./scripts/deployment/pi_setup.sh
```

**Time:** 20-40 minutes

---

## 🎛️ Platform Configuration

### `scripts/platform_config.py`
**Purpose:** Automatic hardware detection and optimization

**Features:**
- 🔍 Detects Raspberry Pi vs desktop/laptop
- 🔍 Detects ARM64 vs x86_64
- 🔍 Measures RAM capacity
- 🔍 Reads `/proc/device-tree/model` (Pi-specific)

**Automatic Optimization:**

| Platform | RAM | Model | Threads | Context | Expected Speed |
|----------|-----|-------|---------|---------|----------------|
| Pi 5 | 16GB | Q5_K_M | 2 | 2048 | 1-2 tok/s |
| Pi 5 | 8GB | Q4_K_M | 2 | 1024 | 2-3 tok/s |
| Desktop | Any | Q5_K_M | 8 | 4096 | 10-15 tok/s |

**Usage:**
```python
from platform_config import PlatformConfig

config = PlatformConfig()
config.print_info()
params = config.get_llm_params()
```

**Test:**
```bash
python scripts/platform_config.py
```

---

## 📝 Code Updates

### `scripts/cascade/llm_handler.py` (MODIFIED)
**Changes:**
- ✅ Imports `PlatformConfig`
- ✅ Detects platform in `__init__()`
- ✅ Uses platform-specific inference parameters
- ✅ Auto-selects model based on RAM
- ✅ Adds context window parameter to llama.cpp command

**Key lines:**
```python
# Line 47-48: Platform detection
self.platform_config = PlatformConfig()

# Line 67-76: Platform-optimized parameters
platform_params = self.platform_config.get_llm_params()
self.default_params = {
    'n_predict': platform_params['n_predict'],
    'temperature': platform_params['temperature'],
    'threads': platform_params['n_threads'],
    'n_ctx': platform_params.get('n_ctx', 2048),
    ...
}

# Line 99: Platform-aware model selection
preferred_models = self.platform_config.get_model_preference()
```

---

### `requirements.txt` (MODIFIED)
**Changes:**
- ✅ Added ARM64 compatibility notes
- ✅ Added OpenBLAS build instructions
- ✅ Added system package prerequisites
- ✅ Added platform-specific installation guides
- ✅ Documented platform auto-detection behavior

**New sections:**
- Raspberry Pi 5 Deployment (lines 57-68)
- Installation examples (lines 70-81)
- Platform Auto-Detection (lines 83-87)

---

## 📚 Documentation

### `docs/PI_DEPLOYMENT.md`
**Comprehensive deployment guide (400+ lines)**

**Sections:**
1. Prerequisites (hardware + software)
2. Quick Start (3-step process)
3. Detailed Setup (9 phases)
4. Performance Tuning
   - Model selection
   - Thermal management
   - Memory optimization
   - Inference speed tweaks
5. Troubleshooting (5 common issues)
6. Hardware Integration (TI-84, ESP32)
7. Performance Benchmarks

**Target audience:** Users who want complete understanding

---

### `QUICKSTART_PI.md`
**Fast-track guide (concise)**

**Sections:**
1. Prerequisites (hardware checklist)
2. Step 1: Prepare on Mac (5 min)
3. Step 2: Setup on Pi (30 min)
4. Step 3: Test (2 min)
5. Usage Examples
6. Performance Reference
7. Common Issues (quick fixes)
8. Monitoring Commands

**Target audience:** Impatient users who just want it working

---

### `PI_MIGRATION_COMPLETE.md`
**Implementation summary (this project)**

**Sections:**
- What was implemented (file list)
- What this achieves (TODO checklist)
- How to use (workflow)
- Expected performance (benchmarks)
- Advanced configuration
- Troubleshooting quick reference
- What's NOT implemented (future work)
- Testing checklist
- Key design decisions

**Target audience:** You (project overview) and future contributors

---

## 🗂️ Generated Files

### `models/quantized/SHA256SUMS`
**Purpose:** Verify model integrity after transfer

**Content:** SHA256 checksums for Q4_K_M and Q5_K_M models

**Usage:**
```bash
# On Pi after transfer:
cd models/quantized
sha256sum -c SHA256SUMS
```

**Expected output:**
```
deepseek-math-7b-q4km.gguf: OK
qwen2.5-math-7b-instruct-q4km.gguf: OK
deepseek-math-7b-q5km.gguf: OK
qwen2.5-math-7b-instruct-q5km.gguf: OK
```

---

### `requirements_dev_frozen.txt` (OPTIONAL)
**Purpose:** Freeze exact versions from your dev environment

**Generated by:** `prepare_for_pi.sh` (if venv is active)

**Usage:** Reference for reproducing exact dev environment

**Not required for Pi deployment** (uses `requirements.txt`)

---

## 📊 File Tree

```
Holy-calc-pi/
├── scripts/
│   ├── deployment/
│   │   ├── prepare_for_pi.sh       ← NEW: Mac-side prep
│   │   ├── transfer_to_pi.sh       ← NEW: Transfer automation
│   │   └── pi_setup.sh             ← NEW: Pi-side setup
│   ├── platform_config.py          ← NEW: Platform detection
│   └── cascade/
│       └── llm_handler.py          ← MODIFIED: Platform-aware
├── docs/
│   └── PI_DEPLOYMENT.md            ← NEW: Comprehensive guide
├── models/
│   └── quantized/
│       ├── *.gguf                  ← Existing models
│       └── SHA256SUMS              ← NEW: Checksums
├── QUICKSTART_PI.md                ← NEW: Fast-track guide
├── PI_MIGRATION_COMPLETE.md        ← NEW: Summary (this file)
├── PI_DEPLOYMENT_FILES.md          ← NEW: File manifest
├── requirements.txt                ← MODIFIED: ARM notes
└── requirements_dev_frozen.txt     ← NEW: (optional)
```

---

## ✅ Quality Assurance

### All Scripts Are:
- ✅ **Executable:** `chmod +x` applied
- ✅ **Well-commented:** Inline documentation
- ✅ **Error-handled:** `set -e` in bash, try/except in Python
- ✅ **Colored output:** Green/Yellow/Red for visual feedback
- ✅ **Progress-tracked:** Shows step numbers (1/6, 2/6, etc.)
- ✅ **Resumable:** Can re-run safely (idempotent where possible)

### All Documentation Is:
- ✅ **Markdown-formatted:** Renders in GitHub
- ✅ **Code-block examples:** Copy-paste ready
- ✅ **Table-organized:** Easy scanning
- ✅ **Cross-referenced:** Links between docs
- ✅ **Platform-specific:** Separate Pi vs Mac instructions

---

## 🧪 Testing Status

### Tested on macOS:
- ✅ `prepare_for_pi.sh` - Runs successfully
- ✅ `platform_config.py` - Detects ARM (Apple Silicon)
- ✅ Platform detection in `llm_handler.py` - Imports cleanly
- ✅ Model checksums - Generate correctly

### Not Yet Tested (requires physical Pi):
- ⏳ `transfer_to_pi.sh` - Needs actual Pi to test
- ⏳ `pi_setup.sh` - Needs to run on Pi
- ⏳ llama.cpp ARM build - Needs Pi to compile
- ⏳ Inference on Pi - Needs to validate speed/temps
- ⏳ Swap configuration - Needs to test on 8GB Pi
- ⏳ Thermal throttling - Needs sustained workload test

**Next step:** Run on your Raspberry Pi 5 to validate!

---

## 🎓 Key Design Principles

1. **Zero Manual Configuration**
   - Platform auto-detection eliminates config files
   - User never needs to set `IS_PI` or `RAM_SIZE` flags

2. **Fail-Fast with Clear Errors**
   - Checksum verification catches corrupt transfers
   - Architecture check prevents running on wrong hardware
   - Missing dependencies halt early with actionable errors

3. **Idempotent Operations**
   - Scripts can be re-run safely
   - Swap config checks before modifying
   - Virtual env recreated if exists

4. **Progressive Enhancement**
   - Works with minimal setup (just 3 commands)
   - Advanced users can tweak `platform_config.py`
   - Documentation layers (quick → comprehensive)

5. **Separation of Concerns**
   - Prep ≠ Transfer ≠ Setup (can run independently)
   - Platform detection separate from LLM logic
   - Documentation separate from code

---

## 📞 Support

**If something doesn't work:**
1. Check `QUICKSTART_PI.md` for common issues
2. Read `docs/PI_DEPLOYMENT.md#troubleshooting`
3. Verify checksums: `sha256sum -c SHA256SUMS`
4. Test platform detection: `python scripts/platform_config.py`
5. Open GitHub issue with logs

---

## 🎉 You're Ready!

All files are in place. Your next steps:

1. Run `./scripts/deployment/prepare_for_pi.sh` on Mac
2. Run `./scripts/deployment/transfer_to_pi.sh` to send to Pi
3. SSH to Pi and run `./scripts/deployment/pi_setup.sh`
4. Test with `python main.py --query "Solve x^2 = 4"`

**Total time:** ~40-60 minutes (mostly transfer and compilation)

**Result:** Portable, battery-powered, offline math reasoning engine! 🧮🥧
