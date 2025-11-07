"""
FastMCP News API Server
"""

import os
from typing import Optional, Dict, Any, List
from fastmcp import FastMCP
from newsapi import NewsApiClient
from dotenv import load_dotenv

load_dotenv()

# create server
mcp = FastMCP("News API Server")

# news api client
api_key = os.getenv('NEWS_API_KEY')
if not api_key:
    raise ValueError("NEWS_API_KEY environment variable is required")

newsapi = NewsApiClient(api_key=api_key)


@mcp.tool
def get_top_headlines(
    q: Optional[str] = None,
    sources: Optional[str] = None,
    category: Optional[str] = None,
    language: Optional[str] = 'en',
    country: Optional[str] = None,
    page_size: Optional[int] = 20,
    page: Optional[int] = 1
) -> Dict[str, Any]:
    """
    get top headlines from news api
    
    args:
        q: keywords or phrases to search for
        sources: comma-separated string of news sources or blogs
        category: category of news (business, entertainment, general, health, science, sports, technology)
        language: language code (en, de, fr, etc.)
        country: country code (us, gb, ca, etc.)
        page_size: number of results to return per page (max 100)
        page: page number to retrieve
    """
    try:
        response = newsapi.get_top_headlines(
            q=q,
            sources=sources,
            category=category,
            language=language,
            country=country,
            page_size=page_size,
            page=page
        )
        return response
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_everything(
    q: Optional[str] = None,
    sources: Optional[str] = None,
    domains: Optional[str] = None,
    exclude_domains: Optional[str] = None,
    from_param: Optional[str] = None,
    to: Optional[str] = None,
    language: Optional[str] = 'en',
    sort_by: Optional[str] = 'publishedAt',
    page_size: Optional[int] = 20,
    page: Optional[int] = 1
) -> Dict[str, Any]:
    """
    search through millions of articles from news sources and blogs
    
    args:
        q: keywords or phrases to search for
        sources: comma-separated string of news sources or blogs
        domains: comma-separated string of domains to restrict search to
        exclude_domains: comma-separated string of domains to exclude
        from_param: oldest article date (iso format: 2024-01-01)
        to: newest article date (iso format: 2024-01-31)
        language: language code (en, de, fr, etc.)
        sort_by: sort order (relevancy, popularity, publishedAt)
        page_size: number of results to return per page (max 100)
        page: page number to retrieve
    """
    try:
        response = newsapi.get_everything(
            q=q,
            sources=sources,
            domains=domains,
            exclude_domains=exclude_domains,
            from_param=from_param,
            to=to,
            language=language,
            sort_by=sort_by,
            page_size=page_size,
            page=page
        )
        return response
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_sources(
    category: Optional[str] = None,
    language: Optional[str] = None,
    country: Optional[str] = None
) -> Dict[str, Any]:
    """
    get available news sources
    
    args:
        category: category to filter by (business, entertainment, general, health, science, sports, technology)
        language: language code to filter by (en, de, fr, etc.)
        country: country code to filter by (us, gb, ca, etc.)
    """
    try:
        response = newsapi.get_sources(
            category=category,
            language=language,
            country=country
        )
        return response
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_italian_news_today(
    category: Optional[str] = None,
    page_size: Optional[int] = 20
) -> Dict[str, Any]:
    """
    get today's italian news headlines
    
    args:
        category: category of news (business, entertainment, general, health, science, sports, technology)
        page_size: number of results to return (max 100)
    """
    try:
        response = newsapi.get_top_headlines(
            country='it',
            language='it',
            category=category,
            page_size=page_size
        )
        return response
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def search_italian_news(
    query: str,
    days_back: Optional[int] = 7,
    sort_by: Optional[str] = 'publishedAt',
    page_size: Optional[int] = 20
) -> Dict[str, Any]:
    """
    search italian news articles
    
    args:
        query: keywords to search for in italian news
        days_back: how many days back to search (default 7)
        sort_by: sort order (relevancy, popularity, publishedAt)
        page_size: number of results to return (max 100)
    """
    try:
        from datetime import datetime, timedelta
        
        # calculate date range
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)
        
        response = newsapi.get_everything(
            q=query,
            language='it',
            from_param=from_date.strftime('%Y-%m-%d'),
            to=to_date.strftime('%Y-%m-%d'),
            sort_by=sort_by,
            page_size=page_size
        )
        return response
    except Exception as e:
        return {"error": str(e)}


@mcp.resource("news://headlines")
def latest_headlines() -> str:
    """get latest top headlines"""
    try:
        response = newsapi.get_top_headlines(language='en', page_size=5)
        if response.get('status') == 'ok':
            articles = response.get('articles', [])
            headlines = []
            for article in articles:
                headlines.append(f"• {article.get('title', 'no title')}")
            return "\n".join(headlines)
        else:
            return f"error: {response.get('message', 'unknown error')}"
    except Exception as e:
        return f"error: {str(e)}"


@mcp.resource("news://sources")
def available_sources() -> str:
    """get list of available news sources"""
    try:
        response = newsapi.get_sources()
        if response.get('status') == 'ok':
            sources = response.get('sources', [])
            source_list = []
            for source in sources[:10]:  # limit to first 10
                source_list.append(f"• {source.get('name', 'unknown')} ({source.get('id', 'no-id')})")
            return "\n".join(source_list)
        else:
            return f"error: {response.get('message', 'unknown error')}"
    except Exception as e:
        return f"error: {str(e)}"


@mcp.resource("news://italian-headlines")
def italian_headlines() -> str:
    """get latest italian headlines"""
    try:
        response = newsapi.get_top_headlines(country='it', language='it', page_size=10)
        if response.get('status') == 'ok':
            articles = response.get('articles', [])
            headlines = []
            for article in articles:
                title = article.get('title', 'no title')
                source = article.get('source', {}).get('name', 'unknown source')
                headlines.append(f"• {title} ({source})")
            return "\n".join(headlines)
        else:
            return f"error: {response.get('message', 'unknown error')}"
    except Exception as e:
        return f"error: {str(e)}"


@mcp.resource("news://italian-sources")
def italian_sources() -> str:
    """get list of italian news sources"""
    try:
        response = newsapi.get_sources(country='it', language='it')
        if response.get('status') == 'ok':
            sources = response.get('sources', [])
            source_list = []
            for source in sources:
                name = source.get('name', 'unknown')
                description = source.get('description', 'no description')
                source_list.append(f"• {name}: {description}")
            return "\n".join(source_list)
        else:
            return f"error: {response.get('message', 'unknown error')}"
    except Exception as e:
        return f"error: {str(e)}"


@mcp.prompt("news_search")
def news_search_prompt(query: str, source_type: str = "headlines") -> str:
    """
    generate a news search prompt
    
    args:
        query: search query
        source_type: type of search (headlines, everything, sources)
    """
    if source_type == "headlines":
        return f"search for top headlines about: {query}"
    elif source_type == "everything":
        return f"search all articles about: {query}"
    elif source_type == "sources":
        return f"find news sources related to: {query}"
    else:
        return f"search news for: {query}"
