#!/usr/bin/env python3
"""
Flask Backend with MQTT Integration
Serves web dashboard with real-time ESP32 data via MQTT.

Architecture:
- MQTT subscriber runs in background thread
- Flask serves HTTP API and dashboard
- Data flows: ESP32 → MQTT → Python → Flask → Browser

Advantages:
- Real-time updates via MQTT (low latency)
- HTTP API for dashboard access
- Decoupled ESP32 and web frontend
- Multiple ESP32 devices supported
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import psutil
import platform
from datetime import datetime
import logging
import sys
from pathlib import Path

# Add monitoring module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))

# Import MQTT monitor
from monitoring.mqtt_monitor import (
    create_mqtt_client,
    get_current_data,
    get_history_data,
    get_statistics,
    is_esp32_connected,
    history_snapshot_task
)

import threading
import paho.mqtt.client as mqtt

app = Flask(__name__)
CORS(app)  # Enable CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# MQTT BACKGROUND THREAD
# ============================================================================

# Global MQTT client
mqtt_client = None
mqtt_thread = None
history_thread = None

def start_mqtt_monitor():
    """Start MQTT monitoring in background thread"""
    global mqtt_client, mqtt_thread, history_thread

    logger.info("Starting MQTT monitor...")

    # Create MQTT client
    mqtt_client = create_mqtt_client()

    # Connect to broker
    try:
        mqtt_client.connect("localhost", 1883, 60)
        logger.info("✓ MQTT client connected")
    except Exception as e:
        logger.error(f"✗ Failed to connect to MQTT broker: {e}")
        logger.error("Make sure Mosquitto is running: sudo systemctl start mosquitto")
        return False

    # Start MQTT loop in background thread
    mqtt_thread = threading.Thread(target=mqtt_client.loop_forever, daemon=True)
    mqtt_thread.start()
    logger.info("✓ MQTT thread started")

    # Start history snapshot thread
    history_thread = threading.Thread(target=history_snapshot_task, daemon=True)
    history_thread.start()
    logger.info("✓ History thread started")

    return True

# ============================================================================
# RASPBERRY PI STATS (Original Functionality)
# ============================================================================

def get_cpu_temperature():
    """Get CPU temperature - works on Raspberry Pi"""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = float(f.read()) / 1000.0
            return round(temp, 1)
    except:
        return None

def get_system_stats():
    """Gather system statistics"""
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=0.5)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()

    # Memory
    memory = psutil.virtual_memory()

    # Disk
    disk = psutil.disk_usage('/')

    # Network
    net_io = psutil.net_io_counters()

    # System info
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time

    stats = {
        'cpu': {
            'percent': cpu_percent,
            'count': cpu_count,
            'freq_current': round(cpu_freq.current, 2) if cpu_freq else None,
            'freq_max': round(cpu_freq.max, 2) if cpu_freq else None,
            'temperature': get_cpu_temperature()
        },
        'memory': {
            'total': round(memory.total / (1024**3), 2),
            'used': round(memory.used / (1024**3), 2),
            'percent': memory.percent,
            'available': round(memory.available / (1024**3), 2)
        },
        'disk': {
            'total': round(disk.total / (1024**3), 2),
            'used': round(disk.used / (1024**3), 2),
            'free': round(disk.free / (1024**3), 2),
            'percent': disk.percent
        },
        'network': {
            'bytes_sent': round(net_io.bytes_sent / (1024**2), 2),
            'bytes_recv': round(net_io.bytes_recv / (1024**2), 2)
        },
        'system': {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'architecture': platform.machine(),
            'hostname': platform.node(),
            'uptime': str(uptime).split('.')[0]
        }
    }

    return stats

# ============================================================================
# API ENDPOINTS - COMBINED STATS
# ============================================================================

@app.route('/api/stats')
def api_stats():
    """
    Combined API endpoint with Raspberry Pi + ESP32 stats.
    ESP32 data comes from MQTT background thread.
    """
    # Get Raspberry Pi stats
    stats = get_system_stats()

    # Add ESP32 data from MQTT
    esp32_data = get_current_data()

    stats['esp32'] = esp32_data

    return jsonify(stats)

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'esp32_connected': is_esp32_connected(),
        'mqtt_active': mqtt_thread is not None and mqtt_thread.is_alive(),
        'timestamp': datetime.now().isoformat()
    })

# ============================================================================
# API ENDPOINTS - ESP32 SPECIFIC
# ============================================================================

@app.route('/api/esp32/current')
def esp32_current():
    """Get current ESP32 readings"""
    return jsonify(get_current_data())

@app.route('/api/esp32/history')
def esp32_history():
    """Get historical ESP32 data"""
    count = request.args.get('count', type=int)
    return jsonify({
        'data': get_history_data(count),
        'count': len(get_history_data(count))
    })

@app.route('/api/esp32/stats')
def esp32_stats():
    """Get ESP32 statistics"""
    return jsonify(get_statistics())

@app.route('/api/esp32/status')
def esp32_status():
    """Get ESP32 connection status"""
    data = get_current_data()
    stats = get_statistics()

    return jsonify({
        'connected': is_esp32_connected(),
        'last_update': data.get('last_update'),
        'status': data.get('status'),
        'battery_runtime_hours': data.get('battery_runtime_hours'),
        'total_messages': stats.get('messages_received'),
        'connection_drops': stats.get('connection_drops')
    })

# ============================================================================
# MQTT CONTROL ENDPOINTS
# ============================================================================

@app.route('/api/mqtt/publish', methods=['POST'])
def mqtt_publish():
    """Publish MQTT message (send command to ESP32)"""
    data = request.get_json()

    if not data or 'topic' not in data or 'message' not in data:
        return jsonify({'error': 'Missing topic or message'}), 400

    try:
        mqtt_client.publish(data['topic'], data['message'], qos=1)
        logger.info(f"Published to {data['topic']}: {data['message']}")
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.error(f"Publish failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mqtt/cmd/reset', methods=['POST'])
def mqtt_cmd_reset():
    """Send reset command to ESP32"""
    mqtt_client.publish('holy-calc/cmd/reset', 'true', qos=1)
    return jsonify({'status': 'ok', 'command': 'reset'})

# ============================================================================
# CALCULATOR INTEGRATION (Optional)
# ============================================================================

@app.route('/api/calculator/stats')
def calculator_stats():
    """Get Holy Calculator performance statistics"""
    try:
        from cascade.calculator_engine import CalculatorEngine

        # Placeholder - integrate with actual calculator instance
        return jsonify({
            'status': 'available',
            'queries_processed': 0,
            'sympy_success_rate': 0,
            'llm_usage_percent': 0
        })

    except ImportError:
        return jsonify({
            'status': 'unavailable',
            'message': 'Calculator engine not found'
        }), 404

# ============================================================================
# DASHBOARD HTML
# ============================================================================

@app.route('/')
def index():
    """Serve simple HTML dashboard"""
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Holy Calculator Monitor</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        .card h2 {
            margin-top: 0;
            border-bottom: 2px solid rgba(255, 255, 255, 0.3);
            padding-bottom: 10px;
        }
        .stat {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
        }
        .value {
            font-weight: bold;
        }
        .status {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 5px;
        }
        .status.online { background: #4ade80; }
        .status.offline { background: #f87171; }
        .alert {
            background: rgba(248, 113, 113, 0.2);
            border-left: 4px solid #f87171;
            padding: 10px;
            margin-top: 10px;
            border-radius: 5px;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            overflow: hidden;
            margin-top: 5px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4ade80 0%, #22c55e 100%);
            transition: width 0.3s;
        }
        .updated {
            text-align: center;
            margin-top: 20px;
            font-size: 0.9em;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🥧 Holy Calculator System Monitor</h1>

        <div class="grid">
            <!-- ESP32 Status -->
            <div class="card">
                <h2>ESP32 Status</h2>
                <div class="stat">
                    <span>Connection:</span>
                    <span><span class="status" id="esp32-status"></span><span id="esp32-conn">Checking...</span></span>
                </div>
                <div class="stat">
                    <span>Last Update:</span>
                    <span class="value" id="esp32-update">-</span>
                </div>
                <div class="stat">
                    <span>Messages:</span>
                    <span class="value" id="esp32-msgs">0</span>
                </div>
            </div>

            <!-- Battery -->
            <div class="card">
                <h2>🔋 Battery</h2>
                <div class="stat">
                    <span>Voltage:</span>
                    <span class="value" id="battery-voltage">-</span>
                </div>
                <div class="stat">
                    <span>Current:</span>
                    <span class="value" id="battery-current">-</span>
                </div>
                <div class="stat">
                    <span>Power:</span>
                    <span class="value" id="battery-power">-</span>
                </div>
                <div class="stat">
                    <span>Level:</span>
                    <span class="value" id="battery-percent">-</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="battery-bar" style="width: 0%"></div>
                </div>
                <div class="stat">
                    <span>Runtime:</span>
                    <span class="value" id="battery-runtime">-</span>
                </div>
                <div id="battery-alert"></div>
            </div>

            <!-- Environment -->
            <div class="card">
                <h2>🌡️ Environment</h2>
                <div class="stat">
                    <span>Temperature:</span>
                    <span class="value" id="env-temp">-</span>
                </div>
                <div class="stat">
                    <span>Humidity:</span>
                    <span class="value" id="env-humidity">-</span>
                </div>
                <div class="stat">
                    <span>Pressure:</span>
                    <span class="value" id="env-pressure">-</span>
                </div>
                <div id="temp-alert"></div>
            </div>

            <!-- Raspberry Pi -->
            <div class="card">
                <h2>🥧 Raspberry Pi</h2>
                <div class="stat">
                    <span>CPU:</span>
                    <span class="value" id="pi-cpu">-</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="pi-cpu-bar" style="width: 0%"></div>
                </div>
                <div class="stat">
                    <span>Memory:</span>
                    <span class="value" id="pi-mem">-</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="pi-mem-bar" style="width: 0%"></div>
                </div>
                <div class="stat">
                    <span>Temp:</span>
                    <span class="value" id="pi-temp">-</span>
                </div>
            </div>
        </div>

        <div class="updated" id="last-updated">Last updated: Never</div>
    </div>

    <script>
        async function updateStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();

                // ESP32 Status
                const esp32 = data.esp32;
                const connected = esp32.connected;

                document.getElementById('esp32-status').className = 'status ' + (connected ? 'online' : 'offline');
                document.getElementById('esp32-conn').textContent = connected ? 'Online' : 'Offline';
                document.getElementById('esp32-update').textContent = esp32.last_update ? new Date(esp32.last_update).toLocaleTimeString() : '-';

                // Battery
                if (esp32.battery.voltage) {
                    document.getElementById('battery-voltage').textContent = esp32.battery.voltage.toFixed(2) + ' V';
                    document.getElementById('battery-current').textContent = esp32.battery.current.toFixed(0) + ' mA';
                    document.getElementById('battery-power').textContent = esp32.battery.power.toFixed(0) + ' mW';
                    document.getElementById('battery-percent').textContent = esp32.battery.percent + '%';
                    document.getElementById('battery-bar').style.width = esp32.battery.percent + '%';

                    if (esp32.battery_runtime_hours) {
                        document.getElementById('battery-runtime').textContent = esp32.battery_runtime_hours.toFixed(1) + ' hours';
                    }

                    // Alerts
                    if (esp32.alerts.battery_critical) {
                        document.getElementById('battery-alert').innerHTML = '<div class="alert">⚠️ CRITICAL: Battery critically low!</div>';
                    } else if (esp32.alerts.battery_low) {
                        document.getElementById('battery-alert').innerHTML = '<div class="alert">⚠️ WARNING: Battery low</div>';
                    } else {
                        document.getElementById('battery-alert').innerHTML = '';
                    }
                }

                // Environment
                if (esp32.environment.temperature) {
                    document.getElementById('env-temp').textContent = esp32.environment.temperature.toFixed(1) + ' °C';
                    document.getElementById('env-humidity').textContent = esp32.environment.humidity.toFixed(0) + ' %';
                    document.getElementById('env-pressure').textContent = esp32.environment.pressure.toFixed(0) + ' hPa';

                    if (esp32.alerts.temp_critical || esp32.alerts.temp_high) {
                        document.getElementById('temp-alert').innerHTML = '<div class="alert">🔥 Temperature high!</div>';
                    } else {
                        document.getElementById('temp-alert').innerHTML = '';
                    }
                }

                // Raspberry Pi
                document.getElementById('pi-cpu').textContent = data.cpu.percent + '%';
                document.getElementById('pi-cpu-bar').style.width = data.cpu.percent + '%';
                document.getElementById('pi-mem').textContent = data.memory.used.toFixed(1) + ' / ' + data.memory.total + ' GB';
                document.getElementById('pi-mem-bar').style.width = data.memory.percent + '%';

                if (data.cpu.temperature) {
                    document.getElementById('pi-temp').textContent = data.cpu.temperature + ' °C';
                }

                // Get ESP32 stats for message count
                const statsResp = await fetch('/api/esp32/stats');
                const statsData = await statsResp.json();
                document.getElementById('esp32-msgs').textContent = statsData.messages_received;

                // Update timestamp
                document.getElementById('last-updated').textContent = 'Last updated: ' + new Date().toLocaleTimeString();

            } catch (error) {
                console.error('Error fetching stats:', error);
            }
        }

        // Update every 2 seconds
        updateStats();
        setInterval(updateStats, 2000);
    </script>
</body>
</html>
'''

# ============================================================================
# STARTUP
# ============================================================================

def initialize():
    """Initialize the application"""
    logger.info("="*70)
    logger.info("Holy Calculator - Flask Backend with MQTT")
    logger.info("="*70)

    # Start MQTT monitor
    if not start_mqtt_monitor():
        logger.error("Failed to start MQTT monitor. Exiting.")
        sys.exit(1)

    logger.info("\nAvailable endpoints:")
    logger.info("  - GET  /                    Dashboard (HTML)")
    logger.info("  - GET  /api/stats           Combined Pi + ESP32 stats")
    logger.info("  - GET  /api/health          Health check")
    logger.info("  - GET  /api/esp32/current   Current ESP32 readings")
    logger.info("  - GET  /api/esp32/history   Historical data")
    logger.info("  - GET  /api/esp32/stats     ESP32 statistics")
    logger.info("  - GET  /api/esp32/status    ESP32 connection status")
    logger.info("  - POST /api/mqtt/publish    Send MQTT message")
    logger.info("  - POST /api/mqtt/cmd/reset  Reset ESP32")
    logger.info("="*70)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    initialize()

    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
