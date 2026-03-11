"""Generate mindmap data structure from summarized text."""

import re


def _extract_key_phrases(text):
    """Extract key phrases from text using simple frequency analysis."""
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "out", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "both", "each", "few", "more", "most", "other",
        "some", "such", "no", "nor", "not", "only", "own", "same", "so",
        "than", "too", "very", "just", "because", "but", "and", "or", "if",
        "while", "although", "this", "that", "these", "those", "i", "me",
        "my", "we", "our", "you", "your", "he", "him", "his", "she", "her",
        "it", "its", "they", "them", "their", "what", "which", "who",
        "whom", "about", "also", "like", "get", "got", "go", "going",
        "know", "think", "make", "take", "come", "see", "look", "want",
        "give", "use", "find", "tell", "ask", "work", "seem", "feel",
        "try", "leave", "call", "keep", "let", "begin", "show", "hear",
        "play", "run", "move", "live", "believe", "bring", "happen",
        "write", "provide", "sit", "stand", "lose", "pay", "meet",
        "include", "continue", "set", "learn", "change", "lead",
        "understand", "watch", "follow", "stop", "create", "speak",
        "read", "allow", "add", "spend", "grow", "open", "walk", "win",
        "offer", "remember", "love", "consider", "appear", "buy", "wait",
        "serve", "die", "send", "expect", "build", "stay", "fall", "cut",
        "reach", "kill", "remain", "really", "actually", "something",
        "thing", "things", "much", "many", "well", "way", "even", "new",
        "one", "two", "three", "four", "five", "still", "back", "up",
        "down", "right", "left", "now", "long", "little", "just", "dont",
        "im", "youre", "theyre", "weve", "ive", "youve", "theyve", "hes",
        "shes", "its", "were", "thats", "whats", "ill", "youll", "theyll",
        "wont", "cant", "couldnt", "shouldnt", "wouldnt", "gonna", "wanna",
        "gotta", "yeah", "okay", "um", "uh", "oh", "ah", "hey", "hi",
        "hello", "bye", "thanks", "thank", "please", "sorry",
    }

    words = re.findall(r'\b[a-z]+\b', text.lower())
    words = [w for w in words if w not in stop_words and len(w) > 2]

    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1

    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:10]]


def _split_into_segments(text, num_segments=4):
    """Split text into roughly equal segments for mindmap branches."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) <= num_segments:
        return sentences

    segment_size = max(1, len(sentences) // num_segments)
    segments = []
    for i in range(0, len(sentences), segment_size):
        chunk = sentences[i:i + segment_size]
        segments.append(" ".join(chunk))
        if len(segments) >= num_segments:
            # Append remaining sentences to the last segment
            remaining = sentences[i + segment_size:]
            if remaining:
                segments[-1] += " " + " ".join(remaining)
            break

    return segments


def _get_segment_title(segment, key_phrases):
    """Generate a short title for a segment based on key phrases found in it."""
    segment_lower = segment.lower()
    found = [kp for kp in key_phrases if kp in segment_lower]
    if found:
        return " & ".join(found[:2]).title()
    # Fallback: use first few meaningful words
    words = re.findall(r'\b[A-Za-z]+\b', segment)
    meaningful = [w for w in words if len(w) > 3][:3]
    return " ".join(meaningful).title() if meaningful else "Topic"


def generate_mindmap(title, summary):
    """Generate a mindmap data structure from a title and summary.

    Args:
        title: The central topic (e.g., video title).
        summary: The summarized text.

    Returns:
        A dictionary representing the mindmap in a nested structure
        compatible with markmap rendering.
    """
    if not summary or not summary.strip():
        return {"name": title, "children": []}

    key_phrases = _extract_key_phrases(summary)
    segments = _split_into_segments(summary)

    children = []
    used_titles = set()
    for segment in segments:
        seg_title = _get_segment_title(segment, key_phrases)
        # Ensure unique titles
        original = seg_title
        counter = 1
        while seg_title in used_titles:
            counter += 1
            seg_title = f"{original} ({counter})"
        used_titles.add(seg_title)

        # Create sub-points from the segment's sentences
        sub_sentences = re.split(r'(?<=[.!?])\s+', segment.strip())
        sub_children = []
        for sent in sub_sentences:
            sent = sent.strip()
            if sent and len(sent) > 10:
                # Truncate very long sentences for readability
                display = sent[:120] + "..." if len(sent) > 120 else sent
                sub_children.append({"name": display})

        children.append({
            "name": seg_title,
            "children": sub_children if sub_children else [{"name": segment[:100]}]
        })

    return {
        "name": title,
        "children": children
    }
