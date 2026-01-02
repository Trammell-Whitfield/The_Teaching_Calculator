#!/usr/bin/env python3
"""
MathBridge - TI-84 Plus CE USB Serial Interface
Receives math queries from TI-84 calculator and sends back solutions.
"""

import serial
import serial.tools.list_ports
import time
import sys
import logging
from pathlib import Path

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cascade.calculator_engine import CalculatorEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TI84Interface:
    """Interface for communicating with TI-84 Plus CE calculator."""

    def __init__(self, port=None, baud_rate=9600, enable_wolfram=False, esp32_mode=False):
        """
        Initialize TI-84 interface.

        Args:
            port: Serial port (auto-detects if None)
            baud_rate: Communication speed (default 9600)
            enable_wolfram: Enable Wolfram Alpha layer
            esp32_mode: Use ESP32 bridge protocol (future enhancement)
        """
        self.port = port or self._find_ti84_port()
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.esp32_mode = esp32_mode

        # Query statistics
        self.stats = {
            'total_queries': 0,
            'sympy_queries': 0,
            'llm_queries': 0,
            'cascade_queries': 0,
            'errors': 0,
            'avg_response_time': 0.0
        }

        # Initialize calculator engine
        logger.info("Initializing MathBridge engine...")
        self.engine = CalculatorEngine(enable_wolfram=enable_wolfram)
        logger.info("✓ Calculator engine ready")

        if esp32_mode:
            logger.info("🔌 ESP32 bridge mode enabled (UART 9600 baud)")

    def _find_ti84_port(self):
        """
        Auto-detect TI-84 USB serial port.

        Returns:
            Port name (e.g., '/dev/ttyACM0') or None if not found
        """
        logger.info("Scanning for TI-84 calculator...")

        ports = serial.tools.list_ports.comports()

        # Look for Texas Instruments device
        for port in ports:
            if "texas instruments" in port.description.lower() or \
               "ti-84" in port.description.lower():
                logger.info(f"✓ Found TI-84 on {port.device}")
                return port.device

        # Fallback: try common ports
        common_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']

        for port in common_ports:
            try:
                # Try to open port briefly
                with serial.Serial(port, self.baud_rate, timeout=0.5):
                    logger.info(f"✓ Found device on {port} (assumed TI-84)")
                    return port
            except (serial.SerialException, FileNotFoundError):
                continue

        logger.warning("⚠ No TI-84 detected. Available ports:")
        for port in ports:
            logger.warning(f"   {port.device}: {port.description}")

        return None

    def connect(self):
        """Open serial connection to TI-84."""
        if not self.port:
            raise ValueError("No TI-84 port found. Connect calculator via USB.")

        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=1,
                write_timeout=1
            )
            logger.info(f"✓ Connected to TI-84 on {self.port}")
            time.sleep(2)  # Wait for connection to stabilize

            # Send ready signal
            self.send_response("READY")

            return True

        except serial.SerialException as e:
            logger.error(f"✗ Failed to connect: {e}")
            return False

    def disconnect(self):
        """Close serial connection."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("✓ Disconnected from TI-84")

    def send_response(self, message):
        """
        Send a response back to TI-84.

        Args:
            message: Text to send
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            logger.warning("Cannot send: Not connected")
            return

        try:
            # Format message (max 16 chars per line for TI-84 screen)
            formatted = self._format_for_ti84(message)

            # Send with newline terminator
            self.serial_conn.write((formatted + '\n').encode('utf-8'))
            self.serial_conn.flush()

            logger.debug(f"📤 Sent: {formatted}")

        except serial.SerialException as e:
            logger.error(f"✗ Send error: {e}")

    def _format_for_ti84(self, text, max_width=16):
        """
        Format text for TI-84 screen (16 chars wide, 8 lines).

        Args:
            text: Text to format
            max_width: Max characters per line

        Returns:
            Formatted text with line breaks
        """
        if len(text) <= max_width:
            return text

        # Split into chunks
        lines = []
        words = text.split()
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= max_width:
                current_line += (" " if current_line else "") + word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        # Max 8 lines for TI-84 screen
        return '\n'.join(lines[:8])

    def listen(self):
        """
        Main loop: listen for queries from TI-84 and respond.

        This runs continuously until interrupted.
        """
        logger.info("\n" + "="*70)
        logger.info("TI-84 INTERFACE ACTIVE - Ready to receive queries")
        logger.info("="*70)
        logger.info("Press Ctrl+C to stop\n")

        try:
            while True:
                # Check for incoming data
                if self.serial_conn.in_waiting > 0:
                    # Read query
                    query_bytes = self.serial_conn.readline()
                    query = query_bytes.decode('utf-8', errors='ignore').strip()

                    if query:
                        logger.info(f"\n📩 Received: {query}")

                        # Process query
                        self._handle_query(query)

                # Small delay to avoid busy-waiting
                time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("\n\nShutting down...")
            self.print_stats()
            self.disconnect()

    def _parse_template(self, query):
        """
        Parse template-based queries and determine routing tier.

        Args:
            query: Query string from TI-84

        Returns:
            tuple: (tier, action, cleaned_query)
                tier: 'sympy', 'llm', or 'cascade'
                action: specific action type
                cleaned_query: query with template prefix removed
        """
        query_lower = query.lower()

        # Template definitions with tier routing
        templates = {
            # Algebra templates → SymPy (Tier 1)
            'solve:': ('sympy', 'solve_equation'),
            'factor:': ('sympy', 'factor'),
            'expand:': ('sympy', 'expand'),
            'simplify:': ('sympy', 'simplify'),
            'solve system:': ('sympy', 'solve_system'),

            # Calculus templates → SymPy (Tier 1)
            'derivative of': ('sympy', 'derivative'),
            'integrate:': ('sympy', 'integrate'),
            'limit of': ('sympy', 'limit'),
            'taylor series of': ('sympy', 'series'),
            'find critical points of': ('sympy', 'critical_points'),

            # Explanation templates → LLM (Tier 3)
            'explain': ('llm', 'explain'),
            'why does': ('llm', 'explain'),
            'how do i': ('llm', 'explain'),
            'show steps to': ('llm', 'show_steps'),
            'give an example of': ('llm', 'example'),
            'compare': ('llm', 'compare'),

            # Geometry templates → SymPy (Tier 1)
            'area of': ('sympy', 'geometry'),
            'volume of': ('sympy', 'geometry'),
            'circumference of': ('sympy', 'geometry'),
            'find angle:': ('sympy', 'geometry'),
            'equation of circle:': ('sympy', 'geometry'),

            # Statistics templates → SymPy (Tier 1)
            'mean of:': ('sympy', 'statistics'),
            'median of:': ('sympy', 'statistics'),
            'std dev of:': ('sympy', 'statistics'),
            'probability:': ('sympy', 'statistics'),
            'linear regression': ('sympy', 'statistics'),
        }

        # Check for template match
        for prefix, (tier, action) in templates.items():
            if query_lower.startswith(prefix):
                # Extract the actual query content
                cleaned = query[len(prefix):].strip()
                logger.info(f"📋 Template detected: '{prefix}' → Tier: {tier}, Action: {action}")
                return tier, action, cleaned

        # No template match - use cascade
        logger.info(f"📋 No template - using cascade routing")
        return 'cascade', 'auto', query

    def _handle_query(self, query):
        """
        Process a query and send result back to TI-84.

        Args:
            query: Mathematical query from TI-84
        """
        # Update statistics
        self.stats['total_queries'] += 1

        # Send acknowledgment
        self.send_response("Processing...")

        # Parse template to determine routing
        tier, action, cleaned_query = self._parse_template(query)

        # Update tier statistics
        if tier == 'sympy':
            self.stats['sympy_queries'] += 1
        elif tier == 'llm':
            self.stats['llm_queries'] += 1
        else:
            self.stats['cascade_queries'] += 1

        # Use cleaned query if template was detected, otherwise use original
        solve_query = cleaned_query if tier != 'cascade' else query

        # Solve using Holy Calculator
        start_time = time.time()
        result = self.engine.solve(solve_query)
        elapsed = time.time() - start_time

        # Update average response time
        total = self.stats['total_queries']
        prev_avg = self.stats['avg_response_time']
        self.stats['avg_response_time'] = ((prev_avg * (total - 1)) + elapsed) / total

        # Format and send response
        if result['success']:
            # Success - send result
            answer = str(result['result'])

            logger.info(f"✓ Solved by {result['source']} in {elapsed:.2f}s")
            logger.info(f"📤 Answer: {answer}")

            self.send_response(answer)

            # Optionally send metadata
            if len(answer) < 100:  # If answer is short, send extra info
                time.sleep(0.5)
                metadata = f"[{result['source']}, {elapsed:.1f}s]"
                self.send_response(metadata)

        else:
            # Failure - send error message
            self.stats['errors'] += 1
            error_msg = "Error: Could not solve"

            logger.warning(f"✗ Failed: {result.get('error', 'Unknown error')}")
            logger.warning(f"📤 Sending: {error_msg}")

            self.send_response(error_msg)

    def print_stats(self):
        """Print query statistics."""
        logger.info("\n" + "="*70)
        logger.info("TI-84 INTERFACE STATISTICS")
        logger.info("="*70)
        logger.info(f"Total queries:      {self.stats['total_queries']}")
        logger.info(f"  SymPy (Tier 1):   {self.stats['sympy_queries']}")
        logger.info(f"  LLM (Tier 3):     {self.stats['llm_queries']}")
        logger.info(f"  Cascade:          {self.stats['cascade_queries']}")
        logger.info(f"Errors:             {self.stats['errors']}")
        logger.info(f"Avg response time:  {self.stats['avg_response_time']:.2f}s")
        logger.info("="*70 + "\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="MathBridge - TI-84 Plus CE interface for offline math AI"
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
        '--test',
        action='store_true',
        help='Test mode: simulate queries without TI-84'
    )
    parser.add_argument(
        '--esp32',
        action='store_true',
        help='ESP32 bridge mode (for 2.5mm UART connection)'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics after shutdown'
    )

    args = parser.parse_args()

    if args.test:
        # Test mode - simulate queries with template demonstrations
        logger.info("TEST MODE: Simulating TI-84 template queries")
        logger.info("="*70)
        interface = TI84Interface(enable_wolfram=args.enable_wolfram)

        test_queries = [
            # Algebra templates (SymPy - Tier 1)
            "Solve: 2x + 5 = 13",
            "Factor: x^2 + 5x + 6",
            "Expand: (x+1)^3",
            "Simplify: (x^2-1)/(x-1)",

            # Calculus templates (SymPy - Tier 1)
            "Derivative of x^3 + 2x",
            "Integrate: x^2",
            "Limit of sin(x)/x as x→0",

            # Geometry templates (SymPy - Tier 1)
            "Area of circle with radius 5",
            "Volume of sphere radius 3",

            # Explanation templates (LLM - Tier 3)
            "Explain derivative",
            "Show steps to solve: x^2 = 9",

            # Custom query (Cascade)
            "What is 2 + 2?",
        ]

        logger.info(f"Running {len(test_queries)} test queries...\n")

        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n{'─'*70}")
            logger.info(f"Test {i}/{len(test_queries)}: {query}")
            logger.info(f"{'─'*70}")
            interface._handle_query(query)
            time.sleep(0.5)

        # Print statistics
        interface.print_stats()
        logger.info("✓ Test complete")

    else:
        # Real mode - connect to TI-84
        interface = TI84Interface(
            port=args.port,
            baud_rate=args.baud,
            enable_wolfram=args.enable_wolfram,
            esp32_mode=args.esp32
        )

        if interface.connect():
            try:
                interface.listen()
            except KeyboardInterrupt:
                if args.stats:
                    interface.print_stats()
        else:
            logger.error("Failed to connect to TI-84")
            sys.exit(1)


if __name__ == "__main__":
    main()
