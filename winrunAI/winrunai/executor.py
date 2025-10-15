import subprocess
import os
import tempfile
from pathlib import Path

def execute_action_plan(action_plan: dict, callback):
    """
    Executes a given action plan.
    """
    wineprefix = action_plan.get('wineprefix')
    if not wineprefix:
        callback("Execution failed: WINEPREFIX not specified in the action plan.")
        return

    callback(f"Executing action for WINEPREFIX: {wineprefix}")
    success = False

    for i, action in enumerate(action_plan.get('actions', [])):
        tool = action.get('tool')
        argument = action.get('argument')

        callback(f"Step {i+1}/{len(action_plan['actions'])}: Running '{tool}' with argument '{argument}'...")

        exec_env = os.environ.copy()
        exec_env['WINEPREFIX'] = wineprefix

        if tool == 'winetricks':
            command = ['winetricks', '-q', argument]
        elif tool == 'regedit':
            # For regedit, the argument is the content of the .reg file
            # e.g., "[HKEY_CURRENT_USER\\Software\\Wine\\Direct3D]\\n\"csmt\"=\"enabled\""
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.reg', delete=False) as reg_file:
                    reg_file.write("REGEDIT4\n\n") # Standard .reg file header
                    reg_file.write(argument)
                    temp_reg_path = reg_file.name

                # The /S switch imports the file silently
                command = ['regedit', '/S', temp_reg_path]
            except Exception as e:
                callback(f"Error creating temporary registry file: {e}")
                success = False
                break
        else:
            callback(f"Warning: Unknown tool type '{tool}' in action plan. Skipping.")
            continue

        try:
            process = subprocess.Popen(
                command,
                env=exec_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            for line in iter(process.stdout.readline, ''):
                callback(f"  [{tool}] {line.strip()}")

            process.stdout.close()
            return_code = process.wait()

            if return_code == 0:
                callback(f"Command '{tool} {argument.splitlines()[0]}' completed successfully.")
                success = True
            else:
                callback(f"Command '{tool} {argument.splitlines()[0]}' failed with exit code {return_code}.")
                success = False
                break

        except FileNotFoundError:
            callback(f"Error: '{command[0]}' command not found. Please make sure it is installed and in your PATH.")
            success = False
            break
        except Exception as e:
            callback(f"An unexpected error occurred while running {tool}: {e}")
            success = False
            break
        finally:
            # Clean up the temp reg file if it exists
            if tool == 'regedit' and 'temp_reg_path' in locals() and os.path.exists(temp_reg_path):
                os.unlink(temp_reg_path)

    if success:
        callback("[bold green]Action plan completed successfully. Please RESTART the Windows application for changes to take effect.[/bold green]")
