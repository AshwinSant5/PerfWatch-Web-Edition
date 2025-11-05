"""
Windows-specific metrics using pywin32 and Windows Performance Counters
"""
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# We only use psutil for Windows metrics, which is already required
# win32pdh is not needed for the metrics we're collecting
WINDOWS_METRICS_AVAILABLE = True


def get_windows_process_metrics(pid: int) -> Dict[str, Any]:
    """
    Get additional Windows-specific process metrics using Performance Counters
    
    Returns:
        Dictionary with Windows-specific metrics
    """
    metrics = {}
    
    if not WINDOWS_METRICS_AVAILABLE or os.name != 'nt':
        logger.debug(f"Windows metrics not available: WINDOWS_METRICS_AVAILABLE={WINDOWS_METRICS_AVAILABLE}, os.name={os.name}")
        return metrics
    
    try:
        # Get process handle for additional metrics
        import psutil
        process = psutil.Process(pid)
        
        # Get memory info with more details
        try:
            memory_info = process.memory_info()
            logger.debug(f"Memory info attributes: {[attr for attr in dir(memory_info) if not attr.startswith('_')]}")
            
            # On Windows, memory_info() has 'private' attribute for private bytes
            # Private bytes (committed memory exclusive to this process)
            if hasattr(memory_info, 'private'):
                private_bytes_mb = memory_info.private / (1024 * 1024)
                metrics['private_bytes_mb'] = round(private_bytes_mb, 2)
                logger.debug(f"Private bytes: {metrics['private_bytes_mb']} MB")
            else:
                # Fallback: approximate from working set
                working_set_mb = memory_info.rss / (1024 * 1024)
                metrics['private_bytes_mb'] = round(working_set_mb * 0.95, 2)
                logger.debug(f"Private bytes (approximated): {metrics['private_bytes_mb']} MB")
            
            # Shared memory (memory shared with other processes)
            # Working set - private bytes = shared (approximate)
            working_set_mb = memory_info.rss / (1024 * 1024)
            private_mb = metrics.get('private_bytes_mb', working_set_mb)
            shared_memory_mb = max(0, working_set_mb - private_mb)
            metrics['shared_memory_mb'] = round(shared_memory_mb, 2)
            logger.debug(f"Shared memory: {metrics['shared_memory_mb']} MB")
            
            # Peak working set size (maximum working set during process lifetime)
            if hasattr(memory_info, 'peak_wset'):
                metrics['peak_working_set_mb'] = round(memory_info.peak_wset / (1024 * 1024), 2)
            
        except Exception as e:
            logger.warning(f"Could not get detailed memory info: {e}", exc_info=True)
        
        # Get network I/O if available
        try:
            connections = process.connections()
            if connections:
                # Count active connections
                metrics['network_connections'] = len(connections)
                
                # Try to get network I/O stats (if psutil supports it)
                # Note: Per-process network I/O is not directly available in psutil
                # This would require ETW or other advanced methods
        except (psutil.AccessDenied, AttributeError):
            pass
        
        # Get process priority
        try:
            # On Windows, use nice() which returns priority class value
            # Use psutil constants for mapping
            try:
                priority_class = process.nice()
                # Map Windows priority class values to human-readable names
                priority_map = {
                    psutil.IDLE_PRIORITY_CLASS: "Idle",
                    psutil.BELOW_NORMAL_PRIORITY_CLASS: "Below Normal",
                    psutil.NORMAL_PRIORITY_CLASS: "Normal",
                    psutil.ABOVE_NORMAL_PRIORITY_CLASS: "Above Normal",
                    psutil.HIGH_PRIORITY_CLASS: "High",
                    psutil.REALTIME_PRIORITY_CLASS: "Realtime"
                }
                # nice() on Windows returns the priority class constant value
                metrics['process_priority'] = priority_map.get(priority_class, f"Class {priority_class}")
            except AttributeError:
                # Fallback: try to get priority directly
                if hasattr(process, 'nice'):
                    metrics['process_priority_raw'] = process.nice()
        except (psutil.AccessDenied, Exception) as e:
            logger.debug(f"Could not get process priority: {e}")
        
        # Get process creation time and uptime
        try:
            create_time = process.create_time()
            import time
            uptime_seconds = time.time() - create_time
            metrics['process_uptime_seconds'] = round(uptime_seconds, 2)
            logger.debug(f"Process uptime: {metrics['process_uptime_seconds']} seconds")
        except (psutil.AccessDenied, AttributeError) as e:
            logger.debug(f"Could not get process uptime: {e}")
        
        # Get CPU affinity (which cores process can run on)
        try:
            cpu_affinity = process.cpu_affinity()
            metrics['cpu_affinity_count'] = len(cpu_affinity)
            metrics['cpu_affinity_list'] = list(cpu_affinity)
            logger.debug(f"CPU affinity: {metrics['cpu_affinity_count']} cores, {metrics['cpu_affinity_list']}")
        except (psutil.AccessDenied, AttributeError) as e:
            logger.debug(f"Could not get CPU affinity: {e}")
        
        logger.info(f"Windows metrics collected successfully: {list(metrics.keys())}")
        
    except Exception as e:
        logger.error(f"Error getting Windows-specific metrics: {e}", exc_info=True)
    
    return metrics


def get_windows_system_metrics() -> Dict[str, Any]:
    """
    Get Windows system-wide metrics
    
    Returns:
        Dictionary with system-wide metrics
    """
    metrics = {}
    
    if not WINDOWS_METRICS_AVAILABLE or os.name != 'nt':
        return metrics
    
    try:
        import psutil
        
        # Get system memory details
        memory = psutil.virtual_memory()
        metrics['system_memory_total_gb'] = round(memory.total / (1024 ** 3), 2)
        metrics['system_memory_available_gb'] = round(memory.available / (1024 ** 3), 2)
        metrics['system_memory_used_percent'] = round(memory.percent, 2)
        
        # Get disk I/O for system
        disk_io = psutil.disk_io_counters()
        if disk_io:
            metrics['system_disk_read_mb'] = round(disk_io.read_bytes / (1024 ** 2), 2)
            metrics['system_disk_write_mb'] = round(disk_io.write_bytes / (1024 ** 2), 2)
            metrics['system_disk_read_count'] = disk_io.read_count
            metrics['system_disk_write_count'] = disk_io.write_count
        
        # Get network I/O for system
        net_io = psutil.net_io_counters()
        if net_io:
            metrics['system_network_sent_mb'] = round(net_io.bytes_sent / (1024 ** 2), 2)
            metrics['system_network_recv_mb'] = round(net_io.bytes_recv / (1024 ** 2), 2)
        
    except Exception as e:
        logger.debug(f"Error getting Windows system metrics: {e}")
    
    return metrics

