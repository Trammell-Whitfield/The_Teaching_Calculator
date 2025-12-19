#!/bin/bash
# Check llama.cpp build configuration and optimizations

echo "======================================================================="
echo "LLAMA.CPP BUILD CONFIGURATION CHECK"
echo "======================================================================="

LLAMA_DIR="llama.cpp"
BUILD_DIR="$LLAMA_DIR/build"

if [ ! -d "$LLAMA_DIR" ]; then
    echo "✗ llama.cpp directory not found!"
    echo "  Expected at: $LLAMA_DIR"
    exit 1
fi

if [ ! -d "$BUILD_DIR" ]; then
    echo "✗ Build directory not found!"
    echo "  llama.cpp has not been built yet."
    echo "  Run: cd llama.cpp && cmake -B build && make -C build"
    exit 1
fi

echo ""
echo "📂 Build Directory: $BUILD_DIR"
echo ""

# Check CMakeCache.txt
CACHE_FILE="$BUILD_DIR/CMakeCache.txt"

if [ ! -f "$CACHE_FILE" ]; then
    echo "✗ CMakeCache.txt not found!"
    exit 1
fi

echo "🔍 CHECKING OPTIMIZATION FLAGS:"
echo "-----------------------------------------------------------------------"

# Check C++ flags
echo ""
echo "C++ Compiler Flags:"
grep "CMAKE_CXX_FLAGS:" "$CACHE_FILE" | head -1

echo ""
echo "C++ Release Flags:"
grep "CMAKE_CXX_FLAGS_RELEASE:" "$CACHE_FILE" | head -1

# Check for ARM-specific optimizations
echo ""
echo "-----------------------------------------------------------------------"
echo "🔧 ARM OPTIMIZATION FLAGS:"
echo "-----------------------------------------------------------------------"

# Check for march/mcpu
if grep -qi "march=native\|mcpu=native" "$CACHE_FILE"; then
    echo "✓ Native CPU optimizations ENABLED (-march=native or -mcpu=native)"
else
    echo "✗ Native CPU optimizations NOT FOUND"
    echo "  Recommendation: Add -march=native to CMAKE_CXX_FLAGS"
fi

# Check for NEON
if grep -qi "neon" "$CACHE_FILE"; then
    echo "✓ NEON SIMD support detected"
else
    echo "⚠ NEON support not explicitly mentioned (may still be enabled via -march=native)"
fi

# Check build type
echo ""
echo "-----------------------------------------------------------------------"
echo "🏗️  BUILD CONFIGURATION:"
echo "-----------------------------------------------------------------------"

BUILD_TYPE=$(grep "CMAKE_BUILD_TYPE:" "$CACHE_FILE" | cut -d'=' -f2)
echo "Build Type: ${BUILD_TYPE:-[NOT SET]}"

if [ "$BUILD_TYPE" = "Release" ]; then
    echo "✓ Release build (optimized)"
elif [ "$BUILD_TYPE" = "RelWithDebInfo" ]; then
    echo "⚠ RelWithDebInfo build (optimized with debug info)"
else
    echo "✗ NOT a release build! Performance will be poor."
    echo "  Recommendation: Rebuild with -DCMAKE_BUILD_TYPE=Release"
fi

# Check GGML options
echo ""
echo "-----------------------------------------------------------------------"
echo "⚙️  GGML OPTIONS:"
echo "-----------------------------------------------------------------------"

# BLAS support
if grep -qi "GGML_BLAS:BOOL=ON" "$CACHE_FILE"; then
    echo "✓ BLAS support ENABLED (accelerated matrix operations)"
    BLAS_VENDOR=$(grep "GGML_BLAS_VENDOR:" "$CACHE_FILE" | cut -d'=' -f2)
    if [ -n "$BLAS_VENDOR" ]; then
        echo "  BLAS vendor: $BLAS_VENDOR"
    fi
else
    echo "✗ BLAS support DISABLED"
    echo "  Recommendation: Enable with -DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS"
fi

# Native support
if grep -qi "GGML_NATIVE:BOOL=ON" "$CACHE_FILE"; then
    echo "✓ GGML_NATIVE ENABLED (platform-specific optimizations)"
else
    echo "⚠ GGML_NATIVE not enabled"
    echo "  Recommendation: Enable with -DGGML_NATIVE=ON"
fi

# Check for GPU support (should be OFF on Pi)
if grep -qi "GGML_CUDA:BOOL=ON\|GGML_METAL:BOOL=ON" "$CACHE_FILE"; then
    echo "⚠ GPU acceleration enabled (not applicable for Raspberry Pi)"
else
    echo "✓ CPU-only build (correct for Raspberry Pi)"
fi

# Binary check
echo ""
echo "-----------------------------------------------------------------------"
echo "🔨 BINARY INFORMATION:"
echo "-----------------------------------------------------------------------"

LLAMA_CLI="$BUILD_DIR/bin/llama-cli"

if [ -f "$LLAMA_CLI" ]; then
    echo "Binary: $LLAMA_CLI"
    echo "Size: $(du -h "$LLAMA_CLI" | cut -f1)"

    # Check if it's ARM binary
    if file "$LLAMA_CLI" | grep -qi "ARM\|aarch64"; then
        echo "✓ ARM binary detected"
    else
        echo "⚠ Not an ARM binary (cross-compiled?)"
    fi

    # Try to run version check
    echo ""
    echo "Version info:"
    "$LLAMA_CLI" --version 2>/dev/null || echo "  (Version flag not supported)"
else
    echo "✗ llama-cli binary not found at: $LLAMA_CLI"
fi

# Summary and recommendations
echo ""
echo "======================================================================="
echo "📋 RECOMMENDATIONS:"
echo "======================================================================="

NEEDS_REBUILD=0

if ! grep -qi "CMAKE_BUILD_TYPE:.*Release" "$CACHE_FILE"; then
    echo "🔴 CRITICAL: Rebuild with Release mode"
    NEEDS_REBUILD=1
fi

if ! grep -qi "march=native\|mcpu=native" "$CACHE_FILE"; then
    echo "🟡 RECOMMENDED: Enable native CPU optimizations (-march=native)"
    NEEDS_REBUILD=1
fi

if ! grep -qi "GGML_BLAS:BOOL=ON" "$CACHE_FILE"; then
    echo "🟡 RECOMMENDED: Enable BLAS for faster matrix operations"
    NEEDS_REBUILD=1
fi

if ! grep -qi "GGML_NATIVE:BOOL=ON" "$CACHE_FILE"; then
    echo "🟡 RECOMMENDED: Enable GGML_NATIVE for platform optimizations"
    NEEDS_REBUILD=1
fi

if [ $NEEDS_REBUILD -eq 1 ]; then
    echo ""
    echo "To rebuild with optimizations, run:"
    echo ""
    echo "  ./scripts/rebuild_llama_optimized.sh"
    echo ""
else
    echo "✓ Build appears optimized! No changes recommended."
fi

echo "======================================================================="
