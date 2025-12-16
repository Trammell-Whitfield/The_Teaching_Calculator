/*
 * ESP32 MQTT Monitor for Holy Calculator
 * Publishes battery & environmental data via MQTT
 *
 * Advantages over HTTP POST:
 * - Lower bandwidth (~70% reduction)
 * - Lower latency (<100ms vs 500ms+)
 * - Persistent connection (no reconnect overhead)
 * - QoS support for reliability
 * - Publish/subscribe pattern (multiple subscribers)
 * - Better for battery-powered devices
 *
 * MQTT Topics Structure:
 *   holy-calc/battery/voltage
 *   holy-calc/battery/current
 *   holy-calc/battery/power
 *   holy-calc/battery/percent
 *   holy-calc/environment/temperature
 *   holy-calc/environment/humidity
 *   holy-calc/environment/pressure
 *   holy-calc/esp32/wifi_rssi
 *   holy-calc/esp32/uptime
 *   holy-calc/alerts/battery_low
 *   holy-calc/alerts/temp_high
 *
 * Hardware:
 * - ESP32 DevKit v1
 * - INA219 current sensor (I2C: 0x40)
 * - BME280 temp/humidity sensor (I2C: 0x76)
 */

#include <WiFi.h>
#include <PubSubClient.h>  // MQTT client library
#include <Wire.h>
#include <Adafruit_INA219.h>
#include <Adafruit_BME280.h>
#include <ArduinoJson.h>

// ============================================================================
// CONFIGURATION
// ============================================================================

// WiFi credentials
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// MQTT Broker settings
const char* MQTT_BROKER = "raspberrypi.local";  // Or IP: "192.168.1.100"
const int MQTT_PORT = 1883;                     // Default MQTT port
const char* MQTT_CLIENT_ID = "holy-calc-esp32"; // Unique client ID
const char* MQTT_USER = "";                     // Leave empty if no auth
const char* MQTT_PASSWORD = "";                 // Leave empty if no auth

// MQTT Topics (base)
const char* MQTT_TOPIC_BASE = "holy-calc";

// Measurement settings
const int MEASUREMENT_INTERVAL_MS = 2000;  // 2 seconds
const int MQTT_KEEPALIVE = 15;             // 15 second keepalive
const int MQTT_QOS = 1;                    // QoS 1 = at least once delivery

// Alert thresholds
const float BATTERY_LOW_VOLTAGE = 3.6;
const float BATTERY_CRITICAL_VOLTAGE = 3.3;
const float TEMP_HIGH_CELSIUS = 80.0;
const float TEMP_CRITICAL_CELSIUS = 85.0;

// ============================================================================
// GLOBALS
// ============================================================================

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

Adafruit_INA219 ina219;
Adafruit_BME280 bme280;

bool ina219_available = false;
bool bme280_available = false;

unsigned long lastMeasurement = 0;
unsigned long lastMqttReconnect = 0;
unsigned long bootTime = 0;

// Statistics
struct Stats {
  unsigned long messages_published = 0;
  unsigned long mqtt_reconnects = 0;
  unsigned long mqtt_errors = 0;
} stats;

// ============================================================================
// SETUP
// ============================================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n\n");
  Serial.println("========================================");
  Serial.println("ESP32 MQTT Monitor for Holy Calculator");
  Serial.println("========================================");

  bootTime = millis();

  // Initialize I2C
  Wire.begin(21, 22);
  Serial.println("\n✓ I2C initialized");

  // Initialize sensors
  initSensors();

  // Connect to WiFi
  connectWiFi();

  // Setup MQTT
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  mqttClient.setKeepAlive(MQTT_KEEPALIVE);

  // Connect to MQTT
  connectMQTT();

  Serial.println("\n========================================");
  Serial.println("Setup complete! Publishing data...");
  Serial.println("========================================\n");
}

// ============================================================================
// MAIN LOOP
// ============================================================================

void loop() {
  // Maintain MQTT connection
  if (!mqttClient.connected()) {
    // Try reconnect every 5 seconds
    if (millis() - lastMqttReconnect > 5000) {
      lastMqttReconnect = millis();
      connectMQTT();
    }
  }
  mqttClient.loop();

  // Take measurements at interval
  if (millis() - lastMeasurement >= MEASUREMENT_INTERVAL_MS) {
    lastMeasurement = millis();

    if (mqttClient.connected()) {
      takeMeasurementsAndPublish();
    } else {
      Serial.println("⚠ Skipping measurement - MQTT disconnected");
    }
  }

  delay(10);  // Small delay
}

// ============================================================================
// SENSOR INITIALIZATION
// ============================================================================

void initSensors() {
  // INA219
  Serial.print("Initializing INA219 current sensor... ");
  if (ina219.begin()) {
    ina219_available = true;
    ina219.setCalibration_16V_400mA();
    Serial.println("✓");
  } else {
    Serial.println("✗ (not found)");
  }

  // BME280
  Serial.print("Initializing BME280 sensor... ");
  if (bme280.begin(0x76)) {
    bme280_available = true;
    Serial.println("✓");
  } else if (bme280.begin(0x77)) {
    bme280_available = true;
    Serial.println("✓ (found at 0x77)");
  } else {
    Serial.println("✗ (not found)");
  }
}

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
    Serial.print("Signal: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println(" ✗ Failed");
  }
}

// ============================================================================
// MQTT FUNCTIONS
// ============================================================================

void connectMQTT() {
  Serial.print("Connecting to MQTT broker: ");
  Serial.print(MQTT_BROKER);
  Serial.print(":");
  Serial.print(MQTT_PORT);
  Serial.print(" ... ");

  // Generate last will topic/message
  String lwt_topic = String(MQTT_TOPIC_BASE) + "/status";
  const char* lwt_message = "offline";

  // Connect with last will
  bool connected = false;
  if (strlen(MQTT_USER) > 0) {
    // Connect with authentication
    connected = mqttClient.connect(
      MQTT_CLIENT_ID,
      MQTT_USER,
      MQTT_PASSWORD,
      lwt_topic.c_str(),
      MQTT_QOS,
      true,  // retain
      lwt_message
    );
  } else {
    // Connect without authentication
    connected = mqttClient.connect(
      MQTT_CLIENT_ID,
      lwt_topic.c_str(),
      MQTT_QOS,
      true,  // retain
      lwt_message
    );
  }

  if (connected) {
    Serial.println("✓");
    stats.mqtt_reconnects++;

    // Publish online status
    publishStatus("online");

    // Subscribe to control topics (optional)
    String cmd_topic = String(MQTT_TOPIC_BASE) + "/cmd/#";
    mqttClient.subscribe(cmd_topic.c_str(), MQTT_QOS);

    Serial.println("✓ MQTT connected and subscribed");
  } else {
    Serial.print("✗ Failed, rc=");
    Serial.println(mqttClient.state());
    stats.mqtt_errors++;
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  // Handle incoming MQTT messages (commands from Pi)
  Serial.print("📩 MQTT message: ");
  Serial.print(topic);
  Serial.print(" = ");

  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);

  // Parse command topic
  String topicStr = String(topic);

  // Example: holy-calc/cmd/reset -> reset statistics
  if (topicStr.endsWith("/cmd/reset")) {
    stats.messages_published = 0;
    stats.mqtt_reconnects = 0;
    stats.mqtt_errors = 0;
    Serial.println("✓ Statistics reset");
    publishStatus("reset_ok");
  }

  // Example: holy-calc/cmd/interval -> change measurement interval
  else if (topicStr.endsWith("/cmd/interval")) {
    // Would update MEASUREMENT_INTERVAL_MS
    Serial.println("✓ Interval command received");
  }
}

// ============================================================================
// MEASUREMENT & PUBLISHING
// ============================================================================

void takeMeasurementsAndPublish() {
  // Battery measurements
  float voltage = 0.0;
  float current = 0.0;
  float power = 0.0;
  float percent = 0.0;

  if (ina219_available) {
    voltage = ina219.getBusVoltage_V();
    current = ina219.getCurrent_mA();
    power = ina219.getPower_mW();
    percent = ((voltage - 3.0) / (4.2 - 3.0)) * 100.0;
    percent = constrain(percent, 0.0, 100.0);
  }

  // Environmental measurements
  float temperature = 0.0;
  float humidity = 0.0;
  float pressure = 0.0;

  if (bme280_available) {
    temperature = bme280.readTemperature();
    humidity = bme280.readHumidity();
    pressure = bme280.readPressure() / 100.0;  // Pa to hPa
  }

  // ESP32 status
  int wifi_rssi = WiFi.RSSI();
  unsigned long uptime = (millis() - bootTime) / 1000;

  // Check alerts
  bool battery_low = (voltage < BATTERY_LOW_VOLTAGE);
  bool battery_critical = (voltage < BATTERY_CRITICAL_VOLTAGE);
  bool temp_high = (temperature > TEMP_HIGH_CELSIUS);
  bool temp_critical = (temperature > TEMP_CRITICAL_CELSIUS);

  // Publish all measurements
  String base = String(MQTT_TOPIC_BASE);

  // Battery
  publishMQTT((base + "/battery/voltage").c_str(), String(voltage, 2).c_str());
  publishMQTT((base + "/battery/current").c_str(), String(current, 1).c_str());
  publishMQTT((base + "/battery/power").c_str(), String(power, 1).c_str());
  publishMQTT((base + "/battery/percent").c_str(), String(percent, 0).c_str());

  // Environment
  if (bme280_available) {
    publishMQTT((base + "/environment/temperature").c_str(), String(temperature, 1).c_str());
    publishMQTT((base + "/environment/humidity").c_str(), String(humidity, 1).c_str());
    publishMQTT((base + "/environment/pressure").c_str(), String(pressure, 1).c_str());
  }

  // ESP32
  publishMQTT((base + "/esp32/wifi_rssi").c_str(), String(wifi_rssi).c_str());
  publishMQTT((base + "/esp32/uptime").c_str(), String(uptime).c_str());
  publishMQTT((base + "/esp32/temperature").c_str(), String(temperatureRead(), 1).c_str());

  // Alerts
  publishMQTT((base + "/alerts/battery_low").c_str(), battery_low ? "true" : "false");
  publishMQTT((base + "/alerts/battery_critical").c_str(), battery_critical ? "true" : "false");
  publishMQTT((base + "/alerts/temp_high").c_str(), temp_high ? "true" : "false");
  publishMQTT((base + "/alerts/temp_critical").c_str(), temp_critical ? "true" : "false");

  // Optional: Publish as single JSON message
  publishJSON(voltage, current, power, percent, temperature, humidity, pressure, wifi_rssi, uptime);

  // Print summary
  Serial.println("────────────────────────────────────────");
  Serial.printf("🔋 Battery: %.2fV, %.0fmA, %.0f%%\n", voltage, current, percent);
  if (bme280_available) {
    Serial.printf("🌡️  Environment: %.1f°C, %.0f%% RH, %.0fhPa\n", temperature, humidity, pressure);
  }
  Serial.printf("📡 MQTT: %lu msgs sent, %lu reconnects\n", stats.messages_published, stats.mqtt_reconnects);

  if (battery_critical || temp_critical) {
    Serial.println("🚨 CRITICAL ALERT!");
  } else if (battery_low || temp_high) {
    Serial.println("⚠️  WARNING");
  }
}

void publishMQTT(const char* topic, const char* payload) {
  if (mqttClient.publish(topic, payload, true)) {  // retained
    stats.messages_published++;
  } else {
    Serial.print("✗ Failed to publish: ");
    Serial.println(topic);
    stats.mqtt_errors++;
  }
}

void publishJSON(float voltage, float current, float power, float percent,
                 float temp, float humidity, float pressure,
                 int rssi, unsigned long uptime) {
  // Publish all data as single JSON message (optional, for easier parsing)
  StaticJsonDocument<512> doc;

  doc["battery"]["voltage"] = round(voltage * 100) / 100.0;
  doc["battery"]["current"] = round(current * 10) / 10.0;
  doc["battery"]["power"] = round(power * 10) / 10.0;
  doc["battery"]["percent"] = round(percent);

  if (bme280_available) {
    doc["environment"]["temperature"] = round(temp * 10) / 10.0;
    doc["environment"]["humidity"] = round(humidity * 10) / 10.0;
    doc["environment"]["pressure"] = round(pressure * 10) / 10.0;
  }

  doc["esp32"]["wifi_rssi"] = rssi;
  doc["esp32"]["uptime"] = uptime;

  String jsonString;
  serializeJson(doc, jsonString);

  String topic = String(MQTT_TOPIC_BASE) + "/data/json";
  publishMQTT(topic.c_str(), jsonString.c_str());
}

void publishStatus(const char* status) {
  String topic = String(MQTT_TOPIC_BASE) + "/status";
  mqttClient.publish(topic.c_str(), status, true);  // retained
}

// ============================================================================
// UTILITY
// ============================================================================

void printStats() {
  Serial.println("\n========================================");
  Serial.println("ESP32 MQTT STATISTICS");
  Serial.println("========================================");
  Serial.printf("Messages published: %lu\n", stats.messages_published);
  Serial.printf("MQTT reconnects:    %lu\n", stats.mqtt_reconnects);
  Serial.printf("MQTT errors:        %lu\n", stats.mqtt_errors);
  Serial.printf("WiFi RSSI:          %d dBm\n", WiFi.RSSI());
  Serial.printf("Uptime:             %lu seconds\n", (millis() - bootTime) / 1000);
  Serial.println("========================================\n");
}
