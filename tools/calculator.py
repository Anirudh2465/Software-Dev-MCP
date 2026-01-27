import math

def calculate(expression: str) -> str:
    """
    Evaluate a mathematical expression safely.
    Supported: +, -, *, /, **, sqrt, sin, cos, tan, log, pi, e
    """
    allowed_names = {
        k: v for k, v in math.__dict__.items() if not k.startswith("__")
    }
    allowed_names.update({"abs": abs, "round": round, "min": min, "max": max})
    
    # Simple sanitization
    if "__" in expression or "import" in expression or "exec" in expression or "eval" in expression:
        return "Error: Unsafe expression detected."
        
    try:
        # Use eval with restricted globals/locals
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"Result: {result}"
    except Exception as e:
        return f"Error calculating: {str(e)}"
