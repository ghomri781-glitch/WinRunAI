import os
import fcntl
import time
import psutil
from .engine import AIEngine
from .executor import execute_action_plan
from .config import config

def make_non_blocking(fd):
    """Make a file descriptor non-blocking."""
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

def analyze_process(proc_info: dict, engine: AIEngine, callback):
    """
    Analyzes a detected Wine process by attaching to its stderr stream to capture logs.
    """
    pid = proc_info['pid']
    wineprefix = proc_info['wineprefix']
    cmdline = ' '.join(proc_info.get('cmdline', ['unknown']))

    callback(f"Starting analysis for running process: PID {pid} ({cmdline})")
    callback(f"Using WINEPREFIX: {wineprefix}")

    stderr_path = f"/proc/{pid}/fd/2"

    try:
        # Check if we can access the process's stderr
        if not os.access(stderr_path, os.R_OK):
            callback(f"Warning: No permission to read logs from PID {pid}. This can happen with sandboxed apps (Flatpak, Snap) or processes run by another user.")
            return

        with open(stderr_path, 'r', encoding='utf-8', errors='replace') as stderr_stream:
            make_non_blocking(stderr_stream.fileno())
            callback(f"Successfully attached to log stream for PID {pid}.")

            already_fixed = set()
            auto_apply_threshold = config.get('ai_engine', {}).get('auto_apply_confidence_threshold', 0.9)

            # Loop as long as the process is running
            while psutil.pid_exists(pid):
                line = stderr_stream.readline()
                if line and "err:" in line:
                    callback(f"Log Error (PID {pid}): {line.strip()}")

                    suggestion = engine.get_suggestion(line, wineprefix)

                    if suggestion:
                        fix_id = (suggestion['actions'][0]['tool'], suggestion['actions'][0]['argument'])

                        if fix_id not in already_fixed:
                            callback("AI Suggestion Found!")
                            callback(suggestion['description'])

                            if suggestion['confidence'] >= auto_apply_threshold:
                                callback(f"Confidence ({suggestion['confidence']:.0%}) meets threshold (>{auto_apply_threshold:.0%}). Executing automatically...")
                                execute_action_plan(suggestion, callback)
                                already_fixed.add(fix_id)
                            else:
                                callback(f"Confidence ({suggestion['confidence']:.0%}) is below threshold. Manual confirmation would be required.")
                else:
                    # If no line, wait a bit to prevent a busy loop
                    time.sleep(0.5)

            callback(f"Process {pid} has terminated. Ending analysis.")

    except FileNotFoundError:
        callback(f"Process {pid} terminated before logs could be attached.")
    except Exception as e:
        callback(f"An unexpected error occurred during analysis of PID {pid}: {e}")
