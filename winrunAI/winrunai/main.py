import sys
from .tui import WinRunAIApp
from .service import run_monitor_loop, start_service, stop_service

def main():
    """Main entry point for the application."""
    if len(sys.argv) > 1 and sys.argv[1] == '--service':
        # This is the service process
        run_monitor_loop()
    else:
        # Launch the TUI
        app = WinRunAIApp()
        app.run()

if __name__ == "__main__":
    main()
