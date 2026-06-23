import os
from src.config import OUTPUT_DIR

def search_kaggle_datasets(query: str = None, max_results: int = 5, **kwargs) -> str:
    """
    Searches Kaggle for datasets matching the query.
    Returns details of matching datasets, including their unique IDs (ref).
    """
    if not query:
        query = kwargs.get("q") or kwargs.get("location") or kwargs.get("ticker") or kwargs.get("symbol")
        
    if not query or not str(query).strip():
        return "Error: 'query' argument is required for search_kaggle_datasets. Please specify the query string, e.g., {'query': 'retail sales'}."
        
    query = str(query).strip()
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")
    
    if not username or not key or "your_" in username:
        return (
            "Kaggle API credentials are not set in the .env file.\n"
            "To resolve:\n"
            "1. Go to kaggle.com -> Profile -> Settings.\n"
            "2. Scroll down and click 'Create New API Token' (downloads kaggle.json).\n"
            "3. Paste KAGGLE_USERNAME and KAGGLE_KEY values into your .env file.\n"
            "Alternatively, prompt the agent to search and scrape data from Google."
        )
        
    try:
        # Import dynamically so it does not fail if client installation is delayed
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        
        datasets = api.dataset_list(search=query)
        if not datasets:
            return f"No Kaggle datasets found for search term: '{query}'."
            
        summary = [f"Kaggle Dataset Search Results for '{query}':"]
        for idx, ds in enumerate(datasets[:max_results]):
            summary.append(
                f"{idx+1}. Dataset ID (Ref): {ds.ref}\n"
                f"   Title: {ds.title}\n"
                f"   Size: {ds.size}\n"
                f"   Downloads: {ds.downloadCount}\n"
                f"   URL: https://www.kaggle.com/datasets/{ds.ref}\n"
            )
        return "\n".join(summary)
    except Exception as e:
        return f"Error while searching Kaggle datasets: {e}"

def download_kaggle_dataset(dataset_id: str = None, **kwargs) -> str:
    """
    Downloads and extracts all files from a Kaggle dataset (by its ID, e.g., 'zsingh/retail-dataset')
    directly into the project output/ folder.
    """
    if not dataset_id:
        dataset_id = kwargs.get("dataset") or kwargs.get("dataset_ref") or kwargs.get("query")
        
    if not dataset_id or not str(dataset_id).strip():
        return "Error: 'dataset_id' argument is required for download_kaggle_dataset. Please specify the dataset ID, e.g., {'dataset_id': 'zsingh/retail-dataset'}."
        
    dataset_id = str(dataset_id).strip()
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")
    
    if not username or not key:
        return "Kaggle API credentials not configured."
        
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        
        # Download files and extract automatically to OUTPUT_DIR
        api.dataset_download_files(dataset_id, path=OUTPUT_DIR, unzip=True)
        
        # List downloaded files
        downloaded = os.listdir(OUTPUT_DIR)
        
        return (
            f"Successfully downloaded and extracted Kaggle dataset '{dataset_id}' to: {OUTPUT_DIR}\n"
            f"Files in output folder: {downloaded}"
        )
    except Exception as e:
        return f"Error downloading Kaggle dataset '{dataset_id}': {e}"
