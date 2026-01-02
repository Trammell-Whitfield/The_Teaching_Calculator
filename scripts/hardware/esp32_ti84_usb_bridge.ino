/*
 * MathBridge - ESP32 TI-84 USB Bridge (Simple Version)
 *
 * This is a simplified version that only uses USB serial (no WiFi).
 * Perfect for initial testing and development.
 *
 * Hardware Connections:
 *   TI-84 I/O Port (2.5mm)     ESP32
 *   ──────────────────────     ─────────
 *   Tip (TX)         ────→     GPIO 16 (RX2)
 *   Ring (RX)        ←────     GPIO 17 (TX2)
 *   Sleeve (GND)     ────→     GND
 *
 *   ESP32 USB  ─────→  Raspberry Pi USB
 *
 * Usage:
 *   1. Flash this to ESP32
 *   2. Connect TI-84 to ESP32 via 2.5mm cable
 *   3. Connect ESP32 to Pi via USB
 *   4. Run on Pi: python3 ti84_interface.py --esp32
 *   5. Run MBMENU or MBQUICK on TI-84
 *
 * Author: MathBridge Project
 * Date: January 2026
 */

#include <HardwareSerial.h>

// Pin definitions for TI-84 UART
#define TI84_RX_PIN   16      // ESP32 RX (receives from TI-84 TX)
#define TI84_TX_PIN   17      // ESP32 TX (sends to TI-84 RX)
#define TI84_BAUD     9600    // TI-84 UART speed

// LED for status
#define STATUS_LED    LED_BUILTIN

// Serial ports
HardwareSerial TI84Serial(2);  // UART2 for TI-84
// Serial = USB to Pi

// Query buffer
#define MAX_QUERY_LEN 512
char queryBuffer[MAX_QUERY_LEN];
int bufferIndex = 0;

// Statistics
unsigned long totalQueries = 0;

// ═══════════════════════════════════════════════════════════
// SETUP
// ═══════════════════════════════════════════════════════════

void setup() {
  // Initialize USB serial to Pi
  Serial.begin(115200);
  while (!Serial) {
    delay(10);  // Wait for USB serial
  }

  Serial.println("\n\n");
  Serial.println("═══════════════════════════════════════════");
  Serial.println("  MathBridge ESP32 - USB Bridge Mode");
  Serial.println("═══════════════════════════════════════════");

  // Initialize status LED
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, LOW);

  // Initialize TI-84 UART
  TI84Serial.begin(TI84_BAUD, SERIAL_8N1, TI84_RX_PIN, TI84_TX_PIN);
  Serial.println("✓ TI-84 UART ready (9600 baud, GPIO 16/17)");
  Serial.println("✓ USB Serial ready (115200 baud)");
  Serial.println();
  Serial.println("Ready to forward queries:");
  Serial.println("  TI-84 → ESP32 → Pi");
  Serial.println("═══════════════════════════════════════════\n");

  // Send ready signal to TI-84
  TI84Serial.println("READY");

  // Flash LED
  for (int i = 0; i < 3; i++) {
    digitalWrite(STATUS_LED, HIGH);
    delay(100);
    digitalWrite(STATUS_LED, LOW);
    delay(100);
  }
}

// ═══════════════════════════════════════════════════════════
// MAIN LOOP
// ═══════════════════════════════════════════════════════════

void loop() {
  // TI-84 → Pi forwarding
  if (TI84Serial.available()) {
    char c = TI84Serial.read();

    if (c == '\n' || c == '\r') {
      if (bufferIndex > 0) {
        queryBuffer[bufferIndex] = '\0';
        handleTI84Query(queryBuffer);
        bufferIndex = 0;
      }
    } else if (bufferIndex < MAX_QUERY_LEN - 1) {
      queryBuffer[bufferIndex++] = c;
    } else {
      // Buffer overflow
      bufferIndex = 0;
      TI84Serial.println("ERROR: Query too long");
    }
  }

  // Pi → TI-84 forwarding
  if (Serial.available()) {
    String response = Serial.readStringUntil('\n');

    // Check if this is a command or a response
    if (response.startsWith("CMD:")) {
      handlePiCommand(response.substring(4));
    } else {
      // Regular response - send to TI-84
      TI84Serial.println(response);
      Serial.print("→ TI-84: ");
      Serial.println(response);
    }
  }

  delay(10);
}

// ═══════════════════════════════════════════════════════════
// HANDLERS
// ═══════════════════════════════════════════════════════════

void handleTI84Query(const char* query) {
  totalQueries++;

  digitalWrite(STATUS_LED, HIGH);

  Serial.println("─────────────────────────────────────────");
  Serial.print("TI-84 → Pi (#");
  Serial.print(totalQueries);
  Serial.print("): ");
  Serial.println(query);

  // Send to Pi
  Serial.print("QUERY:");
  Serial.println(query);

  // Send acknowledgment to TI-84
  TI84Serial.println("Processing...");

  digitalWrite(STATUS_LED, LOW);
}

void handlePiCommand(String cmd) {
  cmd.trim();

  if (cmd == "PING") {
    Serial.println("PONG");
  } else if (cmd == "STATS") {
    Serial.print("QUERIES:");
    Serial.println(totalQueries);
  } else if (cmd == "RESET") {
    totalQueries = 0;
    Serial.println("OK");
  }
}
