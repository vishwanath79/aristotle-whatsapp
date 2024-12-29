"""
News fetching module for Aristotle WhatsApp bot.
Uses NewsAPI to fetch relevant news articles.
"""

import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def fetch_news(skeyword: str) -> Dict[str, Any]:
    """
    Fetch news articles based on a keyword search.
    
    Args:
        skeyword (str): The search keyword for news articles
        
    Returns:
        dict: JSON response containing news articles
        
    Raises:
        requests.RequestException: If the API request fails
    """
    try:
        from cred import news_api_key
        
        url = (
            f'https://newsapi.org/v2/everything'
            f'?q={skeyword}'
            f'&sortBy=popularity'
            f'&pageSize=5'
            f'&apiKey={news_api_key}'
        )
        
        response = requests.get(url)
        response.raise_for_status()
        
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch news: {str(e)}")
        return {"error": "Failed to fetch news articles"}
    except Exception as e:
        logger.error(f"Unexpected error while fetching news: {str(e)}")
        return {"error": "An unexpected error occurred"}

