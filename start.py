import os
import signal
import subprocess
import sys
import threading

BASE = os.path.dirname(os.path.abspath(__file__))

# Color codes for each service output
COLORS = {
    "alert-service":        "\033[92m",   # green
    "market-simulator":     "\033[94m",   # blue
    "price-monitor":        "\033[93m",   # yellow
    "notification-service": "\033[95m",   # magenta
    "dashboard-service":    "\033[96m",   # cyan
}
RESET = "\033[0m"

SERVICES = [
    {
        "name": "alert-service",
        "cmd":  [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"],
        "cwd":  os.path.join(BASE, "backend", "alert-service"),
    },
    {
        "name": "market-simulator",
        "cmd":  [sys.executable, "main.py"],
        "cwd":  os.path.join(BASE, "backend", "market-simulator"),
    },
    {
        "name": "price-monitor",
        "cmd":  [sys.executable, "main.py"],
        "cwd":  os.path.join(BASE, "backend", "price-monitor"),
    },
    {
        "name": "notification-service",
        "cmd":  [sys.executable, "main.py"],
        "cwd":  os.path.join(BASE, "backend", "notification-service"),
    },
    {
        "name": "dashboard-service",
        "cmd":  [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"],
        "cwd":  os.path.join(BASE, "backend", "dashboard-service"),
    },
]


def stream(proc, name):
    color = COLORS.get(name, "")
    for line in iter(proc.stdout.readline, b""):
        print(f"{color}[{name}]{RESET}  {line.decode(errors='replace').rstrip()}", flush=True)


processes = []


def shutdown(sig=None, frame=None):
    print(f"\n{RESET}Stopping all services...")
    for p in processes:
        p.terminate()
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown)
try:
    signal.signal(signal.SIGTERM, shutdown)
except AttributeError:
    pass  # SIGTERM not available on Windows in some environments

print("Starting all services...\n")

for svc in SERVICES:
    proc = subprocess.Popen(
        svc["cmd"],
        cwd=svc["cwd"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    processes.append(proc)

    thread = threading.Thread(target=stream, args=(proc, svc["name"]), daemon=True)
    thread.start()

    color = COLORS.get(svc["name"], "")
    print(f"{color}[{svc['name']}]{RESET}  started  (pid {proc.pid})")

print("\nAll services running. Ctrl+C to stop all.\n")
print("-" * 50)

for p in processes:
    p.wait()
