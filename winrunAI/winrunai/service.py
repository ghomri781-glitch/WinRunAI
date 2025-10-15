import os
import sys
import time
import subprocess
import psutil
import threading
import json
from pathlib import Path

from .monitor import find_wine_processes_iter
from .engine import AIEngine
from .analyzer import analyze_process
from .config import config

PID_FILE = Path(os.environ.get("TMPDIR", "/tmp")) / "winrunai.pid"
LOG_FILE = Path(os.environ.get("TMPDIR", "/tmp")) / "winrunai_service.log"
STATUS_FILE = Path(os.environ.get("TMPDIR", "/tmp")) / "winrunai_status.json"

def is_service_running():
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text())
        return psutil.pid_exists(pid)
    except (ValueError, psutil.NoSuchProcess):
        return False

def start_service(tui_app=None):
    if is_service_running():
        if tui_app:
            tui_app.query_one("#status-display").update("Status: AI is already running.")
        return

    command = [sys.executable, "-m", "winrunai.main", "--service"]
    process = subprocess.Popen(command, start_new_session=True)
    PID_FILE.write_text(str(process.pid))

    if tui_app:
        tui_app.query_one("#status-display").update("Status: AI Enabled")
        tui_app.query_one("#log-viewer").write("AI service started...")

def stop_service(tui_app=None):
    if not PID_FILE.exists():
        if tui_app:
            tui_app.query_one("#status-display").update("Status: AI is already stopped.")
        return

    try:
        pid = int(PID_FILE.read_text())
        if psutil.pid_exists(pid):
            p = psutil.Process(pid)
            p.terminate()
            p.wait(timeout=3)
    except (ValueError, psutil.NoSuchProcess):
        pass
    except psutil.TimeoutExpired:
        p.kill()

    PID_FILE.unlink(missing_ok=True)
    STATUS_FILE.unlink(missing_ok=True) # Clean up status file on stop

    if tui_app:
        tui_app.query_one("#status-display").update("Status: AI Disabled")
        tui_app.query_one("#log-viewer").write("AI service stopped.")

def run_monitor_loop():
    """The main loop for the background service."""
    engine = AIEngine()
    analyzed_procs = {} # Using a dict to store full process info {pid: proc_info}
    scan_interval = config.get('service', {}).get('scan_interval', 5)

    with open(LOG_FILE, "w") as f:
        def log_callback(message):
            f.write(f"[{time.ctime()}] {message}\n")
            f.flush()

        log_callback(f"WinRunAI Service Log Initialized. Scan interval: {scan_interval}s.")

        while True:
            found_processes = list(find_wine_processes_iter())
            current_pids = {p['pid'] for p in found_processes}

            for proc_info in found_processes:
                pid = proc_info['pid']
                if pid not in analyzed_procs:
                    proc_name = Path(proc_info.get('cmdline', ['unknown'])[0]).name
                    log_callback(f"[bold green]New application detected: {proc_name} (PID: {pid}). AI monitoring is now active.[/bold green]")
                    analyzed_procs[pid] = proc_info

                    analysis_thread = threading.Thread(
                        target=analyze_process,
                        args=(proc_info, engine, log_callback)
                    )
                    analysis_thread.start()

            # Clean up terminated processes from our dict
            terminated_pids = set(analyzed_procs.keys()) - current_pids
            for pid in terminated_pids:
                del analyzed_procs[pid]

            # Update the status file
            try:
                status_data = [
                    {"pid": p['pid'], "cmdline": " ".join(p.get('cmdline', []))}
                    for p in analyzed_procs.values()
                ]
                with open(STATUS_FILE, 'w') as sf:
                    json.dump(status_data, sf)
            except Exception as e:
                log_callback(f"Error writing status file: {e}")

            time.sleep(scan_interval)
