import random

def generate_random_matrix() -> str:
    """
    Generate a 3x3 matrix with random integers between 0 and 9.

    Returns:
        A JSON-serializable dictionary containing the generated matrix.
    """
    matrix = [[random.randint(0, 9) for _ in range(3)] for _ in range(3)]
    return {"matrix": matrix}