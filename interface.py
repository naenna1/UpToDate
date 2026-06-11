import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
import webbrowser, requests, json, os, time
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
def create_tabs():
    """
    Create the main tab view with categories and search functionality.
    Each tab contains a search bar and a scrollable frame for news articles.
    
    Returns:
        dict: Dictionary mapping tab names to their scrollable frames
    """
    tabs = ctk.CTkTabview(app)
    tabs.pack(fill="both", expand=True)
    tab_frames = {}
    for name in [
        'General', 'Favorites', 'Business', 'Entertainment', 'Health', 'Science','Sports','Technology'
    ]:
        tab = tabs.add(name)
        search_var = ctk.StringVar(value="")
        search_entry = ctk.CTkEntry(tab, textvariable=search_var, placeholder_text="🔍 Search news...")
        search_entry.pack(pady=10, padx=10, fill="x")
        search_entry.bind("<Return>", lambda event, n=name, sv=search_var: filter_articles(sv.get(), 
                                                                                           n, tab_frames))
        sf = ctk.CTkScrollableFrame(tab)
        sf.pack(fill="both", expand=True, padx=6, pady=6)
        tab_frames[name] = sf
    return tab_frames


def render_favorites(tab_frames):
    """
    Display all favorite articles in the Favorites tab.
    Clears existing content and shows each favorite with Open/Delete buttons.
    
    Args:
        tab_frames (dict): Dictionary of tab frames containing the Favorites frame
    """
    frame = tab_frames["Favorites"]
    for w in frame.winfo_children():
        w.destroy()

    favs = list_favs()
    if not favs:
        ctk.CTkLabel(frame, text="Keine Favoriten gespeichert.").pack(pady=10)
        return

    for idx, art in enumerate(favs):
        row = ctk.CTkFrame(frame)
        row.pack(fill="x", padx=12, pady=8)
        
        row.grid_columnconfigure(0, weight=2)
        row.grid_columnconfigure(1, weight=2)
       # row.grid_columnconfigure(2, weight=1)

        title = art.get("title", "(ohne Titel)")
        src = (art.get("source") or "")
        ts = fmt_time(art.get("publishedAt", ""))

        ctk.CTkLabel(row, text=f"{title}\n\n{ts}   –   {src}", justify="left", wraplength=550, 
                     font = ('Roboto', 16, 'bold'))\
            .grid(row=0, column=0, rowspan=2, columnspan=2, sticky="w", padx=(10,6), pady=6)

        def open_url(u=art.get("url", "")):
            if u: webbrowser.open(u)

        ctk.CTkButton(row, text="Open", command=open_url).grid(row=0, column=1, 
                                                                 padx=(32,6), pady=6,
                                                                  sticky = 'e')
        ctk.CTkButton(row, text="Delete", fg_color="#aa3333",
                      command=lambda i=idx: (remove_favs(i), render_favorites(tab_frames)))\
            .grid(row=1, column=1, columnspan=1,padx=(6,), pady=6, sticky='e')


categories = ['General', 'Business', 'Entertainment', 'Health', 'Science','Sports','Technology']

start_time = time.time()
running = True


def load_categories(tab_frames):
    """
    Load and display news articles for all categories.
    Fetches articles from the API and creates NewsFrame widgets for each.
    
    Args:
        tab_frames (dict): Dictionary of tab frames to populate with articles
    """
    for category in categories:
        articles_category = get_news_category(category)
        for article in articles_category:
            frame = NewsFrame(
                tab_frames[f'{category}'],
                clean_headline(article.get("title", "(ohne Titel)")),
                article.get("url", ""),
                article.get("urlToImage", ""),
                fmt_time(article.get("publishedAt", "")),
                source=(article.get("source") or {}).get("name", ""),
                tab_frames=tab_frames
            )
            frame.pack(fill="both", expand=True)

def filter_articles(word, category, tab_frames):
    """
    Filter and display articles in a specific category based on a search word.
    Clears the category tab and shows only matching articles.
    
    Args:
        word (str): Search term to filter articles
        category (str): Category name to search within
        tab_frames (dict): Dictionary of tab frames
    """

    articles = search_news(word, category)
    # Erase all widgets from a frame
    for widget in tab_frames[f'{category}'].winfo_children():
        widget.destroy()
    for article in articles:
        frame = NewsFrame(
            tab_frames[f'{category}'],
            clean_headline(article.get("title", "(ohne Titel)")),
            article.get("url", ""),
            article.get("urlToImage", ""),
            fmt_time(article.get("publishedAt", "")),
            source=(article.get("source") or {}).get("name", ""),
            tab_frames=tab_frames
        )
        frame.pack(fill="both", expand=True)

def show_loading_screen():
    """
    Display a loading screen with the app logo while news content is being loaded.
    Shows a centered window with logo and loading message, then loads all content
    and shows the main application window.
    """
    
    loading = tk.Toplevel(app)
    loading.overrideredirect(True)
    loading.geometry("300x300+{}+{}".format(
        app.winfo_screenwidth()//2 - 150,
        app.winfo_screenheight()//2 - 150
    ))
    loading.configure(bg="white")

    img = Image.open("UpToDate/logo.png").resize((128, 128), Image.LANCZOS)
    logo_img = ImageTk.PhotoImage(img)
    label = tk.Label(loading, image=logo_img, bg="white")
    label.image = logo_img
    label.pack(expand=True)

    tk.Label(loading, text="Your news is coming....", font=("Arial", 16), bg="white").pack(pady=10)

    def close_loading():
        loading.destroy()
        app.deiconify()

    def load_and_close():
        tab_frames = create_tabs()
        load_categories(tab_frames)
        render_favorites(tab_frames)
        close_loading()

    app.after(500, load_and_close)