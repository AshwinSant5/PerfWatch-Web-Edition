import React, { useEffect, useRef, useState } from 'react';
import Plot from 'react-plotly.js';

const Dashboard = ({ isProfiling, metrics, onMetricsUpdate }) => {
  const [ws, setWs] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const reconnectTimeoutRef = useRef(null);

  // WebSocket connection management
  useEffect(() => {
    if (!isProfiling) {
      // Close WebSocket when not profiling
      if (ws) {
        ws.close();
        setWs(null);
        setWsConnected(false);
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      return;
    }

    // Connect WebSocket when profiling starts
    const connectWebSocket = () => {
      try {
        const websocket = new WebSocket('ws://localhost:8000/ws/metrics');
        
        websocket.onopen = () => {
          console.log('WebSocket connected');
          setWsConnected(true);
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
          }
        };

        websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('Received metrics:', data);
            
            // Check for Windows-specific metrics
            const windowsMetrics = {
              private_bytes_mb: data.private_bytes_mb,
              shared_memory_mb: data.shared_memory_mb,
              process_uptime_seconds: data.process_uptime_seconds,
              cpu_affinity_count: data.cpu_affinity_count,
              network_connections: data.network_connections,
              process_priority: data.process_priority
            };
            const hasWindowsMetrics = Object.values(windowsMetrics).some(v => v !== undefined);
            if (hasWindowsMetrics) {
              console.log('✅ Windows metrics received in WebSocket:', windowsMetrics);
            } else {
              console.log('❌ No Windows metrics in WebSocket data');
            }
            
            // Check if profiling should be stopped automatically
            if (data.profiling_stopped || data.process_ended) {
              console.log('Process ended, stopping profiling automatically');
              // Notify parent component to stop profiling
              if (data.profiling_stopped && onMetricsUpdate) {
                // Pass a special marker to indicate stop
                onMetricsUpdate({ ...data, _stopProfiling: true });
              }
            }
            
            onMetricsUpdate(data);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        websocket.onerror = (error) => {
          console.error('WebSocket error:', error);
          setWsConnected(false);
        };

        websocket.onclose = () => {
          console.log('WebSocket disconnected');
          setWsConnected(false);
          
          // Reconnect if still profiling
          if (isProfiling) {
            reconnectTimeoutRef.current = setTimeout(() => {
              connectWebSocket();
            }, 2000);
          }
        };

        setWs(websocket);
      } catch (error) {
        console.error('Error creating WebSocket:', error);
        setWsConnected(false);
        
        // Retry connection
        if (isProfiling) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, 2000);
        }
      }
    };

    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [isProfiling]);

  // Prepare chart data - metrics array only contains valid metrics now
  // (zero metrics are filtered out in handleMetricsUpdate)
  const timestamps = metrics.map((m, idx) => idx);
  const cpuData = metrics.map(m => m.cpu_percent ?? 0);
  const memoryData = metrics.map(m => m.memory_mb ?? 0);
  const threadsData = metrics.map(m => m.threads ?? 0);
  const ctxSwitchesData = metrics.map(m => m.context_switches ?? 0);
  
  // Advanced metrics data
  const virtualMemoryData = metrics.map(m => m.virtual_memory_mb ?? 0);
  const ioReadData = metrics.map(m => m.io_read_mb ?? 0);
  const ioWriteData = metrics.map(m => m.io_write_mb ?? 0);
  const pageFaultsData = metrics.map(m => m.page_faults ?? 0);
  const majorPageFaultsData = metrics.map(m => m.major_page_faults ?? 0);
  const openHandlesData = metrics.map(m => m.open_handles ?? 0);

  const chartLayout = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#e0e0e0' },
    xaxis: {
      gridcolor: '#333',
      showgrid: true,
    },
    yaxis: {
      gridcolor: '#333',
      showgrid: true,
    },
    margin: { l: 50, r: 20, t: 20, b: 40 },
    height: 300,
  };

  const chartConfig = {
    displayModeBar: false,
    responsive: true,
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold">Real-time Metrics</h2>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-400">
            {wsConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {metrics.length === 0 ? (
        <div className="text-center text-gray-400 py-12">
          {isProfiling 
            ? 'Waiting for metrics data...' 
            : 'Start profiling to see real-time charts'}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* CPU Usage Chart */}
          <div className="bg-gray-900 rounded p-4">
            <h3 className="text-lg font-medium mb-2 text-blue-400">CPU Usage (%)</h3>
            <Plot
              data={[
                {
                  x: timestamps,
                  y: cpuData,
                  type: 'scatter',
                  mode: 'lines',
                  name: 'CPU %',
                  line: { color: '#60a5fa', width: 2 },
                  fill: 'tozeroy',
                  fillcolor: 'rgba(96, 165, 250, 0.2)',
                },
              ]}
              layout={{
                ...chartLayout,
                title: '',
                yaxis: { ...chartLayout.yaxis, title: 'CPU %' },
              }}
              config={chartConfig}
              style={{ width: '100%', height: '100%' }}
            />
          </div>

          {/* Memory Usage Chart */}
          <div className="bg-gray-900 rounded p-4">
            <h3 className="text-lg font-medium mb-2 text-green-400">Memory Usage (MB)</h3>
            <Plot
              data={[
                {
                  x: timestamps,
                  y: memoryData,
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Memory MB',
                  line: { color: '#34d399', width: 2 },
                  fill: 'tozeroy',
                  fillcolor: 'rgba(52, 211, 153, 0.2)',
                },
              ]}
              layout={{
                ...chartLayout,
                title: '',
                yaxis: { ...chartLayout.yaxis, title: 'Memory (MB)' },
              }}
              config={chartConfig}
              style={{ width: '100%', height: '100%' }}
            />
          </div>

          {/* Thread Count Chart */}
          <div className="bg-gray-900 rounded p-4">
            <h3 className="text-lg font-medium mb-2 text-yellow-400">Thread Count</h3>
            <Plot
              data={[
                {
                  x: timestamps,
                  y: threadsData,
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Threads',
                  line: { color: '#fbbf24', width: 2 },
                  fill: 'tozeroy',
                  fillcolor: 'rgba(251, 191, 36, 0.2)',
                },
              ]}
              layout={{
                ...chartLayout,
                title: '',
                yaxis: { ...chartLayout.yaxis, title: 'Threads' },
              }}
              config={chartConfig}
              style={{ width: '100%', height: '100%' }}
            />
          </div>

          {/* Context Switches Chart */}
          <div className="bg-gray-900 rounded p-4">
            <h3 className="text-lg font-medium mb-2 text-purple-400">Context Switches</h3>
            <Plot
              data={[
                {
                  x: timestamps,
                  y: ctxSwitchesData,
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Context Switches',
                  line: { color: '#a78bfa', width: 2 },
                  fill: 'tozeroy',
                  fillcolor: 'rgba(167, 139, 250, 0.2)',
                },
              ]}
              layout={{
                ...chartLayout,
                title: '',
                yaxis: { ...chartLayout.yaxis, title: 'Context Switches' },
              }}
              config={chartConfig}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        </div>
      )}

      {/* Advanced Metrics Charts */}
      {metrics.length > 0 && (
        <div className="mt-6">
          <h3 className="text-xl font-semibold mb-4 text-cyan-400">Advanced Metrics Charts</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Virtual Memory vs Working Set */}
            <div className="bg-gray-900 rounded p-4">
              <h3 className="text-lg font-medium mb-2 text-cyan-400">Memory: Virtual vs Working Set (MB)</h3>
              <Plot
                data={[
                  {
                    x: timestamps,
                    y: virtualMemoryData,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Virtual Memory',
                    line: { color: '#67e8f9', width: 2 },
                  },
                  {
                    x: timestamps,
                    y: memoryData,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Working Set (RSS)',
                    line: { color: '#34d399', width: 2 },
                  },
                ]}
                layout={{
                  ...chartLayout,
                  title: '',
                  yaxis: { ...chartLayout.yaxis, title: 'Memory (MB)' },
                  legend: { x: 0, y: 1 },
                }}
                config={chartConfig}
                style={{ width: '100%', height: '100%' }}
              />
            </div>

            {/* I/O Statistics */}
            <div className="bg-gray-900 rounded p-4">
              <h3 className="text-lg font-medium mb-2 text-orange-400">I/O Statistics (MB)</h3>
              <Plot
                data={[
                  {
                    x: timestamps,
                    y: ioReadData,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Read',
                    line: { color: '#fb923c', width: 2 },
                    fill: 'tozeroy',
                    fillcolor: 'rgba(251, 146, 60, 0.2)',
                  },
                  {
                    x: timestamps,
                    y: ioWriteData,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Write',
                    line: { color: '#f472b6', width: 2 },
                    fill: 'tozeroy',
                    fillcolor: 'rgba(244, 114, 182, 0.2)',
                  },
                ]}
                layout={{
                  ...chartLayout,
                  title: '',
                  yaxis: { ...chartLayout.yaxis, title: 'I/O (MB)' },
                  legend: { x: 0, y: 1 },
                }}
                config={chartConfig}
                style={{ width: '100%', height: '100%' }}
              />
            </div>

            {/* Page Faults */}
            <div className="bg-gray-900 rounded p-4">
              <h3 className="text-lg font-medium mb-2 text-red-400">Page Faults</h3>
              <Plot
                data={[
                  {
                    x: timestamps,
                    y: pageFaultsData,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Total',
                    line: { color: '#f87171', width: 2 },
                  },
                  {
                    x: timestamps,
                    y: majorPageFaultsData,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Major (Hard)',
                    line: { color: '#dc2626', width: 2 },
                  },
                ]}
                layout={{
                  ...chartLayout,
                  title: '',
                  yaxis: { ...chartLayout.yaxis, title: 'Page Faults' },
                  legend: { x: 0, y: 1 },
                }}
                config={chartConfig}
                style={{ width: '100%', height: '100%' }}
              />
            </div>

            {/* Open Handles */}
            <div className="bg-gray-900 rounded p-4">
              <h3 className="text-lg font-medium mb-2 text-indigo-400">Open File Handles</h3>
              <Plot
                data={[
                  {
                    x: timestamps,
                    y: openHandlesData,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Open Handles',
                    line: { color: '#818cf8', width: 2 },
                    fill: 'tozeroy',
                    fillcolor: 'rgba(129, 140, 248, 0.2)',
                  },
                ]}
                layout={{
                  ...chartLayout,
                  title: '',
                  yaxis: { ...chartLayout.yaxis, title: 'Handles' },
                }}
                config={chartConfig}
                style={{ width: '100%', height: '100%' }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;

