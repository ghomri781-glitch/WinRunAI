# WinRunAI - AI-Powered Wine Enhancement Layer

WinRunAI is an intelligent, terminal-based enhancement layer for Wine on Linux. It acts as an AI-driven compatibility assistant that runs as a background service, intelligently analyzes Windows application requirements, and automatically resolves compatibility issues in real-time to enable seamless execution of Windows applications on Linux systems.

## Core Features

*   **Intelligent AI Engine:** Automatically detects common errors in Wine logs (e.g., missing DLLs, required components) and suggests fixes.
*   **Automatic Fix Execution:** Applies required fixes using `winetricks` when a high-confidence solution is found.
*   **Terminal UI (TUI):** A clean, minimalist, menu-driven interface to enable, disable, and monitor the AI service.
*   **Non-Intrusive Monitoring:** Seamlessly attaches to any running Wine process without requiring you to change how you launch your applications.
*   **Configurable:** A simple `config.yml` file allows you to tweak settings like the confidence threshold for applying fixes.

## Installation

### Prerequisites

*   Python 3.10+
*   `pip`
*   `winetricks` must be installed and available in your system's PATH.
*   A functioning Wine installation.

### Setup

1.  **Clone the repository (or download the source code):**
    ```bash
    git clone <repository_url>
    cd winrunai
    ```

2.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Launch the WinRunAI Terminal UI:**
    From inside the `winrunai` directory, run:
    ```bash
    python -m winrunai.main
    ```

2.  **Enable the AI Service:**
    Inside the TUI, click the "Enable AI" button. The status will change to "AI Enabled", and the background monitoring service will start.

3.  **Run a Windows Application:**
    In a *different* terminal, launch any Windows application using Wine as you normally would.
    ```bash
    wine /path/to/your/application.exe
    ```

4.  **Monitor the AI:**
    Observe the "Logs" panel in the WinRunAI TUI.
    *   WinRunAI will automatically detect the running Wine process.
    *   It will attach to the process's log output and analyze it for errors in real-time.
    *   If a known error is found, the AI will suggest a fix.
    *   If the fix confidence is above the configured threshold, it will automatically run `winetricks` to apply the fix.

5.  **Apply Fixes:**
    After a fix is applied, WinRunAI will log a message advising you to restart the Windows application for the changes to take effect.

## Configuration

You can customize WinRunAI's behavior by editing the `winrunai/winrunai/config.yml` file.

*   `auto_apply_confidence_threshold`: The confidence score (from 0.0 to 1.0) required for the AI to apply a fix without asking for confirmation. The default is `0.9` (90%). Set this to `1.1` to disable automatic fixes entirely and always require manual confirmation (once that feature is implemented).

## How It Works

WinRunAI's service manager runs a background loop that uses `psutil` to scan for active `wineserver` processes. When a new process is found, the analyzer attaches to its standard error stream by reading from `/proc/<pid>/fd/2`. This non-intrusive method allows WinRunAI to see the same `WINEDEBUG` log output you would see in a terminal, without re-launching or interfering with the application. Error lines are passed to a rule-based AI engine, which queries an SQLite knowledge base for a known fix. If one is found, the executor module applies it using `winetricks`.
