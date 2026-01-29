import subprocess

def _run_git(args: list) -> str:
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return f"Git Error: {result.stderr.strip()}"
        return result.stdout.strip()
    except Exception as e:
        return f"Error executing git: {str(e)}"

def git_status() -> str:
    """
    Get the current git status.
    """
    return _run_git(["status"])

def git_log(n: int = 5) -> str:
    """
    Get the last n commits.
    """
    return _run_git(["log", f"-n {n}", "--oneline"])

def git_diff() -> str:
    """
    Get the current diff (unstaged changes).
    """
    return _run_git(["diff"])
