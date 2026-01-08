# Technical Specifications

## System Architecture

Holy Calculator uses a 3-layer cascade system that automatically routes math queries to the best solver:
- **Layer 1 (SymPy)**: Fast symbolic math - solves 40-50% of queries in <1 second
- **Layer 2 (Wolfram Alpha)**: Comprehensive math engine - handles 90%+ of queries (requires API key)
- **Layer 3 (LLM)**: Advanced reasoning fallback using **Qwen2.5-Math-7B-Instruct** - tackles word problems, proofs, and conceptual explanations

---

## Performance Metrics

### Layer Performance

| Layer | Success Rate | Avg Response Time | Coverage |
|-------|--------------|-------------------|----------|
| SymPy | 92.9% | 0.005s | ~45% |
| Wolfram | ~95% | 1-3s | ~90% |
| LLM (Qwen2.5-Math) | 83.6% (MATH) / 91.6% (GSM8K) | 5-15s | 100% |

### Model Comparison

| Model | MATH Score | GSM8K | Context | Size (Q4_K_M) |
|-------|-----------|-------|---------|---------------|
| Qwen2.5-Math-7B-Instruct | 83.6% | 91.6% | 32k | 4.4GB |
| DeepSeek-Math-7B-Instruct | ~55% | ~82% | 16k | 3.9GB |

**Winner**: Qwen2.5-Math (+28% accuracy on MATH benchmark)

---

## Hardware Specifications

### Primary Target Platform
- **Device**: Raspberry Pi 5
- **Recommended RAM**: 16GB
- **Minimum RAM**: 8GB
- **CPU**: ARM Cortex-A76 (2.4 GHz quad-core)
- **Storage**: 225GB+ SSD recommended
- **Operating System**: Raspberry Pi OS (64-bit)

### Secondary Hardware Components
- **TI-84 Plus CE**: Calculator interface via serial port
- **ESP32-PICO-MINI-02**: Bridge for wireless/serial communication
- **INA219 Sensor**: Power monitoring via I2C
- **NPU HAT**: 13 TOPS neural processing unit (Phase 4 - visual learning)

### Power System
- **Battery**: Waveshare UPS HAT (D) - 5000mAh @ 3.7V = 18.5Wh
- **Runtime**: 6-8 hours typical usage, 4-5 hours continuous heavy use
- **Power Draw**:
  - Idle: ~2.5W
  - SymPy queries: 4.8W
  - LLM queries: 9.1W
  - Average (50-query session): ~3.0W

### Cooling System
- **Active Cooling**: 30mm 5V fan, 0.7W draw, ~6000 RPM, <25dB
- **Temperature Range**: 65-70°C under LLM load
- **Planned PWM Control**: Temperature-triggered activation (Phase 3)

---

## LLM Specifications

### Quantization Levels

| Quantization | Size | Accuracy | Speed (tok/s) | Use Case |
|--------------|------|----------|---------------|----------|
| Q8_0 | 7GB | ~95% | 1-2 | Too slow |
| Q5_K_M | 4.1GB | 70-80% | 2-5 | **Recommended** |
| Q4_K_M | 4.4GB | ~70% | 3-6 | Alternative |
| Q4_0 | 3.2GB | ~35% | 4-7 | Unusable |

**Selected**: Q5_K_M (mixed-precision, optimal accuracy/speed tradeoff)

### Model Configuration
- **Context Window**: 2048 tokens (optimized for math queries)
- **Temperature**: 0.1 (deterministic mathematical outputs)
- **Max Tokens**: 256 (concise answers)
- **Inference Engine**: llama.cpp with ARM NEON SIMD optimizations

### Compilation Flags (Raspberry Pi 5)
```bash
cmake .. -DLLAMA_NATIVE=ON -DLLAMA_NEON=ON -DCMAKE_BUILD_TYPE=Release
make -j4
```

---

## Cascade Architecture Details

### Routing Decision Tree

1. **Query Analysis** (40ms total overhead)
   - SymPy parser check (35ms)
   - Computational keywords (5ms)
   - Reasoning indicators (5ms)

2. **Routing Accuracy**: 90%+

3. **Execution Order**:
   - Primary layer (router decision)
   - Fallback layers (if primary fails)
   - Tier 4: Decline/external (out-of-domain)

### Power Efficiency

| Scenario | Energy (Wh) | Queries | Improvement |
|----------|-------------|---------|-------------|
| LLM-only | 3.79 | 50 | Baseline |
| Cascade | 0.61 | 50 | **6× better** |

---

## Project Structure

```
Holy_Calculator/
├── main.py              # Main entry point
├── requirements.txt     # Python dependencies
├── .env                 # API keys (Wolfram Alpha)
├── models/
│   ├── base/           # Original models from HuggingFace
│   └── quantized/      # Quantized GGUF models (gitignored)
├── scripts/
│   ├── cascade/        # Cascade orchestration
│   │   ├── calculator_engine.py
│   │   ├── sympy_handler.py
│   │   ├── wolfram_handler.py
│   │   ├── llm_handler.py
│   │   ├── query_classifier.py
│   │   ├── query_translator.py
│   │   └── query_cache.py
│   ├── monitoring/     # Performance monitoring
│   ├── testing/        # Test suites
│   │   ├── test_sympy_handler.py
│   │   ├── test_cascade.py
│   │   └── compare_llm_models.py
│   └── hardware/       # Hardware integration (ESP32, TI-84)
├── data/
│   └── test-cases/     # Mathematical test problems (YAML)
├── logs/               # Test results and performance logs
└── docs/               # Comprehensive documentation
    ├── phase5-summary.md
    ├── phase6-summary.md
    ├── phase7-summary.md
    └── phase7.5-model-comparison-summary.md
```

---

## Development Phases

### Completed ✅
- **Phase 0-2**: Environment setup, llama.cpp build, model acquisition
- **Phase 5**: SymPy integration (92.9% test success rate)
- **Phase 6**: Wolfram Alpha integration (API handler, rate limiting)
- **Phase 7**: Full cascade integration and testing
- **Phase 7.5**: LLM model comparison (Qwen2.5-Math selected)

### Current 🟡
- **Phase 8**: Hardware integration (Raspberry Pi 5, TI-84, ESP32)

### Planned 📋
- **Phase 9**: User interface improvements
- **Phase 10**: Battery optimization and PWM fan control
- **Phase 11**: Comprehensive testing and validation
- **Phase 12**: Documentation finalization
- **Phase 13**: Deployment and packaging

---

## TI-84 Interface Protocol

### Communication Specifications
- **Baud Rate**: 9600
- **Protocol**: UART over 2.5mm I/O port
- **Bridge**: ESP32 (GPIO16/17)
- **Templates**: 7 categories, 25+ question templates
- **Connection Modes**:
  - Direct USB: TI-84 → USB → Pi (~4W)
  - ESP32 Bridge: TI-84 → ESP32 → Pi (~2.3W, 40% savings)

### Template Categories
1. Algebra
2. Calculus
3. Explain
4. Geometry
5. Statistics
6. Custom
7. History

---

## ESP32 PCB Components

### Integrated Components
- **AP2112 voltage regulator**: 3.3V LDO, 600mA capacity
- **MBR540 Schottky diodes**: Reverse current protection (0.4V drop)
- **GPIO21/22**: I2C bus (SDA/SCL) for INA219 power sensor
- **GPIO16/17**: UART (TX/RX) for TI-84 serial communication
- **Flash**: 4MB integrated (PICO variant)
- **Processor**: Dual-core 240 MHz

---

## Accuracy Measurements

### Real-World Performance (150-query validation)

**SymPy Tier**:
- 80% correct final answers on symbolic math
- 8.7ms average latency
- 97% complete under 100ms

**LLM Tier**:
- 80% on straightforward problems with concise answers
- 70% on complex multi-step problems requiring detailed explanations
- Accuracy decreases as answer length/complexity increases

**Note**: These are system accuracy measurements on real student queries, not benchmark scores. The base Qwen2.5-Math-7B-Instruct model scores 83.6% on the academic MATH benchmark; quantization and real-world deployment introduce additional challenges.

---

## System Optimizations

### Implemented Optimizations

| Optimization | Impact | Power Savings |
|--------------|--------|---------------|
| Query caching | 20% fewer computations | ~0.4W |
| Context size (2048 vs 4096) | 30% faster LLM | ~0.3W |
| Temperature = 0.1 | Deterministic outputs | - |
| Reduced token generation | 50% less generation | ~0.5W |
| Disabled peripherals | HDMI, BT, LEDs off | ~0.7W |
| **Total** | - | **~2.15W (43% of budget)** |

### Rejected Optimizations

| Optimization | Power Savings | Rejected Because |
|--------------|---------------|------------------|
| CPU underclocking | 1-3W | 35% slower LLM inference |
| Q4_0 quantization | 900MB RAM | 50% accuracy loss |
| 4096 context window | - | 30% slower, unnecessary |

---

## Configuration Options

### Model Selection Priority
1. `qwen2.5-math-7b-instruct-q5km.gguf` (best quality)
2. `qwen2.5-math-7b-instruct-q4km.gguf` (faster)
3. `deepseek-math-7b-q5km.gguf` (fallback)
4. `deepseek-math-7b-q4km.gguf` (fallback)

Override with `--model` flag

### Wolfram Alpha Setup
- API key required from https://developer.wolframalpha.com/
- Configure in `.env` file
- Enable with `--enable-wolfram` flag

---

## Future Enhancements (Phase 4)

### Visual Learning with NPU HAT
- **NPU**: 13 TOPS neural processing unit
- **Handwriting recognition**: Camera module → step-by-step analysis
- **Diagram analysis**: Hand-drawn graphs, geometric figures
- **Offline processing**: No cloud APIs, complete privacy

---

## License

Independent Study Project
