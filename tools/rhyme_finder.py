# REQUIREMENTS: requests
import requests

def find_rhymes(word: str) -> str:
    """
    Find rhyming words.
    """
    try:
        url = f"https://api.datamuse.com/words?rel_rhy={word}&max=15"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if not data:
            return f"No rhymes found for '{word}'."
            
        rhymes = [item["word"] for item in data]
        return f"Rhymes for '{word}': " + ", ".join(rhymes)
        
    except Exception as e:
        return f"Error finding rhymes: {str(e)}"
