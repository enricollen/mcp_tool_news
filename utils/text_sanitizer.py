"""
text sanitization and beautification utilities for rss content
"""

import re
from html import unescape
from typing import Optional


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
