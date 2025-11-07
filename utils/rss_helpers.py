"""
helper functions for rss feed parsing and processing
"""

from rss_parser import RSSParser
from requests import get
from datetime import datetime
from dateutil import parser as date_parser


# rss feed collections
RSS_FEEDS = {
    "italian_news": {
        "name": "Italian News Feeds",
        "description": "Major Italian news sources",
        "feeds": [
            {"name": "ANSA", "url": "https://www.ansa.it/sito/notizie/topnews/topnews_rss.xml"},
            {"name": "Corriere della Sera", "url": "https://xml2.corriereobjects.it/feed-hp/homepage.xml"},
            {"name": "La Repubblica", "url": "https://www.repubblica.it/rss/homepage/rss2.0.xml"},
            {"name": "Il Sole 24 Ore", "url": "https://www.ilsole24ore.com/rss/notizie.xml"},
            {"name": "La Gazzetta dello Sport", "url": "https://www.gazzetta.it/rss/home.xml"},
            {"name": "Sky TG24", "url": "https://tg24.sky.it/rss/tg24_homepage.xml"}
        ]
    },
    "international_news": {
        "name": "International News Feeds",
        "description": "Global news sources in English",
        "feeds": [
            {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/rss.xml"},
            {"name": "CNN", "url": "https://rss.cnn.com/rss/edition.rss"},
            {"name": "Reuters", "url": "https://feeds.reuters.com/reuters/topNews"},
            {"name": "Associated Press", "url": "https://feeds.apnews.com/rss/apf-topnews"},
            {"name": "The Guardian", "url": "https://www.theguardian.com/world/rss"},
            {"name": "NPR News", "url": "https://feeds.npr.org/1001/rss.xml"}
        ]
    },
    "tech_news": {
        "name": "Technology News Feeds",
        "description": "Technology and startup news",
        "feeds": [
            {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
            {"name": "Hacker News", "url": "https://hnrss.org/frontpage"},
            {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index"},
            {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
            {"name": "Wired", "url": "https://www.wired.com/feed/rss"},
            {"name": "Engadget", "url": "https://www.engadget.com/rss.xml"}
        ]
    },
    "business_news": {
        "name": "Business News Feeds",
        "description": "Financial and business news",
        "feeds": [
            {"name": "Bloomberg", "url": "https://feeds.bloomberg.com/markets/news.rss"},
            {"name": "Financial Times", "url": "https://www.ft.com/rss/home"},
            {"name": "Wall Street Journal", "url": "https://www.wsj.com/xml/rss/3_7085.xml"},
            {"name": "MarketWatch", "url": "https://feeds.marketwatch.com/marketwatch/topstories/"},
            {"name": "Forbes", "url": "https://www.forbes.com/real-time/feed2/"},
            {"name": "CNBC", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"}
        ]
    },
    "science_news": {
        "name": "Science News Feeds", 
        "description": "Science and research news",
        "feeds": [
            {"name": "Science Daily", "url": "https://www.sciencedaily.com/rss/all.xml"},
            {"name": "Nature News", "url": "https://www.nature.com/nature.rss"},
            {"name": "Scientific American", "url": "https://rss.sciam.com/ScientificAmerican-Global"},
            {"name": "New Scientist", "url": "https://www.newscientist.com/feed/home/"},
            {"name": "Phys.org", "url": "https://phys.org/rss-feed/"},
            {"name": "Space.com", "url": "https://www.space.com/feeds/all"}
        ]
    }
}


def extract_field_content(field) -> str:
    """
    extract content from rss field that may be a string or object
    handles rss-parser's object format with content and attributes
    """
    if field is None:
        return ''
    
    # check for content attribute (rss-parser object format)
    if hasattr(field, 'content'):
        return str(field.content)
    
    # fallback to string conversion
    return str(field)


def get_article_link(item) -> str:
    """
    extract the best available link from rss item
    prefers guid permalink over regular link for corriere della sera
    """
    # try guid link first (corriere della sera uses this)
    if hasattr(item, 'guid') and item.guid:
        guid_link = extract_field_content(item.guid)
        if guid_link.startswith('http'):
            return guid_link
    
    # fallback to regular link
    return extract_field_content(getattr(item, 'link', ''))


def parse_date_safely(date_str: str) -> datetime:
    """parse date string, returning datetime.min if parsing fails"""
    try:
        if date_str:
            return date_parser.parse(date_str)
    except:
        pass
    return datetime.min


def fetch_rss_feed(url: str, timeout: int = 15) -> RSSParser:
    """
    fetch and parse rss feed from url
    
    args:
        url: rss feed url
        timeout: request timeout in seconds
        
    returns:
        parsed rss feed object
    """
    # add headers to mimic a real browser (some sites require this)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0'
    }
    
    response = get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return RSSParser.parse(response.text)

