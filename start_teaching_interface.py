#!/usr/bin/env python3
"""
Auto-Start Teaching Interface for TI-84
Automatically detects TI-84 port and launches the teaching interface with pedagogical features.
"""

import sys
import time
import logging
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from hardware.ti84_interface import TI84Interface
from cascade.calculator_engine import CalculatorEngine
from cascade.pedagogical_wrapper import PedagogicalWrapper
from cascade.intent_classifier import IntentClassifier
from cascade.response_validator import ResponseValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TeachingInterface(TI84Interface):
    """
    Enhanced TI-84 interface with pedagogical features for teaching.

    This extends the basic TI-84Interface to include:
    - Intent classification (tutoring, explanation, verification, quick answer)
    - Pedagogical response generation
    - Response validation (prevents answer leakage)
    - Socratic questioning approach
    """

    def __init__(self, port=None, baud_rate=9600, enable_wolfram=False):
        """
        Initialize the teaching interface.

        Args:
            port: Serial port (auto-detects if None)
            baud_rate: Communication speed (default 9600)
            enable_wolfram: Enable Wolfram Alpha layer
        """
        # Set baud_rate before calling parent init (needed for auto-detection)
        self.baud_rate = baud_rate

        # Initialize base TI-84 interface
        super().__init__(port=port, baud_rate=baud_rate, enable_wolfram=enable_wolfram)

        # Initialize pedagogical components
        logger.info("Initializing teaching components...")
        self.pedagogical_wrapper = PedagogicalWrapper()
        self.intent_classifier = IntentClassifier()
        self.response_validator = ResponseValidator()
        logger.info("✓ Teaching interface ready")

        # Teaching statistics
        self.teaching_stats = {
            'tutoring_queries': 0,
            'explanation_queries': 0,
            'verification_queries': 0,
            'quick_answer_queries': 0,
            'answer_leakage_prevented': 0,
        }

    def _handle_query(self, query):
        """
        Process a query with pedagogical enhancements.

        Args:
            query: Mathematical query from TI-84
        """
        # Update statistics
        self.stats['total_queries'] += 1

        # Send acknowledgment
        self.send_response("Thinking...")

        # Step 1: Prepare pedagogical prompt
        start_time = time.time()

        try:
            prompt_result = self.pedagogical_wrapper.prepare_prompt(query)

            intent = prompt_result['intent']
            tutoring_mode = prompt_result['tutoring_mode']

            logger.info(f"Intent: {intent.value} (confidence: {prompt_result['metadata']['confidence']:.2f})")
            logger.info(f"Mode: {prompt_result['mode'].value}, Tutoring: {tutoring_mode}")

            # Update teaching statistics
            if intent.value in self.teaching_stats:
                key = f"{intent.value}_queries"
                if key in self.teaching_stats:
                    self.teaching_stats[key] += 1

            # Step 2: Send prompt to LLM (force LLM layer for pedagogical responses)
            # The pedagogical wrapper has already formatted the prompt appropriately
            result = self.engine.solve(prompt_result['prompt'], force_layer='llm')

            elapsed = time.time() - start_time

            # Update average response time
            total = self.stats['total_queries']
            prev_avg = self.stats['avg_response_time']
            self.stats['avg_response_time'] = ((prev_avg * (total - 1)) + elapsed) / total

            if result['success']:
                response_text = result['result']

                # Step 3: Validate response to ensure good pedagogical quality
                validation = self.response_validator.validate(
                    response=response_text,
                    original_problem=query,
                    tutoring_mode=tutoring_mode
                )

                # Check for critical issues (like answer leakage in tutoring mode)
                critical_issues = [issue for issue in validation['issues']
                                 if issue['severity'].value == 'critical']

                if critical_issues and tutoring_mode:
                    # Response leaked the answer - regenerate with stronger guidance
                    logger.warning("⚠ Answer leakage detected, regenerating response...")
                    self.teaching_stats['answer_leakage_prevented'] += 1

                    # Add explicit reminder in the prompt
                    enhanced_prompt = prompt_result['prompt'] + "\n\nCRITICAL: DO NOT reveal the final answer. Only guide the student."
                    result = self.engine.solve(enhanced_prompt, force_layer='llm')

                    if result['success']:
                        response_text = result['result']
                    else:
                        response_text = "Let me guide you through this. What's your first step?"

                # Send the pedagogically-appropriate response
                logger.info(f"✓ Response ({intent.value}) in {elapsed:.2f}s")
                logger.info(f"   Validation: {validation['score']:.2f}/1.00 ({validation['passed_checks']}/{validation['total_checks']} checks)")
                logger.info(f"📤 Sending: {response_text[:100]}...")

                self.send_response(response_text)

            else:
                # Failure - send error message
                self.stats['errors'] += 1
                error_msg = "I'm having trouble with that. Can you rephrase?"

                logger.warning(f"✗ Failed: {result.get('error', 'Unknown error')}")
                self.send_response(error_msg)

        except Exception as e:
            logger.error(f"✗ Error processing query: {e}")
            logger.exception(e)  # Log full traceback
            self.stats['errors'] += 1
            self.send_response("Error: Something went wrong")

    def print_stats(self):
        """Print enhanced statistics including teaching metrics."""
        # Print base statistics
        super().print_stats()

        # Print teaching-specific statistics
        logger.info("\n" + "="*70)
        logger.info("TEACHING INTERFACE STATISTICS")
        logger.info("="*70)
        logger.info(f"Tutoring queries:        {self.teaching_stats['tutoring_queries']}")
        logger.info(f"Explanation queries:     {self.teaching_stats['explanation_queries']}")
        logger.info(f"Verification queries:    {self.teaching_stats['verification_queries']}")
        logger.info(f"Quick answer queries:    {self.teaching_stats['quick_answer_queries']}")
        logger.info(f"Answer leakage prevented: {self.teaching_stats['answer_leakage_prevented']}")
        logger.info("="*70 + "\n")


def main():
    """Main entry point for the teaching interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Teaching Interface - Auto-detecting TI-84 with pedagogical AI"
    )
    parser.add_argument(
        '--port',
        type=str,
        help='Serial port (auto-detects if not specified)'
    )
    parser.add_argument(
        '--baud',
        type=int,
        default=9600,
        help='Baud rate (default: 9600)'
    )
    parser.add_argument(
        '--enable-wolfram',
        action='store_true',
        help='Enable Wolfram Alpha layer (requires API key)'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics after shutdown'
    )

    args = parser.parse_args()

    logger.info("="*70)
    logger.info("TEACHING INTERFACE - AUTO-START")
    logger.info("="*70)
    logger.info("Initializing TI-84 teaching interface...")
    logger.info("Features:")
    logger.info("  ✓ Auto-detect TI-84 USB port")
    logger.info("  ✓ Intent classification (tutoring, explanation, etc.)")
    logger.info("  ✓ Socratic questioning approach")
    logger.info("  ✓ Answer leakage prevention")
    logger.info("  ✓ Battery-optimized responses")
    logger.info("="*70 + "\n")

    # Create teaching interface (port auto-detection happens here)
    try:
        interface = TeachingInterface(
            port=args.port,
            baud_rate=args.baud,
            enable_wolfram=args.enable_wolfram
        )
    except Exception as e:
        logger.error(f"✗ Failed to initialize teaching interface: {e}")
        sys.exit(1)

    # Try to connect
    logger.info("Connecting to TI-84...")
    if interface.connect():
        logger.info("✓ Successfully connected!")
        logger.info("Teaching interface is now active.\n")

        try:
            # Start listening for queries
            interface.listen()
        except KeyboardInterrupt:
            logger.info("\n\nShutting down teaching interface...")
            if args.stats:
                interface.print_stats()
    else:
        logger.error("✗ Failed to connect to TI-84")
        logger.error("\nTroubleshooting:")
        logger.error("  1. Ensure TI-84 is connected via USB")
        logger.error("  2. Check that USB cable supports data transfer")
        logger.error("  3. Try running with --port /dev/ttyACM0 (or appropriate port)")
        logger.error("  4. Check USB permissions: ls -l /dev/ttyACM*")
        sys.exit(1)


if __name__ == "__main__":
    main()
