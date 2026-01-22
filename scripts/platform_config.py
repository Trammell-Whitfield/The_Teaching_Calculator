#!/usr/bin/env python3
"""
Platform Configuration Module
Automatically detects platform and adjusts performance parameters.

This module ensures Holy Calculator runs optimally on:
- Development machines (macOS/Linux/Windows with desktop CPUs)
- Raspberry Pi 5 (ARM64, 8GB or 16GB)
- Other ARM devices
"""

import platform
import os
import psutil
from pathlib import Path
from typing import Dict, Any, Optional


class PlatformConfig:
    """Platform-aware configuration manager."""

    def __init__(self):
        """Initialize platform detection."""
        self.machine = platform.machine().lower()
        self.system = platform.system().lower()
        self.cpu_count = os.cpu_count() or 2
        self.total_ram_gb = psutil.virtual_memory().total / (1024**3)

        # Detect platform type
        self.is_raspberry_pi = self._detect_raspberry_pi()
        self.is_arm = self.machine in ['aarch64', 'armv7l', 'arm64']
        # macOS (Darwin) on ARM (M-series) is still a desktop/laptop
        self.is_desktop = not self.is_arm or self.system == 'darwin'

        # Determine optimal configuration
        self.config = self._build_config()

    def _detect_raspberry_pi(self) -> bool:
        """
        Detect if running on a Raspberry Pi.

        Returns:
            True if Raspberry Pi is detected, False otherwise
        """
        # Check /proc/device-tree/model (most reliable for Pi)
        model_file = Path('/proc/device-tree/model')
        if model_file.exists():
            try:
                model = model_file.read_text().strip('\x00').lower()
                if 'raspberry pi' in model:
                    return True
            except:
                pass

        # Fallback: Check for ARM + specific CPU patterns
        if self.machine in ['aarch64', 'armv7l']:
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read().lower()
                    if 'bcm' in cpuinfo or 'raspberry' in cpuinfo:
                        return True
            except:
                pass

        return False

    def _build_config(self) -> Dict[str, Any]:
        """
        Build platform-specific configuration.

        Returns:
            Dictionary with optimized parameters
        """
        if self.is_raspberry_pi:
            return self._pi_config()
        elif self.is_arm:
            return self._generic_arm_config()
        else:
            return self._desktop_config()

    def _pi_config(self) -> Dict[str, Any]:
        """
        Raspberry Pi optimized configuration.

        Assumes Pi 5 with either 8GB or 16GB RAM.
        """
        # Determine model preference based on RAM
        if self.total_ram_gb >= 14:  # 16GB Pi
            preferred_quantization = 'q5km'
            context_window = 2048
        else:  # 8GB Pi
            preferred_quantization = 'q4km'
            context_window = 1024

        return {
            'platform': 'raspberry_pi',
            'description': f'Raspberry Pi ({self.total_ram_gb:.1f}GB RAM)',

            # Model selection
            'preferred_quantization': preferred_quantization,
            'model_preference_order': [
                f'qwen2.5-math-7b-instruct-{preferred_quantization}.gguf',
                'qwen2.5-math-7b-instruct-q4km.gguf',  # Always have Q4 fallback
                f'deepseek-math-7b-{preferred_quantization}.gguf',
                'deepseek-math-7b-q4km.gguf',
            ],

            # Inference parameters (optimized for math queries)
            'n_threads': 4,  # Increased from 2 - safe with good cooling (<70°C)
            'n_ctx': context_window,
            'n_predict': 256,  # Increased for full explanations (calculus, word problems)
            'temperature': 0.3,  # Increased from 0.1 - prevents reasoning loops

            # Memory management
            'use_mmap': True,  # Essential for fast model loading
            'use_mlock': False,  # Don't lock memory (let system manage)
            'n_gpu_layers': 0,  # No GPU on Pi

            # Performance expectations
            'expected_tokens_per_sec': 3.5,  # 2-5 tok/s with optimized build & 4 threads
            'model_load_time_sec': 20,  # 15-25s typical
            'thermal_threshold_celsius': 80,  # Start warning at 80°C

            # Battery optimization
            'enable_aggressive_caching': True,
            'cache_responses_indefinitely': True,  # Math answers don't change
        }

    def _generic_arm_config(self) -> Dict[str, Any]:
        """Configuration for generic ARM devices (not Pi-specific)."""
        # Prefer Q5 for better quality if enough RAM
        if self.total_ram_gb >= 12:
            preferred_quant = 'q5km'
            fallback_quant = 'q4km'
        else:
            preferred_quant = 'q4km'
            fallback_quant = 'q5km'

        return {
            'platform': 'generic_arm',
            'description': f'ARM device ({self.total_ram_gb:.1f}GB RAM)',

            'preferred_quantization': preferred_quant,
            'model_preference_order': [
                f'qwen2.5-math-7b-instruct-{preferred_quant}.gguf',
                f'qwen2.5-math-7b-instruct-{fallback_quant}.gguf',
                f'deepseek-math-7b-{preferred_quant}.gguf',
                f'deepseek-math-7b-{fallback_quant}.gguf',
            ],

            'n_threads': min(4, self.cpu_count),
            'n_ctx': 2048,
            'n_predict': 256,  # Reduced from 512 - math answers are usually concise
            'temperature': 0.3,  # Increased from 0.1 - prevents reasoning loops

            'use_mmap': True,
            'use_mlock': False,
            'n_gpu_layers': 0,

            'expected_tokens_per_sec': 3.0,
            'model_load_time_sec': 15,
            'thermal_threshold_celsius': 85,

            'enable_aggressive_caching': True,
            'cache_responses_indefinitely': True,
        }

    def _desktop_config(self) -> Dict[str, Any]:
        """Configuration for desktop/laptop development machines."""
        # More RAM = prefer Q5 for quality
        if self.total_ram_gb >= 16:
            preferred_quant = 'q5km'
        else:
            preferred_quant = 'q4km'

        return {
            'platform': 'desktop',
            'description': f'Desktop/Laptop ({self.total_ram_gb:.1f}GB RAM)',

            'preferred_quantization': preferred_quant,
            'model_preference_order': [
                f'qwen2.5-math-7b-instruct-{preferred_quant}.gguf',
                'qwen2.5-math-7b-instruct-q5km.gguf',
                'qwen2.5-math-7b-instruct-q4km.gguf',
                f'deepseek-math-7b-{preferred_quant}.gguf',
            ],

            # Desktop: use more threads for speed
            'n_threads': min(8, self.cpu_count),
            'n_ctx': 4096,  # Larger context window
            'n_predict': 256,  # Reduced from 1024 - math answers are usually concise
            'temperature': 0.3,  # Increased from 0.1 - prevents reasoning loops

            'use_mmap': True,
            'use_mlock': False,
            'n_gpu_layers': 0,  # CPU-only (GPU support could be added)

            'expected_tokens_per_sec': 10.0,  # Much faster on desktop
            'model_load_time_sec': 5,
            'thermal_threshold_celsius': 90,

            'enable_aggressive_caching': True,
            'cache_responses_indefinitely': True,
        }

    def get_llm_params(self) -> Dict[str, Any]:
        """
        Get LLM inference parameters for current platform.

        Returns:
            Dictionary suitable for passing to LLMHandler
        """
        return {
            'n_threads': self.config['n_threads'],
            'n_ctx': self.config['n_ctx'],
            'n_predict': self.config['n_predict'],
            'temperature': self.config['temperature'],
            'use_mmap': self.config['use_mmap'],
            'use_mlock': self.config['use_mlock'],
        }

    def get_model_preference(self) -> list:
        """Get ordered list of preferred models for this platform."""
        return self.config['model_preference_order']

    def print_info(self):
        """Print platform detection results."""
        print("=" * 70)
        print("PLATFORM CONFIGURATION")
        print("=" * 70)
        print(f"Platform: {self.config['description']}")
        print(f"Architecture: {self.machine}")
        print(f"System: {self.system}")
        print(f"CPU cores: {self.cpu_count}")
        print(f"Total RAM: {self.total_ram_gb:.1f}GB")
        print(f"\nOptimized for: {self.config['platform']}")
        print(f"Preferred quantization: {self.config['preferred_quantization']}")
        print(f"Inference threads: {self.config['n_threads']}")
        print(f"Context window: {self.config['n_ctx']}")
        print(f"Expected performance: ~{self.config['expected_tokens_per_sec']:.1f} tokens/sec")
        print("=" * 70 + "\n")


def get_platform_config() -> PlatformConfig:
    """
    Get platform configuration (convenience function).

    Returns:
        PlatformConfig instance
    """
    return PlatformConfig()


def main():
    """Test platform detection."""
    config = PlatformConfig()
    config.print_info()

    print("LLM Parameters:")
    for key, value in config.get_llm_params().items():
        print(f"  {key}: {value}")

    print("\nModel Preference Order:")
    for i, model in enumerate(config.get_model_preference(), 1):
        print(f"  {i}. {model}")


if __name__ == '__main__':
    main()
