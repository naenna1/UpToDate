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
from newsapi import *
from favorites import *
from interface import *

placeholder_pic = "photo.jpg"
EXECUTOR = ThreadPoolExecutor(max_workers=6)  # Global executor for all image loads

# Simple in-memory image byte cache to avoid re-downloading duplicates
_IMAGE_CACHE = {}


class NewsFrame(ctk.CTkFrame):
    """
    A custom frame widget that displays a single news article with title, metadata,
    image, and action buttons (Read more, Add to Favorites).
    """
    def __init__(self, master, headline, url, imgurl, time_iso, source="", tab_frames=None):
        """
        Initialize a news article frame.

        Args:
            master: The parent widget
            headline (str): The article title/headline
            url (str): The article URL
            imgurl (str): URL of the article's image
            time_iso (str): Publication time in ISO format
            source (str): Name of the news source
            tab_frames (dict): Dictionary of tab frames for updating favorites
        """
        super().__init__(master)
        self.url = url
        self.tab_frames = tab_frames
        self.article_dict = {
            "title" : headline,
            "url" : url,
            "urlToImage" : imgurl,
            "publishedAt" : time_iso,
            "source" : source,
        }

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1, minsize=225)

        self.label= ctk.CTkLabel(self, text=headline, font=("Roboto", 16, "bold"),
                                 wraplength=420, justify = "left")
        self.label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10,2), sticky="w")

        meta = f"{fmt_time(time_iso)}"
        if source: meta += f"   -   {source}"
        self.age = ctk.CTkLabel(self, text=meta, font=("Roboto", 12), justify = 'left')
        self.age.grid(row=1, column=0,columnspan=2, padx=10, pady=(0,8), sticky="w")

        self.img = ctk.CTkImage(light_image=Image.open(placeholder_pic), size=(225, 150))
        self.img_label = ctk.CTkLabel(self, image=self.img, text="")
        self.img_label.grid(row=0, column=2, rowspan=2, padx=20, pady=10, sticky="ns")

        self.read_button = ctk.CTkButton(self, text="Read more", command=self.read_more,
                                         width=120)
        self.read_button.grid(row=2, column=0, padx=(10,5), pady=(0,10), sticky="ew",
                              )

        self.fav_button= ctk.CTkButton(self, text="Add to Favorites", command=self.add_to_favorites,
                                       width=120)
        self.fav_button.grid(row=2, column=1, padx=(10,5), pady=(0,10), sticky="ew",
                             )

        if imgurl and imgurl.strip():
            EXECUTOR.submit(self._load_image_async, imgurl)

    def _load_image_async(self, imgurl: str):
        """
        Load an image asynchronously from a URL and cache it.

        Args:
            imgurl (str): URL of the image to load
        """
        try:
            if imgurl in _IMAGE_CACHE:
                img_bytes = _IMAGE_CACHE[imgurl]
            else:
                headers = {"User-Agent": "Mozilla/5.0", "Referer": self.url or ""}
                r = requests.get(imgurl, headers=headers, timeout=(3, 5))
                r.raise_for_status()
                img_bytes = r.content
                _IMAGE_CACHE[imgurl] = img_bytes

            # schedule image creation on main thread
            self.img_label.after(0, lambda: self._create_image_on_main(img_bytes))
        except Exception as e:
            print("Image load failed:", e)

    def _create_image_on_main(self, img_bytes):
        """
        Create and display the image on the main thread from downloaded bytes.

        Args:
            img_bytes (bytes): Image data in bytes format
        """
        if not self.winfo_exists():
            return  # widget destroyed
        try:
            im = Image.open(BytesIO(img_bytes))
            im.thumbnail((225, 150), Image.LANCZOS)
            new_img = ctk.CTkImage(light_image=im, size=(225, 150))
            self.img = new_img
            self.img_label.configure(image=self.img)
        except Exception as e:
            print("Image create failed:", e)

    def read_more(self):
        """
        Open the article URL in the default web browser.
        """
        if self.url:
            webbrowser.open(self.url)

    def add_to_favorites(self):
        """
        Add the current article to favorites and update the UI.
        Disables the button and updates the favorites tab.
        """
        try:
            add_fav(self.article_dict)
            self.fav_button.configure(text="Saved ✓", state="disabled")
            try:
                self.after(0, render_favorites(self.tab_frames))
            except NameError:
                pass
        except Exception as e:
            print(f"Favorit speichern fehlgeschlagen: {e}")

app = ctk.CTk()
app.title("UpToDate")
app.geometry("800x600")
img = Image.open("logo.png")
img = img.resize((64, 64), Image.LANCZOS)
img.save("logo.ico", format="ICO")
app.iconbitmap("logo.ico")

app.withdraw()


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

    img = Image.open("logo.png").resize((128, 128), Image.LANCZOS)
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


app.after(50,show_loading_screen) # Call this before mainloop
app.mainloop()
