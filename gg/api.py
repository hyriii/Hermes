"""
Hermes API Module
Handles Groq API communication, Google Books search, and data models.
"""

import requests
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from groq import Groq

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class SummaryResult:
    english_summary: str = ""
    arabic_summary: str = ""
    key_points: List[str] = field(default_factory=list)
    scientific_terms: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Client Instructions
# ---------------------------------------------------------------------------

CLIENT_INSTRUCTIONS = {
    "system_prompt": (
        "You are a professional academic assistant. Summarize provided text "
        "accurately. Use ONLY the provided information. Do not add outside "
        "information or hallucinations."
    ),
    "temperature": 0.1,
    "rules": [
        "NO EXTERNAL KNOWLEDGE: Use ONLY text provided in current input",
        "ARABIC RENDERING: Never use fix_text on text before sending to API",
        "SPACING FIX: Ensure words are not merged in fix_text function",
        "PPTX FIX: Wrap all slide content in fix_text() before adding to slides",
    ],
}


# ---------------------------------------------------------------------------
# Google Books Search
# ---------------------------------------------------------------------------

def search_google_books(query: str, max_results: int = 10) -> List[Dict]:
    """Search Google Books API."""
    try:
        url = (
            "https://www.googleapis.com/books/v1/volumes"
            f"?q={requests.utils.quote(query)}"
            f"&maxResults={max_results}"
        )
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return []

        data = response.json()
        items = data.get("items", [])
        books = []
        for item in items:
            vol = item.get("volumeInfo", {})
            pub_date = vol.get("publishedDate", "")
            year = pub_date[:4] if pub_date else "Unknown"
            authors = vol.get("authors", ["Unknown"])
            description = vol.get("description", "")
            categories = vol.get("categories", [])
            language = vol.get("language", "en")
            thumbnail = vol.get("imageLinks", {}).get("thumbnail", "")

            books.append(
                {
                    "id": item.get("id"),
                    "title": vol.get("title", "Unknown"),
                    "author": ", ".join(authors),
                    "year": year,
                    "description": description,
                    "page_count": vol.get("pageCount", 0),
                    "categories": categories,
                    "language": language,
                    "thumbnail": thumbnail,
                }
            )
        return books
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Language Detection
# ---------------------------------------------------------------------------

def detect_dominant_language(text: str) -> str:
    """Detect dominant language (ar / en)."""
    arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
    english_chars = sum(
        1 for c in text if ("a" <= c <= "z") or ("A" <= c <= "Z")
    )
    total_sample = min(len(text), 1000)
    if total_sample == 0:
        return "en"

    arabic_ratio = arabic_chars / total_sample
    english_ratio = english_chars / total_sample

    if arabic_ratio > 0.3:
        return "ar"
    elif english_ratio > 0.3:
        return "en"
    return "ar" if arabic_chars > english_chars else "en"


# ---------------------------------------------------------------------------
# Text Splitting
# ---------------------------------------------------------------------------

def split_text_by_pages(text: str, doc=None) -> List[Dict]:
    """Split text by pages (or chunks) for sequential processing."""
    if doc:
        pages = []
        for i, page in enumerate(doc):
            page_text = page.get_text()
            if page_text and page_text.strip():
                pages.append({"page_num": i + 1, "text": page_text.strip()})
        return pages

    chunk_size = 12000  # ~1500-3000 words per chunk
    pages = []
    text = text.strip()
    for i in range(0, len(text), chunk_size):
        chunk = text[i : i + chunk_size].strip()
        if chunk:
            pages.append({"page_num": len(pages) + 1, "text": chunk})
    return pages


# ---------------------------------------------------------------------------
# Structured Prompt Builder
# ---------------------------------------------------------------------------

def _build_analysis_prompt(
    section_text: str,
    section_num: int,
    book_info: Dict,
    page_range: tuple = None,
) -> str:
    """
    Build a prompt that asks the AI to return structured JSON-like output
    instead of relying on [SECTION] markers.
    """
    is_arabic = detect_dominant_language(section_text) == "ar"
    book_title = book_info.get("title", "the document")

    page_instruction = ""
    if page_range and page_range[0] and page_range[1]:
        page_instruction = (
            f" Focus ONLY on pages {page_range[0]} to {page_range[1]} "
            "from the source."
        )

    if is_arabic:
        prompt = f"""Provide a comprehensive academic summary of the following text chunk. Extract ALL key concepts, main ideas, and important details.

IMPORTANT: Write the summary and titles in the ORIGINAL language of the provided text. Do not translate. The output MUST be in Arabic since the source text is in Arabic.

Create 4-8 detailed sections that comprehensively cover ALL aspects of this text chunk.

Your response MUST use this exact structure for every section:

## Section Title Here
Content for this section...

{page_instruction}

النص:
{section_text}

⚠️ استخدم النص الأصلي فقط - لا تترجم إلى الإنجليزية. غطِّ جميع المحتوى بالتفصيل."""
    else:
        prompt = f"""Provide a comprehensive academic summary of the following text chunk. Extract ALL key concepts, main ideas, and important details.

IMPORTANT: Write the summary and titles in the ORIGINAL language of the provided text. Do not translate. The output MUST be in English since the source text is in English.

Create 4-8 detailed sections that comprehensively cover ALL aspects of this text chunk.

Your response MUST use this exact structure for every section:

## Section Title Here
Content for this section...

{page_instruction}

Text:
{section_text}

⚠️ Use source text only - do not translate. Cover ALL content in detail."""
    return prompt


# ---------------------------------------------------------------------------
# Groq API Call
# ---------------------------------------------------------------------------

def analyze_section(
    section_text: str,
    section_num: int,
    book_info: Dict,
    api_key: str,
    mode: str = "Quick Summary",
    page_range: tuple = None,
) -> Optional[Dict]:
    """
    Send a text chunk to Groq API and return structured content.
    Returns None on failure.
    """
    if not section_text or len(section_text.strip()) < 100:
        return {
            "section_num": section_num,
            "content": (
                "Error: Could not read PDF content. "
                "The extracted text is empty or too short."
            ),
        }

    # Build the prompt (does NOT rely on [SECTION] markers)
    user_prompt = _build_analysis_prompt(
        section_text, section_num, book_info, page_range
    )

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": CLIENT_INSTRUCTIONS["system_prompt"]},
                {"role": "user", "content": user_prompt},
            ],
            temperature=CLIENT_INSTRUCTIONS["temperature"],
            max_tokens=8000,
        )

        content = response.choices[0].message.content
        if not content or not content.strip():
            return None

        return {"section_num": section_num, "content": content.strip()}

    except Exception as e:
        # We return a dict with error info so the caller can decide how to handle
        return {"section_num": section_num, "content": f"API Error: {str(e)}", "error": True}