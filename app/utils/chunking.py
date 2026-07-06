from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    text: str
    index: int


# Strategy 1: Fixed-size character chunks

def fixed_size_chunks(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[TextChunk]:
    """Split *text* into fixed-size character windows with optional overlap.

    Args:
        text:       Raw text to split.
        chunk_size: Maximum number of characters per chunk.
        overlap:    Number of trailing characters carried into the next chunk.
                    Must be < chunk_size.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer.")
    overlap = min(overlap, chunk_size - 1)

    chunks: list[TextChunk] = []
    start = 0
    index = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(TextChunk(text=chunk_text, index=index))
            index += 1
        start += chunk_size - overlap

    return chunks


# Strategy 2: Sentence-boundary chunks

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

def sentence_chunks(
    text: str,
    max_sentences: int = 5,
    overlap_sentences: int = 1,
) -> list[TextChunk]:
    """Split *text* at sentence boundaries and group into chunks.

    Args:
        text:               Raw text to split.
        max_sentences:      Maximum sentences per chunk.
        overlap_sentences:  Sentences shared between consecutive chunks.
                            Must be < max_sentences.
    """
    if max_sentences <= 0:
        raise ValueError("max_sentences must be a positive integer.")
    overlap_sentences = min(overlap_sentences, max_sentences - 1)

    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
    if not sentences:
        return []

    chunks: list[TextChunk] = []
    index = 0
    i = 0
    step = max(1, max_sentences - overlap_sentences)

    while i < len(sentences):
        group = sentences[i : i + max_sentences]
        chunk_text = " ".join(group).strip()
        if chunk_text:
            chunks.append(TextChunk(text=chunk_text, index=index))
            index += 1
        i += step

    return chunks
