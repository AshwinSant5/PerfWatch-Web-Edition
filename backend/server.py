"""
FastAPI Server - Main backend API for PerfWatch
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import asyncio
import logging
import os
from datetime import datetime

from process_manager import ProcessManager
from telemetry import TelemetryCollector
from logger import MetricsLogger
from compiler import CppCompiler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="PerfWatch API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
process_manager = ProcessManager()
telemetry_collector = TelemetryCollector()
metrics_logger = MetricsLogger()
cpp_compiler = CppCompiler()
is_profiling = False
telemetry_task: Optional[asyncio.Task] = None


class RunRequest(BaseModel):
    program: str


class CompileAndRunRequest(BaseModel):
    source_code: str
    compiler_flags: Optional[list] = None


class StopRequest(BaseModel):
    kill_process: bool = True


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "PerfWatch API", "status": "running"}


@app.get("/status")
async def get_status():
    """Get current profiling status"""
    return {
        "is_profiling": is_profiling,
        "process_running": process_manager.is_running(),
        "pid": process_manager.get_pid(),
        "metrics_count": metrics_logger.get_history_count()
    }


@app.get("/compiler-status")
async def compiler_status():
    """Check if C++ compiler is available and test it"""
    compiler = cpp_compiler._find_compiler()
    if compiler:
        # Test the compiler with version check
        import subprocess
        import tempfile
        import os
        
        test_results = {}
        
        # Test 1: Version check
        try:
            result = subprocess.run(
                [compiler, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=5
            )
            test_results["version_check"] = {
                "success": result.returncode == 0,
                "output": result.stdout.strip()[:300] if result.stdout else "No output",
                "return_code": result.returncode
            }
        except Exception as e:
            test_results["version_check"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test 2: Simple compilation test
        try:
            test_code = "int main() { return 0; }"
            test_dir = tempfile.mkdtemp(prefix="perfwatch_test_")
            test_file = os.path.join(test_dir, "test.cpp")
            test_exe = os.path.join(test_dir, "test.exe")
            
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_code)
            
            compile_result = subprocess.run(
                [compiler, "-std=c++17", test_file, "-o", test_exe],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10
            )
            
            test_results["compile_test"] = {
                "success": compile_result.returncode == 0 and os.path.exists(test_exe),
                "output": compile_result.stdout.strip()[:500] if compile_result.stdout else "No output",
                "return_code": compile_result.returncode,
                "exe_exists": os.path.exists(test_exe) if compile_result.returncode == 0 else False
            }
            
            # Cleanup
            try:
                import shutil
                shutil.rmtree(test_dir)
            except:
                pass
                
        except Exception as e:
            test_results["compile_test"] = {
                "success": False,
                "error": str(e)
            }
        
        return {
            "available": True,
            "compiler_path": compiler,
            "tests": test_results
        }
    else:
        return {
            "available": False,
            "compiler_path": None,
            "version": None,
            "message": "No C++ compiler found. See INSTALL_COMPILER.md for installation instructions."
        }


@app.post("/run")
async def run_program(request: RunRequest):
    """Start profiling a program"""
    global is_profiling, telemetry_task
    
    if is_profiling:
        raise HTTPException(status_code=400, detail="Already profiling a process")
    
    program_path = request.program.strip()
    
    # Validate path
    if not program_path:
        raise HTTPException(status_code=400, detail="Program path is required")
    
    # Start the process
    success, message = process_manager.start_process(program_path)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    pid = process_manager.get_pid()
    
    # Initialize telemetry collector
    telemetry_collector.update_pid(pid)
    
    # Start logging session
    metrics_logger.start_session()
    
    # Start profiling
    is_profiling = True
    
    logger.info(f"Started profiling process {pid}: {program_path}")
    
    return {
        "success": True,
        "message": message,
        "pid": pid,
        "program": program_path
    }


@app.post("/compile-and-run")
async def compile_and_run(request: CompileAndRunRequest):
    """Compile C++ source code and start profiling the executable"""
    global is_profiling, telemetry_task
    
    if is_profiling:
        raise HTTPException(status_code=400, detail="Already profiling a process")
    
    source_code = request.source_code.strip()
    
    # Validate source code
    if not source_code:
        raise HTTPException(status_code=400, detail="Source code is required")
    
    # Clean up any previous compilation
    cpp_compiler.cleanup()
    
    # Compile the code
    success, message, exe_path = cpp_compiler.compile(
        source_code,
        request.compiler_flags
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    if exe_path is None:
        raise HTTPException(status_code=500, detail="Compilation succeeded but no executable path returned")
    
    # Start the process
    success, process_message = process_manager.start_process(exe_path)
    
    if not success:
        raise HTTPException(status_code=400, detail=f"Compilation succeeded but failed to start: {process_message}")
    
    pid = process_manager.get_pid()
    
    # Initialize telemetry collector
    telemetry_collector.update_pid(pid)
    
    # Start logging session
    metrics_logger.start_session()
    
    # Start profiling
    is_profiling = True
    
    logger.info(f"Compiled and started profiling process {pid}: {exe_path}")
    
    return {
        "success": True,
        "message": f"{message}. {process_message}",
        "pid": pid,
        "program": exe_path,
        "compiled": True
    }


@app.post("/stop")
async def stop_profiling(request: Optional[StopRequest] = None):
    """Stop profiling and optionally kill the process"""
    global is_profiling, telemetry_task
    
    if not is_profiling:
        return {"success": False, "message": "No active profiling session"}
    
    # Stop profiling flag
    is_profiling = False
    
    # Stop telemetry task if running
    if telemetry_task and not telemetry_task.done():
        telemetry_task.cancel()
        try:
            await telemetry_task
        except asyncio.CancelledError:
            pass
    
    # Stop process if requested
    process_message = ""
    if request and request.kill_process:
        success, process_message = process_manager.stop_process()
    else:
        process_message = "Process left running"
    
    # Clean up compiled executable if it was a compiled C++ program
    compiled_exe = cpp_compiler.get_compiled_exe()
    if compiled_exe:
        try:
            # Wait a bit for process to fully terminate
            await asyncio.sleep(0.5)
            # Cleanup will remove temp files
            cpp_compiler.cleanup()
        except Exception as e:
            logger.warning(f"Failed to cleanup compiled executable: {e}")
    
    # Export CSV
    try:
        csv_path = metrics_logger.export_csv()
        export_message = f"Metrics exported to {csv_path}"
    except Exception as e:
        export_message = f"Export failed: {str(e)}"
    
    logger.info("Stopped profiling")
    
    return {
        "success": True,
        "message": "Profiling stopped",
        "process_message": process_message,
        "export_message": export_message
    }


@app.get("/export")
async def export_metrics(format: str = "csv"):
    """Export metrics data"""
    if metrics_logger.get_history_count() == 0:
        raise HTTPException(status_code=404, detail="No metrics to export")
    
    try:
        if format.lower() == "json":
            filepath = metrics_logger.export_json()
            media_type = "application/json"
        else:
            filepath = metrics_logger.export_csv()
            media_type = "text/csv"
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Export file not found")
        
        return FileResponse(
            filepath,
            media_type=media_type,
            filename=os.path.basename(filepath)
        )
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket endpoint for streaming metrics"""
    global is_profiling, telemetry_task
    
    await websocket.accept()
    logger.info(f"WebSocket client connected. is_profiling={is_profiling}, pid={process_manager.get_pid()}")
    
    # If not profiling yet, wait a bit for it to start
    if not is_profiling:
        logger.info("Waiting for profiling to start...")
        for _ in range(20):  # Wait up to 5 seconds
            await asyncio.sleep(0.25)
            if is_profiling:
                logger.info("Profiling started, beginning metrics collection")
                break
        if not is_profiling:
            logger.warning("WebSocket connected but profiling never started")
            await websocket.send_json({
                "error": "Profiling not active",
                "message": "Please start profiling first"
            })
            return
    
    async def send_metrics():
        """Continuously send metrics while profiling"""
        global is_profiling  # Access global profiling flag
        logger.info("Starting metrics collection loop")
        iteration = 0
        process_ended_count = 0  # Track how many iterations the process has been ended
        process_ended_threshold = 2  # Stop profiling after 2 iterations (0.5 seconds) of process being ended
        
        while is_profiling:
            try:
                iteration += 1
                process_running = process_manager.is_running()
                pid = process_manager.get_pid()
                
                logger.debug(f"Metrics iteration {iteration}: process_running={process_running}, pid={pid}, is_profiling={is_profiling}")
                
                # Collect metrics
                if process_running:
                    process_ended_count = 0  # Reset counter if process is running
                    metrics = telemetry_collector.collect_metrics()
                    if metrics is None:
                        logger.warning(f"Failed to collect metrics for PID {pid} - process may have terminated")
                        # Don't send zero metrics - process ended, just mark it
                        process_ended_count += 1
                        # Skip sending this metric - we'll handle it in the else branch
                        continue
                else:
                    # Process has terminated
                    process_ended_count += 1
                    logger.info(f"Process is no longer running (ended for {process_ended_count} iterations)")
                    
                    # If process has been ended for enough iterations, automatically stop profiling
                    if process_ended_count >= process_ended_threshold:
                        logger.info("Process ended, automatically stopping profiling")
                        is_profiling = False
                        # Send final notification without zero metrics - just a stop signal
                        metrics = {
                            "profiling_stopped": True,
                            "message": "Profiling stopped automatically - program execution completed",
                            "process_ended": True,
                            "pid": pid if pid else None,
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                    else:
                        # Still counting down - don't send any metrics, just wait
                        # This prevents zero metrics from corrupting the charts
                        await asyncio.sleep(0.25)
                        continue
                
                # If metrics is None, skip sending (don't send zero metrics)
                if metrics is None:
                    logger.warning("Metrics collection returned None, skipping this metric")
                    # Wait before next collection
                    await asyncio.sleep(0.25)
                    continue
                
                # Log metric
                metrics_logger.add_metric(metrics)
                
                # Send via WebSocket
                try:
                    # Log Windows-specific metrics if present
                    windows_keys = ['private_bytes_mb', 'shared_memory_mb', 'process_uptime_seconds', 
                                   'cpu_affinity_count', 'network_connections', 'process_priority']
                    present_windows_metrics = {k: metrics.get(k) for k in windows_keys if k in metrics}
                    if present_windows_metrics:
                        logger.info(f"Sending Windows metrics via WebSocket: {present_windows_metrics}")
                    
                    await websocket.send_json(metrics)
                    logger.debug(f"Sent metrics: PID={metrics.get('pid')}, CPU={metrics.get('cpu_percent')}%, Memory={metrics.get('memory_mb')}MB")
                except Exception as ws_error:
                    logger.error(f"Failed to send metrics via WebSocket: {ws_error}")
                    break
                
                # If profiling was stopped due to process ending, break the loop
                if not is_profiling:
                    logger.info("Profiling stopped, exiting metrics loop")
                    break
                
                # Wait before next collection
                await asyncio.sleep(0.25)  # 250ms interval
                
            except asyncio.CancelledError:
                logger.info("Metrics collection cancelled")
                break
            except Exception as e:
                logger.error(f"Error in metrics loop: {e}", exc_info=True)
                # Send error metric
                try:
                    error_metric = {
                        "cpu_percent": 0.0,
                        "system_cpu_percent": 0.0,
                        "memory_mb": 0.0,
                        "threads": 0,
                        "context_switches": 0,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "pid": process_manager.get_pid(),
                        "error": str(e)
                    }
                    await websocket.send_json(error_metric)
                except:
                    pass
                break
    
    # Start telemetry task
    telemetry_task = asyncio.create_task(send_metrics())
    
    try:
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages (or timeout)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                # Handle any incoming messages if needed
                logger.debug(f"Received WebSocket message: {data}")
            except asyncio.TimeoutError:
                # Continue loop if no message
                if not is_profiling:
                    break
                continue
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cancel telemetry task
        if telemetry_task and not telemetry_task.done():
            telemetry_task.cancel()
            try:
                await telemetry_task
            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

