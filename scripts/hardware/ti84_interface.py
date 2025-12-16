#!/usr/bin/env python3
"""
TI-84 Plus CE USB Serial Interface
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

    def __init__(self, port=None, baud_rate=9600, enable_wolfram=False):
        """
        Initialize TI-84 interface.

        Args:
            port: Serial port (auto-detects if None)
            baud_rate: Communication speed (default 9600)
            enable_wolfram: Enable Wolfram Alpha layer
        """
        self.port = port or self._find_ti84_port()
        self.baud_rate = baud_rate
        self.serial_conn = None

        # Initialize calculator engine
        logger.info("Initializing Holy Calculator engine...")
        self.engine = CalculatorEngine(enable_wolfram=enable_wolfram)
        logger.info("✓ Calculator engine ready")

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
            self.disconnect()

    def _handle_query(self, query):
        """
        Process a query and send result back to TI-84.

        Args:
            query: Mathematical query from TI-84
        """
        # Send acknowledgment
        self.send_response("Processing...")

        # Solve using Holy Calculator
        start_time = time.time()
        result = self.engine.solve(query)
        elapsed = time.time() - start_time

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
            error_msg = "Error: Could not solve"

            logger.warning(f"✗ Failed: {result['error']}")
            logger.warning(f"📤 Sending: {error_msg}")

            self.send_response(error_msg)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="TI-84 Plus CE interface for Holy Calculator"
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

    args = parser.parse_args()

    if args.test:
        # Test mode - simulate queries
        logger.info("TEST MODE: Simulating TI-84 queries")
        interface = TI84Interface(enable_wolfram=args.enable_wolfram)

        test_queries = [
            "Solve: 2x + 5 = 13",
            "Derivative of x^2",
            "What is 5 + 5?",
        ]

        for query in test_queries:
            logger.info(f"\n📩 Test query: {query}")
            interface._handle_query(query)
            time.sleep(1)

        logger.info("\n✓ Test complete")

    else:
        # Real mode - connect to TI-84
        interface = TI84Interface(
            port=args.port,
            baud_rate=args.baud,
            enable_wolfram=args.enable_wolfram
        )

        if interface.connect():
            interface.listen()
        else:
            logger.error("Failed to connect to TI-84")
            sys.exit(1)


if __name__ == "__main__":
    main()
