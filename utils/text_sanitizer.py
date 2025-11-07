"""
text sanitization and beautification utilities for rss content
"""

import re
from html import unescape
from typing import Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from dateutil import parser as date_parser
import xml.etree.ElementTree as ET
import json


def clean_html_tags(text) -> str:
    """
    remove html tags from text
    
    args:
        text: text with html tags (can be string or Tag object)
        
    returns:
        clean text without html tags
    """
    if not text:
        return ""
    
    # convert to string if it's a Tag object
    text_str = str(text)
    
    # remove html tags
    clean_text = re.sub(r'<[^>]+>', '', text_str)
    
    # decode html entities
    clean_text = unescape(clean_text)
    
    return clean_text.strip()


def beautify_description(description) -> str:
    """
    beautify rss description text
    
    args:
        description: raw description text (can be string or Tag object)
        
    returns:
        beautified and cleaned description
    """
    if not description:
        return ""
    
    # clean html tags
    clean_desc = clean_html_tags(description)
    
    # remove extra whitespace and newlines
    clean_desc = re.sub(r'\s+', ' ', clean_desc)
    
    # remove common rss artifacts
    clean_desc = re.sub(r'^\s*-\s*', '', clean_desc)  # remove leading dashes
    clean_desc = re.sub(r'\s*\.\.\.\s*$', '...', clean_desc)  # normalize ellipsis
    
    # ensure proper sentence ending
    if clean_desc and not clean_desc.endswith(('.', '!', '?', '...')):
        clean_desc += '.'
    
    return clean_desc.strip()


def sanitize_title(title) -> str:
    """
    sanitize and clean article title
    
    args:
        title: raw title text (can be string or Tag object)
        
    returns:
        clean title
    """
    if not title:
        return ""
    
    # clean html tags
    clean_title = clean_html_tags(title)
    
    # remove extra whitespace
    clean_title = re.sub(r'\s+', ' ', clean_title)
    
    # remove common artifacts
    clean_title = re.sub(r'^\s*-\s*', '', clean_title)
    
    return clean_title.strip()


def extract_clean_text(text, max_length: Optional[int] = None) -> str:
    """
    extract and clean text with optional length limit
    
    args:
        text: raw text to clean
        max_length: optional maximum length for truncation
        
    returns:
        clean text, optionally truncated
    """
    if not text:
        return ""
    
    # clean html and beautify
    clean_text = beautify_description(text)
    
    # truncate if needed
    if max_length and len(clean_text) > max_length:
        # find last complete word before limit
        truncated = clean_text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.8:  # if we can keep most of the text
            clean_text = truncated[:last_space] + '...'
        else:
            clean_text = truncated + '...'
    
    return clean_text


def format_article_summary(title, description, link: str = "", pub_date: str = "") -> str:
    """
    format a complete article summary with clean text
    
    args:
        title: article title
        description: article description
        link: article url (optional)
        pub_date: publication date (optional)
        
    returns:
        formatted article summary
    """
    clean_title = sanitize_title(title)
    clean_desc = beautify_description(description)
    
    summary_parts = []
    
    # add title
    if clean_title:
        summary_parts.append(f"Title: {clean_title}")
    
    # add description
    if clean_desc:
        summary_parts.append(f"Description: {clean_desc}")
    
    # add metadata if available
    metadata_parts = []
    if pub_date:
        metadata_parts.append(f"Date: {pub_date}")
    if link:
        metadata_parts.append(f"Link: {link}")
    
    if metadata_parts:
        summary_parts.append(f"{' | '.join(metadata_parts)}")
    
    return '\n'.join(summary_parts)


def _get_browser_headers() -> dict:
    """get http headers that mimic a real browser"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }


def _extract_from_json_ld(soup: BeautifulSoup) -> str:
    """
    extract article content from json-ld structured data
    this is the most reliable method for corriere della sera
    """
    json_ld_scripts = soup.find_all('script', {'type': 'application/ld+json'})
    
    for json_ld in json_ld_scripts:
        try:
            if json_ld.string:
                data = json.loads(json_ld.string)
                if isinstance(data, dict) and 'articleBody' in data:
                    content = data['articleBody']
                    if content and len(content) > 200:
                        return content
        except (json.JSONDecodeError, Exception):
            continue
    
    return ""


def _clean_soup_for_extraction(soup: BeautifulSoup):
    """remove unwanted html elements that interfere with content extraction"""
    # remove script, style, and navigation elements
    unwanted_tags = [
        "script", "style", "nav", "header", "footer", "aside", "menu",
        "iframe", "noscript", "svg", "form", "button", "link", "meta"
    ]
    for element in soup(unwanted_tags):
        element.decompose()
    
    # remove elements with ad/navigation class names
    unwanted_classes = [
        'ad', 'ads', 'advertisement', 'social-share', 'related-articles',
        'comments', 'newsletter', 'subscription', 'paywall', 'menu',
        'navbar', 'sidebar', 'widget', 'promo', 'banner', 'popup',
        'overlay', 'modal', 'taboola', 'outbrain', 'recommend',
        'share', 'toolbar', 'breadcrumb', 'tag', 'meta'
    ]
    for class_name in unwanted_classes:
        for elem in soup.find_all(class_=re.compile(class_name, re.I)):
            elem.decompose()
    
    # remove elements with navigation/ad id patterns
    unwanted_ids = ['menu', 'nav', 'sidebar', 'footer', 'header', 'comment', 'ad']
    for id_pattern in unwanted_ids:
        for elem in soup.find_all(id=re.compile(id_pattern, re.I)):
            elem.decompose()


def _extract_paragraphs(elements, min_length: int = 50) -> list:
    """extract text from paragraph elements, filtering out short ones"""
    return [
        elem.get_text(strip=True) 
        for elem in elements 
        if len(elem.get_text(strip=True)) > min_length
    ]


def _try_corriere_selectors(soup: BeautifulSoup) -> str:
    """try corriere della sera specific css selectors"""
    selectors = [
        'article .chapter-paragraph p',
        'article .body-text p',
        'article p.text',
        '.article-text p',
        '.story-text p',
        '#content-body p'
    ]
    
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            paragraphs = _extract_paragraphs(elements)
            if len(paragraphs) >= 3:
                return ' '.join(paragraphs)
    
    return ""


def _try_gazzetta_selectors(soup: BeautifulSoup) -> str:
    """try gazzetta dello sport specific css selectors"""
    selectors = [
        'div.content p',                    # main content div
        '.entry-content p',                 # wordpress-style content
        '.wp-block-post-content p',         # wordpress block content
        '.article__body p',
        '.article-body p',
        '.content__body p',
        'article .body p',
        '.text-content p',
        '#article-text p',
        '.story__content p',
        'article p'                         # fallback to any article paragraphs
    ]
    
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            paragraphs = _extract_paragraphs(elements)
            if len(paragraphs) >= 2:  # gazzetta articles can be shorter
                return ' '.join(paragraphs)
    
    return ""


def _try_article_tag(soup: BeautifulSoup) -> str:
    """extract content from article tag"""
    article_tag = soup.find('article')
    if not article_tag:
        return ""
    
    # remove nested unwanted elements
    for unwanted in article_tag.find_all(['aside', 'figure', 'figcaption']):
        unwanted.decompose()
    
    paragraphs = _extract_paragraphs(article_tag.find_all('p'))
    if len(paragraphs) >= 3:
        return ' '.join(paragraphs)
    
    return ""


def _try_common_selectors(soup: BeautifulSoup) -> str:
    """try common news site css selectors"""
    selectors = [
        '[itemprop="articleBody"]',
        '.article-content',
        '.post-content',
        '.entry-content',
        '.story-body',
        '.article-body',
        '.post-body',
        '.content-body',
        '.main-content',
        '.text-content',
        '.article__body',
        '.story-content',
        'main article'
    ]
    
    for selector in selectors:
        content_elem = soup.select_one(selector)
        if content_elem:
            paragraphs = _extract_paragraphs(content_elem.find_all('p'))
            if len(paragraphs) >= 3:
                return ' '.join(paragraphs)
    
    return ""


def _try_main_tag(soup: BeautifulSoup) -> str:
    """extract content from main tag"""
    main_elem = soup.find('main')
    if not main_elem:
        return ""
    
    paragraphs = _extract_paragraphs(main_elem.find_all('p'))
    if len(paragraphs) >= 3:
        return ' '.join(paragraphs)
    
    return ""


def _is_valid_paragraph(p_tag) -> bool:
    """check if a paragraph is likely article content (not navigation/ads)"""
    text = p_tag.get_text(strip=True)
    
    # must be substantial
    if len(text) < 50:
        return False
    
    # skip navigation/metadata keywords
    skip_words = ['cookie', 'privacy', 'terms', 'login', 'subscribe', 'menu']
    if any(word in text.lower() for word in skip_words):
        return False
    
    # skip paragraphs with too many links (likely navigation)
    if len(p_tag.find_all('a')) > 3:
        return False
    
    return True


def _try_body_paragraphs(soup: BeautifulSoup) -> str:
    """fallback: extract valid paragraphs from body"""
    body = soup.find('body')
    if not body:
        return ""
    
    candidate_paragraphs = [
        p.get_text(strip=True) 
        for p in body.find_all('p') 
        if _is_valid_paragraph(p)
    ]
    
    if len(candidate_paragraphs) >= 3:
        return ' '.join(candidate_paragraphs)
    
    return ""


def _clean_extracted_text(text: str) -> str:
    """clean and normalize extracted article text"""
    if not text:
        return text
    
    # normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # remove common italian article prefixes
    text = re.sub(r'^(DAL NOSTRO INVIATO|ROMA|MILANO|di|Di)\s*-?\s*', '', text)
    
    # remove duplicated content (some sites repeat the article text)
    text = _remove_duplicate_content(text)
    
    return text.strip()


def _remove_duplicate_content(text: str) -> str:
    """
    detect and remove duplicated content in the text
    some news sites repeat the article text multiple times
    """
    if not text or len(text) < 200:
        return text
    
    # split text in half and check if they're similar
    mid_point = len(text) // 2
    first_half = text[:mid_point]
    second_half = text[mid_point:]
    
    # check if first 200 chars of each half are very similar
    # (allowing for small differences due to formatting)
    first_sample = first_half[:200].lower()
    second_sample = second_half[:200].lower()
    
    # calculate similarity (simple approach: check if 80% of words match)
    first_words = set(first_sample.split())
    second_words = set(second_sample.split())
    
    if len(first_words) > 0:
        similarity = len(first_words & second_words) / len(first_words)
        
        # if very similar, it's likely duplicated - return first half
        if similarity > 0.8:
            return first_half.strip()
    
    return text


def scrape_article_content(url: str, timeout: int = 10) -> str:
    """
    scrape full article content from a url
    uses multiple strategies: json-ld, css selectors, and smart paragraph extraction
    
    args:
        url: article url to scrape
        timeout: request timeout in seconds
        
    returns:
        cleaned article text content or error message
    """
    try:
        response = requests.get(url, headers=_get_browser_headers(), timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # strategy 1: json-ld structured data (best for corriere della sera)
        content = _extract_from_json_ld(soup)
        if content:
            return _clean_extracted_text(content)
        
        # prepare soup for paragraph extraction
        _clean_soup_for_extraction(soup)
        
        # strategy 2: site-specific selectors (corriere, gazzetta)
        content = _try_corriere_selectors(soup)
        if content:
            return _clean_extracted_text(content)
        
        content = _try_gazzetta_selectors(soup)
        if content:
            return _clean_extracted_text(content)
        
        # strategy 3: article tag
        content = _try_article_tag(soup)
        if content:
            return _clean_extracted_text(content)
        
        # strategy 4: common news site selectors
        content = _try_common_selectors(soup)
        if content:
            return _clean_extracted_text(content)
        
        # strategy 5: main tag
        content = _try_main_tag(soup)
        if content:
            return _clean_extracted_text(content)
        
        # strategy 6: fallback to body paragraphs
        content = _try_body_paragraphs(soup)
        if content:
            return _clean_extracted_text(content)
        
        # no content found
        return "limited content extracted (0 chars) - article may be behind paywall or use dynamic loading"
        
    except Exception as e:
        return f"error scraping content: {str(e)}"


def is_today_news(pub_date_str: str) -> bool:
    """
    check if a publication date is from today
    
    args:
        pub_date_str: publication date string from rss feed
        
    returns:
        true if the news is from today
    """
    if not pub_date_str:
        return True  # include items without date to be safe
    
    try:
        # parse the date string
        pub_date = date_parser.parse(pub_date_str)
        today = date.today()
        
        # check if it's today's date
        return pub_date.date() == today
        
    except Exception:
        return True  # include items with unparseable dates to be safe


def extract_guid_link(item_xml: str) -> str:
    """
    extract the permalink url from guid element in rss item
    
    args:
        item_xml: xml string of the rss item
        
    returns:
        permalink url or empty string if not found
    """
    try:
        # parse the xml
        root = ET.fromstring(f"<root>{item_xml}</root>")
        
        # find guid element with ispermalink="true"
        guid_elem = root.find('.//guid[@isPermalink="true"]')
        if guid_elem is not None and guid_elem.text:
            return guid_elem.text.strip()
        
        # fallback: try any guid element
        guid_elem = root.find('.//guid')
        if guid_elem is not None and guid_elem.text:
            return guid_elem.text.strip()
            
        return ""
        
    except Exception:
        return ""


def create_news_summary(title: str, description: str, link: str, pub_date: str, 
                       title_limit: int = 100, desc_limit: int = 300, 
                       scrape_content: bool = True, content_limit: int = 3000,
                       summarize_content: bool = False, summary_method: str = 'auto') -> Dict[str, Any]:
    """
    create a comprehensive news summary with optional content scraping and summarization
    
    args:
        title: article title
        description: article description from rss
        link: article url
        pub_date: publication date
        title_limit: maximum title length
        desc_limit: maximum description length
        scrape_content: whether to scrape full article content
        content_limit: maximum scraped content length (default: 3000)
        summarize_content: whether to summarize scraped content (default: false)
        summary_method: summarization method - 'auto', 'extractive', 'keyword', or 'lead' (default: 'auto')
        
    returns:
        dictionary with cleaned title, description, link, date and scraped content (optionally summarized)
    """
    from utils.text_summarizer import auto_summarize
    
    # clean and truncate title
    clean_title = sanitize_title(title)
    if len(clean_title) > title_limit:
        clean_title = clean_title[:title_limit-3] + "..."
    
    # clean and truncate description
    clean_desc = beautify_description(description)
    if len(clean_desc) > desc_limit:
        clean_desc = clean_desc[:desc_limit-3] + "..."
    
    # scrape full content if requested
    scraped_content = ""
    if scrape_content and link:
        scraped_content = scrape_article_content(link)
        
        # summarize if requested
        if summarize_content and scraped_content:
            if not scraped_content.startswith("error") and not scraped_content.startswith("limited"):
                scraped_content = auto_summarize(scraped_content, max_length=content_limit, method=summary_method)
        else:
            # just limit to reasonable size
            if len(scraped_content) > content_limit and not scraped_content.startswith("error") and not scraped_content.startswith("limited"):
                scraped_content = scraped_content[:content_limit] + "..."
    
    return {
        "title": clean_title,
        "description": clean_desc,
        # "link": link,
        # "pub_date": pub_date,
        "scraped_content": scraped_content
    }
