import requests
import os

def scrape_url(url: str = None, **kwargs) -> str:
    """
    Extracts text content from a web page URL.
    Attempts to use the free Jina Reader API (https://r.jina.ai/) for clean markdown,
    and falls back to standard HTTP requests and BeautifulSoup parsing if Jina is unavailable.
    """
    if not url:
        url = kwargs.get("uri") or kwargs.get("link") or kwargs.get("query")
        
    if not url or not str(url).strip():
        return "Error: 'url' argument is required for scrape_url. Please specify the URL to scrape, e.g., {'url': 'https://example.com'}."
        
    url = str(url).strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        return "Error: Invalid URL. URL must start with http:// or https://"

    # Method 1: Jina Reader API (recommended for LLM agents)
    jina_url = f"https://r.jina.ai/{url}"
    try:
        response = requests.get(jina_url, timeout=15)
        if response.status_code == 200:
            content = response.text
            # Return first 10,000 characters to prevent prompt bloat
            if len(content) > 10000:
                return content[:10000] + "\n\n[Content truncated due to size...]"
            return content
    except Exception as e:
        print(f"[Warning] Jina Reader API failed for {url}: {e}. Trying standard scraper.")

    # Method 2: BeautifulSoup extraction fallback
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return f"Error: Failed to fetch the URL, status code {response.status_code}"
            
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Strip script, style, nav, footer
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
            
        text = soup.get_text()
        # Clean whitespaces
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = "\n".join(chunk for chunk in chunks if chunk)
        
        if len(clean_text) > 8000:
            return clean_text[:8000] + "\n\n[Content truncated due to size...]"
        return clean_text
    except Exception as e:
        return f"Error: Scraper fallback failed for URL '{url}': {e}"
