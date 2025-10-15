from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, RichLog
from textual.containers import Container
from textual.events import Mount
import os
import json

from .service import start_service, stop_service, is_service_running, LOG_FILE, STATUS_FILE

class WinRunAIApp(App):
    """A Textual app to manage WinRunAI."""

    CSS_PATH = "winrunai.css"

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.log_file_position = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Container(id="app-grid"):
            with Container(id="left-pane"):
                yield Static("Menu", id="menu-title")
                yield Button("Enable AI", id="enable-ai", variant="success")
                yield Button("Disable AI", id="disable-ai", variant="error")
                yield Button("Configuration", id="config", disabled=True)
                yield Button("Exit", id="exit")
            with Container(id="right-pane"):
                yield Static("Status: Unknown", id="status-display")
                yield Static("Monitored Processes: None", id="proc-display") # New widget
                yield RichLog(id="log-viewer", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        """Called when the app is first mounted."""
        self.update_status_display()
        log_viewer = self.query_one("#log-viewer")
        log_viewer.write("[bold cyan]Welcome to WinRunAI![/bold cyan]")
        log_viewer.write("Enable the AI to begin monitoring Wine processes.")

        # Start timers to update logs and process list
        self.set_interval(1.0, self.tail_log_file)
        self.set_interval(2.0, self.update_monitored_processes)

    def update_monitored_processes(self) -> None:
        """Reads the status file and updates the process display widget."""
        proc_widget = self.query_one("#proc-display")
        if not is_service_running():
            proc_widget.update("Monitored Processes: None")
            return

        try:
            with open(STATUS_FILE, 'r') as f:
                procs = json.load(f)

            if not procs:
                proc_widget.update("Monitored Processes: None")
            else:
                proc_names = [f"{os.path.basename(p['cmdline'].split()[0])} (PID: {p['pid']})" for p in procs]
                proc_widget.update(f"Monitored Processes: [bold yellow]{', '.join(proc_names)}[/bold yellow]")

        except (FileNotFoundError, json.JSONDecodeError):
            proc_widget.update("Monitored Processes: None")

    def tail_log_file(self) -> None:
        """Read new lines from the service log file and display them."""
        log_viewer = self.query_one("#log-viewer")
        try:
            with open(LOG_FILE, "r") as f:
                f.seek(self.log_file_position)
                new_lines = f.readlines()
                if new_lines:
                    for line in new_lines:
                        log_viewer.write(line.strip())
                    self.log_file_position = f.tell()
        except FileNotFoundError:
            pass

    def update_status_display(self) -> None:
        status_widget = self.query_one("#status-display")
        if is_service_running():
            status_widget.update("Status: [bold green]AI Enabled[/bold green]")
        else:
            status_widget.update("Status: [bold red]AI Disabled[/bold red]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log_viewer = self.query_one("#log-viewer")
        if event.button.id == "enable-ai":
            log_viewer.write("Attempting to enable AI service...")
            start_service(self)
        elif event.button.id == "disable-ai":
            log_viewer.write("Attempting to disable AI service...")
            stop_service(self)
        elif event.button.id == "exit":
            if is_service_running():
                log_viewer.write("Stopping AI service before exiting...")
                stop_service(self)
            self.exit()

        self.update_status_display()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark
