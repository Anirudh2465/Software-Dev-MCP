import math

def calculate_factorial(input_str):
    """
    Calculates the factorial of a non‑negative integer provided as an input string.
    
    Parameters
    ----------
    input_str : str
        The string representation of a non‑negative integer.
    
    Returns
    -------
    str or dict
        If the computation is successful, returns the factorial as a string.
        If the input is invalid (not an integer or negative), returns a dictionary
        with an 'error' key describing the issue.
    """
    try:
        # Convert the input string to an integer
        number = int(input_str)
    except (ValueError, TypeError):
        return {"error": "input must be a valid integer string"}
    
    if number < 0:
        return {"error": "input must be a non-negative integer"}
    
    try:
        result = math.factorial(number)
    except OverflowError:
        return {"error": "result too large to compute"}
    
    return str(result)