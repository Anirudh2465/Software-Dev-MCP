import math

def factorial_calc(input_str: str) -> str:
    """
    Calculates the factorial of a non-negative integer provided as an input string.
    
    Parameters
    ----------
    input_str : str
        A string representation of a non-negative integer.
    
    Returns
    -------
    str
        The factorial result converted to a string.
    
    Raises
    ------
    ValueError
        If the input string does not represent a non-negative integer.
    """
    # Validate and convert input to an integer
    try:
        n = int(input_str)
    except (TypeError, ValueError):
        raise ValueError("Input must be a string representing an integer.")
    
    if n < 0:
        raise ValueError("Factorial is not defined for negative integers.")
    
    # Compute factorial using the math module
    result = math.factorial(n)
    
    return str(result)