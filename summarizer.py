"""Extractive text summarization using TF-IDF sentence scoring."""

import math
import re
from collections import Counter


def _split_sentences(text):
    """Split text into sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _tokenize(text):
    """Tokenize text into lowercase words, removing punctuation."""
    return re.findall(r'\b[a-z]+\b', text.lower())


def _compute_tf(words):
    """Compute term frequency for a list of words."""
    count = Counter(words)
    total = len(words)
    if total == 0:
        return {}
    return {word: freq / total for word, freq in count.items()}


def _compute_idf(sentences_words):
    """Compute inverse document frequency across sentences."""
    n = len(sentences_words)
    if n == 0:
        return {}
    all_words = set()
    for words in sentences_words:
        all_words.update(words)

    idf = {}
    for word in all_words:
        doc_count = sum(1 for words in sentences_words if word in set(words))
        idf[word] = math.log(n / (1 + doc_count)) + 1
    return idf


def summarize(text, num_sentences=5):
    """Summarize text using extractive TF-IDF scoring.

    Args:
        text: The input text to summarize.
        num_sentences: Maximum number of sentences in the summary.

    Returns:
        A string containing the summary sentences.
    """
    if not text or not text.strip():
        return ""

    sentences = _split_sentences(text)
    if len(sentences) <= num_sentences:
        return text.strip()

    sentences_words = [_tokenize(s) for s in sentences]
    idf = _compute_idf(sentences_words)

    scored = []
    for i, (sentence, words) in enumerate(zip(sentences, sentences_words)):
        tf = _compute_tf(words)
        score = sum(tf.get(w, 0) * idf.get(w, 0) for w in set(words))
        # Slight boost for earlier sentences (positional bias)
        position_boost = 1.0 / (1.0 + 0.1 * i)
        scored.append((i, sentence, score * position_boost))

    scored.sort(key=lambda x: x[2], reverse=True)
    top = scored[:num_sentences]
    # Restore original order
    top.sort(key=lambda x: x[0])

    return " ".join(item[1] for item in top)
