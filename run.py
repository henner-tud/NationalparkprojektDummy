import subprocess
import time
import webbrowser
import signal
import sys
import threading
import os

processes = []
shutdown_event = threading.Event()

def start_process(command):
    proc = subprocess.Popen(command)
    processes.append(proc)
    return proc

def stop_processes():
    if shutdown_event.is_set():
        return  # Already shutting down
    shutdown_event.set()
    os.write(sys.stdout.fileno(), b"\nShutting down processes...\n")
    for proc in processes:
        if proc.poll() is None:
            proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.write(sys.stdout.fileno(), f"Process {proc.pid} unresponsive, killing...\n".encode())
                proc.kill()
    os.write(sys.stdout.fileno(), b"All processes stopped.\n")
    sys.exit(0)

def wait_for_enter():
    try:
        input("Press Enter to exit...\n")
        stop_processes()
    except EOFError:
        stop_processes()

if __name__ == "__main__":
    print("\n" + "="*50)
    print("National Park Project Dummy")
    print("="*50 + "\n")
    print("Starting services...\n")

    print("Starting FastAPI server...")
    start_process([
        sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"
    ])
    time.sleep(2)

    print("Starting Streamlit application...")
    start_process([
        sys.executable, "-m", "streamlit", "run", "frontend/app.py",
        "--server.port=8501",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false"
    ])

    time.sleep(3)

    #webbrowser.open("http://localhost:8501")

    wait_thread = threading.Thread(target=wait_for_enter, daemon=True)
    wait_thread.start()
    wait_thread.join()
