"""
C++ Compiler Service - Compiles C++ source code to executables
"""
import subprocess
import os
import tempfile
import shutil
import glob
from typing import Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CppCompiler:
    """Handles C++ compilation on Windows"""
    
    def __init__(self):
        self.temp_dir: Optional[str] = None
        self.compiled_exe: Optional[str] = None
        self._setup_temp_directory()
    
    def _setup_temp_directory(self):
        """Create a temporary directory for compilation artifacts"""
        if self.temp_dir is None:
            # Use a directory that avoids short path names
            # Try to use a location without spaces or special characters
            base_temp = os.environ.get('TEMP', os.environ.get('TMP', tempfile.gettempdir()))
            # Create a subdirectory with a simple name
            perfwatch_base = os.path.join(base_temp, 'perfwatch_compile')
            os.makedirs(perfwatch_base, exist_ok=True)
            # Use a unique subdirectory to avoid conflicts
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            self.temp_dir = os.path.join(perfwatch_base, unique_id)
            os.makedirs(self.temp_dir, exist_ok=True)
            logger.info(f"Created temp directory: {self.temp_dir}")
    
    def _find_compiler(self) -> Optional[str]:
        """
        Find an available C++ compiler on the system
        
        Returns:
            Path to compiler executable or None if not found
        """
        # First, try to find g++ in PATH using shutil.which
        gpp_in_path = shutil.which("g++") or shutil.which("g++.exe")
        if gpp_in_path:
            try:
                result = subprocess.run(
                    [gpp_in_path, "--version"],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                if result.returncode == 0:
                    logger.info(f"Found compiler in PATH: {gpp_in_path}")
                    return gpp_in_path
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass
        
        # Try common MinGW/MSYS2 installation paths
        gpp_paths = [
            "g++",
            "g++.exe",
            r"C:\mingw64\bin\g++.exe",
            r"C:\mingw\bin\g++.exe",
            r"C:\msys64\mingw64\bin\g++.exe",
            r"C:\msys64\ucrt64\bin\g++.exe",
            r"C:\msys64\clang64\bin\g++.exe",
            r"C:\Program Files\mingw-w64\*\mingw64\bin\g++.exe",
            r"C:\Program Files (x86)\mingw-w64\*\mingw64\bin\g++.exe",
            r"C:\tools\mingw64\bin\g++.exe",
        ]
        
        for path in gpp_paths:
            # Handle glob patterns
            if '*' in path:
                matches = glob.glob(path)
                test_paths = matches
            else:
                test_paths = [path]
            
            for test_path in test_paths:
                if not os.path.exists(test_path):
                    continue
                
                try:
                    result = subprocess.run(
                        [test_path, "--version"],
                        capture_output=True,
                        timeout=5,
                        text=True
                    )
                    if result.returncode == 0:
                        logger.info(f"Found compiler: {test_path}")
                        return test_path
                except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                    continue
        
        # Try to find cl.exe (MSVC) - check multiple Visual Studio versions
        vs_base_paths = [
            r"C:\Program Files\Microsoft Visual Studio",
            r"C:\Program Files (x86)\Microsoft Visual Studio",
        ]
        
        vs_versions = ["2022", "2019", "2017", "2022"]
        vs_editions = ["Community", "Professional", "Enterprise", "BuildTools"]
        
        for base_path in vs_base_paths:
            for version in vs_versions:
                for edition in vs_editions:
                    pattern = os.path.join(
                        base_path, version, edition, 
                        "VC", "Tools", "MSVC", "*", "bin", "Hostx64", "x64", "cl.exe"
                    )
                    matches = glob.glob(pattern)
                    if matches:
                        # MSVC requires special environment, but we can at least detect it
                        logger.info(f"Found MSVC (may require setup): {matches[0]}")
                        # Note: MSVC typically requires vcvars64.bat to be run first
                        # For now, return it but compilation may fail
                        return matches[0]
        
        return None
    
    def compile(self, source_code: str, compiler_flags: Optional[list] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Compile C++ source code to an executable
        
        Args:
            source_code: C++ source code as string
            compiler_flags: Optional list of compiler flags
            
        Returns:
            Tuple of (success: bool, message: str, exe_path: Optional[str])
        """
        compiler = self._find_compiler()
        
        if compiler is None:
            error_msg = """No C++ compiler found. Please install one of the following:

Option 1: MinGW-w64 (Recommended)
  - Download from: https://www.mingw-w64.org/downloads/
  - Or install via MSYS2: https://www.msys2.org/
  - Add the bin directory to your system PATH
  - Example: C:\\msys64\\mingw64\\bin

Option 2: Visual Studio (MSVC)
  - Install Visual Studio with C++ workload
  - Download: https://visualstudio.microsoft.com/downloads/

After installation, restart the backend server."""
            return False, error_msg, None
        
        # Setup temp directory
        self._setup_temp_directory()
        
        # Generate unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        source_file = os.path.join(self.temp_dir, f"source_{timestamp}.cpp")
        exe_file = os.path.join(self.temp_dir, f"program_{timestamp}.exe")
        
        # Normalize paths to avoid short name issues on Windows
        source_file = os.path.abspath(os.path.normpath(source_file))
        exe_file = os.path.abspath(os.path.normpath(exe_file))
        
        # Expand short path names on Windows (e.g., ASHWIN~1 -> AshwinSanthosh)
        if os.name == 'nt':  # Windows
            def expand_short_path(path, must_exist=False):
                """Expand Windows short path names to long path names"""
                # Only expand if path exists (or if must_exist is False, try anyway)
                if must_exist and not os.path.exists(path):
                    return path
                
                try:
                    import win32api
                    # GetLongPathName requires the path to exist
                    if os.path.exists(path):
                        return win32api.GetLongPathName(path)
                    else:
                        # For non-existent paths, try to expand the directory part
                        dir_path = os.path.dirname(path)
                        if os.path.exists(dir_path):
                            expanded_dir = win32api.GetLongPathName(dir_path)
                            filename = os.path.basename(path)
                            return os.path.join(expanded_dir, filename)
                        return path
                except ImportError:
                    # win32api not available, use subprocess method
                    pass
                except Exception as e:
                    logger.debug(f"win32api expansion failed: {e}")
                    pass
                
                # Fallback: use PowerShell to expand the path
                try:
                    # Use PowerShell to expand the path
                    result = subprocess.run(
                        ['powershell', '-Command', 
                         f'[System.IO.Path]::GetFullPath("{path}")'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        expanded = result.stdout.strip()
                        # Remove quotes if present
                        if expanded.startswith('"') and expanded.endswith('"'):
                            expanded = expanded[1:-1]
                        return expanded
                except Exception as e:
                    logger.debug(f"PowerShell expansion failed: {e}")
                    pass
                
                # Final fallback: try to rebuild using gettempdir() which should give us the full path
                try:
                    import tempfile
                    temp_base = tempfile.gettempdir()
                    if '~' in path:
                        # Extract the relative part after Temp
                        if 'Temp' in path:
                            rel_path = path.split('Temp', 1)[-1].lstrip('\\/')
                            return os.path.join(temp_base, rel_path)
                        elif 'TMP' in path.upper():
                            rel_path = path.split('TMP', 1)[-1].lstrip('\\/')
                            return os.path.join(temp_base, rel_path)
                except Exception as e:
                    logger.debug(f"Fallback expansion failed: {e}")
                    pass
                
                return path
            
            # Expand temp_dir first (it exists)
            if '~' in self.temp_dir and os.path.exists(self.temp_dir):
                self.temp_dir = expand_short_path(self.temp_dir, must_exist=True)
                logger.info(f"Expanded temp_dir: {self.temp_dir}")
            
            # Rebuild source_file and exe_file using the expanded temp_dir
            # This ensures we use the full path names
            source_filename = os.path.basename(source_file)
            exe_filename = os.path.basename(exe_file)
            source_file = os.path.join(self.temp_dir, source_filename)
            exe_file = os.path.join(self.temp_dir, exe_filename)
            
            logger.info(f"Final paths - source: {source_file}, exe: {exe_file}")
        
        try:
            # Write source code to file
            logger.info(f"Writing source code to: {source_file}")
            logger.debug(f"Source code length: {len(source_code)} characters")
            with open(source_file, 'w', encoding='utf-8', newline='\n') as f:
                f.write(source_code)
            
            # Verify file was written
            if not os.path.exists(source_file):
                return False, f"Failed to write source file to {source_file}", None
            
            file_size = os.path.getsize(source_file)
            logger.info(f"Source file written successfully: {file_size} bytes")
            
            # Verify file content
            with open(source_file, 'r', encoding='utf-8') as f:
                read_content = f.read()
            if len(read_content) != len(source_code):
                logger.warning(f"File size mismatch: wrote {len(source_code)} chars, read {len(read_content)} chars")
            
            # Default compiler flags
            if compiler_flags is None:
                # Use static linking to avoid DLL dependency issues
                # -static-libgcc and -static-libstdc++ link runtime libraries statically
                compiler_flags = ["-std=c++17", "-O2", "-Wall", "-static-libgcc", "-static-libstdc++"]
            
            # Build compile command
            # Use relative paths when working directory is set to temp_dir
            # This avoids path length and permission issues
            source_file_rel = os.path.relpath(source_file, self.temp_dir)
            exe_file_rel = os.path.relpath(exe_file, self.temp_dir)
            
            if "cl.exe" in compiler or "cl" in compiler:
                # MSVC compiler
                compile_cmd = [
                    compiler,
                    source_file_rel,
                    f"/Fe:{exe_file_rel}",
                    "/EHsc",  # Exception handling
                    "/std:c++17",
                ]
            else:
                # g++ compiler - use relative paths
                compile_cmd = [compiler] + compiler_flags + [
                    source_file_rel,
                    "-o", exe_file_rel
                ]
            
            logger.info(f"Using relative paths - source: {source_file_rel}, exe: {exe_file_rel}")
            
            logger.info(f"Compiling: {' '.join(compile_cmd)}")
            
            # Log the exact command being run
            logger.info(f"Full compile command: {compile_cmd}")
            logger.info(f"Working directory: {self.temp_dir}")
            logger.info(f"Source file exists: {os.path.exists(source_file)}")
            logger.info(f"Source file path: {source_file}")
            
            # For MSYS2/MinGW, we might need to set up environment
            env = os.environ.copy()
            
            # If using MSYS2 compiler, ensure PATH includes MSYS2 bin directories
            if "msys64" in compiler.lower() or "mingw64" in compiler.lower():
                # Compiler path: C:\msys64\mingw64\bin\g++.exe
                # We want: C:\msys64\mingw64\bin and C:\msys64\usr\bin
                compiler_dir = os.path.dirname(compiler)  # C:\msys64\mingw64\bin
                if "mingw64" in compiler.lower():
                    # Go up one level to get mingw64, then up another to get msys64
                    mingw_dir = os.path.dirname(compiler_dir)  # C:\msys64\mingw64
                    msys_base = os.path.dirname(mingw_dir)  # C:\msys64
                    mingw_bin = compiler_dir  # C:\msys64\mingw64\bin
                    msys_bin = os.path.join(msys_base, "usr", "bin")  # C:\msys64\usr\bin
                else:
                    msys_base = os.path.dirname(os.path.dirname(compiler_dir))
                    mingw_bin = compiler_dir
                    msys_bin = os.path.join(msys_base, "usr", "bin")
                
                # Add MSYS2 paths to environment
                current_path = env.get("PATH", "")
                if mingw_bin not in current_path:
                    env["PATH"] = f"{mingw_bin};{msys_bin};{current_path}"
                    logger.info(f"Added to PATH: {mingw_bin} and {msys_bin}")
            
            # Try multiple approaches to capture output
            # On Windows with MSYS2, sometimes output doesn't get captured properly
            result = None
            output_captured = False
            
            # Approach 1: Direct subprocess with combined streams
            try:
                logger.info("Attempting compilation with direct subprocess...")
                logger.info(f"Working in directory: {self.temp_dir}")
                logger.info(f"Source file (relative): {source_file_rel}")
                logger.info(f"Source file (absolute): {source_file}")
                logger.info(f"Source exists: {os.path.exists(source_file)}")
                
                # Verify temp directory exists and is accessible
                if not os.path.exists(self.temp_dir):
                    raise Exception(f"Temp directory does not exist: {self.temp_dir}")
                if not os.path.exists(source_file):
                    raise Exception(f"Source file does not exist: {source_file}")
                
                # Verify relative path resolves correctly
                rel_path_check = os.path.join(self.temp_dir, source_file_rel)
                if not os.path.exists(rel_path_check):
                    logger.warning(f"Relative path check failed: {rel_path_check}")
                
                result = subprocess.run(
                    compile_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=30,
                    cwd=self.temp_dir,
                    shell=False,
                    env=env
                )
                if result.stdout and len(result.stdout.strip()) > 0:
                    output_captured = True
                    logger.info("Output captured successfully with direct subprocess")
            except Exception as e:
                logger.warning(f"Direct subprocess failed: {e}")
            
            # Approach 2: If no output, try with a temp file to capture output
            if not output_captured or (result and result.returncode != 0 and not result.stdout):
                logger.info("Trying compilation with output redirection to file...")
                try:
                    output_file = os.path.join(self.temp_dir, "compile_output.txt")
                    error_file = os.path.join(self.temp_dir, "compile_error.txt")
                    
                    # Try running with output redirection
                    if os.name == 'nt':  # Windows
                        # Use cmd /c to run command with redirection
                        # Quote all paths properly
                        compile_cmd_quoted = []
                        for arg in compile_cmd:
                            if ' ' in arg or '~' in arg or '\\' in arg:
                                compile_cmd_quoted.append(f'"{arg}"')
                            else:
                                compile_cmd_quoted.append(arg)
                        
                        compile_cmd_str = ' '.join(compile_cmd_quoted)
                        # Use cmd /c with proper redirection
                        # Redirect both stdout and stderr to the same file
                        # Note: Don't quote the entire command, just use cmd /c with the command
                        full_cmd = f'cmd /c {compile_cmd_str} > "{output_file}" 2>&1'
                        
                        logger.info(f"Running file redirection command: {full_cmd}")
                        
                        result_file = subprocess.run(
                            full_cmd,
                            shell=True,
                            cwd=self.temp_dir,
                            env=env,
                            timeout=30
                        )
                        
                        logger.info(f"File redirection return code: {result_file.returncode}")
                        
                        # Read the output files
                        stdout_content = ""
                        stderr_content = ""
                        
                        if os.path.exists(output_file):
                            try:
                                with open(output_file, 'r', encoding='utf-8', errors='replace') as f:
                                    stdout_content = f.read()
                                logger.info(f"Read {len(stdout_content)} chars from output file")
                            except Exception as e:
                                logger.warning(f"Failed to read output file: {e}")
                        
                        if os.path.exists(error_file):
                            try:
                                with open(error_file, 'r', encoding='utf-8', errors='replace') as f:
                                    stderr_content = f.read()
                                logger.info(f"Read {len(stderr_content)} chars from error file")
                            except Exception as e:
                                logger.warning(f"Failed to read error file: {e}")
                        
                        # Combine outputs (stderr was redirected to stdout, so check both)
                        combined_output = (stdout_content + "\n" + stderr_content).strip()
                        
                        if combined_output:
                            # Create a result-like object
                            class FakeResult:
                                def __init__(self, returncode, stdout):
                                    self.returncode = returncode
                                    self.stdout = stdout
                            
                            result = FakeResult(result_file.returncode, combined_output)
                            output_captured = True
                            logger.info(f"Captured output via file: {len(combined_output)} chars")
                            logger.info(f"Output preview: {combined_output[:500]}")
                        else:
                            logger.warning("No output found in files after redirection")
                    else:
                        # Unix-like systems
                        result_file = subprocess.run(
                            compile_cmd,
                            stdout=open(output_file, 'w'),
                            stderr=open(error_file, 'w'),
                            timeout=30,
                            cwd=self.temp_dir,
                            env=env
                        )
                        
                        with open(output_file, 'r') as f:
                            stdout_content = f.read()
                        with open(error_file, 'r') as f:
                            stderr_content = f.read()
                        
                        combined_output = (stderr_content + "\n" + stdout_content).strip()
                        if combined_output:
                            class FakeResult:
                                def __init__(self, returncode, stdout):
                                    self.returncode = returncode
                                    self.stdout = stdout
                            result = FakeResult(result_file.returncode, combined_output)
                            output_captured = True
                except Exception as e:
                    logger.warning(f"File redirection approach failed: {e}")
            
            # Approach 3: If still no output, try with shell=True (Windows)
            if not output_captured or (result and result.returncode != 0 and not result.stdout):
                logger.info("Trying compilation with shell=True...")
                try:
                    # Quote paths with spaces
                    quoted_cmd = []
                    for arg in compile_cmd:
                        if ' ' in arg or '~' in arg:
                            quoted_cmd.append(f'"{arg}"')
                        else:
                            quoted_cmd.append(arg)
                    
                    cmd_str = ' '.join(quoted_cmd)
                    result = subprocess.run(
                        cmd_str,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        timeout=30,
                        cwd=self.temp_dir,
                        env=env
                    )
                    if result.stdout and len(result.stdout.strip()) > 0:
                        output_captured = True
                        logger.info("Output captured with shell=True")
                except Exception as e:
                    logger.warning(f"Shell approach failed: {e}")
            
            # If we still don't have a result, create a minimal one
            if result is None:
                class FakeResult:
                    def __init__(self):
                        self.returncode = 1
                        self.stdout = ""
                result = FakeResult()
            
            # Log raw output for debugging
            logger.info(f"Compilation return code: {result.returncode}")
            logger.info(f"Output length: {len(result.stdout) if result.stdout else 0}")
            if result.stdout:
                logger.info(f"Output preview: {result.stdout[:500]}")
            
            if result.returncode != 0:
                # Since we redirected stderr to stdout, all output is in stdout
                error_parts = []
                
                # Get error output from stdout (since stderr was redirected)
                error_output = result.stdout.strip() if result.stdout else ""
                
                if error_output:
                    error_parts.append("Compiler Output:")
                    error_parts.append(error_output)
                else:
                    # No output received - this is unusual. Try to diagnose the issue
                    error_parts.append("No compiler output received (this is unusual).")
                    error_parts.append("\nPossible causes:")
                    error_parts.append("1. Compiler crashed silently")
                    error_parts.append("2. Output was redirected elsewhere")
                    error_parts.append("3. Path issues with short names on Windows")
                    
                    # Try to manually test the compiler
                    try:
                        test_result = subprocess.run(
                            [compiler, "--version"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            encoding='utf-8',
                            errors='replace',
                            timeout=5
                        )
                        if test_result.returncode == 0:
                            error_parts.append(f"\nCompiler is working (version check succeeded):")
                            error_parts.append(test_result.stdout[:200])
                        else:
                            error_parts.append(f"\nCompiler version check failed: {test_result.stdout}")
                    except Exception as e:
                        error_parts.append(f"\nCould not test compiler: {str(e)}")
                    
                    # Try to read the source file to verify it's valid
                    try:
                        with open(source_file, 'r', encoding='utf-8') as f:
                            source_preview = f.read(500)
                        error_parts.append(f"\nSource file preview (first 500 chars):")
                        error_parts.append(source_preview)
                    except Exception as e:
                        error_parts.append(f"\nCould not read source file: {str(e)}")
                
                # Always include command and return code
                error_parts.append(f"\n--- Debug Info ---")
                error_parts.append(f"Compiler: {compiler}")
                error_parts.append(f"Command: {' '.join(compile_cmd)}")
                error_parts.append(f"Return code: {result.returncode}")
                error_parts.append(f"Source file: {source_file}")
                error_parts.append(f"Source exists: {os.path.exists(source_file)}")
                if os.path.exists(source_file):
                    error_parts.append(f"Source size: {os.path.getsize(source_file)} bytes")
                
                error_msg = "\n".join(error_parts) if error_parts else "Unknown compilation error"
                
                # Add helpful context
                full_error = f"Compilation Error:\n{error_msg}"
                if len(full_error) > 3000:
                    # Truncate very long errors but keep the end
                    full_error = f"Compilation Error:\n{error_msg[:2000]}...\n(Error message truncated)\n\nLast 1000 chars:\n{error_msg[-1000:]}"
                
                logger.error(f"Compilation failed: {error_msg}")
                return False, full_error, None
            
            # Check for exe_file - it was created with relative path, so resolve it
            exe_file_abs = os.path.join(self.temp_dir, exe_file_rel)
            if not os.path.exists(exe_file_abs):
                # Also check the original absolute path
                if not os.path.exists(exe_file):
                    return False, f"Compilation succeeded but executable not found at {exe_file_abs} or {exe_file}", None
                exe_file_abs = exe_file
            
            self.compiled_exe = exe_file_abs
            logger.info(f"Successfully compiled: {exe_file_abs}")
            return True, f"Compiled successfully to {exe_file_abs}", exe_file_abs
            
        except subprocess.TimeoutExpired:
            return False, "Compilation timed out (exceeded 30 seconds).\nThe code may be too complex or there may be an infinite loop.", None
        except FileNotFoundError as e:
            error_msg = f"Compiler executable not found: {e}\n\n"
            error_msg += "Please ensure the compiler is installed and in your PATH.\n"
            error_msg += "See INSTALL_COMPILER.md for installation instructions."
            logger.error(f"Compiler not found: {e}")
            return False, error_msg, None
        except PermissionError as e:
            error_msg = f"Permission denied: {e}\n\n"
            error_msg += "Please check file permissions and ensure the compiler can write to the temp directory."
            logger.error(f"Permission error: {e}")
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Unexpected compilation error: {str(e)}\n\n"
            error_msg += f"Error type: {type(e).__name__}\n"
            error_msg += "Please check the backend logs for more details."
            logger.error(f"Compilation error: {e}", exc_info=True)
            return False, error_msg, None
    
    def get_compiled_exe(self) -> Optional[str]:
        """Get the path to the compiled executable"""
        return self.compiled_exe
    
    def cleanup(self):
        """Clean up temporary files and directories"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory: {e}")
            finally:
                self.temp_dir = None
                self.compiled_exe = None
    
    def __del__(self):
        """Cleanup on destruction"""
        self.cleanup()

