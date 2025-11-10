"""
helper functions for rss feed parsing and processing
"""

from rss_parser import RSSParser
from requests import get
from datetime import datetime
from dateutil import parser as date_parser

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

