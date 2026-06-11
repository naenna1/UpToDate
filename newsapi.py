import requests
from dotenv import load_dotenv
import os
load_dotenv()
API_KEY = os.getenv('API_KEY')  # set API_KEY=your_key in a .env file (see .env.example)
url = 'https://newsapi.org/v2/top-headlines'

def get_news_category(category:str):
    """
    Fetch top headlines from NewsAPI for a specific category.
    
    Args:
        category (str): The news category to fetch (e.g., 'business', 'sports', 'technology')
    
    Returns:
        list: A list of article dictionaries containing news data, or None if request fails
    """
   
    # Set up the endpoint and parameters
    
    params = {'category': category,
        'apiKey': API_KEY
    }

    # Make the request
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        articles = data['articles']
        return articles

def search_news(word, category):
    """
    Search for news articles within a specific category using a search query.
    
    Args:
        word (str): The search term/query to look for in articles
        category (str): The news category to search within
    
    Returns:
        list: A list of article dictionaries matching the search criteria, or None if request fails
    """
    
    params = {'category': category,
        'apiKey': API_KEY,
        'q': word  # Search query
    }

    # Make the request
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        articles = data['articles']
        return articles
    
def clean_headline(headline):
    """
    Clean and format a news headline for better display.
    
    Removes leading/trailing whitespace, normalizes spacing, strips unwanted characters,
    capitalizes words (except those already in uppercase), and removes trailing source information.
    
    Args:
        headline (str): Raw headline text to be cleaned
    
    Returns:
        str: Cleaned and formatted headline text
    
    Examples:
        >>> clean_headline("'hello' World USA! - BBC  ")
        "'Hello' World USA!"
    """
    headline = headline.strip()
    headline = ' '.join([word.strip() for word in headline.split()])  # Replace multiple spaces with a single space
                                    
    for x in r'&:\/*@':
        headline = headline.removeprefix(x)
        headline = headline.removesuffix(x)

    words = headline.rsplit()
    headline_xx = [wort.strip() if wort.isupper() else wort.capitalize() for wort in words] #capitalize every word, but only if it is not already in uppercase
    headline = ' '.join(headline_xx)
    headline = ' '.join(headline.split('-')[:-1])  # remove source name at the end
    return headline

def main():
    print(clean_headline("'hello' World USA! - BBC  "))  # Example usage

if __name__ == "__main__":
    main()
