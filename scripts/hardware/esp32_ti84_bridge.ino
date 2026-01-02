/*
 * MathBridge - ESP32 TI-84 UART Bridge
 *
 * This firmware turns an ESP32 into a bridge between:
 *   - TI-84 Plus CE (2.5mm UART @ 9600 baud)
 *   - Raspberry Pi (WiFi or USB Serial)
 *
 * Hardware Connections:
 *   TI-84 I/O Port (2.5mm)     ESP32 Feather
 *   ──────────────────────     ─────────────
 *   Tip (TX)         ────→     GPIO 16 (RX2)
 *   Ring (RX)        ←────     GPIO 17 (TX2)
 *   Sleeve (GND)     ────→     GND
 *
 * Connection Modes:
 *   1. WiFi Mode: ESP32 forwards queries to Pi via HTTP POST
 *   2. USB Mode: ESP32 forwards queries to Pi via USB serial
 *
 * Author: MathBridge Project
 * Date: January 2026
 */

// ═══════════════════════════════════════════════════════════
// INCLUDES & CONFIGURATION
// ═══════════════════════════════════════════════════════════

#include <WiFi.h>
#include <HTTPClient.h>
#include <HardwareSerial.h>

// Configuration - UPDATE THESE FOR YOUR SETUP
#define WIFI_SSID     "YOUR_WIFI_SSID"        // Replace with your WiFi name
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"    // Replace with your WiFi password
#define PI_IP         "192.168.1.100"         // Replace with your Pi's IP address
#define PI_PORT       5000                     // Pi HTTP server port

// Connection mode
#define USE_WIFI      true    // true = WiFi mode, false = USB serial mode

// Pin definitions for TI-84 UART
#define TI84_RX_PIN   16      // ESP32 RX (receives from TI-84 TX)
#define TI84_TX_PIN   17      // ESP32 TX (sends to TI-84 RX)
#define TI84_BAUD     9600    // TI-84 UART speed

// LED for status indication
#define STATUS_LED    LED_BUILTIN

// Serial ports
HardwareSerial TI84Serial(2);  // UART2 for TI-84 (pins 16, 17)
// Serial = USB serial to Pi (already defined)

// Query buffer
#define MAX_QUERY_LEN 512
char queryBuffer[MAX_QUERY_LEN];
int bufferIndex = 0;

// Statistics
unsigned long totalQueries = 0;
unsigned long successfulQueries = 0;
unsigned long failedQueries = 0;

// ═══════════════════════════════════════════════════════════
// SETUP
// ═══════════════════════════════════════════════════════════

void setup() {
  // Initialize USB serial (for debugging and USB mode)
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n\n");
  Serial.println("═══════════════════════════════════════════");
  Serial.println("  MathBridge - ESP32 TI-84 UART Bridge");
  Serial.println("═══════════════════════════════════════════");
  Serial.println();

  // Initialize status LED
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, LOW);

  // Initialize TI-84 UART (UART2 on pins 16, 17)
  TI84Serial.begin(TI84_BAUD, SERIAL_8N1, TI84_RX_PIN, TI84_TX_PIN);
  Serial.println("✓ TI-84 UART initialized (9600 baud, pins 16/17)");

  // Initialize connection mode
  if (USE_WIFI) {
    setupWiFi();
  } else {
    setupUSB();
  }

  // Ready signal
  Serial.println("\n✓ Bridge ready - Waiting for TI-84 queries...");
  Serial.println("═══════════════════════════════════════════\n");

  // Send ready signal to TI-84
  TI84Serial.println("READY");

  // Flash LED to indicate ready
  for (int i = 0; i < 3; i++) {
    digitalWrite(STATUS_LED, HIGH);
    delay(100);
    digitalWrite(STATUS_LED, LOW);
    delay(100);
  }
}

// ═══════════════════════════════════════════════════════════
// WIFI SETUP
// ═══════════════════════════════════════════════════════════

void setupWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi connected!");
    Serial.print("  ESP32 IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("  Pi IP: ");
    Serial.println(PI_IP);
    Serial.print("  Signal strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println("\n✗ WiFi connection failed!");
    Serial.println("  Falling back to USB serial mode...");
    // Note: This is a simple fallback; in production you might want to retry
  }
}

// ═══════════════════════════════════════════════════════════
// USB SETUP
// ═══════════════════════════════════════════════════════════

void setupUSB() {
  Serial.println("✓ USB Serial mode enabled");
  Serial.println("  Connect ESP32 USB to Raspberry Pi");
  Serial.println("  Pi should run: python3 ti84_interface.py --esp32");
}

// ═══════════════════════════════════════════════════════════
// MAIN LOOP
// ═══════════════════════════════════════════════════════════

void loop() {
  // Check for data from TI-84
  if (TI84Serial.available()) {
    char c = TI84Serial.read();

    // Debug: echo to USB serial
    Serial.print(c);

    // Build query buffer
    if (c == '\n' || c == '\r') {
      // End of query - process it
      if (bufferIndex > 0) {
        queryBuffer[bufferIndex] = '\0';  // Null terminate
        processQuery(queryBuffer);
        bufferIndex = 0;  // Reset buffer
      }
    } else if (bufferIndex < MAX_QUERY_LEN - 1) {
      queryBuffer[bufferIndex++] = c;
    } else {
      // Buffer overflow - reset
      Serial.println("\n⚠ Query too long - buffer overflow");
      bufferIndex = 0;
      TI84Serial.println("ERROR: Query too long");
    }
  }

  // Small delay to prevent busy-waiting
  delay(10);
}

// ═══════════════════════════════════════════════════════════
// QUERY PROCESSING
// ═══════════════════════════════════════════════════════════

void processQuery(const char* query) {
  Serial.println("\n─────────────────────────────────────────");
  Serial.print("📩 Query from TI-84: ");
  Serial.println(query);

  // LED on during processing
  digitalWrite(STATUS_LED, HIGH);

  // Update statistics
  totalQueries++;

  // Send acknowledgment to TI-84
  TI84Serial.println("Processing...");

  // Forward to Pi and get response
  String response;
  bool success;

  if (USE_WIFI && WiFi.status() == WL_CONNECTED) {
    success = forwardToWiFi(query, response);
  } else {
    success = forwardToUSB(query, response);
  }

  // Send response back to TI-84
  if (success) {
    successfulQueries++;
    Serial.print("✓ Response: ");
    Serial.println(response);
    TI84Serial.println(response);
  } else {
    failedQueries++;
    Serial.println("✗ Failed to get response from Pi");
    TI84Serial.println("ERROR: No response");
  }

  // LED off after processing
  digitalWrite(STATUS_LED, LOW);

  // Print statistics every 10 queries
  if (totalQueries % 10 == 0) {
    printStats();
  }

  Serial.println("─────────────────────────────────────────\n");
}

// ═══════════════════════════════════════════════════════════
// WIFI FORWARDING
// ═══════════════════════════════════════════════════════════

bool forwardToWiFi(const char* query, String& response) {
  HTTPClient http;

  // Build URL: http://PI_IP:PI_PORT/query
  String url = "http://" + String(PI_IP) + ":" + String(PI_PORT) + "/query";

  Serial.print("🌐 Sending to Pi via WiFi: ");
  Serial.println(url);

  http.begin(url);
  http.addHeader("Content-Type", "text/plain");

  // Send POST request with query
  int httpCode = http.POST(query);

  bool success = false;

  if (httpCode == HTTP_CODE_OK) {
    response = http.getString();
    success = true;
  } else {
    Serial.print("✗ HTTP error: ");
    Serial.println(httpCode);
    response = "ERROR: Pi unreachable";
  }

  http.end();
  return success;
}

// ═══════════════════════════════════════════════════════════
// USB SERIAL FORWARDING
// ═══════════════════════════════════════════════════════════

bool forwardToUSB(const char* query, String& response) {
  Serial.println("🔌 Sending to Pi via USB serial...");

  // Send query to Pi via USB serial
  Serial.print("QUERY:");
  Serial.println(query);

  // Wait for response (with timeout)
  unsigned long startTime = millis();
  unsigned long timeout = 30000;  // 30 second timeout

  response = "";
  bool receivedResponse = false;

  while (millis() - startTime < timeout) {
    if (Serial.available()) {
      char c = Serial.read();

      if (c == '\n' || c == '\r') {
        if (response.length() > 0) {
          receivedResponse = true;
          break;
        }
      } else {
        response += c;
      }
    }
    delay(10);
  }

  if (!receivedResponse) {
    Serial.println("✗ Timeout waiting for Pi response");
    response = "ERROR: Timeout";
    return false;
  }

  return true;
}

// ═══════════════════════════════════════════════════════════
// STATISTICS
// ═══════════════════════════════════════════════════════════

void printStats() {
  Serial.println("\n═══════════════════════════════════════════");
  Serial.println("  BRIDGE STATISTICS");
  Serial.println("═══════════════════════════════════════════");
  Serial.print("  Total queries:      ");
  Serial.println(totalQueries);
  Serial.print("  Successful:         ");
  Serial.println(successfulQueries);
  Serial.print("  Failed:             ");
  Serial.println(failedQueries);

  if (totalQueries > 0) {
    float successRate = (float)successfulQueries / totalQueries * 100;
    Serial.print("  Success rate:       ");
    Serial.print(successRate, 1);
    Serial.println("%");
  }

  if (USE_WIFI && WiFi.status() == WL_CONNECTED) {
    Serial.print("  WiFi signal:        ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  }

  Serial.print("  Free heap:          ");
  Serial.print(ESP.getFreeHeap());
  Serial.println(" bytes");

  Serial.println("═══════════════════════════════════════════\n");
}

// ═══════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════

// Optional: Add command interface for debugging via USB serial
// You can send commands like "stats", "reset", "test" from Serial Monitor
void handleSerialCommands() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "stats") {
      printStats();
    } else if (cmd == "reset") {
      Serial.println("Resetting statistics...");
      totalQueries = 0;
      successfulQueries = 0;
      failedQueries = 0;
    } else if (cmd == "test") {
      Serial.println("Sending test query to TI-84...");
      TI84Serial.println("Test message from ESP32");
    } else if (cmd == "wifi") {
      Serial.print("WiFi status: ");
      if (WiFi.status() == WL_CONNECTED) {
        Serial.println("Connected");
        Serial.print("IP: ");
        Serial.println(WiFi.localIP());
        Serial.print("RSSI: ");
        Serial.print(WiFi.RSSI());
        Serial.println(" dBm");
      } else {
        Serial.println("Disconnected");
      }
    }
  }
}
