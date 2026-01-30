# REQUIREMENTS: 
import csv
import random
import string

def create_csv(file_name: str, columns: list[str], num_rows: int) -> dict:
    """
    Generate a CSV file with the specified columns and number of rows containing random data.
    
    Parameters:
        file_name (str): Name (including path if desired) for the generated CSV file.
        columns (list[str]): List of column headers to include in the CSV.
        num_rows (int): Number of data rows to generate.

    Returns:
        dict: JSON-serializable dictionary containing the path to the created CSV and a status message.
    """
    def _random_string(length=8):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    with open(file_name, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(columns)
        for _ in range(num_rows):
            row = [_random_string() for _ in columns]
            writer.writerow(row)

    return {"file_path": file_name, "status": f"CSV with {num_rows} rows created successfully."}