#!/usr/bin/env python3
"""
Enhanced Flask Backend with ESP32 Integration
Extends the original stats server to accept and display ESP32 sensor data.

This version adds:
- ESP32 data ingestion endpoint
- Battery monitoring
- Environmental sensors
- Alert system
- Historical data storage
- Calculator stats integration
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import psutil
import platform
from datetime import datetime, timedelta
from collections import deque
import json
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# ESP32 DATA STORAGE
# ============================================================================

# Current ESP32 data (most recent reading)
esp32_data = {
    'battery': {
        'voltage': None,
        'current': None,
        'power': None,
        'percent': None
    },
    'environment': {
        'temperature': None,
        'humidity': None,
        'pressure': None
    },
    'esp32': {
        'wifi_rssi': None,
        'uptime': None,
        'temperature': None
    },
    'alerts': {
        'battery_low': False,
        'battery_critical': False,
        'temp_high': False,
        'temp_critical': False
    },
    'last_update': None,
    'connected': False
}

# Historical data (last 100 readings, ~3 minutes at 2s interval)
esp32_history = deque(maxlen=100)

# Statistics
esp32_stats = {
    'total_readings': 0,
    'first_reading': None,
    'connection_drops': 0,
    'alert_count': {
        'battery_low': 0,
        'battery_critical': 0,
        'temp_high': 0,
        'temp_critical': 0
    }
}

# Timeout for ESP32 (consider disconnected if no data for 10 seconds)
ESP32_TIMEOUT_SECONDS = 10

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
    cpu_percent = psutil.cpu_percent(interval=0.5)  # Reduced from 1s for faster response
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
# ESP32 DATA MANAGEMENT
# ============================================================================

def check_esp32_connection():
    """Check if ESP32 is still connected based on last update time"""
    if esp32_data['last_update'] is None:
        return False

    last_update = datetime.fromisoformat(esp32_data['last_update'])
    elapsed = (datetime.now() - last_update).total_seconds()

    return elapsed < ESP32_TIMEOUT_SECONDS

def update_esp32_stats(data):
    """Update ESP32 statistics"""
    # Increment total readings
    esp32_stats['total_readings'] += 1

    # Record first reading time
    if esp32_stats['first_reading'] is None:
        esp32_stats['first_reading'] = datetime.now().isoformat()

    # Check for connection drops (gap > 5 seconds from previous reading)
    if esp32_data['last_update'] is not None:
        last_update = datetime.fromisoformat(esp32_data['last_update'])
        gap = (datetime.now() - last_update).total_seconds()
        if gap > 5:
            esp32_stats['connection_drops'] += 1
            logger.warning(f"ESP32 connection gap detected: {gap:.1f}s")

    # Count alerts
    for alert_type in ['battery_low', 'battery_critical', 'temp_high', 'temp_critical']:
        if data.get('alerts', {}).get(alert_type, False):
            esp32_stats['alert_count'][alert_type] += 1

def calculate_battery_runtime():
    """Estimate remaining battery runtime based on current draw"""
    if not esp32_data['connected']:
        return None

    voltage = esp32_data['battery'].get('voltage')
    current = esp32_data['battery'].get('current')
    percent = esp32_data['battery'].get('percent')

    if voltage is None or current is None or current <= 0:
        return None

    # Assume 5000mAh battery (typical power bank)
    BATTERY_CAPACITY_MAH = 5000.0

    # Estimate remaining capacity
    remaining_mah = (BATTERY_CAPACITY_MAH * percent) / 100.0

    # Calculate runtime in hours
    runtime_hours = remaining_mah / current

    return round(runtime_hours, 2)

# ============================================================================
# API ENDPOINTS - ESP32
# ============================================================================

@app.route('/api/esp32/data', methods=['POST'])
def esp32_data_endpoint():
    """
    Receive sensor data from ESP32.

    Expected JSON format:
    {
        "battery": {"voltage": 4.1, "current": 450, "power": 1845, "percent": 75},
        "environment": {"temperature": 28.5, "humidity": 45.2, "pressure": 1013.2},
        "esp32": {"wifi_rssi": -45, "uptime": 1234, "temperature": 42.0},
        "alerts": {"battery_low": false, "battery_critical": false, ...},
        "timestamp": 12345678
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        # Update current data
        esp32_data['battery'] = data.get('battery', {})
        esp32_data['environment'] = data.get('environment', {})
        esp32_data['esp32'] = data.get('esp32', {})
        esp32_data['alerts'] = data.get('alerts', {})
        esp32_data['last_update'] = datetime.now().isoformat()
        esp32_data['connected'] = True

        # Update statistics
        update_esp32_stats(data)

        # Add to history
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'voltage': data.get('battery', {}).get('voltage'),
            'current': data.get('battery', {}).get('current'),
            'temperature': data.get('environment', {}).get('temperature'),
            'cpu_temp': get_cpu_temperature()
        }
        esp32_history.append(history_entry)

        # Log alerts
        alerts = data.get('alerts', {})
        if alerts.get('battery_critical'):
            logger.error("⚠️  CRITICAL: Battery critically low!")
        elif alerts.get('battery_low'):
            logger.warning("⚠️  WARNING: Battery low")

        if alerts.get('temp_critical'):
            logger.error("🔥 CRITICAL: Temperature critically high!")
        elif alerts.get('temp_high'):
            logger.warning("⚠️  WARNING: Temperature high")

        logger.info(f"✓ ESP32 data received: {data.get('battery', {}).get('voltage')}V, "
                   f"{data.get('environment', {}).get('temperature')}°C")

        return jsonify({
            'status': 'ok',
            'message': 'Data received',
            'readings_count': esp32_stats['total_readings']
        })

    except Exception as e:
        logger.error(f"Error processing ESP32 data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/esp32/status')
def esp32_status():
    """Get ESP32 connection status and current readings"""
    # Update connection status
    esp32_data['connected'] = check_esp32_connection()

    # Calculate runtime estimate
    runtime = calculate_battery_runtime()

    return jsonify({
        'connected': esp32_data['connected'],
        'last_update': esp32_data['last_update'],
        'battery_runtime_hours': runtime,
        'total_readings': esp32_stats['total_readings'],
        'connection_drops': esp32_stats['connection_drops'],
        'data': esp32_data
    })

@app.route('/api/esp32/history')
def esp32_history_endpoint():
    """Get historical ESP32 data"""
    return jsonify({
        'count': len(esp32_history),
        'data': list(esp32_history)
    })

@app.route('/api/esp32/stats')
def esp32_stats_endpoint():
    """Get ESP32 statistics"""
    # Calculate uptime
    uptime_str = "N/A"
    if esp32_stats['first_reading']:
        first = datetime.fromisoformat(esp32_stats['first_reading'])
        uptime = datetime.now() - first
        uptime_str = str(uptime).split('.')[0]

    return jsonify({
        'total_readings': esp32_stats['total_readings'],
        'uptime': uptime_str,
        'connection_drops': esp32_stats['connection_drops'],
        'alerts': esp32_stats['alert_count']
    })

# ============================================================================
# API ENDPOINTS - COMBINED STATS
# ============================================================================

@app.route('/api/stats')
def api_stats():
    """
    Combined API endpoint with both Raspberry Pi and ESP32 stats.
    This extends the original endpoint with ESP32 data.
    """
    # Get Raspberry Pi stats
    stats = get_system_stats()

    # Add ESP32 data if available
    esp32_data['connected'] = check_esp32_connection()

    stats['esp32'] = {
        'connected': esp32_data['connected'],
        'last_update': esp32_data['last_update'],
        'battery': esp32_data['battery'],
        'environment': esp32_data['environment'],
        'esp32_status': esp32_data['esp32'],
        'alerts': esp32_data['alerts'],
        'battery_runtime_hours': calculate_battery_runtime()
    }

    return jsonify(stats)

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'esp32_connected': check_esp32_connection(),
        'timestamp': datetime.now().isoformat()
    })

# ============================================================================
# API ENDPOINTS - CALCULATOR INTEGRATION (Optional)
# ============================================================================

@app.route('/api/calculator/stats')
def calculator_stats():
    """
    Get Holy Calculator performance statistics.
    This requires the calculator engine to be accessible.
    """
    try:
        import sys
        from pathlib import Path

        # Add scripts to path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))

        from cascade.calculator_engine import CalculatorEngine

        # This assumes you have a running instance somewhere
        # In production, you'd want to maintain a singleton
        # For now, we'll return a placeholder
        return jsonify({
            'status': 'available',
            'message': 'Calculator stats integration available'
        })

    except ImportError:
        return jsonify({
            'status': 'unavailable',
            'message': 'Calculator engine not found'
        }), 404

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    logger.info("="*70)
    logger.info("Flask Backend with ESP32 Integration")
    logger.info("="*70)
    logger.info("Starting server on http://0.0.0.0:5000")
    logger.info("\nAvailable endpoints:")
    logger.info("  - GET  /api/stats           Combined Pi + ESP32 stats")
    logger.info("  - GET  /api/health          Health check")
    logger.info("  - POST /api/esp32/data      ESP32 sensor data ingestion")
    logger.info("  - GET  /api/esp32/status    ESP32 connection status")
    logger.info("  - GET  /api/esp32/history   Historical data")
    logger.info("  - GET  /api/esp32/stats     ESP32 statistics")
    logger.info("="*70)

    # Run on all interfaces so you can access from ESP32 and other devices
    app.run(host='0.0.0.0', port=5000, debug=True)
