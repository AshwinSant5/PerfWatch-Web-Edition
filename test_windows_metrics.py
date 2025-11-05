"""Quick test to verify Windows metrics are being collected"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from windows_metrics import get_windows_process_metrics
import psutil

# Test with current process
pid = os.getpid()
print(f"Testing Windows metrics for PID {pid}...")

metrics = get_windows_process_metrics(pid)
print(f"\nCollected metrics: {list(metrics.keys())}")
print(f"\nMetric values:")
for key, value in metrics.items():
    print(f"  {key}: {value}")

if not metrics:
    print("\n⚠️  No metrics collected! Check the logs above for errors.")
else:
    print(f"\n✅ Successfully collected {len(metrics)} Windows-specific metrics!")

