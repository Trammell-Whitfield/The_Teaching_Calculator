/*
 * ESP32 Battery & Environmental Monitor for Holy Calculator
 * Monitors battery voltage, current, temperature, and humidity
 * Sends data to Raspberry Pi via WiFi
 *
 * Hardware:
 * - ESP32 DevKit v1
 * - INA219 current sensor (I2C address: 0x40)
 * - BME280 temp/humidity sensor (I2C address: 0x76)
 *
 * Connections:
 * - INA219 SCL → ESP32 GPIO22
 * - INA219 SDA → ESP32 GPIO21
 * - BME280 SCL → ESP32 GPIO22 (shared)
 * - BME280 SDA → ESP32 GPIO21 (shared)
 * - INA219 V+ → Battery (+)
 * - INA219 V- → Raspberry Pi VIN
 *
 * Libraries Required:
 * - Adafruit INA219
 * - Adafruit BME280
 * - WiFi (built-in)
 * - HTTPClient (built-in)
 * - ArduinoJson
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_INA219.h>
#include <Adafruit_BME280.h>
#include <ArduinoJson.h>

// ============================================================================
// CONFIGURATION - MODIFY THESE FOR YOUR SETUP
// ============================================================================

// WiFi credentials
const char* WIFI_SSID = "YOUR_WIFI_SSID";        // Change this!
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"; // Change this!

// Raspberry Pi settings
const char* PI_HOSTNAME = "raspberrypi.local";   // Or use IP: "192.168.1.100"
const int PI_PORT = 5000;
const char* PI_ENDPOINT = "/api/esp32/data";

// Measurement settings
const int MEASUREMENT_INTERVAL_MS = 2000;  // 2 seconds (matches pi-stats refresh)
const int WIFI_RECONNECT_DELAY_MS = 5000;  // 5 seconds between WiFi reconnect attempts
const int HTTP_TIMEOUT_MS = 3000;          // 3 second HTTP timeout

// Battery voltage divider settings (if using voltage divider instead of INA219)
const float VOLTAGE_DIVIDER_RATIO = 2.0;   // Adjust based on your resistor values
const int VOLTAGE_PIN = 34;                // ADC pin for voltage measurement

// Alert thresholds
const float BATTERY_LOW_VOLTAGE = 3.6;     // Alert when battery below this
const float BATTERY_CRITICAL_VOLTAGE = 3.3;
const float TEMP_HIGH_CELSIUS = 80.0;      // Alert when CPU temp exceeds this
const float TEMP_CRITICAL_CELSIUS = 85.0;

// ============================================================================
// GLOBALS
// ============================================================================

Adafruit_INA219 ina219;
Adafruit_BME280 bme280;

bool ina219_available = false;
bool bme280_available = false;

unsigned long lastMeasurement = 0;
unsigned long bootTime = 0;

// Statistics
struct Stats {
  unsigned long measurements_sent = 0;
  unsigned long errors = 0;
  unsigned long wifi_reconnects = 0;
} stats;

// ============================================================================
// SETUP
// ============================================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n\n");
  Serial.println("========================================");
  Serial.println("ESP32 Monitor for Holy Calculator");
  Serial.println("========================================");

  bootTime = millis();

  // Initialize I2C
  Wire.begin(21, 22); // SDA=21, SCL=22 (default for ESP32)
  Serial.println("\n✓ I2C initialized");

  // Initialize INA219
  Serial.print("Initializing INA219 current sensor... ");
  if (ina219.begin()) {
    ina219_available = true;

    // Configure INA219 for 16V, 400mA max
    // Calibration for Raspberry Pi 5 power draw (2-10W at 5V = 400mA-2A)
    ina219.setCalibration_16V_400mA();

    Serial.println("✓");
  } else {
    Serial.println("✗ (not found, will use voltage divider)");
  }

  // Initialize BME280
  Serial.print("Initializing BME280 sensor... ");
  if (bme280.begin(0x76)) {  // Try address 0x76
    bme280_available = true;
    Serial.println("✓");
  } else if (bme280.begin(0x77)) {  // Try alternate address
    bme280_available = true;
    Serial.println("✓ (found at 0x77)");
  } else {
    Serial.println("✗ (not found, will skip environmental data)");
  }

  // Configure ADC for voltage measurement
  if (!ina219_available) {
    pinMode(VOLTAGE_PIN, INPUT);
    analogSetAttenuation(ADC_11db);  // 0-3.3V range
    Serial.println("✓ ADC configured for voltage divider");
  }

  // Connect to WiFi
  connectWiFi();

  Serial.println("\n========================================");
  Serial.println("Setup complete! Starting measurements...");
  Serial.println("========================================\n");
}

// ============================================================================
// MAIN LOOP
// ============================================================================

void loop() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠ WiFi disconnected, reconnecting...");
    connectWiFi();
  }

  // Take measurements at specified interval
  if (millis() - lastMeasurement >= MEASUREMENT_INTERVAL_MS) {
    lastMeasurement = millis();

    // Collect data
    MeasurementData data = collectMeasurements();

    // Display locally
    displayMeasurements(data);

    // Send to Raspberry Pi
    sendToPi(data);
  }

  delay(100);  // Small delay to prevent busy-waiting
}

// ============================================================================
// DATA STRUCTURES
// ============================================================================

struct MeasurementData {
  // Battery measurements
  float battery_voltage = 0.0;
  float battery_current = 0.0;
  float battery_power = 0.0;
  float battery_percent = 0.0;

  // Environmental measurements
  float ambient_temp = 0.0;
  float ambient_humidity = 0.0;
  float ambient_pressure = 0.0;

  // ESP32 status
  int wifi_rssi = 0;
  unsigned long uptime_seconds = 0;
  float esp32_temp = 0.0;

  // Alerts
  bool battery_low = false;
  bool battery_critical = false;
  bool temp_high = false;
  bool temp_critical = false;
};

// ============================================================================
// WiFi FUNCTIONS
// ============================================================================

void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.print(WIFI_SSID);
  Serial.print(" ");

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(" ✓");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");

    stats.wifi_reconnects++;
  } else {
    Serial.println(" ✗");
    Serial.println("Failed to connect to WiFi. Will retry...");
  }
}

// ============================================================================
// MEASUREMENT FUNCTIONS
// ============================================================================

MeasurementData collectMeasurements() {
  MeasurementData data;

  // Battery measurements
  if (ina219_available) {
    // Use INA219 for accurate measurements
    data.battery_voltage = ina219.getBusVoltage_V();
    data.battery_current = ina219.getCurrent_mA();
    data.battery_power = ina219.getPower_mW();
  } else {
    // Use voltage divider as fallback
    int raw = analogRead(VOLTAGE_PIN);
    data.battery_voltage = (raw / 4095.0) * 3.3 * VOLTAGE_DIVIDER_RATIO;
    data.battery_current = 0.0;  // Not available without INA219
    data.battery_power = 0.0;
  }

  // Calculate battery percentage (assuming Li-ion: 3.0V-4.2V range)
  data.battery_percent = ((data.battery_voltage - 3.0) / (4.2 - 3.0)) * 100.0;
  data.battery_percent = constrain(data.battery_percent, 0.0, 100.0);

  // Environmental measurements
  if (bme280_available) {
    data.ambient_temp = bme280.readTemperature();
    data.ambient_humidity = bme280.readHumidity();
    data.ambient_pressure = bme280.readPressure() / 100.0;  // Convert Pa to hPa
  }

  // ESP32 status
  data.wifi_rssi = WiFi.RSSI();
  data.uptime_seconds = (millis() - bootTime) / 1000;

  // ESP32 internal temperature (rough estimate)
  #ifdef ESP32
  data.esp32_temp = temperatureRead();
  #endif

  // Check alert conditions
  data.battery_low = (data.battery_voltage < BATTERY_LOW_VOLTAGE);
  data.battery_critical = (data.battery_voltage < BATTERY_CRITICAL_VOLTAGE);
  data.temp_high = (data.ambient_temp > TEMP_HIGH_CELSIUS);
  data.temp_critical = (data.ambient_temp > TEMP_CRITICAL_CELSIUS);

  return data;
}

void displayMeasurements(const MeasurementData& data) {
  Serial.println("────────────────────────────────────────");

  // Battery status
  Serial.println("🔋 BATTERY:");
  Serial.print("   Voltage: ");
  Serial.print(data.battery_voltage, 2);
  Serial.println(" V");

  if (ina219_available) {
    Serial.print("   Current: ");
    Serial.print(data.battery_current, 1);
    Serial.println(" mA");

    Serial.print("   Power:   ");
    Serial.print(data.battery_power, 1);
    Serial.println(" mW");
  }

  Serial.print("   Level:   ");
  Serial.print(data.battery_percent, 0);
  Serial.println(" %");

  if (data.battery_critical) {
    Serial.println("   ⚠️  CRITICAL - Battery very low!");
  } else if (data.battery_low) {
    Serial.println("   ⚠️  WARNING - Battery low");
  }

  // Environmental
  if (bme280_available) {
    Serial.println("\n🌡️  ENVIRONMENT:");
    Serial.print("   Temperature: ");
    Serial.print(data.ambient_temp, 1);
    Serial.println(" °C");

    Serial.print("   Humidity:    ");
    Serial.print(data.ambient_humidity, 1);
    Serial.println(" %");

    Serial.print("   Pressure:    ");
    Serial.print(data.ambient_pressure, 1);
    Serial.println(" hPa");

    if (data.temp_critical) {
      Serial.println("   🔥 CRITICAL - Temperature very high!");
    } else if (data.temp_high) {
      Serial.println("   ⚠️  WARNING - Temperature high");
    }
  }

  // ESP32 status
  Serial.println("\n📡 ESP32:");
  Serial.print("   WiFi RSSI: ");
  Serial.print(data.wifi_rssi);
  Serial.println(" dBm");

  Serial.print("   Uptime:    ");
  Serial.print(data.uptime_seconds);
  Serial.println(" seconds");

  Serial.print("   Chip Temp: ");
  Serial.print(data.esp32_temp, 1);
  Serial.println(" °C");

  // Statistics
  Serial.println("\n📊 STATS:");
  Serial.print("   Sent:   ");
  Serial.println(stats.measurements_sent);
  Serial.print("   Errors: ");
  Serial.println(stats.errors);
}

// ============================================================================
// NETWORK FUNCTIONS
// ============================================================================

void sendToPi(const MeasurementData& data) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("✗ Cannot send: WiFi not connected");
    stats.errors++;
    return;
  }

  HTTPClient http;

  // Build URL
  String url = String("http://") + PI_HOSTNAME + ":" + String(PI_PORT) + PI_ENDPOINT;

  http.begin(url);
  http.setTimeout(HTTP_TIMEOUT_MS);
  http.addHeader("Content-Type", "application/json");

  // Build JSON payload
  StaticJsonDocument<512> doc;

  doc["battery"]["voltage"] = round(data.battery_voltage * 100) / 100.0;
  doc["battery"]["current"] = round(data.battery_current * 10) / 10.0;
  doc["battery"]["power"] = round(data.battery_power * 10) / 10.0;
  doc["battery"]["percent"] = round(data.battery_percent);

  doc["environment"]["temperature"] = round(data.ambient_temp * 10) / 10.0;
  doc["environment"]["humidity"] = round(data.ambient_humidity * 10) / 10.0;
  doc["environment"]["pressure"] = round(data.ambient_pressure * 10) / 10.0;

  doc["esp32"]["wifi_rssi"] = data.wifi_rssi;
  doc["esp32"]["uptime"] = data.uptime_seconds;
  doc["esp32"]["temperature"] = round(data.esp32_temp * 10) / 10.0;

  doc["alerts"]["battery_low"] = data.battery_low;
  doc["alerts"]["battery_critical"] = data.battery_critical;
  doc["alerts"]["temp_high"] = data.temp_high;
  doc["alerts"]["temp_critical"] = data.temp_critical;

  doc["timestamp"] = millis();

  // Serialize to string
  String jsonPayload;
  serializeJson(doc, jsonPayload);

  // Send POST request
  Serial.print("\n📤 Sending to ");
  Serial.print(url);
  Serial.print(" ... ");

  int httpCode = http.POST(jsonPayload);

  if (httpCode > 0) {
    Serial.print("✓ (");
    Serial.print(httpCode);
    Serial.println(")");

    if (httpCode == HTTP_CODE_OK) {
      stats.measurements_sent++;

      // Print response
      String response = http.getString();
      if (response.length() > 0) {
        Serial.print("   Response: ");
        Serial.println(response);
      }
    }
  } else {
    Serial.print("✗ Error: ");
    Serial.println(http.errorToString(httpCode));
    stats.errors++;
  }

  http.end();
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// Calculate battery runtime estimate
float estimateRuntimeHours(float voltage, float current_ma) {
  if (current_ma <= 0) return -1;  // Invalid

  // Assume 5000mAh battery (typical power bank)
  const float BATTERY_CAPACITY_MAH = 5000.0;

  // Estimate remaining capacity based on voltage
  float remaining_percent = ((voltage - 3.0) / (4.2 - 3.0)) * 100.0;
  remaining_percent = constrain(remaining_percent, 0.0, 100.0);

  float remaining_mah = (BATTERY_CAPACITY_MAH * remaining_percent) / 100.0;

  return remaining_mah / current_ma;
}
