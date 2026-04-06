import requests
from typing import List

def get_synonyms(word: str) -> List[str]:
    """
    Use the Datamuse API to retrieve a list of synonyms.
    This is a public API and does not require an API key for basic usage.
    
    Args:
        word (str): The English word to find synonyms for.
        
    Returns:
        List[str]: A list of synonyms.
    """
    # Datamuse endpoint: rel_syn is used to find synonyms
    api_url = f"https://api.datamuse.com/words?rel_syn={word}"

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        # The response format: [{"word": "cheerful", "score": 1234}, ...]
        data = response.json()
        
        # Extract only the word field from the results
        synonyms = [item['word'] for item in data]
        
        return synonyms

    except requests.exceptions.RequestException as e:
        print(f"API connection error: {e}")
        return []