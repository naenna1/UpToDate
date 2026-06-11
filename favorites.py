from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import webbrowser, requests, json, os, time
def fmt_time(iso_str: str) -> str:
    """
    Format an ISO timestamp into a human-readable date and time string.
    
    Args:
        iso_str (str): ISO 8601 formatted timestamp (e.g., '2023-10-01T12:00:00Z')
    
    Returns:
        str: Formatted date and time string (e.g., '01.10.2023 14:00')
    """
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00")).astimezone(ZoneInfo("Europe/Berlin"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception as e:
        
        return iso_str or ""

def _favorites_path():
    """
    Get the file path for storing favorites data.
    
    Returns:
        Path: A Path object pointing to the favorites JSON file location
    """
    try:
        home = Path.home()
        path = home / ".news_app" / "favorites.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    except Exception:
        return Path(__file__).with_name("favorites.json")

def ensure_favorites_file():
    """
    Ensure that the favorites file exists, creating it with an empty array if needed.
    """
    path = _favorites_path()
    if not path.exists():
        path.write_text("[]", encoding="UTF-8")

def load_favorites():
    """
    Load favorite articles from the favorites JSON file.
    
    Returns:
        list: List of article dictionaries saved as favorites
    """
    ensure_favorites_file()
    path = _favorites_path()
    try:
        return json.loads(path.read_text(encoding="UTF-8"))
    except json.JSONDecodeError:
        path.write_text("[]", encoding="UTF-8")
        return []

def save_favs(items: list):
    """
    Save a list of favorite articles to the favorites JSON file.
    
    Args:
        items (list): List of article dictionaries to save
    """
    path = _favorites_path()
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="UTF-8")

def add_fav(item: dict):
    """
    Add a new article to favorites.
    
    Args:
        item (dict): Article dictionary to add to favorites
    """
    favs = load_favorites()
    favs.append(item)
    save_favs(favs)

def remove_favs(index: int) -> bool:
    """
    Remove an article from favorites by its index.
    
    Args:
        index (int): Index of the article to remove
    
    Returns:
        bool: True if removal was successful, False if index was out of range
    """
    favs = load_favorites()
    if 0 <= index < len(favs):
        favs.pop(index)
        save_favs(favs)
        return True
    return False

def list_favs() -> list:
    """
    Get a list of all favorite articles.
    
    Returns:
        list: List of article dictionaries saved as favorites
    """
    return load_favorites()

def main():
    print(fmt_time("2023-10-01T12:00:00Z"))  # Example usage

if __name__ == "__main__":
    main()