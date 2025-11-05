# Available Metrics Guide

## Currently Available Metrics

### Basic Metrics (Task Manager-like)
- **CPU Usage** - Percentage of CPU used by the process
- **Memory (Working Set)** - Physical RAM currently in use
- **Threads** - Number of threads in the process
- **Context Switches** - Number of times CPU switched to/from this process

### Advanced Metrics (Not in Task Manager)

#### Memory Metrics
- **Virtual Memory** - Total virtual address space
- **Private Bytes** - Memory exclusively used by this process (Windows)
- **Shared Memory** - Memory shared with other processes (Windows)
- **Peak Working Set** - Maximum working set during process lifetime (Windows)

#### I/O Metrics
- **I/O Read MB** - Total bytes read from disk/network
- **I/O Write MB** - Total bytes written to disk/network
- **I/O Read Ops** - Number of read operations
- **I/O Write Ops** - Number of write operations

#### Process Metrics
- **Page Faults** - Total, Major (Hard), Minor (Soft) page faults
- **Open File Handles** - Number of open file handles/descriptors
- **CPU User Time** - Total CPU time in user mode
- **CPU System Time** - Total CPU time in kernel mode
- **Process Uptime** - How long the process has been running (Windows)
- **CPU Affinity** - Which CPU cores the process can run on (Windows)
- **Process Priority** - Process priority class (Windows)
- **Network Connections** - Active network connections (Windows)

## Metrics NOT Available (and Why)

### Cache Hit/Miss Rates
**Status**: ❌ Not directly available via standard Windows APIs

**Why**: Cache performance metrics require:
- Hardware Performance Counters (HPC) - Requires special drivers
- Intel VTune Profiler or AMD uProf - Commercial tools
- ETW (Event Tracing for Windows) - Complex setup, requires admin privileges
- Kernel-mode drivers - Not practical for user-space applications

**Workaround**: You can indirectly infer cache behavior through:
- Page faults (high page faults = potential cache issues)
- Memory access patterns (sequential vs random)
- CPU stall cycles (if using advanced profiling tools)

### Memory Access Count
**Status**: ❌ Not directly available via standard Windows APIs

**Why**: Counting every memory access requires:
- Hardware-level profiling (Intel PT, AMD Instruction-Based Sampling)
- Specialized profiling tools (VTune, Perf)
- Kernel-mode instrumentation
- Significant performance overhead

**What You CAN Monitor Instead**:
- **Page Faults** - Memory accesses that required OS intervention
- **Working Set Size** - How much memory is actively used
- **Memory Allocation/Deallocation** - Through your application's allocator

## How to Add More Metrics

### Option 1: Using Windows Performance Counters (PDH)
The `windows_metrics.py` module can be extended to use `win32pdh` to query additional counters:
- Processor performance counters
- Disk performance counters
- Network performance counters

### Option 2: Using ETW (Event Tracing for Windows)
For more advanced metrics, you could use ETW:
- Requires admin privileges
- More complex setup
- Can provide detailed CPU, memory, and I/O events

### Option 3: Hardware Performance Counters
For cache metrics, you'd need:
- Intel VTune Profiler integration
- AMD uProf integration
- Custom kernel-mode drivers

## Recommended Approach

For most use cases, the current metrics provide excellent insight:
1. **CPU metrics** - Show performance bottlenecks
2. **Memory metrics** - Show memory leaks and usage patterns
3. **I/O metrics** - Show disk/network bottlenecks
4. **Thread/Context Switch metrics** - Show concurrency issues

For cache analysis, consider:
- Using specialized profiling tools (VTune, Perf) for detailed analysis
- Monitoring page faults as an indicator of memory access patterns
- Using the I/O metrics to understand memory pressure

