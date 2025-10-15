import psutil
import os

def get_wine_prefix_from_environ(environ):
    """Extracts the WINEPREFIX from a process's environment variables."""
    return environ.get("WINEPREFIX", os.path.expanduser("~/.wine"))

def find_wine_processes_iter():
    """
    A generator that yields information about running Wine processes.

    Yields:
        dict: A dictionary containing 'pid', 'cmdline', 'environ', and 'wineprefix'.
    """
    # Look for 'wineserver' as it's the parent process for a Wine session.
    # This is more reliable than looking for 'wine' which might be a short-lived process.
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'environ']):
        try:
            # Check if process name is 'wineserver' or a 'wine' related process
            if proc.info['name'] and ('wine' in proc.info['name'].lower() or 'wineserver' in proc.info['name'].lower()):

                # We need the environment to determine the WINEPREFIX
                proc_environ = proc.info.get('environ')
                if not proc_environ:
                    # Fallback for processes where we can't get environ directly
                    try:
                        # On Linux, /proc/{pid}/environ can be read
                        with open(f"/proc/{proc.pid}/environ", "r") as f:
                            proc_environ = dict(line.strip().split('=', 1) for line in f if '=' in line)
                    except (IOError, FileNotFoundError):
                        proc_environ = {} # Could not get environment

                wine_prefix = get_wine_prefix_from_environ(proc_environ)

                yield {
                    'pid': proc.info['pid'],
                    'cmdline': proc.info['cmdline'],
                    'environ': proc_environ,
                    'wineprefix': wine_prefix,
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process might have terminated or we don't have permission to access it
            continue

if __name__ == '__main__':
    # Example usage:
    print("Searching for running Wine processes...")
    found_processes = list(find_wine_processes_iter())

    if not found_processes:
        print("No Wine processes found.")
    else:
        for proc_data in found_processes:
            print(f"  - PID: {proc_data['pid']}")
            print(f"    Cmdline: {' '.join(proc_data['cmdline'])}")
            print(f"    WINEPREFIX: {proc_data['wineprefix']}")
            print("-" * 20)
