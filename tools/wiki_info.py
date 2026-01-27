# REQUIREMENTS: requests
import requests

def get_wiki_summary(topic: str) -> str:
    """
    Fetch a summary of a topic from Wikipedia.
    """
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic}"
        headers = {
            "User-Agent": "JarvisAgent/1.0 (https://github.com/your-repo; contact@example.com)"
        }
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 404:
            return f"Topic '{topic}' not found on Wikipedia. Try a more specific term."
        
        response.raise_for_status()
        data = response.json()
        
        title = data.get("title", topic)
        extract = data.get("extract", "No summary available.")
        
        return f"## {title}\n{extract}\n\n[Read more]({data.get('content_urls', {}).get('desktop', {}).get('page', '')})"
        
    except Exception as e:
        return f"Error fetching Wikipedia info: {str(e)}"
