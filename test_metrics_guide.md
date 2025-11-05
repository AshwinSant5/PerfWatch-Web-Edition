# 📊 Test Files for PerfWatch

I've created test C++ programs to demonstrate all the performance metrics. Here's what each one does:

## 🎯 `test_performance.cpp` (Comprehensive Test)

This is the **main test file** that demonstrates all metrics:

### Features:
- **CPU Usage**: 4 threads performing intensive mathematical calculations (sin, cos, sqrt)
- **Memory Usage**: Dynamic allocation/deallocation cycles (grows to ~400MB, then shrinks)
- **Thread Count**: 4 worker threads + 1 memory thread + main thread = 6 threads total
- **Context Switches**: 
  - Thread synchronization with mutexes
  - Periodic sleep calls
  - Thread contention on shared counter

### What You'll See:
- CPU usage spikes to 100%+ (multiple cores)
- Memory usage grows and shrinks in cycles
- Thread count shows 6 threads
- Context switches increase significantly due to mutex contention

### Runtime: ~10-15 seconds

---

## 🚀 `test_simple.cpp` (Quick Test)

A simpler, faster test program:

### Features:
- **CPU Usage**: Single-threaded intensive calculations
- **Memory Usage**: Allocates ~4MB vector
- **Thread Count**: 1 thread (main thread)
- **Context Switches**: Minimal (just sleep calls)

### What You'll See:
- CPU usage around 25-50% (single core)
- Steady memory usage (~4MB)
- Thread count = 1
- Lower context switch count

### Runtime: ~2-3 seconds

---

## 📝 How to Use

1. **In PerfWatch UI**:
   - Switch to "Compile C++" mode
   - Drag and drop `test_performance.cpp` or `test_simple.cpp`
   - Click "🔨 Compile & Profile"
   - Watch the metrics!

2. **Or Compile Manually** (if you want to test compilation):
   ```bash
   g++ -std=c++17 -O2 -Wall test_performance.cpp -o test_performance.exe
   ./test_performance.exe
   ```

---

## 📈 Expected Metrics

### For `test_performance.cpp`:
- **CPU %**: 80-100%+ (utilizing multiple cores)
- **Memory (MB)**: Cycles between 50-400 MB
- **Threads**: 6 threads
- **Context Switches**: High (thousands per second)

### For `test_simple.cpp`:
- **CPU %**: 25-50% (single core)
- **Memory (MB)**: ~4 MB (steady)
- **Threads**: 1 thread
- **Context Switches**: Low (hundreds per second)

---

## 💡 Tips

- **Start with `test_simple.cpp`** to verify everything works
- **Use `test_performance.cpp`** to see dramatic metric changes
- **Watch the charts** - you'll see:
  - CPU spikes during calculations
  - Memory waves during allocation cycles
  - Thread count increases when threads start
  - Context switches spike during mutex contention

---

## 🔧 Customization

Feel free to modify the test files:
- Change `num_threads` to see more/fewer threads
- Adjust `iterations_per_thread` for longer/shorter runs
- Modify `chunk_size` to change memory usage patterns
- Add more sleep calls to see more context switches

Happy profiling! 🎉

