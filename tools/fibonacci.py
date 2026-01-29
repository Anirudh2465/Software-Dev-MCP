def fibonacci(n_str: str) -> str:
    """
    Calculates the nth Fibonacci number. 0-indexed (F0=0, F1=1).
    Input should be a string representing an integer.
    """
    try:
        n = int(float(n_str))
    except ValueError:
        return "Error: Input must be a valid integer."
        
    if n < 0:
        return "Error: Input must be non-negative."
    
    if n == 0: return "0"
    if n == 1: return "1"
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return str(b)
