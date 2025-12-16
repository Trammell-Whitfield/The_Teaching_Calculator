import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('/api/stats');
        if (!response.ok) {
          throw new Error('Failed to fetch stats');
        }
        const data = await response.json();
        setStats(data);
        setLoading(false);
        setError(null);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    // Fetch immediately
    fetchStats();

    // Then fetch every 2 seconds
    const interval = setInterval(fetchStats, 2000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="App">
        <div className="container">
          <h1>Raspberry Pi 5 Stats</h1>
          <div className="loading">Loading...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="App">
        <div className="container">
          <h1>Raspberry Pi 5 Stats</h1>
          <div className="error">Error: {error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <div className="container">
        <h1>Raspberry Pi 5 Stats</h1>

        <div className="stats-grid">
          {/* System Info */}
          <div className="stat-card">
            <h2>System Info</h2>
            <div className="stat-item">
              <span className="label">Hostname:</span>
              <span className="value">{stats.system.hostname}</span>
            </div>
            <div className="stat-item">
              <span className="label">Platform:</span>
              <span className="value">{stats.system.platform}</span>
            </div>
            <div className="stat-item">
              <span className="label">Architecture:</span>
              <span className="value">{stats.system.architecture}</span>
            </div>
            <div className="stat-item">
              <span className="label">Uptime:</span>
              <span className="value">{stats.system.uptime}</span>
            </div>
          </div>

          {/* CPU */}
          <div className="stat-card">
            <h2>CPU</h2>
            <div className="stat-item">
              <span className="label">Usage:</span>
              <span className="value highlight">{stats.cpu.percent}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${stats.cpu.percent}%` }}></div>
            </div>
            <div className="stat-item">
              <span className="label">Cores:</span>
              <span className="value">{stats.cpu.count}</span>
            </div>
            {stats.cpu.temperature && (
              <div className="stat-item">
                <span className="label">Temperature:</span>
                <span className="value highlight">{stats.cpu.temperature}°C</span>
              </div>
            )}
            {stats.cpu.freq_current && (
              <div className="stat-item">
                <span className="label">Frequency:</span>
                <span className="value">{stats.cpu.freq_current} MHz</span>
              </div>
            )}
          </div>

          {/* Memory */}
          <div className="stat-card">
            <h2>Memory</h2>
            <div className="stat-item">
              <span className="label">Usage:</span>
              <span className="value highlight">{stats.memory.percent}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${stats.memory.percent}%` }}></div>
            </div>
            <div className="stat-item">
              <span className="label">Used:</span>
              <span className="value">{stats.memory.used} GB</span>
            </div>
            <div className="stat-item">
              <span className="label">Total:</span>
              <span className="value">{stats.memory.total} GB</span>
            </div>
            <div className="stat-item">
              <span className="label">Available:</span>
              <span className="value">{stats.memory.available} GB</span>
            </div>
          </div>

          {/* Disk */}
          <div className="stat-card">
            <h2>Disk</h2>
            <div className="stat-item">
              <span className="label">Usage:</span>
              <span className="value highlight">{stats.disk.percent}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${stats.disk.percent}%` }}></div>
            </div>
            <div className="stat-item">
              <span className="label">Used:</span>
              <span className="value">{stats.disk.used} GB</span>
            </div>
            <div className="stat-item">
              <span className="label">Free:</span>
              <span className="value">{stats.disk.free} GB</span>
            </div>
            <div className="stat-item">
              <span className="label">Total:</span>
              <span className="value">{stats.disk.total} GB</span>
            </div>
          </div>

          {/* Network */}
          <div className="stat-card">
            <h2>Network</h2>
            <div className="stat-item">
              <span className="label">Sent:</span>
              <span className="value">{stats.network.bytes_sent} MB</span>
            </div>
            <div className="stat-item">
              <span className="label">Received:</span>
              <span className="value">{stats.network.bytes_recv} MB</span>
            </div>
          </div>
        </div>

        <div className="footer">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}

export default App;
