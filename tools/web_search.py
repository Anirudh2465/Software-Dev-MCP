# REQUIREMENTS: duckduckgo-search
from duckduckgo_search import DDGS

def web_search(query: str) -> str:
    """
    Search the web for a given query.
    """
    try:
        results = DDGS().text(query, max_results=5)
        if not results:
            return "No results found."
        
        formatted_results = []
        for r in results:
            formatted_results.append(f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n")
        
        return "\n".join(formatted_results)
    except Exception as e:
        return f"Error performing web search: {str(e)}"
