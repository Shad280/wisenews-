import os
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime

# --- CONFIG ---
DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# RSS feeds for major news
RSS_URLS = [
    "https://rss.cnn.com/rss/edition.rss",
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://feeds.skynews.com/feeds/rss/home.xml",
]

# --- HELPERS ---
def fetch_article_text(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        return '\n'.join([p.text for p in soup.find_all('p')])
    except Exception as e:
        return f"Error fetching article: {e}"

def save_to_file(content, title, prefix=""):
    safe_title = "".join([c if c.isalnum() else "_" for c in title])[:50]
    filename = f"{prefix}{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(DOWNLOADS_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved: {filepath}")

def fetch_rss_articles(rss_url, limit=3):  # Reduced to 3 for testing
    print(f"Fetching from: {rss_url}")
    feed = feedparser.parse(rss_url)
    articles = []
    for entry in feed.entries[:limit]:
        print(f"  - Processing: {entry.title[:60]}...")
        content = fetch_article_text(entry.link)
        articles.append({"title": entry.title, "content": content})
    return articles

def test_rss_only():
    print("🔄 Testing RSS feeds only...")
    for rss in RSS_URLS:
        articles = fetch_rss_articles(rss)
        for article in articles:
            save_to_file(article['content'], article['title'], prefix="RSS_")
    
    print("✅ RSS test completed! Check the downloads folder.")

if __name__ == "__main__":
    test_rss_only()
