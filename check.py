import psutil
import time
import os

def get_django_stats(proc_name_filter="manage.py"):
    """
    Finds the main Django process and all its children 
    to calculate total 'Docker-style' stats.
    """
    total_rss = 0
    total_cpu = 0
    process_count = 0

    # Look for processes running your Django app
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
        try:
            cmdline = " ".join(proc.info['cmdline'] or [])
            if proc_name_filter in cmdline and "monitor.py" not in cmdline:
                # Get memory in MB
                total_rss += proc.info['memory_info'].rss / (1024 * 1024)
                # Get CPU (first call might be 0.0)
                total_cpu += proc.cpu_percent(interval=None)
                process_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return total_rss, total_cpu, process_count

print(f"{'PROCESSES':<12} | {'MEM USAGE':<12} | {'CPU %':<10}")
print("-" * 40)

try:
    while True:
        mem, cpu, count = get_django_stats()
        # Using \r to overwrite the line for a 'live' feel
        print(f"{count:<12} | {mem:>7.2f} MB    | {cpu:>7.1f}%", end="\r")
        time.sleep(1)
except KeyboardInterrupt:
    print("\nMonitoring stopped.")