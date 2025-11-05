"""
Process Manager - Handles launching and stopping target executables
"""
import subprocess
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ProcessManager:
    """Manages the lifecycle of the target process being profiled"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.pid: Optional[int] = None
        
    def start_process(self, program_path: str) -> tuple[bool, str]:
        """
        Start the target executable
        
        Args:
            program_path: Path to the executable file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if self.process is not None:
            return False, "Process is already running"
        
        if not os.path.exists(program_path):
            return False, f"Executable not found: {program_path}"
        
        try:
            # Launch the process
            # For console apps, we want to see output but also prevent blocking
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
            if os.name == 'nt':  # Windows
                # Set up environment to include MinGW DLL paths if needed
                env = os.environ.copy()
                
                # If program is in a temp directory and might need MinGW DLLs, add them to PATH
                program_dir = os.path.dirname(program_path)
                # Check if we need to add MinGW bin to PATH
                # Look for common MinGW locations
                mingw_paths = [
                    r"C:\msys64\mingw64\bin",
                    r"C:\mingw64\bin",
                    r"C:\mingw\bin",
                ]
                
                current_path = env.get("PATH", "")
                for mingw_path in mingw_paths:
                    if os.path.exists(mingw_path) and mingw_path not in current_path:
                        env["PATH"] = f"{mingw_path};{env.get('PATH', '')}"
                        logger.info(f"Added MinGW bin to PATH: {mingw_path}")
                
                # Launch process with proper environment
                self.process = subprocess.Popen(
                    [program_path],
                    stdout=subprocess.DEVNULL,  # Discard output but don't block
                    stderr=subprocess.DEVNULL,  # Discard errors but don't block
                    creationflags=creation_flags,
                    shell=False,
                    env=env  # Pass environment with MinGW paths
                )
            else:
                self.process = subprocess.Popen(
                    [program_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=False
                )
            self.pid = self.process.pid
            logger.info(f"Started process {self.pid}: {program_path}")
            
            # Verify process is actually running
            import time
            time.sleep(0.2)  # Wait a bit longer to let process start and load DLLs
            if self.process.poll() is not None:
                # Process already terminated
                return_code = self.process.returncode
                
                # Decode Windows error codes
                error_msg = f"Process started but terminated immediately with return code {return_code}"
                if os.name == 'nt':
                    if return_code == 3221225781:  # 0xC0000142 STATUS_DLL_INIT_FAILED
                        error_msg += "\n\nError: Missing DLL dependencies (STATUS_DLL_INIT_FAILED)."
                        error_msg += "\nThe executable needs MinGW runtime DLLs. Try compiling with static linking."
                        error_msg += "\nAlternatively, ensure MinGW bin directory is in PATH."
                    elif return_code < 0:
                        error_code = return_code & 0xFFFFFFFF
                        error_msg += f"\n\nWindows error code: 0x{error_code:08X}"
                
                logger.warning(f"Process {self.pid} terminated immediately: {error_msg}")
                self.process = None
                self.pid = None
                return False, error_msg
            
            return True, f"Process started with PID {self.pid}"
            
        except Exception as e:
            logger.error(f"Failed to start process: {e}")
            self.process = None
            self.pid = None
            return False, f"Error starting process: {str(e)}"
    
    def stop_process(self) -> tuple[bool, str]:
        """
        Stop the target process
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if self.process is None:
            return False, "No process is running"
        
        try:
            # Terminate the process
            self.process.terminate()
            
            # Wait for graceful termination (2 seconds)
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate gracefully
                self.process.kill()
                self.process.wait()
            
            pid = self.pid
            self.process = None
            self.pid = None
            
            logger.info(f"Stopped process {pid}")
            return True, f"Process {pid} stopped"
            
        except Exception as e:
            logger.error(f"Error stopping process: {e}")
            return False, f"Error stopping process: {str(e)}"
    
    def is_running(self) -> bool:
        """Check if the process is currently running"""
        if self.process is None:
            return False
        
        # Check if process is still alive
        if self.process.poll() is not None:
            # Process has terminated
            self.process = None
            self.pid = None
            return False
        
        return True
    
    def get_pid(self) -> Optional[int]:
        """Get the current process PID"""
        return self.pid

