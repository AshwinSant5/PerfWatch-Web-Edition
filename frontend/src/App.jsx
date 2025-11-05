import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import Controls from './components/Controls';
import MetricsPanel from './components/MetricsPanel';
import './App.css';

function App() {
  const [isProfiling, setIsProfiling] = useState(false);
  const [metrics, setMetrics] = useState([]);
  const [currentMetric, setCurrentMetric] = useState(null);
  const [status, setStatus] = useState(null);

  // Fetch status on mount
  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/status');
      const data = await response.json();
      setStatus(data);
      setIsProfiling(data.is_profiling);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  const handleStartProfiling = () => {
    setIsProfiling(true);
    setMetrics([]);
    setCurrentMetric(null);
  };

  const handleStopProfiling = () => {
    setIsProfiling(false);
  };

  const handleMetricsUpdate = (newMetric) => {
    // Check if profiling should be stopped automatically
    if (newMetric._stopProfiling || newMetric.profiling_stopped) {
      console.log('Stopping profiling automatically - program execution completed');
      setIsProfiling(false);
      // Show notification message if available
      if (newMetric.message) {
        console.log('Message:', newMetric.message);
      }
      // Don't update currentMetric or add to metrics array when process ends
      // Keep the last valid metric visible and charts intact
      return;
    }
    
    // Check if this is a "process ended" metric with all zeros
    // Don't add these to metrics array at all - they'll corrupt the charts
    const isZeroMetric = (newMetric.cpu_percent === 0 && 
                          newMetric.memory_mb === 0 && 
                          newMetric.threads === 0 &&
                          (newMetric.note === "Process terminated" || 
                           newMetric.note === "Process not running" ||
                           newMetric.process_ended));
    
    // Skip zero metrics entirely - don't add them to charts or update currentMetric
    if (isZeroMetric) {
      console.log('Skipping zero metric - process has ended');
      return;
    }
    
    // Only update currentMetric if it has valid data
    setCurrentMetric(newMetric);
    
    // Add to metrics array for chart history (only valid metrics get here)
    setMetrics((prev) => {
      const updated = [...prev, newMetric];
      // Keep only last 200 data points for performance
      return updated.slice(-200);
    });
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-center mb-2">
            🌐 PerfWatch Web Edition
          </h1>
          <p className="text-center text-gray-400">
            Real-time Performance Monitoring for Windows
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
          <div className="lg:col-span-1">
            <Controls
              isProfiling={isProfiling}
              onStart={handleStartProfiling}
              onStop={handleStopProfiling}
              status={status}
            />
          </div>
          <div className="lg:col-span-3">
            <MetricsPanel currentMetric={currentMetric} status={status} />
          </div>
        </div>

        <Dashboard
          isProfiling={isProfiling}
          metrics={metrics}
          onMetricsUpdate={handleMetricsUpdate}
        />
      </div>
    </div>
  );
}

export default App;

