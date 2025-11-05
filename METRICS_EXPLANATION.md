# Complete Metrics Explanation Guide

## Basic Metrics (Task Manager-like)

### CPU Usage (102.4%)
**What it means:** Percentage of CPU time used by this process. On multi-core systems, this can exceed 100% (e.g., 102.4% means using slightly more than one full CPU core's worth of work, spread across multiple cores).

---

### Memory / Working Set (1639.8 MB)
**What it means:** Physical RAM (working set) currently in use by the process. This is memory that's actually loaded into RAM, not just reserved.

---

### Virtual Memory (1656.3 MB)
**What it means:** Total virtual address space reserved/committed by the process. This includes memory in RAM, paged to disk, and reserved but not yet used.

---

### Threads (6)
**What it means:** Number of threads (execution paths) in the process. Each thread can run independently on a CPU core.

---

### Context Switches (32,554)
**What it means:** Number of times the CPU switched from this process to another (or vice versa). Includes both voluntary (thread yields) and involuntary (time slice expires).

---

## I/O Metrics

### I/O Read (714.74 MB)
**What it means:** Total bytes read from disk/network by this process since it started.

---

### I/O Write (717.00 MB)
**What it means:** Total bytes written to disk/network by this process since it started.

---

### I/O Read Ops (1,296) & Write Ops (1,408)
**What it means:** Number of read/write system calls made, not the data size.

---

## Memory Details

### Private Bytes (1681.4 MB)
**What it means:** Memory exclusively used by this process - cannot be shared with other processes. This is committed memory (reserved and backed by page file or RAM).

**Why it makes sense:** 
- All your program's data structures are private
- File buffers are private to this process
- Memory chunks allocated are private
- Includes memory in RAM + memory paged to disk

---

### Shared Memory (0.0 MB)
**What it means:** Memory shared between this process and other processes (e.g., shared libraries, memory-mapped files).

---

### Page Faults (0)
**What it means:** Number of times the process tried to access memory that wasn't in physical RAM, requiring the OS to load it from disk.

**What if > 0?** High page faults would indicate:
- Not enough RAM (system is swapping)
- Memory pressure (OS paging out memory)
- Performance degradation (disk is much slower than RAM)

---

## Windows-Specific Metrics

### Process Uptime (0m 30s)
**What it means:** How long the process has been running since it was created.


---

### CPU Affinity (8 cores)
**What it means:** Which CPU cores this process is allowed to run on. Shows the process can use all available cores.

---

### Process Priority (Normal)
**What it means:** The process's priority class in the Windows scheduler. Normal = default priority, gets equal CPU time with other normal-priority processes.

**Priority levels:**
- Idle: Lowest priority
- Below Normal: Lower than normal
- **Normal**: Default (your value)
- Above Normal: Higher than normal
- High: High priority
- Realtime: Highest (system-critical)

---

### Network Connections (N/A)
**What it means:** Number of active network connections (TCP/UDP sockets).

---

## File Handles

### Open Handles (83)
**What it means:** Number of open file handles, sockets, pipes, and other I/O resources currently open.

**Why it matters:** Too many handles can indicate:
- Resource leaks (files not closed)
- System limits (Windows has handle limits per process)
- Performance issues

---

## CPU Time Breakdown

### CPU User Time (10.84s)
**What it means:** Total CPU time spent executing your program's code (user mode). This is actual computation time.

---

### CPU System Time (15.12s)
**What it means:** Total CPU time spent in kernel mode (OS system calls). This is time the OS spends on behalf of your process.

---


