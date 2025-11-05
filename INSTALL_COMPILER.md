# 📦 Installing a C++ Compiler for PerfWatch

PerfWatch requires a C++ compiler to compile and profile C++ source code. Here are the easiest ways to install one:

## 🚀 Quick Install Options

### Option 1: MSYS2 (Recommended - Easiest)

1. **Download MSYS2**:
   - Visit: https://www.msys2.org/
   - Download and run the installer

2. **Install MinGW-w64**:
   - Open MSYS2 terminal (or run in PowerShell):
   ```bash
   pacman -S mingw-w64-x86_64-gcc
   ```

3. **Add to PATH**:
   - Add `C:\msys64\mingw64\bin` to your system PATH
   - Or restart your terminal/backend after installation

4. **Verify Installation**:
   ```bash
   g++ --version
   ```

### Option 2: Standalone MinGW-w64

1. **Download MinGW-w64**:
   - Visit: https://www.mingw-w64.org/downloads/
   - Or use: https://winlibs.com/ (pre-built binaries)

2. **Extract** to a folder (e.g., `C:\mingw64`)

3. **Add to PATH**:
   - Add `C:\mingw64\bin` to your system PATH
   - Restart your terminal/backend

4. **Verify Installation**:
   ```bash
   g++ --version
   ```

### Option 3: Visual Studio (MSVC)

1. **Download Visual Studio**:
   - Visit: https://visualstudio.microsoft.com/downloads/
   - Download "Community" edition (free)

2. **Install C++ Workload**:
   - During installation, select "Desktop development with C++"
   - Or use Visual Studio Installer to add it later

3. **Note**: MSVC requires special environment setup, so MinGW-w64 is recommended for easier use.

## 🔧 Adding to PATH (Windows)

1. **Open System Properties**:
   - Press `Win + X` → System
   - Click "Advanced system settings"
   - Click "Environment Variables"

2. **Edit PATH**:
   - Under "System variables", find `Path`
   - Click "Edit"
   - Click "New"
   - Add: `C:\msys64\mingw64\bin` (or your MinGW path)
   - Click "OK" on all dialogs

3. **Restart**:
   - Close all terminal windows
   - Restart the PerfWatch backend server

## ✅ Verify Installation

After installation, verify the compiler is accessible:

```bash
g++ --version
```

You should see output like:
```
g++ (x86_64-posix-seh-rev0, Built by MinGW-W64 project) 13.2.0
```

## 🐛 Troubleshooting

### Compiler still not found?

1. **Check PATH**:
   ```bash
   echo $env:PATH
   ```
   (PowerShell) or check System Environment Variables

2. **Restart Backend**:
   - Close the backend terminal
   - Restart it completely

3. **Manual Path**:
   - If installed in a non-standard location, you may need to manually specify the path in the compiler detection code

### Still having issues?

- Make sure you installed the **64-bit** version
- Ensure the `bin` directory contains `g++.exe`
- Try running `g++.exe --version` directly from the bin folder

## 📝 Next Steps

Once installed:
1. Restart the PerfWatch backend server
2. Try compiling a C++ file again
3. The compiler should now be detected automatically!

