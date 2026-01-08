# Setup Guide

Complete installation and configuration guide for the Holy Calculator project.

---

## System Requirements

### Hardware
- **Raspberry Pi 5** (16GB recommended, 8GB minimum) or
- **macOS** (Apple Silicon or Intel) for development
- **Storage**: 20GB+ free space
- **Optional**: TI-84 Plus CE calculator
- **Optional**: ESP32-PICO-MINI-02 for wireless bridge

### Software
- **Python**: 3.8 or higher
- **Git**: For cloning repository
- **Git LFS**: For downloading large model files
- **Build tools**: cmake, make, gcc/clang

---

## Quick Start Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Holy_Calculator.git
cd Holy_Calculator
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt
```

### 4. Build llama.cpp

#### For macOS (Apple Silicon)
```bash
cd llama.cpp
cmake -B build -DLLAMA_METAL=ON
cmake --build build --config Release
cd ..
```

#### For Raspberry Pi 5
```bash
cd llama.cpp
cmake -B build -DLLAMA_NATIVE=ON -DLLAMA_NEON=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j4
cd ..
```

#### For Linux (x86_64)
```bash
cd llama.cpp
cmake -B build
cmake --build build --config Release
cd ..
```

---

## Model Setup

### Option 1: Download Qwen2.5-Math (Recommended)

```bash
# Install Git LFS
git lfs install

# Download model from HuggingFace
cd models/base
git clone https://huggingface.co/Qwen/Qwen2.5-Math-7B-Instruct
cd ../..
```

### Option 2: Download DeepSeek-Math (Alternative)

```bash
cd models/base
git clone https://huggingface.co/deepseek-ai/deepseek-math-7b-instruct
cd ../..
```

---

## Model Quantization

### Convert to GGUF Format

```bash
cd llama.cpp

# Convert HuggingFace model to F16 GGUF
python convert_hf_to_gguf.py \
  ../models/base/Qwen2.5-Math-7B-Instruct \
  --outtype f16 \
  --outfile ../models/quantized/qwen2.5-math-7b-instruct-f16.gguf
```

### Quantize the Model

#### For 16GB RAM (Best Quality - Recommended)
```bash
./build/bin/llama-quantize \
  ../models/quantized/qwen2.5-math-7b-instruct-f16.gguf \
  ../models/quantized/qwen2.5-math-7b-instruct-q5km.gguf \
  Q5_K_M
```

#### For 8GB RAM (Faster, Lower Quality)
```bash
./build/bin/llama-quantize \
  ../models/quantized/qwen2.5-math-7b-instruct-f16.gguf \
  ../models/quantized/qwen2.5-math-7b-instruct-q4km.gguf \
  Q4_K_M
```

```bash
cd ..
```

---

## Configuration

### Wolfram Alpha Setup (Optional)

1. **Get API Key**:
   - Visit https://developer.wolframalpha.com/
   - Sign up for free account
   - Generate App ID

2. **Create .env file**:
```bash
echo "WOLFRAM_ALPHA_APP_ID=your_api_key_here" > .env
```

3. **Enable when running**:
```bash
python main.py --query "Your query" --enable-wolfram
```

---

## Basic Usage

### Single Query Mode

```bash
# Basic query
python main.py --query "Solve for x: 2x + 5 = 13"

# With Wolfram Alpha enabled
python main.py --query "Integrate x^2 from 0 to 5" --enable-wolfram

# Verbose mode (shows cascade decisions)
python main.py --query "Derivative of x^3 + 2x" --verbose
```

### Interactive Mode

```bash
python main.py --interactive
```

In interactive mode:
- Type math questions directly
- Type `exit` or `quit` to exit
- Type `stats` to see performance statistics

### Test Mode

```bash
# Run built-in test suite
python main.py --test

# Run specific cascade tests
python scripts/testing/test_cascade.py

# Run SymPy handler tests
python scripts/testing/test_sympy_handler.py
```

---

## Command-Line Options

### Main Options

| Option | Description |
|--------|-------------|
| `--query TEXT` | Single query mode |
| `--interactive` | Interactive REPL mode |
| `--test` | Run test suite |
| `--enable-wolfram` | Enable Wolfram Alpha layer |
| `--verbose` | Show detailed logging |
| `--model PATH` | Specify custom model path |
| `--force-layer LAYER` | Force specific layer (sympy/wolfram/llm) |

### Example Commands

```bash
# Force SymPy layer only
python main.py --query "Factor x^2 - 4" --force-layer sympy

# Use custom model
python main.py --query "Solve x^2 = 4" --model models/quantized/custom-model.gguf

# Verbose mode with stats
python main.py --interactive --verbose
```

---

## Testing

### Run All Tests

```bash
python scripts/testing/test_cascade.py
```

### Run Specific Test Suites

```bash
# Test router logic only
python scripts/testing/test_cascade.py --test router

# Test SymPy layer only
python scripts/testing/test_cascade.py --test sympy

# Test cascade fallback
python scripts/testing/test_cascade.py --test cascade

# Performance testing
python scripts/testing/test_cascade.py --test performance
```

### Model Comparison

```bash
python scripts/testing/compare_llm_models.py
```

---

## Raspberry Pi Specific Setup

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv git git-lfs cmake build-essential
```

### 2. Increase Swap (for 8GB models)

```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 3. Optimize for ARM

Ensure llama.cpp is compiled with ARM NEON optimizations:

```bash
cd llama.cpp
cmake -B build -DLLAMA_NATIVE=ON -DLLAMA_NEON=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j4
cd ..
```

### 4. Power Management

```bash
# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable hciuart

# Disable HDMI (when headless)
sudo /usr/bin/tvservice -o

# Monitor temperature
vcgencmd measure_temp
```

---

## Troubleshooting

### Model Not Found

**Error**: `Could not find quantized model in models/quantized/`

**Solution**:
1. Verify model was quantized: `ls models/quantized/`
2. Check quantization step completed successfully
3. Ensure correct file name pattern (see Model Setup section)

### Out of Memory

**Error**: `RuntimeError: Out of memory`

**Solutions**:
1. Use Q4_K_M quantization instead of Q5_K_M
2. Increase swap space (Raspberry Pi)
3. Close other applications
4. Reduce context window: edit `llm_handler.py` → `n_ctx=1024`

### Slow Inference (Raspberry Pi)

**Issue**: LLM takes >30 seconds per query

**Solutions**:
1. Verify ARM NEON optimizations: Check llama.cpp compilation flags
2. Check thermal throttling: `vcgencmd measure_temp`
3. Ensure active cooling is working
4. Try Q4_K_M quantization for faster speed

### Wolfram Alpha Not Working

**Error**: `Wolfram Alpha request failed`

**Solutions**:
1. Verify `.env` file exists with correct API key
2. Check API key is valid at developer.wolframalpha.com
3. Ensure `--enable-wolfram` flag is used
4. Check internet connection

### Low Accuracy on Raspberry Pi

**Issue**: Model gives gibberish or incorrect answers

**Solutions**:
1. **Critical**: Recompile llama.cpp with ARM NEON flags:
   ```bash
   cd llama.cpp
   cmake -B build -DLLAMA_NATIVE=ON -DLLAMA_NEON=ON -DCMAKE_BUILD_TYPE=Release
   cmake --build build --config Release -j4
   cd ..
   ```
2. Re-quantize model after recompiling
3. Verify model file integrity: Check file size matches expected

---

## Hardware Integration (TI-84 + ESP32)

### ESP32 Setup

1. **Install ESP32 toolchain**:
   ```bash
   # Install PlatformIO or Arduino IDE
   # Upload firmware from scripts/hardware/esp32/
   ```

2. **Wire connections**:
   - GPIO16 → TI-84 TX (via 2.5mm jack)
   - GPIO17 → TI-84 RX
   - GPIO21 → INA219 SDA
   - GPIO22 → INA219 SCL

3. **Power**: 5V USB or Pi GPIO

### TI-84 Setup

1. **Transfer TI-BASIC programs**:
   - Connect TI-84 to computer
   - Copy programs from `scripts/hardware/ti84/`
   - Programs: MATHMENU, ALGEBRA, CALCULUS, etc.

2. **Run MATHMENU**:
   - Opens template selection interface
   - Sends queries via serial to Pi

---

## Performance Optimization

### Memory Usage
- **8GB RAM**: Use Q4_K_M, limit context to 1024
- **16GB RAM**: Use Q5_K_M, context 2048 (recommended)

### Speed Optimization
1. Enable query caching (enabled by default)
2. Use SymPy for simple queries (automatic)
3. Reduce max_tokens in `llm_handler.py` if answers are too long

### Battery Life (Raspberry Pi)
1. Disable HDMI: `sudo /usr/bin/tvservice -o`
2. Disable Bluetooth: `sudo systemctl disable bluetooth`
3. Disable WiFi if not needed: `sudo ifconfig wlan0 down`
4. Use cascade routing (automatic)

---

## Updating

### Update Code

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Update llama.cpp

```bash
cd llama.cpp
git pull
cmake --build build --config Release
cd ..
```

### Update Models

```bash
cd models/base/Qwen2.5-Math-7B-Instruct
git pull
cd ../../..
# Re-run quantization steps
```

---

## Getting Help

### Documentation
- [Technical Specifications](TECHNICAL_SPECS.md)
- [Main README](README.md)
- [Phase Documentation](docs/)

### Logs
Check logs for detailed error information:
```bash
cat logs/calculator_engine.log
cat logs/test_results_latest.json
```

### Common Commands

```bash
# Check Python version
python3 --version

# Check installed packages
pip list

# Verify llama.cpp build
./llama.cpp/build/bin/llama-cli --version

# Test model loading
python main.py --query "2+2" --verbose
```

---

## Next Steps

After successful installation:

1. **Run tests**: `python main.py --test`
2. **Try interactive mode**: `python main.py --interactive`
3. **Read [Technical Specs](TECHNICAL_SPECS.md)** for performance details
4. **Explore cascade routing**: Use `--verbose` to see decision-making
5. **Configure Wolfram Alpha** for enhanced capabilities

---

## License

Independent Study Project
