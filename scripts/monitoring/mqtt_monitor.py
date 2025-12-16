#!/usr/bin/env python3
"""
MQTT Monitor for Holy Calculator
Subscribes to ESP32 sensor data via MQTT and stores for dashboard display.

Advantages over HTTP POST:
- Lower latency (<100ms vs 500ms+)
- Persistent connection (no HTTP overhead)
- Automatic reconnection
- QoS support for reliability
- Can handle multiple ESP32 devices
- Lower power consumption on ESP32

MQTT Broker: Mosquitto running on Raspberry Pi
Topics: holy-calc/battery/*, holy-calc/environment/*, etc.
"""

import paho.mqtt.client as mqtt
import json
import logging
import time
from datetime import datetime
from collections import deque
from typing import Dict, Any, Optional
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# MQTT Broker settings
MQTT_BROKER = "localhost"  # Mosquitto on same Pi
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60
MQTT_CLIENT_ID = "holy-calc-monitor"

# MQTT Topics
MQTT_TOPIC_BASE = "holy-calc"
MQTT_TOPIC_SUBSCRIBE = f"{MQTT_TOPIC_BASE}/#"  # Subscribe to all

# Data storage
MAX_HISTORY_SIZE = 500  # ~15 minutes at 2s interval
DATA_TIMEOUT_SECONDS = 10  # Consider ESP32 disconnected if no data

# ============================================================================
# GLOBAL DATA STORAGE
# ============================================================================

class ESP32Data:
    """Thread-safe storage for ESP32 sensor data"""

    def __init__(self):
        self.lock = threading.Lock()

        # Current readings
        self.battery = {
            'voltage': None,
            'current': None,
            'power': None,
            'percent': None
        }

        self.environment = {
            'temperature': None,
            'humidity': None,
            'pressure': None
        }

        self.esp32 = {
            'wifi_rssi': None,
            'uptime': None,
            'temperature': None
        }

        self.alerts = {
            'battery_low': False,
            'battery_critical': False,
            'temp_high': False,
            'temp_critical': False
        }

        # Metadata
        self.status = 'offline'
        self.last_update = None
        self.connected = False

        # Historical data
        self.history = deque(maxlen=MAX_HISTORY_SIZE)

        # Statistics
        self.stats = {
            'messages_received': 0,
            'connection_drops': 0,
            'last_reconnect': None,
            'first_message': None
        }

    def update_field(self, category: str, field: str, value: Any):
        """Update a single field (thread-safe)"""
        with self.lock:
            if category == 'battery':
                self.battery[field] = value
            elif category == 'environment':
                self.environment[field] = value
            elif category == 'esp32':
                self.esp32[field] = value
            elif category == 'alerts':
                self.alerts[field] = value
            elif category == 'status':
                self.status = value

            # Update metadata
            self.last_update = datetime.now()
            self.connected = True
            self.stats['messages_received'] += 1

            # Record first message
            if self.stats['first_message'] is None:
                self.stats['first_message'] = datetime.now()

    def add_to_history(self):
        """Snapshot current data to history"""
        with self.lock:
            snapshot = {
                'timestamp': datetime.now().isoformat(),
                'voltage': self.battery.get('voltage'),
                'current': self.battery.get('current'),
                'temperature': self.environment.get('temperature'),
                'cpu_usage': None  # Will be filled by pi-stats integration
            }
            self.history.append(snapshot)

    def get_snapshot(self) -> Dict[str, Any]:
        """Get current data snapshot (thread-safe)"""
        with self.lock:
            return {
                'battery': self.battery.copy(),
                'environment': self.environment.copy(),
                'esp32': self.esp32.copy(),
                'alerts': self.alerts.copy(),
                'status': self.status,
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'connected': self.is_connected()
            }

    def get_history(self, count: Optional[int] = None) -> list:
        """Get historical data"""
        with self.lock:
            if count:
                return list(self.history)[-count:]
            return list(self.history)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        with self.lock:
            uptime = None
            if self.stats['first_message']:
                uptime = str(datetime.now() - self.stats['first_message']).split('.')[0]

            return {
                **self.stats,
                'uptime': uptime,
                'history_size': len(self.history)
            }

    def is_connected(self) -> bool:
        """Check if ESP32 is connected based on last update time"""
        if self.last_update is None:
            return False
        elapsed = (datetime.now() - self.last_update).total_seconds()
        return elapsed < DATA_TIMEOUT_SECONDS

    def calculate_runtime(self) -> Optional[float]:
        """Estimate battery runtime in hours"""
        voltage = self.battery.get('voltage')
        current = self.battery.get('current')
        percent = self.battery.get('percent')

        if not all([voltage, current, percent]) or current <= 0:
            return None

        # Assume 5000mAh battery
        BATTERY_CAPACITY_MAH = 5000.0
        remaining_mah = (BATTERY_CAPACITY_MAH * percent) / 100.0
        runtime_hours = remaining_mah / current

        return round(runtime_hours, 2)

# Global data instance
esp32_data = ESP32Data()

# ============================================================================
# MQTT CALLBACKS
# ============================================================================

def on_connect(client, userdata, flags, rc):
    """Called when connected to MQTT broker"""
    if rc == 0:
        logger.info(f"✓ Connected to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")

        # Subscribe to all topics
        client.subscribe(MQTT_TOPIC_SUBSCRIBE, qos=1)
        logger.info(f"✓ Subscribed to: {MQTT_TOPIC_SUBSCRIBE}")

        # Update stats
        if esp32_data.stats['last_reconnect']:
            esp32_data.stats['connection_drops'] += 1
        esp32_data.stats['last_reconnect'] = datetime.now()

    else:
        logger.error(f"✗ Connection failed with code {rc}")

def on_disconnect(client, userdata, rc):
    """Called when disconnected from MQTT broker"""
    if rc != 0:
        logger.warning(f"⚠ Unexpected disconnect (code: {rc})")
    else:
        logger.info("Disconnected from MQTT broker")

def on_message(client, userdata, msg):
    """Called when MQTT message received"""
    topic = msg.topic
    payload = msg.payload.decode('utf-8')

    # Parse topic (e.g., "holy-calc/battery/voltage")
    parts = topic.split('/')

    if len(parts) < 3:
        return

    category = parts[1]  # battery, environment, esp32, alerts, status
    field = parts[2] if len(parts) > 2 else None

    # Handle different message types
    try:
        # Status messages
        if category == 'status':
            esp32_data.update_field('status', None, payload)
            logger.info(f"ESP32 status: {payload}")

        # JSON data message (all-in-one)
        elif category == 'data' and field == 'json':
            data = json.loads(payload)
            handle_json_data(data)

        # Individual field updates
        elif category in ['battery', 'environment', 'esp32']:
            # Convert to appropriate type
            value = parse_value(payload)
            esp32_data.update_field(category, field, value)

            # Log interesting events
            if category == 'battery' and field == 'voltage':
                logger.debug(f"Battery: {value}V")

        # Alert messages
        elif category == 'alerts':
            value = payload.lower() == 'true'
            esp32_data.update_field('alerts', field, value)

            if value:
                if field == 'battery_critical':
                    logger.error("🚨 CRITICAL: Battery critically low!")
                elif field == 'battery_low':
                    logger.warning("⚠️  WARNING: Battery low")
                elif field == 'temp_critical':
                    logger.error("🔥 CRITICAL: Temperature critically high!")
                elif field == 'temp_high':
                    logger.warning("⚠️  WARNING: Temperature high")

    except Exception as e:
        logger.error(f"Error processing message {topic}: {e}")

def handle_json_data(data: dict):
    """Handle JSON data message (all fields at once)"""
    # Update all fields from JSON
    for category in ['battery', 'environment', 'esp32']:
        if category in data:
            for field, value in data[category].items():
                esp32_data.update_field(category, field, value)

    logger.debug(f"JSON update: {data.get('battery', {}).get('voltage')}V")

def parse_value(payload: str):
    """Convert string payload to appropriate type"""
    try:
        # Try float first
        if '.' in payload:
            return float(payload)
        # Try int
        return int(payload)
    except ValueError:
        # Return as string
        return payload

# ============================================================================
# MQTT CLIENT SETUP
# ============================================================================

def create_mqtt_client():
    """Create and configure MQTT client"""
    client = mqtt.Client(client_id=MQTT_CLIENT_ID, clean_session=False)

    # Set callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    # Configure
    client.reconnect_delay_set(min_delay=1, max_delay=120)

    return client

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

def history_snapshot_task():
    """Periodically save snapshots to history"""
    while True:
        time.sleep(10)  # Every 10 seconds
        esp32_data.add_to_history()

# ============================================================================
# API INTERFACE (for Flask integration)
# ============================================================================

def get_current_data() -> Dict[str, Any]:
    """Get current ESP32 data (for Flask API)"""
    snapshot = esp32_data.get_snapshot()
    snapshot['battery_runtime_hours'] = esp32_data.calculate_runtime()
    return snapshot

def get_history_data(count: Optional[int] = None) -> list:
    """Get historical data (for Flask API)"""
    return esp32_data.get_history(count)

def get_statistics() -> Dict[str, Any]:
    """Get statistics (for Flask API)"""
    return esp32_data.get_stats()

def is_esp32_connected() -> bool:
    """Check if ESP32 is currently connected"""
    return esp32_data.is_connected()

# ============================================================================
# STANDALONE MODE
# ============================================================================

def main():
    """Run as standalone monitor (without Flask)"""
    logger.info("="*70)
    logger.info("Holy Calculator MQTT Monitor")
    logger.info("="*70)
    logger.info(f"Broker: {MQTT_BROKER}:{MQTT_PORT}")
    logger.info(f"Topics: {MQTT_TOPIC_SUBSCRIBE}")
    logger.info("="*70)

    # Create MQTT client
    client = create_mqtt_client()

    # Start background history task
    history_thread = threading.Thread(target=history_snapshot_task, daemon=True)
    history_thread.start()

    # Connect to broker
    try:
        logger.info("Connecting to MQTT broker...")
        client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)

        # Start MQTT loop
        logger.info("Starting MQTT loop... (Press Ctrl+C to stop)")
        client.loop_forever()

    except KeyboardInterrupt:
        logger.info("\n\nShutting down...")
        client.disconnect()
        print_final_stats()

    except Exception as e:
        logger.error(f"Error: {e}")
        client.disconnect()

def print_final_stats():
    """Print final statistics"""
    stats = get_statistics()
    data = get_current_data()

    print("\n" + "="*70)
    print("FINAL STATISTICS")
    print("="*70)
    print(f"Messages received: {stats['messages_received']}")
    print(f"Connection drops:  {stats['connection_drops']}")
    print(f"Monitor uptime:    {stats['uptime']}")
    print(f"History size:      {stats['history_size']} snapshots")

    print("\n" + "="*70)
    print("LAST READINGS")
    print("="*70)
    print(f"Battery:      {data['battery'].get('voltage')}V, "
          f"{data['battery'].get('current')}mA, "
          f"{data['battery'].get('percent')}%")

    if data['environment'].get('temperature'):
        print(f"Environment:  {data['environment'].get('temperature')}°C, "
              f"{data['environment'].get('humidity')}% RH, "
              f"{data['environment'].get('pressure')} hPa")

    print(f"ESP32:        RSSI {data['esp32'].get('wifi_rssi')} dBm, "
          f"uptime {data['esp32'].get('uptime')}s")

    if data['battery_runtime_hours']:
        print(f"Est. runtime: {data['battery_runtime_hours']} hours")

    print("="*70 + "\n")

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
