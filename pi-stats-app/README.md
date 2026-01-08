# Raspberry Pi 5 Stats Monitor

A simple web application to monitor your Raspberry Pi 5 system statistics in real-time.

## Features

- Real-time monitoring of:
  - CPU usage, temperature, and frequency
  - Memory usage
  - Disk usage
  - Network statistics
  - System information and uptime
- Auto-refreshes every 2 seconds
- Beautiful, responsive UI with gradient design
- Works on desktop and mobile

## Architecture

- **Frontend**: React app with modern UI
- **Backend**: Flask API that gathers system stats using psutil

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (optional but recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the Flask server:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The app will open at `http://localhost:3000`

## Deployment on Raspberry Pi 5

### Option 1: Development Mode (Quick Setup)

1. SSH into your Raspberry Pi 5
2. Clone/copy this project to your Pi
3. Follow the setup instructions above
4. Access from other devices using `http://<pi-ip-address>:3000`

### Option 2: Production Build

1. Build the React app:
```bash
cd frontend
npm run build
```

2. Serve the build folder using the Flask backend by modifying `app.py`:
```python
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__, static_folder='../frontend/build', static_url_path='')

@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')
```

3. Run Flask on port 80 (requires sudo):
```bash
sudo python app.py
```

### Run on Boot (Optional)

Create a systemd service to start the app automatically:

1. Create service file: `/etc/systemd/system/pi-stats.service`
```ini
[Unit]
Description=Pi Stats Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/pi-stats-app/backend
ExecStart=/usr/bin/python3 /home/pi/pi-stats-app/backend/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

2. Enable and start:
```bash
sudo systemctl enable pi-stats
sudo systemctl start pi-stats
```

## API Endpoints

- `GET /api/stats` - Returns all system statistics as JSON
- `GET /api/health` - Health check endpoint

## Notes

- CPU temperature reading works specifically on Raspberry Pi (reads from `/sys/class/thermal/thermal_zone0/temp`)
- The app runs on all network interfaces (`0.0.0.0`), so you can access it from other devices on your network
- Default ports: Backend on 5000, Frontend on 3000

## License

MIT
