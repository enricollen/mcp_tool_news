"""
mcp server for rss news parsing with content scraping
https://pypi.org/project/rss-parser/
"""

from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any

from utils.text_sanitizer import is_today_news, create_news_summary
from utils.rss_helpers import (
    extract_field_content,
    get_article_link,
    parse_date_safely,
    fetch_rss_feed
)

# create mcp server
mcp = FastMCP("rss-feeds-parser-server")


@mcp.tool()
def get_all_news_summary(
    rss_url: str = "https://www.corriere.it/feed-hp/homepage.xml",
    limit: int = 10,
    title_limit: int = 100,
    desc_limit: int = 300,
    content_limit: int = 1000,
    scrape_content: bool = True,
    summarize_content: bool = False,
    summary_method: str = 'auto',
    today_only: bool = True
) -> List[Dict[str, Any]]:
    """
    get comprehensive news summary with date filtering, content scraping, and optional summarization
    
    args:
        rss_url: rss feed url to parse (default: corriere della sera)
        limit: maximum number of articles to return (default: 10)
        title_limit: maximum title length (default: 100)
        desc_limit: maximum description length (default: 300)
        content_limit: maximum scraped content length (default: 1000)
        scrape_content: whether to scrape full article content from links (default: true)
        summarize_content: whether to automatically summarize scraped content (default: false)
        summary_method: summarization method - 'auto', 'extractive', 'keyword', or 'lead' (default: 'auto')
        today_only: filter to show only today's news (default: true)
    
    returns:
        list of news articles with title, description, link, date, and scraped content (optionally summarized), ordered by latest first
    """
    try:
        # fetch and parse rss feed
        rss = fetch_rss_feed(rss_url)
        
        articles = []
        
        for item in rss.channel.items:
            # extract article fields
            title = extract_field_content(getattr(item, 'title', ''))
            description = extract_field_content(getattr(item, 'description', ''))
            pub_date = extract_field_content(getattr(item, 'pub_date', ''))
            link = get_article_link(item)
            
            # apply date filter if requested
            if today_only and pub_date and not is_today_news(pub_date):
                continue
            
            # create news summary with optional content scraping and summarization
            news_summary = create_news_summary(
                title=title,
                description=description,
                link=link,
                pub_date=pub_date,
                title_limit=title_limit,
                desc_limit=desc_limit,
                scrape_content=scrape_content,
                content_limit=content_limit,
                summarize_content=summarize_content,
                summary_method=summary_method
            )
            
            articles.append(news_summary)
            
            # stop when we have enough articles
            if len(articles) >= limit:
                break
        
        # sort by publication date (latest first)
        articles.sort(
            key=lambda article: parse_date_safely(article['pub_date']),
            reverse=True
        )
        
        return articles
        
    except Exception as e:
        return [{"error": f"failed to fetch news: {str(e)}"}]


@mcp.tool()
def get_serie_a_news(
    limit: int = 10,
    title_limit: int = 100,
    desc_limit: int = 300,
    content_limit: int = 800,
    scrape_content: bool = False,
    summarize_content: bool = True,
    summary_method: str = 'lead',
    today_only: bool = True
) -> List[Dict[str, Any]]:
    """
    get serie a soccer news from gazzetta dello sport with content scraping and summarization
    
    args:
        limit: maximum number of articles to return (default: 10)
        title_limit: maximum title length (default: 100)
        desc_limit: maximum description length (default: 300)
        content_limit: maximum scraped content length (default: 1000)
        scrape_content: whether to scrape full article content from links (default: true)
        summarize_content: whether to automatically summarize scraped content (default: false)
        summary_method: summarization method - 'auto', 'extractive', 'keyword', or 'lead' (default: 'auto')
        today_only: filter to show only today's news (default: true)
    
    returns:
        list of serie a news articles with title, description, link, date, and scraped content (optionally summarized), ordered by latest first
    """
    # use gazzetta dello sport serie a rss feed
    rss_url = "https://www.gazzetta.it/dynamic-feed/rss/section/Calcio/Serie-A.xml"
    
    try:
        # fetch and parse rss feed
        rss = fetch_rss_feed(rss_url)
        
        articles = []
        
        for item in rss.channel.items:
            # extract article fields
            title = extract_field_content(getattr(item, 'title', ''))
            description = extract_field_content(getattr(item, 'description', ''))
            pub_date = extract_field_content(getattr(item, 'pub_date', ''))
            link = get_article_link(item)
            
            # apply date filter if requested
            if today_only and pub_date and not is_today_news(pub_date):
                continue
            
            # create news summary with optional content scraping and summarization
            news_summary = create_news_summary(
                title=title,
                description=description,
                link=link,
                pub_date=pub_date,
                title_limit=title_limit,
                desc_limit=desc_limit,
                scrape_content=scrape_content,
                content_limit=content_limit,
                summarize_content=summarize_content,
                summary_method=summary_method
            )
            
            articles.append(news_summary)
            
            # stop when we have enough articles
            if len(articles) >= limit:
                break
        
        # sort by publication date (latest first)
        articles.sort(
            key=lambda article: parse_date_safely(article['pub_date']),
            reverse=True
        )
        
        return articles
        
    except Exception as e:
        return [{"error": f"failed to fetch serie a news: {str(e)}"}]