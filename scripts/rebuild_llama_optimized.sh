#!/bin/bash
# Rebuild llama.cpp with ARM-optimized settings for Raspberry Pi

set -e  # Exit on error

echo "======================================================================="
echo "LLAMA.CPP OPTIMIZED REBUILD FOR ARM/RASPBERRY PI"
echo "======================================================================="

LLAMA_DIR="llama.cpp"

if [ ! -d "$LLAMA_DIR" ]; then
    echo "✗ llama.cpp directory not found!"
    echo "  Please clone it first: git clone https://github.com/ggerganov/llama.cpp.git"
    exit 1
fi

cd "$LLAMA_DIR"

echo ""
echo "📍 Current directory: $(pwd)"
echo ""

# Check for dependencies
echo "🔍 Checking dependencies..."

# Check for OpenBLAS (optional but recommended)
if pkg-config --exists openblas; then
    echo "✓ OpenBLAS found"
    USE_BLAS=1
else
    echo "⚠ OpenBLAS not found (performance will be reduced)"
    echo "  Install with: sudo apt install libopenblas-dev"

    read -p "Continue without OpenBLAS? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborting. Please install OpenBLAS first."
        exit 1
    fi
    USE_BLAS=0
fi

# Backup old build if it exists
if [ -d "build" ]; then
    echo ""
    echo "📦 Backing up old build..."
    BACKUP_NAME="build.backup.$(date +%Y%m%d_%H%M%S)"
    mv build "$BACKUP_NAME"
    echo "✓ Old build saved to: $BACKUP_NAME"
fi

# Configure build
echo ""
echo "🔧 Configuring optimized build..."
echo "-----------------------------------------------------------------------"

CMAKE_FLAGS=(
    -B build
    -DCMAKE_BUILD_TYPE=Release
    -DCMAKE_CXX_FLAGS="-O3 -march=native -mcpu=native -mtune=native"
    -DCMAKE_C_FLAGS="-O3 -march=native -mcpu=native -mtune=native"
    -DGGML_NATIVE=ON
)

# Add BLAS if available
if [ $USE_BLAS -eq 1 ]; then
    CMAKE_FLAGS+=(
        -DGGML_BLAS=ON
        -DGGML_BLAS_VENDOR=OpenBLAS
    )
    echo "✓ BLAS support: ENABLED (OpenBLAS)"
else
    echo "⚠ BLAS support: DISABLED"
fi

# CPU-only (no CUDA, no Metal)
CMAKE_FLAGS+=(
    -DGGML_CUDA=OFF
    -DGGML_METAL=OFF
)

echo ""
echo "CMake configuration:"
for flag in "${CMAKE_FLAGS[@]}"; do
    echo "  $flag"
done

echo ""
read -p "Proceed with this configuration? (Y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "Aborting."
    exit 1
fi

# Run CMake
echo ""
echo "🏗️  Running CMake..."
cmake "${CMAKE_FLAGS[@]}"

if [ $? -ne 0 ]; then
    echo "✗ CMake configuration failed!"
    exit 1
fi

echo "✓ CMake configuration complete"

# Build
echo ""
echo "🔨 Building llama.cpp..."
echo "This may take 10-20 minutes on Raspberry Pi..."
echo "-----------------------------------------------------------------------"

# Determine number of cores (use n-1 to avoid freezing)
CORES=$(nproc)
MAKE_JOBS=$((CORES > 1 ? CORES - 1 : 1))

echo "Using $MAKE_JOBS parallel jobs (${CORES} cores available)"
echo ""

START_TIME=$(date +%s)

make -C build -j$MAKE_JOBS

if [ $? -ne 0 ]; then
    echo "✗ Build failed!"
    exit 1
fi

END_TIME=$(date +%s)
BUILD_DURATION=$((END_TIME - START_TIME))

echo ""
echo "✓ Build complete in ${BUILD_DURATION}s ($((BUILD_DURATION / 60))m $((BUILD_DURATION % 60))s)"

# Verify binary
echo ""
echo "🔍 Verifying build..."

LLAMA_CLI="build/bin/llama-cli"

if [ ! -f "$LLAMA_CLI" ]; then
    echo "✗ llama-cli binary not found!"
    exit 1
fi

echo "✓ Binary: $LLAMA_CLI"
echo "  Size: $(du -h "$LLAMA_CLI" | cut -f1)"

# Test run (quick check)
echo ""
echo "🧪 Testing binary..."

if $LLAMA_CLI --help > /dev/null 2>&1; then
    echo "✓ Binary runs successfully"
else
    echo "✗ Binary test failed!"
    exit 1
fi

# Summary
echo ""
echo "======================================================================="
echo "✅ REBUILD COMPLETE"
echo "======================================================================="
echo ""
echo "Optimizations applied:"
echo "  ✓ Release build (-O3)"
echo "  ✓ Native CPU optimizations (-march=native -mcpu=native)"
echo "  ✓ GGML native optimizations"
if [ $USE_BLAS -eq 1 ]; then
    echo "  ✓ OpenBLAS acceleration"
fi
echo ""
echo "Next steps:"
echo "  1. Test performance: python3 scripts/benchmark_quantizations.py"
echo "  2. Update threads in platform_config.py if you have good cooling"
echo "  3. Run interactive mode: ./run_interactive.sh"
echo ""
echo "Expected improvements:"
echo "  • 1.5-3x faster inference"
echo "  • Better NEON SIMD utilization"
if [ $USE_BLAS -eq 1 ]; then
    echo "  • Accelerated matrix operations"
fi
echo ""
echo "======================================================================="

cd ..
