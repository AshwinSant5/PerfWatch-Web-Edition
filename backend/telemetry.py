"""
Telemetry Collector - Collects performance metrics using psutil
"""
import psutil
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Windows-specific metrics
try:
    # Try relative import first (when used as a package)
    try:
        from .windows_metrics import get_windows_process_metrics, get_windows_system_metrics
    except ImportError:
        # Fall back to absolute import (when running as script)
        from windows_metrics import get_windows_process_metrics, get_windows_system_metrics
    
    WINDOWS_METRICS_ENABLED = True
    logger.info("Windows-specific metrics enabled")
except ImportError as e:
    WINDOWS_METRICS_ENABLED = False
    logger.warning(f"Windows-specific metrics disabled: {e}")


class TelemetryCollector:
    """Collects performance metrics from a target process"""
    
    def __init__(self, pid: Optional[int] = None):
        self.pid = pid
        self.process: Optional[psutil.Process] = None
        self.last_cpu_times = None
        self._initialize_process()
    
    def _initialize_process(self):
        """Initialize psutil Process object"""
        if self.pid is not None:
            try:
                self.process = psutil.Process(self.pid)
                # Get initial CPU times for percentage calculation
                self.last_cpu_times = self.process.cpu_times()
            except psutil.NoSuchProcess:
                logger.warning(f"Process {self.pid} not found")
                self.process = None
            except Exception as e:
                logger.error(f"Error initializing process: {e}")
                self.process = None
    
    def update_pid(self, pid: Optional[int]):
        """Update the target process PID"""
        self.pid = pid
        self._initialize_process()
    
    def collect_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Collect current metrics from the target process
        
        Returns:
            Dictionary with metrics or None if process not available
        """
        if self.process is None or self.pid is None:
            logger.debug("No process or PID available for metrics collection")
            return None
        
        try:
            # Re-initialize process if needed (it might have been recreated)
            if self.process is None:
                try:
                    self.process = psutil.Process(self.pid)
                except psutil.NoSuchProcess:
                    logger.warning(f"Process {self.pid} no longer exists")
                    return None
            
            # Check if process is still alive
            if not self.process.is_running():
                logger.debug(f"Process {self.pid} is no longer running")
                return None
            
            # Get CPU percentage (non-blocking, but first call needs interval)
            # First call initializes the counter, second call gives actual percentage
            try:
                # First call to initialize (returns 0.0)
                _ = self.process.cpu_percent(interval=None)
                # Small delay then get actual percentage
                import time
                time.sleep(0.1)
                cpu_percent = self.process.cpu_percent(interval=None)
            except Exception:
                # Fallback method
                cpu_percent = self.process.cpu_percent(interval=0.1)
            
            # Get memory information
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # Resident Set Size (working set) in MB
            virtual_memory_mb = memory_info.vms / (1024 * 1024)  # Virtual memory size in MB
            
            # Ensure virtual memory >= working set (should always be true, but handle edge cases)
            # On Windows, VMS might sometimes be slightly less due to how psutil reports it
            # In reality, VMS should always be >= RSS, so we ensure this for display consistency
            if virtual_memory_mb < memory_mb:
                # If VMS < RSS, use RSS as the minimum (VMS should be at least as large as RSS)
                virtual_memory_mb = memory_mb
                logger.debug(f"Adjusted VMS ({virtual_memory_mb} MB) to be >= RSS ({memory_mb} MB)")
            
            # Get thread count
            num_threads = self.process.num_threads()
            
            # Get context switches
            try:
                ctx_switches = self.process.num_ctx_switches()
                ctx_switches_total = ctx_switches.voluntary + ctx_switches.involuntary
            except (AttributeError, psutil.AccessDenied):
                # Some systems may not support this
                ctx_switches_total = 0
            
            # Get I/O statistics (read/write bytes and operations)
            try:
                io_counters = self.process.io_counters()
                io_read_bytes = io_counters.read_bytes / (1024 * 1024)  # MB
                io_write_bytes = io_counters.write_bytes / (1024 * 1024)  # MB
                io_read_count = io_counters.read_count
                io_write_count = io_counters.write_count
            except (AttributeError, psutil.AccessDenied):
                io_read_bytes = 0
                io_write_bytes = 0
                io_read_count = 0
                io_write_count = 0
            
            # Get page faults (major and minor)
            # Note: Page fault information varies by platform
            page_faults_count = 0
            major_page_faults = 0
            minor_page_faults = 0
            try:
                # Try Windows-specific memory info
                if hasattr(self.process, 'memory_info_ex'):
                    memory_info_ex = self.process.memory_info_ex()
                    # Windows may have different attributes
                    if hasattr(memory_info_ex, 'pagefaults'):
                        page_faults_count = memory_info_ex.pagefaults
                    elif hasattr(memory_info_ex, 'pfaults'):
                        page_faults_count = memory_info_ex.pfaults
                        major_page_faults = page_faults_count  # On Windows, pfaults is often major faults
                # Try to get from memory_info (some platforms)
                elif hasattr(memory_info, 'pagefaults'):
                    page_faults_count = memory_info.pagefaults
            except (AttributeError, psutil.AccessDenied, Exception) as e:
                logger.debug(f"Could not get page faults: {e}")
                page_faults_count = 0
                major_page_faults = 0
                minor_page_faults = 0
            
            # Minor page faults are total - major (if we can't get them separately)
            if page_faults_count > 0 and minor_page_faults == 0:
                minor_page_faults = max(0, page_faults_count - major_page_faults)
            
            # Get open file handles/descriptors
            num_handles = 0
            try:
                # On Windows, use num_handles()
                if hasattr(self.process, 'num_handles'):
                    num_handles = self.process.num_handles()
                # On Unix, use num_fds()
                elif hasattr(self.process, 'num_fds'):
                    num_handles = self.process.num_fds()
                # Fallback: count open files (may not be accurate for all handles)
                else:
                    try:
                        num_handles = len(self.process.open_files())
                    except:
                        num_handles = 0
            except (AttributeError, psutil.AccessDenied, Exception) as e:
                logger.debug(f"Could not get handle count: {e}")
                num_handles = 0
            
            # Get CPU time breakdown (user vs system)
            try:
                cpu_times = self.process.cpu_times()
                cpu_user_time = cpu_times.user
                cpu_system_time = cpu_times.system
            except (AttributeError, psutil.AccessDenied):
                cpu_user_time = 0
                cpu_system_time = 0
            
            # Get system-wide CPU percentage for reference
            system_cpu = psutil.cpu_percent(interval=0.1)
            
            # Get Windows-specific metrics if available
            windows_metrics = {}
            if WINDOWS_METRICS_ENABLED:
                try:
                    windows_metrics = get_windows_process_metrics(self.pid)
                    if windows_metrics:
                        logger.debug(f"Collected Windows-specific metrics: {list(windows_metrics.keys())}")
                except Exception as e:
                    logger.warning(f"Could not get Windows-specific metrics: {e}", exc_info=True)
            
            metrics = {
                # Basic metrics (shown in Task Manager)
                "cpu_percent": round(cpu_percent, 2),
                "system_cpu_percent": round(system_cpu, 2),
                "memory_mb": round(memory_mb, 2),
                "threads": num_threads,
                "context_switches": ctx_switches_total,
                
                # Advanced metrics (NOT in Task Manager)
                "virtual_memory_mb": round(virtual_memory_mb, 2),
                "io_read_mb": round(io_read_bytes, 2),
                "io_write_mb": round(io_write_bytes, 2),
                "io_read_count": io_read_count,
                "io_write_count": io_write_count,
                "page_faults": page_faults_count,
                "major_page_faults": major_page_faults,
                "minor_page_faults": minor_page_faults,
                "open_handles": num_handles,
                "cpu_user_time": round(cpu_user_time, 2),
                "cpu_system_time": round(cpu_system_time, 2),
                
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "pid": self.pid
            }
            
            # Add Windows-specific metrics
            metrics.update(windows_metrics)
            
            # Log if Windows metrics were added
            if windows_metrics:
                logger.info(f"Added Windows metrics: {list(windows_metrics.keys())}")
            
            logger.debug(f"Collected metrics for PID {self.pid}: CPU={cpu_percent}%, Memory={memory_mb}MB, Threads={num_threads}")
            return metrics
            
        except psutil.NoSuchProcess:
            logger.warning(f"Process {self.pid} no longer exists")
            self.process = None
            return None
        except psutil.AccessDenied:
            logger.error(f"Access denied reading process {self.pid}")
            return None
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}", exc_info=True)
            return None
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """
        Collect system-wide metrics (fallback when process not available)
        
        Returns:
            Dictionary with system metrics
        """
        try:
            system_cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            return {
                "cpu_percent": 0.0,
                "system_cpu_percent": round(system_cpu, 2),
                "memory_mb": 0.0,
                "threads": 0,
                "context_switches": 0,
                "virtual_memory_mb": 0.0,
                "io_read_mb": 0.0,
                "io_write_mb": 0.0,
                "io_read_count": 0,
                "io_write_count": 0,
                "page_faults": 0,
                "major_page_faults": 0,
                "minor_page_faults": 0,
                "open_handles": 0,
                "cpu_user_time": 0.0,
                "cpu_system_time": 0.0,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "pid": None
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {
                "cpu_percent": 0.0,
                "system_cpu_percent": 0.0,
                "memory_mb": 0.0,
                "threads": 0,
                "context_switches": 0,
                "virtual_memory_mb": 0.0,
                "io_read_mb": 0.0,
                "io_write_mb": 0.0,
                "io_read_count": 0,
                "io_write_count": 0,
                "page_faults": 0,
                "major_page_faults": 0,
                "minor_page_faults": 0,
                "open_handles": 0,
                "cpu_user_time": 0.0,
                "cpu_system_time": 0.0,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "pid": None
            }

