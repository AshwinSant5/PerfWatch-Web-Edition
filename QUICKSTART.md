# 🚀 Quick Start Guide

Get PerfWatch running in 5 minutes!

## Step 1: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Step 2: Install Frontend Dependencies

```bash
cd ../frontend
npm install
```

## Step 3: Start the Backend

In Terminal 1:
```bash
cd backend
python server.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 4: Start the Frontend

In Terminal 2:
```bash
cd frontend
npm start
```

Your browser should automatically open to `http://localhost:3000`

## Step 5: Profile a Program!

1. Enter a program path (e.g., `notepad.exe` or `C:\Windows\System32\notepad.exe`)
2. Click **"▶ Start Profiling"**
3. Watch the real-time charts update!
4. Click **"⏹ Stop Profiling"** when done
5. Click **"📥 Export CSV"** to download your metrics

## 🎯 Example Programs to Test

- `notepad.exe` - Simple text editor
- `calc.exe` - Calculator
- `mspaint.exe` - Paint application
- `C:\Windows\System32\cmd.exe` - Command prompt

## ⚠️ Troubleshooting

**Backend won't start?**
- Make sure Python 3.8+ is installed
- Check if port 8000 is already in use
- Verify all dependencies are installed: `pip install -r requirements.txt`

**Frontend won't start?**
- Make sure Node.js 16+ is installed
- Delete `node_modules` and run `npm install` again
- Check if port 3000 is available

**No metrics showing?**
- Make sure backend is running on port 8000
- Check browser console for WebSocket errors
- Verify the program path is correct

**WebSocket connection failed?**
- Ensure backend is running before starting frontend
- Check firewall settings
- Verify CORS settings in `server.py`

---

**Happy Profiling! 🎉**

