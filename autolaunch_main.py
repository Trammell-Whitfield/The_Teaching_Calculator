#!/usr/bin/env python3
"""
Holy Calculator - Auto-Launch Entry Point
Auto-launched by systemd when TI-84 is connected via USB.

This script:
1. Verifies TI-84 Plus Silver is connected (VID: 0451, PID: e008)
2. Initializes the cascade engine (SymPy -> Wolfram -> LLM)
3. Starts the teaching interface
4. Handles graceful shutdown on disconnect/signals
"""

import logging
import sys
import signal
import time
import subprocess
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

# Configuration
LOG_DIR = Path(__file__).parent
LOG_FILE = LOG_DIR / "calculator.log"
USB_VENDOR = "0451"
USB_PRODUCT = "e008"
MAX_DETECTION_ATTEMPTS = 10
DETECTION_RETRY_DELAY = 2  # seconds


class HolyCalculatorApp:
    """Main application class for Holy Calculator auto-launch."""

    def __init__(self):
        self.running = False
        self.interface = None
        self.setup_logging()
        self.setup_signal_handlers()

    def setup_logging(self):
        """Configure logging to file and console (journald)."""
        # Create log directory if needed
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("HolyCalculator")

    def setup_signal_handlers(self):
        """Handle graceful shutdown on SIGTERM/SIGINT."""
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Graceful shutdown handler."""
        signal_names = {signal.SIGTERM: 'SIGTERM', signal.SIGINT: 'SIGINT'}
        signal_name = signal_names.get(signum, str(signum))

        self.logger.info(f"Received {signal_name}, shutting down gracefully...")
        self.running = False

        # Clean up interface if active
        if self.interface:
            try:
                self.interface.print_stats()
                self.logger.info("Statistics logged before shutdown")
            except Exception as e:
                self.logger.warning(f"Could not log final stats: {e}")

        self.logger.info("Holy Calculator shutdown complete")
        sys.exit(0)

    def verify_calculator_connected(self) -> bool:
        """
        Check if TI-84 Plus Silver is connected via USB.

        Uses lsusb to detect the device by VID:PID (0451:e008).
        Retries up to MAX_DETECTION_ATTEMPTS with delays.

        Returns:
            True if TI-84 detected, False otherwise
        """
        for attempt in range(1, MAX_DETECTION_ATTEMPTS + 1):
            try:
                result = subprocess.run(
                    ['lsusb'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                # Check for our specific device
                device_id = f"{USB_VENDOR}:{USB_PRODUCT}"
                if device_id in result.stdout:
                    self.logger.info(f"TI-84 Plus Silver detected (attempt {attempt})")

                    # Log device details
                    for line in result.stdout.split('\n'):
                        if device_id in line:
                            self.logger.info(f"  Device: {line.strip()}")
                            break

                    return True

                self.logger.info(
                    f"Waiting for TI-84... ({attempt}/{MAX_DETECTION_ATTEMPTS})"
                )
                time.sleep(DETECTION_RETRY_DELAY)

            except subprocess.TimeoutExpired:
                self.logger.warning(f"lsusb timeout on attempt {attempt}")
            except FileNotFoundError:
                self.logger.error("lsusb not found - install usbutils package")
                return False
            except Exception as e:
                self.logger.error(f"Error checking USB: {e}")

        return False

    def initialize_cascade_engine(self):
        """
        Initialize the three-tier cascade engine.

        Layers:
            1. SymPy (fast, offline symbolic math)
            2. Wolfram Alpha (comprehensive, online API)
            3. Qwen2.5-Math-7B (LLM fallback, offline)
        """
        self.logger.info("Initializing cascade engine...")

        try:
            from cascade.calculator_engine import CalculatorEngine

            # Find the best available model
            model_path = self._get_best_model()
            self.logger.info(f"Using model: {model_path}")

            # Initialize engine (Wolfram disabled by default for offline operation)
            self.engine = CalculatorEngine(
                enable_wolfram=False,
                model_path=str(model_path) if model_path else None
            )

            self.logger.info("Cascade engine initialized successfully")
            return True

        except ImportError as e:
            self.logger.error(f"Failed to import cascade engine: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to initialize cascade engine: {e}")
            return False

    def _get_best_model(self) -> Path:
        """Find the best available quantized model."""
        quantized_dir = Path(__file__).parent / 'models' / 'quantized'

        # Prefer Q5_K_M for quality on 16GB Raspberry Pi 5
        preferred_models = [
            'qwen2.5-math-7b-instruct-q5km.gguf',
            'qwen2.5-math-7b-instruct-q4km.gguf',
            'deepseek-math-7b-q5km.gguf',
            'deepseek-math-7b-q4km.gguf',
        ]

        for model_name in preferred_models:
            model_path = quantized_dir / model_name
            if model_path.exists():
                return model_path

        self.logger.warning("No preferred model found, using default path")
        return quantized_dir / 'qwen2.5-math-7b-instruct-q5km.gguf'

    def start_teaching_interface(self):
        """
        Launch the teaching interface with pedagogical features.

        Features:
            - Intent classification (tutoring, explanation, verification, quick-answer)
            - Socratic questioning approach
            - Answer leakage prevention
            - Auto-detection of TI-84 serial port
        """
        self.logger.info("Starting teaching interface...")

        try:
            from hardware.ti84_interface import TI84Interface
            from cascade.pedagogical_wrapper import PedagogicalWrapper
            from cascade.intent_classifier import IntentClassifier
            from cascade.response_validator import ResponseValidator

            # Import the TeachingInterface class
            # We create a local version that uses our pre-initialized engine
            class TeachingInterfaceWithEngine(TI84Interface):
                """Teaching interface that uses pre-initialized cascade engine."""

                def __init__(self_inner, engine, port=None, baud_rate=9600):
                    # Set baud_rate before parent init
                    self_inner.baud_rate = baud_rate

                    # Initialize base TI-84 interface with our engine
                    super().__init__(port=port, baud_rate=baud_rate, enable_wolfram=False)

                    # Replace engine with our pre-initialized one
                    self_inner.engine = engine

                    # Initialize pedagogical components
                    self_inner.pedagogical_wrapper = PedagogicalWrapper()
                    self_inner.intent_classifier = IntentClassifier()
                    self_inner.response_validator = ResponseValidator()

                    # Teaching statistics
                    self_inner.teaching_stats = {
                        'tutoring_queries': 0,
                        'explanation_queries': 0,
                        'verification_queries': 0,
                        'quick_answer_queries': 0,
                        'answer_leakage_prevented': 0,
                    }

                def _handle_query(self_inner, query):
                    """Process query with pedagogical enhancements."""
                    self_inner.stats['total_queries'] += 1
                    self_inner.send_response("Thinking...")

                    start_time = time.time()

                    try:
                        prompt_result = self_inner.pedagogical_wrapper.prepare_prompt(query)
                        intent = prompt_result['intent']
                        tutoring_mode = prompt_result['tutoring_mode']

                        self.logger.info(
                            f"Intent: {intent.value} "
                            f"(confidence: {prompt_result['metadata']['confidence']:.2f})"
                        )

                        # Send to LLM for pedagogical response
                        result = self_inner.engine.solve(
                            prompt_result['prompt'],
                            force_layer='llm'
                        )

                        elapsed = time.time() - start_time

                        if result['success']:
                            response_text = result['result']

                            # Validate response for answer leakage
                            validation = self_inner.response_validator.validate(
                                response=response_text,
                                original_problem=query,
                                tutoring_mode=tutoring_mode
                            )

                            critical_issues = [
                                issue for issue in validation['issues']
                                if issue['severity'].value == 'critical'
                            ]

                            if critical_issues and tutoring_mode:
                                self.logger.warning(
                                    "Answer leakage detected, regenerating..."
                                )
                                self_inner.teaching_stats['answer_leakage_prevented'] += 1

                                enhanced_prompt = (
                                    prompt_result['prompt'] +
                                    "\n\nCRITICAL: DO NOT reveal the final answer. "
                                    "Only guide the student."
                                )
                                result = self_inner.engine.solve(
                                    enhanced_prompt,
                                    force_layer='llm'
                                )

                                if result['success']:
                                    response_text = result['result']

                            self.logger.info(f"Response ({intent.value}) in {elapsed:.2f}s")
                            self_inner.send_response(response_text)

                        else:
                            self_inner.stats['errors'] += 1
                            self.logger.warning(f"Failed: {result.get('error')}")
                            self_inner.send_response(
                                "I'm having trouble with that. Can you rephrase?"
                            )

                    except Exception as e:
                        self.logger.error(f"Error processing query: {e}")
                        self_inner.stats['errors'] += 1
                        self_inner.send_response("Error: Something went wrong")

            # Create teaching interface with our engine
            self.interface = TeachingInterfaceWithEngine(
                engine=self.engine,
                port=None,  # Auto-detect
                baud_rate=9600
            )

            self.logger.info("Connecting to TI-84...")
            if self.interface.connect():
                self.logger.info("Successfully connected to TI-84!")
                self.running = True

                # Start listening (this blocks until shutdown)
                self.interface.listen()

                return True
            else:
                self.logger.error("Failed to connect to TI-84")
                return False

        except ImportError as e:
            self.logger.error(f"Failed to import teaching components: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to start teaching interface: {e}")
            return False

    def run(self):
        """Main application loop."""
        self.logger.info("=" * 60)
        self.logger.info("Holy Calculator Auto-Launch Starting...")
        self.logger.info("=" * 60)
        self.logger.info(f"Log file: {LOG_FILE}")
        self.logger.info(f"Target device: TI-84 Plus Silver (VID:{USB_VENDOR} PID:{USB_PRODUCT})")
        self.logger.info("=" * 60)

        # Step 1: Verify calculator connection
        self.logger.info("[1/3] Verifying TI-84 connection...")
        if not self.verify_calculator_connected():
            self.logger.error("TI-84 not detected after maximum attempts")
            self.logger.error("Ensure calculator is connected and in USB mode")
            self.logger.error("(Press 2nd + LINK on calculator)")
            sys.exit(1)

        # Step 2: Initialize cascade engine
        self.logger.info("[2/3] Initializing cascade engine...")
        if not self.initialize_cascade_engine():
            self.logger.error("Failed to initialize cascade engine")
            sys.exit(1)

        # Step 3: Start teaching interface
        self.logger.info("[3/3] Starting teaching interface...")
        if not self.start_teaching_interface():
            self.logger.error("Failed to start teaching interface")
            sys.exit(1)

        self.logger.info("Holy Calculator running successfully")


def main():
    """Entry point for auto-launch."""
    app = HolyCalculatorApp()
    try:
        app.run()
    except KeyboardInterrupt:
        logging.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
