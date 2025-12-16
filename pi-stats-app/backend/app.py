from flask import Flask, jsonify
from flask_cors import CORS
import psutil
import platform
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

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
    cpu_percent = psutil.cpu_percent(interval=1)
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

@app.route('/api/stats')
def api_stats():
    """API endpoint for getting stats as JSON"""
    stats = get_system_stats()
    return jsonify(stats)

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Run on all interfaces so you can access from other devices
    app.run(host='0.0.0.0', port=5000, debug=True)
