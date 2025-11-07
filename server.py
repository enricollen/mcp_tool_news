"""
simple mcp server for rss parsing
"""

from mcp.server.fastmcp import FastMCP
from rss_parser import RSSParser
from requests import get
from typing import List, Dict, Any
from utils.text_sanitizer import sanitize_title, beautify_description, format_article_summary

# create mcp server
mcp = FastMCP("simple-rss-server")

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

# add resources for feed collections
@mcp.resource("rss-feeds://italian_news")
def get_italian_feeds():
    """italian news rss feeds collection"""
    return RSS_FEEDS["italian_news"]

@mcp.resource("rss-feeds://international_news") 
def get_international_feeds():
    """international news rss feeds collection"""
    return RSS_FEEDS["international_news"]

@mcp.resource("rss-feeds://tech_news")
def get_tech_feeds():
    """technology news rss feeds collection"""
    return RSS_FEEDS["tech_news"]

@mcp.resource("rss-feeds://business_news")
def get_business_feeds():
    """business news rss feeds collection"""
    return RSS_FEEDS["business_news"]

@mcp.resource("rss-feeds://science_news")
def get_science_feeds():
    """science news rss feeds collection"""
    return RSS_FEEDS["science_news"]

@mcp.resource("rss-feeds://all")
def get_all_feeds():
    """all available rss feed collections"""
    return {
        "collections": RSS_FEEDS,
        "total_categories": len(RSS_FEEDS),
        "total_feeds": sum(len(category["feeds"]) for category in RSS_FEEDS.values())
    }

@mcp.tool()
def parse_rss_feed(url: str = "https://xml2.corriereobjects.it/feed-hp/homepage.xml", limit: int = 10) -> Dict[str, Any]:
    """
    parse rss feed and return structured data
    
    args:
        url: rss feed url (default: corriere homepage)
        limit: maximum number of articles to return (default: 10)
    
    returns:
        dict containing feed metadata and items
    """
    try:
        response = get(url)
        response.raise_for_status()
        
        rss = RSSParser.parse(response.text)
        
        # extract feed metadata
        feed_data = {
            "language": rss.channel.language,
            "version": rss.version,
            "title": getattr(rss.channel, 'title', 'unknown'),
            "description": getattr(rss.channel, 'description', ''),
            "items": []
        }
        
        # extract items with sanitization
        count = 0
        for item in rss.channel.items:
            if count >= limit:
                break
                
            raw_title = getattr(item, 'title', '')
            raw_description = getattr(item, 'description', '')
            
            item_data = {
                "title": sanitize_title(raw_title),
                "description": beautify_description(raw_description),
                "link": getattr(item, 'link', ''),
                "pub_date": getattr(item, 'pub_date', ''),
                "raw_title": raw_title,  # keep original for reference
                "raw_description": raw_description  # keep original for reference
            }
            feed_data["items"].append(item_data)
            count += 1
        
        return feed_data
        
    except Exception as e:
        return {"error": f"failed to parse rss feed: {str(e)}"}

@mcp.tool()
def get_feed_titles(url: str = "https://xml2.corriereobjects.it/feed-hp/homepage.xml", limit: int = 10) -> List[str]:
    """
    get just the titles from rss feed
    
    args:
        url: rss feed url (default: corriere homepage)
        limit: maximum number of titles to return (default: 10)
    
    returns:
        list of article titles
    """
    try:
        response = get(url)
        response.raise_for_status()
        
        rss = RSSParser.parse(response.text)
        
        titles = []
        count = 0
        for item in rss.channel.items:
            if count >= limit:
                break
            if hasattr(item, 'title'):
                clean_title = sanitize_title(item.title)
                titles.append(clean_title)
                count += 1
        
        return titles
        
    except Exception as e:
        return [f"error: failed to get titles: {str(e)}"]

@mcp.tool()
def get_formatted_feed(url: str = "https://xml2.corriereobjects.it/feed-hp/homepage.xml", limit: int = 10) -> List[str]:
    """
    get beautifully formatted feed summaries
    
    args:
        url: rss feed url (default: corriere homepage)
        limit: maximum number of articles to return (default: 10)
    
    returns:
        list of formatted article summaries
    """
    try:
        response = get(url)
        response.raise_for_status()
        
        rss = RSSParser.parse(response.text)
        
        formatted_articles = []
        count = 0
        
        for item in rss.channel.items:
            if count >= limit:
                break
                
            title = getattr(item, 'title', '')
            description = getattr(item, 'description', '')
            link = getattr(item, 'link', '')
            pub_date = getattr(item, 'pub_date', '')
            
            formatted_summary = format_article_summary(title, description, link, pub_date)
            formatted_articles.append(formatted_summary)
            count += 1
        
        return formatted_articles
        
    except Exception as e:
        return [f"error: failed to get formatted feed: {str(e)}"]

@mcp.tool()
def get_category_news(category: str = "italian_news", limit: int = 10, per_feed_limit: int = 3) -> List[str]:
    """
    get formatted news from a specific category of feeds
    
    args:
        category: feed category (italian_news, international_news, tech_news, business_news, science_news)
        limit: maximum total number of articles to return (default: 10)
        per_feed_limit: maximum number of articles per individual feed (default: 3)
    
    returns:
        list of formatted articles from all feeds in the category
    """
    if category not in RSS_FEEDS:
        return [f"error: category '{category}' not found. available categories: {', '.join(RSS_FEEDS.keys())}"]
    
    all_articles = []
    category_data = RSS_FEEDS[category]
    total_count = 0
    
    for feed in category_data["feeds"]:
        if total_count >= limit:
            break
            
        try:
            response = get(feed["url"])
            response.raise_for_status()
            
            rss = RSSParser.parse(response.text)
            
            feed_count = 0
            for item in rss.channel.items:
                if feed_count >= per_feed_limit or total_count >= limit:
                    break
                    
                title = getattr(item, 'title', '')
                description = getattr(item, 'description', '')
                link = getattr(item, 'link', '')
                pub_date = getattr(item, 'pub_date', '')
                
                # add source name to the formatted summary
                formatted_summary = format_article_summary(title, description, link, pub_date)
                formatted_summary = f"Source: {feed['name']}\n{formatted_summary}\n{'-'*50}"
                
                all_articles.append(formatted_summary)
                feed_count += 1
                total_count += 1
                
        except Exception as e:
            all_articles.append(f"error loading {feed['name']}: {str(e)}")
    
    return all_articles

# add prompts for common workflows
@mcp.prompt("daily-news-briefing")
def daily_news_briefing():
    """get a comprehensive daily news briefing from multiple sources"""
    return """
You are a news analyst providing a daily briefing. Please:

1. Get the latest Italian news using get_category_news("italian_news", 5)
2. Get international headlines using get_category_news("international_news", 5) 
3. Get top tech stories using get_category_news("tech_news", 3)
4. Get business updates using get_category_news("business_news", 3)

Then provide:
- A brief executive summary of the most important stories
- Key trends or themes you notice across sources
- Any breaking news or urgent developments
- A concise conclusion with the day's main takeaways

Format your response as a professional news briefing suitable for busy executives.
"""

@mcp.prompt("tech-focus-digest")
def tech_focus_digest():
    """get focused technology news digest with analysis"""
    return """
You are a technology analyst. Please:

1. Get comprehensive tech news using get_category_news("tech_news", 8)
2. Get business news that might relate to tech using get_category_news("business_news", 5)

Then provide:
- Top 3 most significant tech stories with brief analysis
- Emerging trends in technology sector
- Any major product launches, acquisitions, or funding rounds
- Impact on major tech companies (Apple, Google, Microsoft, etc.)
- Brief outlook on what these developments mean for the industry

Focus on actionable insights for tech professionals and investors.
"""

@mcp.prompt("italian-news-summary")
def italian_news_summary():
    """get italian news summary with context for international readers"""
    return """
You are an Italian news correspondent reporting for an international audience. Please:

1. Get Italian news using get_category_news("italian_news", 10)
2. Get relevant international context using get_category_news("international_news", 5)

Then provide:
- Top Italian stories with context for non-Italian readers
- Political developments and their significance
- Economic news and market impacts
- Cultural or social issues making headlines
- How Italian news connects to broader European/global trends
- Brief explanation of any Italian-specific context needed

Write in clear English suitable for international readers unfamiliar with Italian politics and culture.
"""

@mcp.prompt("breaking-news-monitor")
def breaking_news_monitor():
    """monitor for breaking news across all categories"""
    return """
You are a breaking news monitor. Please:

1. Quickly scan all news categories:
   - get_category_news("italian_news", 3)
   - get_category_news("international_news", 3)
   - get_category_news("tech_news", 2)
   - get_category_news("business_news", 2)
   - get_category_news("science_news", 2)

Then identify:
- Any breaking or urgent news stories
- Stories that appear across multiple sources (indicating importance)
- Developing situations that need monitoring
- Time-sensitive information

Provide a rapid-fire briefing focusing only on:
- What happened
- When it happened
- Why it matters
- What to watch for next

Keep it concise and action-oriented for news professionals.
"""

@mcp.prompt("custom-feed-analysis")
def custom_feed_analysis():
    """analyze news from a custom RSS feed with deep insights"""
    return """
You are a media analyst. The user will provide a specific RSS feed URL. Please:

1. Ask the user for the RSS feed URL they want analyzed
2. Use get_formatted_feed(url, 10) with their provided URL
3. Use parse_rss_feed(url, 15) to get additional metadata

Then provide:
- Source credibility assessment
- Content themes and focus areas
- Writing style and target audience analysis
- Frequency and timeliness of updates
- Comparison to mainstream sources
- Recommendations for regular monitoring
- Any biases or editorial perspectives noticed

Provide a professional media analysis suitable for journalists, researchers, or media professionals.
"""

if __name__ == "__main__":
    # run the server
    print("Starting RSS feed MCP server...")
    mcp.run(transport="streamable-http")