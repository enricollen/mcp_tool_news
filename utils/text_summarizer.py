"""
text summarization utilities without llm calls
uses extractive summarization techniques
"""

import re
from typing import List, Tuple
from collections import Counter


def _clean_sentence(sentence: str) -> str:
    """clean and normalize a sentence"""
    # remove extra whitespace
    sentence = re.sub(r'\s+', ' ', sentence)
    return sentence.strip()


def _split_into_sentences(text: str) -> List[str]:
    """
    split text into sentences
    handles common abbreviations and edge cases
    """
    # replace common abbreviations to avoid false splits
    text = re.sub(r'\b(Dr|Mr|Mrs|Ms|Prof|Sr|Jr)\.', r'\1<DOT>', text)
    
    # split on sentence endings
    sentences = re.split(r'[.!?]+\s+', text)
    
    # restore dots and clean
    sentences = [_clean_sentence(s.replace('<DOT>', '.')) for s in sentences if s.strip()]
    
    return sentences


def _calculate_word_frequencies(sentences: List[str]) -> dict:
    """
    calculate word frequency scores for ranking
    filters out common stop words
    """
    # italian and english stop words (common ones)
    stop_words = {
        # italian
        'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una', 'di', 'a', 'da', 'in', 
        'con', 'su', 'per', 'tra', 'fra', 'del', 'dello', 'della', 'dei', 'degli', 'delle',
        'al', 'allo', 'alla', 'ai', 'agli', 'alle', 'dal', 'dallo', 'dalla', 'dai', 'dagli',
        'dalle', 'nel', 'nello', 'nella', 'nei', 'negli', 'nelle', 'sul', 'sullo', 'sulla',
        'sui', 'sugli', 'sulle', 'che', 'è', 'sono', 'hai', 'ha', 'hanno', 'come', 'più',
        'anche', 'se', 'non', 'ma', 'quando', 'dove', 'chi', 'cosa', 'quale', 'questo',
        'questa', 'questi', 'queste', 'quello', 'quella', 'quelli', 'quelle', 'ogni',
        'altro', 'altra', 'altri', 'altre', 'molto', 'poco', 'tanto', 'troppo',
        # english
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
        'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might',
        'can', 'this', 'that', 'these', 'those', 'as', 'if', 'when', 'where', 'who',
        'which', 'what', 'how', 'why', 'all', 'each', 'every', 'some', 'any', 'no',
        'not', 'very', 'more', 'most', 'much', 'many', 'few', 'less', 'least'
    }
    
    # collect all words
    all_words = []
    for sentence in sentences:
        words = re.findall(r'\b\w+\b', sentence.lower())
        all_words.extend([w for w in words if w not in stop_words and len(w) > 2])
    
    # calculate frequencies
    word_freq = Counter(all_words)
    
    # normalize frequencies (0-1 scale)
    if word_freq:
        max_freq = max(word_freq.values())
        word_freq = {word: freq / max_freq for word, freq in word_freq.items()}
    
    return word_freq


def _score_sentences(sentences: List[str], word_freq: dict) -> List[Tuple[int, float, str]]:
    """
    score sentences based on word frequency and position
    returns list of (index, score, sentence) tuples
    """
    scored_sentences = []
    
    for idx, sentence in enumerate(sentences):
        # skip very short sentences
        if len(sentence.split()) < 5:
            continue
        
        # calculate word frequency score
        words = re.findall(r'\b\w+\b', sentence.lower())
        sentence_score = sum(word_freq.get(word, 0) for word in words)
        
        # normalize by sentence length to avoid bias towards long sentences
        if len(words) > 0:
            sentence_score /= len(words)
        
        # boost score for sentences at the beginning (usually more important)
        position_boost = 1.0
        if idx < 3:  # first 3 sentences
            position_boost = 1.3
        elif idx < 5:  # next 2 sentences
            position_boost = 1.15
        
        sentence_score *= position_boost
        
        scored_sentences.append((idx, sentence_score, sentence))
    
    return scored_sentences


def extractive_summary(text: str, num_sentences: int = 3, max_length: int = 500) -> str:
    """
    create an extractive summary by selecting the most important sentences
    
    args:
        text: original text to summarize
        num_sentences: number of sentences to extract (default: 3)
        max_length: maximum summary length in characters (default: 500)
        
    returns:
        summary text composed of key sentences
    """
    if not text or len(text) < 100:
        return text
    
    # split into sentences
    sentences = _split_into_sentences(text)
    
    # if text is already short, return as-is
    if len(sentences) <= num_sentences:
        return text
    
    # calculate word frequencies
    word_freq = _calculate_word_frequencies(sentences)
    
    if not word_freq:
        # fallback: return first sentences
        return ' '.join(sentences[:num_sentences])
    
    # score sentences
    scored_sentences = _score_sentences(sentences, word_freq)
    
    # sort by score (descending)
    scored_sentences.sort(key=lambda x: x[1], reverse=True)
    
    # select top sentences
    selected = scored_sentences[:num_sentences]
    
    # sort by original position to maintain reading flow
    selected.sort(key=lambda x: x[0])
    
    # build summary
    summary_parts = [sentence for _, _, sentence in selected]
    summary = ' '.join(summary_parts)
    
    # trim to max length if needed
    if len(summary) > max_length:
        summary = summary[:max_length].rsplit(' ', 1)[0] + '...'
    
    return summary


def keyword_based_summary(text: str, max_length: int = 500) -> str:
    """
    create a summary by extracting sentences with the most important keywords
    focuses on entities and key terms
    
    args:
        text: original text to summarize
        max_length: maximum summary length in characters (default: 500)
        
    returns:
        summary text
    """
    if not text or len(text) < 100:
        return text
    
    sentences = _split_into_sentences(text)
    
    if len(sentences) <= 2:
        return text
    
    # identify potential keywords (capitalized words, numbers, quoted text)
    keywords = set()
    
    # capitalized words (likely names, places, organizations)
    keywords.update(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text))
    
    # numbers with context
    keywords.update(re.findall(r'\b\d+(?:[.,]\d+)?(?:\s*%|€|\$|km|km/h|mila|milioni|miliardi)?\b', text))
    
    # score sentences by keyword density
    scored = []
    for idx, sentence in enumerate(sentences):
        if len(sentence.split()) < 5:
            continue
        
        keyword_count = sum(1 for kw in keywords if kw in sentence)
        score = keyword_count / len(sentence.split()) if sentence else 0
        
        # boost first sentences
        if idx < 2:
            score *= 1.3
        
        scored.append((idx, score, sentence))
    
    # select top 3 sentences
    scored.sort(key=lambda x: x[1], reverse=True)
    selected = scored[:3]
    selected.sort(key=lambda x: x[0])
    
    summary = ' '.join(s for _, _, s in selected)
    
    if len(summary) > max_length:
        summary = summary[:max_length].rsplit(' ', 1)[0] + '...'
    
    return summary


def lead_summary(text: str, max_length: int = 500) -> str:
    """
    simple lead-based summary: extract the first few sentences
    works well for news articles where key info is at the beginning
    
    args:
        text: original text to summarize
        max_length: maximum summary length in characters (default: 500)
        
    returns:
        summary text
    """
    if not text or len(text) < 100:
        return text
    
    sentences = _split_into_sentences(text)
    
    # take first 2-3 sentences
    summary_parts = []
    current_length = 0
    
    for sentence in sentences[:4]:  # check up to 4 sentences
        sentence_length = len(sentence)
        if current_length + sentence_length > max_length:
            break
        summary_parts.append(sentence)
        current_length += sentence_length + 1  # +1 for space
    
    if not summary_parts:
        # fallback if first sentence is too long
        return text[:max_length].rsplit(' ', 1)[0] + '...'
    
    return ' '.join(summary_parts)


def auto_summarize(text: str, max_length: int = 500, method: str = 'keyword') -> str:
    """
    automatically summarize text using the best method
    
    args:
        text: original text to summarize
        max_length: maximum summary length in characters (default: 500)
        method: summarization method - 'auto', 'extractive', 'keyword', or 'lead'
        
    returns:
        summary text
    """
    if not text or text.startswith('error') or text.startswith('limited'):
        return text
    
    # if already short enough, return as-is
    if len(text) <= max_length:
        return text
    
    if method == 'extractive':
        return extractive_summary(text, num_sentences=3, max_length=max_length)
    elif method == 'keyword':
        return keyword_based_summary(text, max_length=max_length)
    elif method == 'lead':
        return lead_summary(text, max_length=max_length)
    else:  # 'auto'
        # use extractive for longer texts, lead for shorter
        if len(text) > 1500:
            return extractive_summary(text, num_sentences=3, max_length=max_length)
        else:
            return lead_summary(text, max_length=max_length)

