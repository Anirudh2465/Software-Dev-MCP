# REQUIREMENTS: requests
import requests

def get_associations(word: str) -> str:
    """
    Find related words and associations (triggers, adjectives, etc).
    """
    try:
        # rel_trg: "Triggers" (words often associated with the target)
        # rel_jjb: "Adjectives" modifying the noun
        url = f"https://api.datamuse.com/words?rel_trg={word}&max=10"
        response = requests.get(url, timeout=5)
        triggers = [item["word"] for item in response.json()]
        
        url_adj = f"https://api.datamuse.com/words?rel_jjb={word}&max=10"
        response_adj = requests.get(url_adj, timeout=5)
        adjectives = [item["word"] for item in response_adj.json()]
        
        output = f"Associations for '{word}':\n"
        if triggers:
            output += f"- Related: {', '.join(triggers)}\n"
        if adjectives:
            output += f"- Described as: {', '.join(adjectives)}"
            
        if not triggers and not adjectives:
            return f"No strong associations found for '{word}'."
            
        return output
        
    except Exception as e:
        return f"Error finding associations: {str(e)}"
