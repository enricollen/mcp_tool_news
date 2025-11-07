"""
mcp server for rss parsing
https://pypi.org/project/rss-parser/
"""

from fastmcp import FastMCP
from rss_parser import RSSParser
from requests import get
from typing import List, Dict, Any
from utils.text_sanitizer import sanitize_title, beautify_description

# create mcp server
mcp = FastMCP("rss-feeds-parser-server")

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

@mcp.tool
def get_all_news_summary(limit_per_category: int = 3) -> List[str]:
    """
    get detailed summary of latest news for each topic category
    
    args:
        limit_per_category: maximum number of articles per category (default: 3)
    
    returns:
        list of formatted news summaries organized by category
    """
    all_summaries = []
    
    for category_key, category_data in RSS_FEEDS.items():
        category_summary = [f"\n=== {category_data['name'].upper()} ==="]
        article_count = 0
        
        for feed in category_data["feeds"]:
            if article_count >= limit_per_category:
                break
                
            try:
                response = get(feed["url"])
                response.raise_for_status()
                rss = RSSParser.parse(response.text)
                
                for item in rss.channel.items:
                    if article_count >= limit_per_category:
                        break
                        
                    # convert to string to avoid serialization issues
                    title = str(getattr(item, 'title', ''))
                    description = str(getattr(item, 'description', ''))
                    link = str(getattr(item, 'link', ''))
                    
                    clean_title = sanitize_title(title)
                    clean_desc = beautify_description(description)
                    
                    summary = f"• {clean_title}"
                    if clean_desc:
                        summary += f"\n  {clean_desc[:200]}..."
                    if link:
                        summary += f"\n  Link: {link}"
                    summary += f"\n  Source: {feed['name']}\n"
                    
                    category_summary.append(summary)
                    article_count += 1
                    break  # one article per feed for variety
                    
            except Exception as e:
                category_summary.append(f"  Error loading {feed['name']}: {str(e)}")
        
        all_summaries.extend(category_summary)
    
    return all_summaries

@mcp.tool
def get_topic_news(topic: str = "italian_news", limit: int = 10) -> List[str]:
    """
    get news filtered by specific topic category
    
    args:
        topic: news category (italian_news, international_news, tech_news, business_news, science_news)
        limit: maximum number of articles to return (default: 10)
    
    returns:
        list of formatted articles from the specified topic
    """
    if topic not in RSS_FEEDS:
        return [f"Error: topic '{topic}' not found. Available topics: {', '.join(RSS_FEEDS.keys())}"]
    
    articles = []
    category_data = RSS_FEEDS[topic]
    total_count = 0
    
    for feed in category_data["feeds"]:
        if total_count >= limit:
            break
            
        try:
            response = get(feed["url"])
            response.raise_for_status()
            rss = RSSParser.parse(response.text)
            
            for item in rss.channel.items:
                if total_count >= limit:
                    break
                    
                # convert to string to avoid serialization issues
                title = str(getattr(item, 'title', ''))
                description = str(getattr(item, 'description', ''))
                link = str(getattr(item, 'link', ''))
                pub_date = str(getattr(item, 'pub_date', ''))
                
                clean_title = sanitize_title(title)
                clean_desc = beautify_description(description)
                
                article = f"Title: {clean_title}"
                if clean_desc:
                    article += f"\nDescription: {clean_desc}"
                if pub_date:
                    article += f"\nDate: {pub_date}"
                article += f"\nSource: {feed['name']}"
                article += "\n" + "-"*50
                
                articles.append(article)
                total_count += 1
                
        except Exception as e:
            articles.append(f"Error loading {feed['name']}: {str(e)}")
    
    return articles
