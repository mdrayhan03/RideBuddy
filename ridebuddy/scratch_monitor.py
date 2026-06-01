import psutil
import time

def find_django_processes():
    django_procs = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd = proc.info['cmdline']
            if cmd and any('manage.py' in part for part in cmd) and any('runserver' in part for part in cmd):
                django_procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return django_procs

def monitor():
    print("=== RideBuddy Resource Monitor ===")
    procs = find_django_processes()
    if not procs:
        print("Could not find any active 'manage.py runserver' process. Please make sure Django is running.")
        return

    print(f"Found {len(procs)} active Django server processes:")
    for p in procs:
        print(f"  - PID {p.pid}: {' '.join(p.info['cmdline'][:5])}")

    print("\nMeasuring CPU & RAM usage over 5 seconds under active Locust load...")
    # Initialize CPU percentage reading
    for p in procs:
        p.cpu_percent(interval=None)
    
    time.sleep(5)
    
    print("\n=== Resource Metrics Results ===")
    total_ram = 0
    total_cpu = 0
    for p in procs:
        try:
            # Memory in Megabytes
            mem_info = p.memory_info()
            ram_mb = mem_info.rss / (1024 * 1024)
            total_ram += ram_mb
            
            # CPU utilization
            cpu_pct = p.cpu_percent(interval=None)
            total_cpu += cpu_pct
            
            print(f"Process PID {p.pid} -> RAM: {ram_mb:.2f} MB | CPU: {cpu_pct:.1f}%")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    print("-" * 40)
    print(f"TOTAL DJANGO RAM USE: {total_ram:.2f} MB")
    print(f"TOTAL DJANGO CPU USE: {total_cpu:.1f}%")
    print("=================================")

if __name__ == "__main__":
    monitor()
