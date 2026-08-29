"""
Document Tool
=============
Extracts clean text from an uploaded supplier RFP PDF.
Deterministic, no LLM involved.
"""
from __future__ import annotations

import io
import re
from typing import Union

from pypdf import PdfReader


def extract_text_from_pdf(file: Union[str, io.BytesIO, bytes]) -> str:
    """
    Extract and lightly clean text from a PDF.

    Accepts a file path, raw bytes, or a file-like object (e.g. Streamlit's
    UploadedFile, which behaves like a BytesIO stream).
    """
    if isinstance(file, (bytes, bytearray)):
        file = io.BytesIO(file)

    reader = PdfReader(file)
    pages_text = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages_text.append(f"\n--- Page {i + 1} ---\n{text}")

    full_text = "\n".join(pages_text)
    return _clean_text(full_text)


def _clean_text(text: str) -> str:
    # Collapse excessive whitespace while preserving paragraph breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate_for_prompt(text: str, max_chars: int = 12000) -> str:
    """Guard against oversized prompts; keeps head and tail of the document."""
    if len(text) <= max_chars:
        return text
    head = text[: int(max_chars * 0.7)]
    tail = text[-int(max_chars * 0.3):]
    return head + "\n\n...[truncated]...\n\n" + tail
