import os

def search_files(query: str, path: str = ".") -> str:
    """
    Search for a string or pattern in files within a directory (recursive).
    Simple case-insensitive string matching.
    """
    results = []
    try:
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist."
            
        for root, _, files in os.walk(path):
            if ".git" in root or "__pycache__" in root or "node_modules" in root or ".venv" in root:
                continue
                
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".html", ".css", ".md", ".json", ".txt", ".toml")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            lines = f.readlines()
                            for i, line in enumerate(lines):
                                if query.lower() in line.lower():
                                    # limit line length for output
                                    clean_line = line.strip()[:200]
                                    results.append(f"{file_path}:{i+1}: {clean_line}")
                                    if len(results) >= 50: # Limit results
                                        return "\n".join(results) + "\n... (more results truncated)"
                    except Exception:
                        continue
                        
        return "\n".join(results) if results else "No matches found."
        
    except Exception as e:
        return f"Error searching files: {str(e)}"
