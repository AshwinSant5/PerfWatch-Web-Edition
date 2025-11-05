# 🌐 PerfWatch Web Edition

Real-time performance monitoring web application for Windows executables. Profile CPU, memory, threads, and context switches with live visualizations.

## 🚀 Features

- **Launch & Monitor**: Start any Windows executable and monitor its performance in real-time
- **Compile C++ Code**: Paste C++ source code, compile it automatically, and profile the executable
- **Live Metrics**: Track CPU usage, memory consumption, thread count, and context switches
- **Interactive Charts**: Beautiful Plotly.js charts that update in real-time
- **Data Export**: Export collected metrics as CSV or JSON files
- **WebSocket Streaming**: Low-latency metric streaming (250ms intervals)
- **Modern UI**: Clean, dark-themed interface built with React and TailwindCSS

## 📋 Prerequisites

- **Windows 10/11** (required for Windows-specific APIs)
- **Python 3.8+** (for backend)
- **Node.js 16+** (for frontend)
- **npm** or **yarn** (for frontend dependencies)
- **C++ Compiler** (optional, for C++ compilation feature):
  - MinGW-w64 (g++) - Recommended
  - MSVC (Visual Studio) - Also supported

## 🛠️ Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## 🎯 Usage

### Starting the Application

1. **Start the Backend Server** (Terminal 1):
```bash
cd backend
python server.py
# Or use uvicorn directly:
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

The backend will start on `http://localhost:8000`

2. **Start the Frontend** (Terminal 2):
```bash
cd frontend
npm start
```

The frontend will open automatically at `http://localhost:3000`

### Using PerfWatch

#### Option 1: Run an Executable

1. **Select "Run Executable" mode** (default)
2. **Enter Executable Path**: 
   - Type the full path to your executable (e.g., `C:\Windows\System32\notepad.exe`)
   - Or use a simple name if it's in PATH (e.g., `notepad.exe`)
3. **Start Profiling**: Click "▶ Start Profiling"
4. **View Metrics**: Watch real-time charts update

#### Option 2: Compile & Run C++ Code

1. **Select "Compile C++" mode**
2. **Paste C++ Source Code**: 
   - Paste your C++ code into the textarea
   - Or click "Load Example" for a sample program
3. **Compile & Profile**: Click "🔨 Compile & Profile"
   - The code will be compiled automatically
   - If compilation succeeds, the executable will be run and profiled
4. **View Metrics**: Watch real-time performance data

#### Stop & Export

1. **Stop Profiling**: Click "⏹ Stop Profiling" to stop monitoring
2. **Export Data**: Click "📥 Export CSV" to download the collected metrics

## 📁 Project Structure

```
performance_utility/
├── backend/
│   ├── server.py              # FastAPI main server
│   ├── process_manager.py     # Process launch/stop logic
│   ├── telemetry.py           # Metrics collection (psutil)
│   ├── logger.py               # CSV/JSON export
│   ├── compiler.py             # C++ compilation service
│   └── requirements.txt       # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Main app component
│   │   ├── components/
│   │   │   ├── Dashboard.jsx  # Real-time charts
│   │   │   ├── Controls.jsx   # Start/Stop controls
│   │   │   └── MetricsPanel.jsx # Current metrics display
│   │   └── index.js           # React entry point
│   ├── package.json
│   └── tailwind.config.js
│
└── README.md
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API status |
| `/status` | GET | Get current profiling status |
| `/run` | POST | Start profiling a program |
| `/compile-and-run` | POST | Compile C++ code and start profiling |
| `/stop` | POST | Stop profiling |
| `/export` | GET | Export metrics (CSV/JSON) |
| `/ws/metrics` | WebSocket | Stream live metrics |

### Example API Usage

**Start Profiling:**
```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"program": "notepad.exe"}'
```

**Compile & Run C++:**
```bash
curl -X POST http://localhost:8000/compile-and-run \
  -H "Content-Type: application/json" \
  -d '{"source_code": "#include <iostream>\nint main() { std::cout << \"Hello!\\n\"; return 0; }"}'
```

**Stop Profiling:**
```bash
curl -X POST http://localhost:8000/stop \
  -H "Content-Type: application/json" \
  -d '{"kill_process": true}'
```

**Export Metrics:**
```bash
curl http://localhost:8000/export?format=csv -o metrics.csv
```

## 📊 Metrics Collected

- **CPU Usage (%)**: Per-process CPU utilization
- **Memory (MB)**: Resident Set Size (RSS) in megabytes
- **Thread Count**: Number of active threads
- **Context Switches**: OS-level context switch count
- **System CPU (%)**: System-wide CPU usage for reference

## 🛡️ Troubleshooting

### Backend Issues

- **Port already in use**: Change the port in `server.py` or kill the process using port 8000
- **Permission denied**: Ensure you have permission to run the target executable
- **psutil errors**: Some processes may require elevated privileges

### C++ Compilation Issues

- **No compiler found**: Install MinGW-w64 or MSVC
  - MinGW-w64: Download from [mingw-w64.org](https://www.mingw-w64.org/) or use MSYS2
  - MSVC: Install Visual Studio with C++ workload
- **Compilation errors**: Check the error message in the UI - it will show compiler output
- **g++ not in PATH**: Add MinGW bin directory to your system PATH

### Frontend Issues

- **WebSocket connection failed**: Ensure backend is running on port 8000
- **Charts not updating**: Check browser console for WebSocket errors
- **CORS errors**: Verify CORS settings in `server.py` match your frontend URL

### Common Issues

- **Process not found**: Verify the executable path is correct
- **No metrics showing**: Check if the process is still running
- **Export fails**: Ensure metrics have been collected before exporting

## 🔧 Development

### Backend Development

The backend uses FastAPI with automatic reload:
```bash
uvicorn server:app --reload
```

### Frontend Development

The React app uses Create React App with hot reload:
```bash
npm start
```

## 📝 Notes

- Metrics are collected every 250ms (4 samples per second)
- CSV files are saved in the `backend/logs/` directory
- The frontend keeps the last 200 data points in memory for performance
- WebSocket automatically reconnects if the connection is lost
- Compiled C++ executables are stored in temporary directories and cleaned up after profiling

## 🚧 Future Enhancements

- [ ] Process selector dropdown (list running processes)
- [ ] System-wide metrics view
- [ ] Power consumption metrics
- [ ] Historical run analytics
- [ ] Electron desktop wrapper
- [ ] ARM/Qualcomm support enhancements
- [ ] Support for additional languages (Python, Rust, etc.)

## 📄 License

This project is provided as-is for performance monitoring purposes.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!
