import React from 'react';

const MetricsPanel = ({ currentMetric, status }) => {
  // Debug: Log what metrics we have
  if (currentMetric) {
    const windowsMetrics = {
      private_bytes_mb: currentMetric.private_bytes_mb,
      shared_memory_mb: currentMetric.shared_memory_mb,
      process_uptime_seconds: currentMetric.process_uptime_seconds,
      cpu_affinity_count: currentMetric.cpu_affinity_count,
      network_connections: currentMetric.network_connections,
      process_priority: currentMetric.process_priority
    };
    console.log('Windows metrics in currentMetric:', windowsMetrics);
  }
  
  // Show "no metrics" only if we truly have no data and aren't profiling
  const hasNoData = !currentMetric && (!status || !status.is_profiling);
  
  if (hasNoData) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
        <h2 className="text-2xl font-semibold mb-4">Current Metrics</h2>
        <div className="text-center text-gray-400 py-8">
          No metrics available. Start profiling to see data.
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
      <h2 className="text-2xl font-semibold mb-4">Current Metrics</h2>
      
      {currentMetric ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            label="CPU Usage"
            value={`${(currentMetric.cpu_percent ?? 0).toFixed(1)}%`}
            color="text-blue-400"
            icon="⚡"
          />
          <MetricCard
            label="Memory"
            value={`${(currentMetric.memory_mb ?? 0).toFixed(1)} MB`}
            color="text-green-400"
            icon="💾"
          />
          <MetricCard
            label="Threads"
            value={currentMetric.threads ?? 0}
            color="text-yellow-400"
            icon="🧵"
          />
          <MetricCard
            label="Context Switches"
            value={(currentMetric.context_switches ?? 0).toLocaleString()}
            color="text-purple-400"
            icon="🔄"
          />
        </div>
      ) : (
        <div className="text-center text-gray-400 py-4">
          Waiting for metrics...
        </div>
      )}

      {currentMetric && (
        <>
          {/* Advanced Metrics Section */}
          <div className="mt-6 pt-6 border-t border-gray-700">
            <h3 className="text-lg font-semibold mb-4 text-cyan-400">Advanced Metrics (Not in Task Manager)</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              <AdvancedMetricCard
                label="Virtual Memory"
                value={`${(currentMetric.virtual_memory_mb ?? 0).toFixed(1)} MB`}
                tooltip="Total virtual memory address space"
                color="text-cyan-300"
              />
              <AdvancedMetricCard
                label="I/O Read"
                value={`${(currentMetric.io_read_mb ?? 0).toFixed(2)} MB`}
                tooltip="Total bytes read from disk/network"
                color="text-orange-300"
              />
              <AdvancedMetricCard
                label="I/O Write"
                value={`${(currentMetric.io_write_mb ?? 0).toFixed(2)} MB`}
                tooltip="Total bytes written to disk/network"
                color="text-pink-300"
              />
              <AdvancedMetricCard
                label="I/O Read Ops"
                value={(currentMetric.io_read_count ?? 0).toLocaleString()}
                tooltip="Number of read operations"
                color="text-orange-400"
              />
              <AdvancedMetricCard
                label="I/O Write Ops"
                value={(currentMetric.io_write_count ?? 0).toLocaleString()}
                tooltip="Number of write operations"
                color="text-pink-400"
              />
              <AdvancedMetricCard
                label="Page Faults"
                value={(currentMetric.page_faults ?? 0).toLocaleString()}
                tooltip="Total page faults (memory access issues)"
                color="text-red-300"
              />
              <AdvancedMetricCard
                label="Major Page Faults"
                value={(currentMetric.major_page_faults ?? 0).toLocaleString()}
                tooltip="Hard faults requiring disk I/O"
                color="text-red-400"
              />
              <AdvancedMetricCard
                label="Minor Page Faults"
                value={(currentMetric.minor_page_faults ?? 0).toLocaleString()}
                tooltip="Soft faults resolved in memory"
                color="text-yellow-300"
              />
              <AdvancedMetricCard
                label="Open Handles"
                value={(currentMetric.open_handles ?? 0).toLocaleString()}
                tooltip="Open file handles/descriptors"
                color="text-indigo-300"
              />
              <AdvancedMetricCard
                label="CPU User Time"
                value={`${(currentMetric.cpu_user_time ?? 0).toFixed(2)}s`}
                tooltip="Total CPU time in user mode"
                color="text-blue-300"
              />
              <AdvancedMetricCard
                label="CPU System Time"
                value={`${(currentMetric.cpu_system_time ?? 0).toFixed(2)}s`}
                tooltip="Total CPU time in kernel mode"
                color="text-purple-300"
              />
              {/* Windows-specific metrics - always show if available */}
              <AdvancedMetricCard
                label="Private Bytes"
                value={currentMetric.private_bytes_mb !== undefined 
                  ? `${(currentMetric.private_bytes_mb ?? 0).toFixed(1)} MB`
                  : 'N/A'}
                tooltip="Memory exclusively used by this process"
                color="text-teal-300"
              />
              <AdvancedMetricCard
                label="Shared Memory"
                value={currentMetric.shared_memory_mb !== undefined
                  ? `${(currentMetric.shared_memory_mb ?? 0).toFixed(1)} MB`
                  : 'N/A'}
                tooltip="Memory shared with other processes"
                color="text-lime-300"
              />
              <AdvancedMetricCard
                label="Process Uptime"
                value={currentMetric.process_uptime_seconds !== undefined
                  ? `${Math.floor((currentMetric.process_uptime_seconds ?? 0) / 60)}m ${Math.floor((currentMetric.process_uptime_seconds ?? 0) % 60)}s`
                  : 'N/A'}
                tooltip="How long the process has been running"
                color="text-emerald-300"
              />
              <AdvancedMetricCard
                label="CPU Affinity"
                value={currentMetric.cpu_affinity_count !== undefined
                  ? `${currentMetric.cpu_affinity_count ?? 0} cores`
                  : 'N/A'}
                tooltip={currentMetric.cpu_affinity_list 
                  ? `Can run on cores: ${currentMetric.cpu_affinity_list.join(', ')}`
                  : 'CPU cores this process can run on'}
                color="text-violet-300"
              />
              <AdvancedMetricCard
                label="Network Connections"
                value={currentMetric.network_connections !== undefined
                  ? (currentMetric.network_connections ?? 0)
                  : 'N/A'}
                tooltip="Active network connections"
                color="text-sky-300"
              />
              {currentMetric.process_priority && (
                <AdvancedMetricCard
                  label="Process Priority"
                  value={currentMetric.process_priority}
                  tooltip="Process priority class"
                  color="text-amber-300"
                />
              )}
            </div>
          </div>

          {/* Basic Info Footer */}
          <div className="mt-4 pt-4 border-t border-gray-700">
            <div className="text-xs text-gray-400 space-y-1">
              <div>System CPU: {(currentMetric.system_cpu_percent ?? 0).toFixed(1)}%</div>
              {currentMetric.pid && <div>PID: {currentMetric.pid}</div>}
              {currentMetric.timestamp && (
                <div>Time: {new Date(currentMetric.timestamp).toLocaleTimeString()}</div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

const MetricCard = ({ label, value, color, icon }) => {
  return (
    <div className="bg-gray-700 rounded p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-400">{label}</span>
        <span className="text-lg">{icon}</span>
      </div>
      <div className={`text-2xl font-bold ${color}`}>
        {value}
      </div>
    </div>
  );
};

const AdvancedMetricCard = ({ label, value, tooltip, color }) => {
  return (
    <div className="bg-gray-700 rounded p-3 hover:bg-gray-650 transition-colors" title={tooltip}>
      <div className="text-xs text-gray-400 mb-1">{label}</div>
      <div className={`text-lg font-semibold ${color}`}>
        {value}
      </div>
    </div>
  );
};

export default MetricsPanel;

