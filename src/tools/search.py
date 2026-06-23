import os
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools import DuckDuckGoSearchRun

def web_search(query: str = None, max_results: int = 5, **kwargs) -> str:
    """
    Searches the web for the given query.
    Tries Tavily search API if TAVILY_API_KEY is configured.
    Otherwise, falls back to DuckDuckGo search.
    """
    if not query:
        query = kwargs.get("q") or kwargs.get("location") or kwargs.get("ticker") or kwargs.get("symbol")
        
    if not query or not str(query).strip():
        return "Error: 'query' argument is required for web_search. Please specify the search query, e.g., {'query': 'latest stock market news'}."
        
    query = str(query).strip()
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key and tavily_key.strip():
        try:
            api_wrapper = TavilySearchAPIWrapper(tavily_api_key=tavily_key)
            search = TavilySearchResults(api_wrapper=api_wrapper, max_results=max_results)
            results = search.run(query)
            
            # Format results into a single string
            if isinstance(results, list):
                formatted = []
                for idx, r in enumerate(results):
                    url = r.get("url", "No URL")
                    content = r.get("content", "")
                    formatted.append(f"Result {idx+1}:\nURL: {url}\nContent: {content}\n")
                return "\n".join(formatted)
            return str(results)
        except Exception as e:
            print(f"[Warning] Tavily search failed: {e}. Falling back to DuckDuckGo.")
            
    # Fallback to DuckDuckGo Search
    try:
        ddg = DuckDuckGoSearchRun()
        return ddg.run(query)
    except Exception as e:
        return f"Error: Search failed because of configuration or connection issues. Details: {e}"
