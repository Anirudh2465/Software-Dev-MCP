
import subprocess
import asyncio

def _run_ps_dialog():
    """
    Synchronous function to run the PowerShell dialog.
    """
    ps_script = """
    Add-Type -AssemblyName System.Windows.Forms
    $f = New-Object System.Windows.Forms.FolderBrowserDialog
    $f.Description = 'Select a directory to monitor'
    $f.ShowNewFolderButton = $true
    $result = $f.ShowDialog()
    if ($result -eq 'OK') {
        Write-Output $f.SelectedPath
    }
    """
    try:
        # Use STARTUPINFO to hide the console window created by PowerShell
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            startupinfo=startupinfo
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception as e:
        print(f"Error opening dialog: {e}")
    return None

async def open_folder_dialog():
    """
    Opens a Windows Folder Browser Dialog via PowerShell and returns the selected path.
    Uses asyncio.to_thread to run the synchronous subprocess call without blocking the loop,
    and avoids asyncio.create_subprocess_shell compatibility issues on Windows.
    """
    return await asyncio.to_thread(_run_ps_dialog)
