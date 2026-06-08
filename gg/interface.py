"""
Hermes Interface Module
Streamlit UI, CSS styling, session state, and main application flow.
"""

import re
import sys
import os

import streamlit as st

# Ensure imports work from the project directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import (
    search_google_books,
    detect_dominant_language,
    split_text_by_pages,
    analyze_section,
)
from logic import (
    fix_text,
    fix_arabic,
    format_text_for_output,
    is_arabic_text,
    extract_text_from_pdf,
    parse_content_into_sections,
    create_creative_pptx,
    create_hermes_pdf,
    inspect_pptx_arabic_correctness,
    download_amiri_font,
)

# ===================================================================
# Session State Initialization
# ===================================================================

def init_session_state():
    """Initialize all session state keys."""
    defaults = {
        "search_results": {},
        "selected_book": None,
        "pdf_text": "",
        "pdf_page_range": None,
        "summary_output": "",
        "pptx_file": None,
        "sections_data": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ===================================================================
# CSS / Theme
# ===================================================================

HERMES_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@200;300;400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&display=swap');

    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #1a1a2e 100%);
        background-attachment: fixed;
        min-height: 100vh;
    }

    .stMarkdownContainer, .stTextArea, .stTextInput, .stNumberInput, .stRadio, .stSelectbox {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
        padding: 15px !important;
        margin: 10px 0 !important;
    }

    .stApp, .stApp p, .stApp div, .stApp span {
        color: #e0e0e0 !important;
        font-family: 'Cairo', 'Arial', sans-serif !important;
    }

    .stApp p[dir="rtl"], .stApp div[dir="rtl"], .stApp span[dir="rtl"] {
        font-family: 'Cairo', 'Arial', sans-serif !important;
        font-weight: 400 !important;
        text-align: right !important;
    }

    h1, h2, h3 {
        font-family: 'Cairo', 'Cinzel', serif !important;
        color: #FFD700 !important;
        text-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
        font-weight: 700 !important;
    }

    h1 {
        font-size: 2.8em !important;
        background: linear-gradient(45deg, #FFD700, #FFA500, #FFD700);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text;
    }

    section[data-testid="stSidebar"] {
        background: rgba(26, 26, 46, 0.8) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
        border-right: 2px solid rgba(255, 215, 0, 0.3) !important;
        box-shadow: 5px 0 15px rgba(0, 0, 0, 0.5) !important;
    }

    section[data-testid="stSidebar"] * {
        color: #FFD700 !important;
        font-family: 'Cairo', sans-serif !important;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #FFD700 !important;
        text-shadow: 0 0 10px rgba(255, 215, 0, 0.5) !important;
    }

    .stButton > button {
        background: rgba(255, 215, 0, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 2px solid rgba(255, 215, 0, 0.5) !important;
        color: #FFD700 !important;
        font-family: 'Cairo', 'Cinzel', serif !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.2) !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        background: rgba(255, 215, 0, 0.2) !important;
        box-shadow: 0 6px 20px rgba(255, 215, 0, 0.4) !important;
        transform: translateY(-2px) !important;
        border-color: #FFD700 !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 12px !important;
        padding: 5px !important;
        gap: 8px !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border: 1px solid rgba(255, 215, 0, 0.3) !important;
        border-radius: 8px !important;
        color: #e0e0e0 !important;
        font-family: 'Cairo', sans-serif !important;
        transition: all 0.3s ease !important;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(255, 215, 0, 0.2) !important;
        color: #FFD700 !important;
        border-color: #FFD700 !important;
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.3) !important;
    }

    .stDownloadButton > button {
        background: rgba(0, 102, 204, 0.8) !important;
        backdrop-filter: blur(10px) !important;
        border: 2px solid rgba(0, 191, 255, 0.5) !important;
        color: #FFD700 !important;
        font-family: 'Cairo', sans-serif !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0, 191, 255, 0.2) !important;
    }

    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 215, 0, 0.3) !important;
        border-radius: 10px !important;
        color: #FFD700 !important;
        font-family: 'Cairo', sans-serif !important;
    }

    .stExpander {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(255, 215, 0, 0.2) !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    }

    .stAlert {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px) !important;
        border-left: 4px solid #FFD700 !important;
        border-radius: 10px !important;
        color: #e0e0e0 !important;
    }

    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px)!important;
        border: 1px solid rgba(255, 215, 0, 0.3) !important;
        border-radius: 8px !important;
        color: #e0e0e0 !important;
        font-family: 'Cairo', sans-serif !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
        border-color: #FFD700 !important;
        box-shadow: 0 0 10px rgba(255, 215, 0, 0.3) !important;
    }

    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); border-radius: 10px; }
    ::-webkit-scrollbar-thumb { background: rgba(255, 215, 0, 0.3); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255, 215, 0, 0.5); }
</style>
"""


# ===================================================================
# Sidebar
# ===================================================================

def render_sidebar():
    """
    Render the sidebar with settings.
    Returns (api_key, mode, page_from, page_to, file_name_input).
    """
    with st.sidebar:
        st.header("🔑 Settings")
        api_key = st.text_input("API Key", type="password", help="Get from console.groq.com")

        if not api_key:
            st.info("Enter API key to continue")
            st.stop()
        elif not api_key.startswith("gsk_"):
            st.error("Invalid format. Must start with 'gsk_'")
            st.stop()

        st.divider()
        st.subheader("📊 Output Mode")
        mode = st.radio(
            "Choose mode:",
            ["Quick Summary", "Detailed Explanation"],
            label_visibility="visible",
            captions=["5 key insights", "In-depth explanations"],
        )

        st.divider()
        st.subheader("📄 Page Range")
        col1, col2 = st.columns(2)
        with col1:
            page_from = st.number_input("From", min_value=1, value=1)
        with col2:
            page_to = st.number_input("To", min_value=1, value=1)
        st.divider()
        st.subheader("📁 File Name")
        file_name_input = st.text_input("سمِّ ملفك يا بطل (File Name)", "Summary")
        st.divider()
        st.caption("💡 Tip: Upload a PDF or paste text")

    return api_key, mode, page_from, page_to, file_name_input


# ===================================================================
# Tab 1 – Search Books
# ===================================================================

def render_search_tab():
    """
    Render the Google Books search tab.
    Returns True if a book was just selected (to signal a potential rerun).
    """
    st.subheader("Search Google Books")
    search_query = st.text_input("Book title or author:", placeholder="e.g., Clean Code")

    if st.button("🔍 Search", type="primary", use_container_width=True):
        if search_query.strip():
            with st.spinner("Searching..."):
                try:
                    books = search_google_books(search_query.strip())
                    if books:
                        st.session_state["search_results"] = {book["id"]: book for book in books}
                        st.toast(f"Found {len(books)} books!", icon="✅")
                    else:
                        st.warning("No books found")
                except Exception as e:
                    st.error(f"Search failed: {e}")
        else:
            st.warning("Enter a search term")

    search_results = st.session_state.get("search_results", {})
    if search_results:
        st.markdown("---")
        for book_id, book in search_results.items():
            title_display = format_text_for_output(book["title"][:30])
            with st.expander(f"📗 {title_display}...", expanded=False):
                st.write(f"**Author:** {format_text_for_output(book['author'])}")
                st.write(f"**Year:** {book['year']}")
                if book.get("description"):
                    desc = format_text_for_output(book["description"][:200])
                    st.write(f"**Description:** {desc}...")
                if st.button("✅ Select", key=f"select_{book_id}", use_container_width=True):
                    st.session_state["selected_book"] = book
                    book_title = book.get("title", "")
                    book_author = book.get("author", "")
                    book_desc = book.get("description", "")
                    combined = f"Book: {book_title}\nAuthor: {book_author}\n\nDescription:\n{book_desc}"
                    st.session_state["pdf_text"] = combined
                    st.success(f"⚖️ Book '{format_text_for_output(book_title)}' selected by Hermes. Ready to summarize.")


# ===================================================================
# Tab 2 – Upload PDF
# ===================================================================

def render_upload_tab(page_from: int, page_to: int):
    """
    Render the PDF upload tab.
    """
    st.subheader("Upload PDF Book")
    uploaded_file = st.file_uploader("Choose PDF file", type="pdf", accept_multiple_files=False)

    if uploaded_file:
        page_range = (page_from, page_to) if page_from and page_to else None

        if st.button("📤 Extract Text from PDF", type="primary", use_container_width=True):
            with st.spinner("Extracting text from PDF..."):
                try:
                    pdf_text = extract_text_from_pdf(uploaded_file, page_range)

                    if pdf_text:
                        st.session_state["pdf_text"] = pdf_text
                        st.session_state["pdf_page_range"] = page_range
                        st.session_state["selected_book"] = {
                            "title": uploaded_file.name.replace(".pdf", "")[:30],
                            "author": "Uploaded Document",
                            "year": "Unknown",
                            "language": detect_dominant_language(pdf_text),
                        }
                        st.success(f"✅ Extracted {len(pdf_text)} characters successfully!")
                    else:
                        st.error("❌ Failed to extract text from PDF")

                except Exception as e:
                    st.error(f"❌ PDF extraction error: {str(e)}")


# ===================================================================
# Process & Analysis Section
# ===================================================================

def render_processing_section(api_key: str, mode: str, page_from: int, page_to: int):
    """
    Render the processing area: book info, additional content, summarize button, results.
    """
    has_book = st.session_state.get("selected_book") is not None
    has_text = bool(st.session_state.get("pdf_text", ""))

    if not has_book:
        return

    book = st.session_state["selected_book"]

    st.markdown("---")
    st.markdown(f"### 📖 {format_text_for_output(book['title'])}")
    st.caption(f"✍️ By: {format_text_for_output(book['author'])} | 📅 Year: {book['year']}")

    text = st.session_state.get("pdf_text", "")

    if has_text:
        source = "Book Description" if "Book:" in text else "PDF Content"
        st.info(f"📚 Source: {source}")
        st.write(f"📊 Text length: {len(text)} characters")
    else:
        st.warning("No content available. Please paste text or upload a PDF.")

    # Additional content text area
    st.markdown("#### 📝 Additional Content (Optional)")
    additional_text = st.text_area(
        "Paste additional text here:",
        height=80,
        placeholder="Paste any additional content...",
    )

    # Combine texts
    if text and additional_text:
        combined = f"{text}\n\n--- Additional Content ---\n{additional_text}"
    elif additional_text:
        combined = additional_text
    elif text:
        combined = text
    else:
        combined = ""

    if combined:
        st.write(f"🔍 Combined text length: {len(combined.strip())} characters")

    # ================================================================
    # Summarize Button
    # ================================================================
    if combined and len(combined.strip()) >= 50:
        output_mode = "quick" if mode == "Quick Summary" else "explanation"

        st.markdown("""
        <style>
        .summarize-btn button {
            background: linear-gradient(135deg, #D4AF37 0%, #B8960C 100%) !important;
            color: #0D3486 !important;
            font-family: 'Cinzel', serif !important;
            font-weight: bold !important;
            font-size: 18px !important;
            padding: 12px 24px !important;
            border: 3px solid #0D3486 !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 12px rgba(212, 175, 55, 0.4) !important;
        }
        .summarize-btn button:hover {
            background: linear-gradient(135deg, #B8960C 0%, #D4AF37 100%) !important;
            transform: scale(1.02) !important;
        }
        </style>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="summarize-btn">', unsafe_allow_html=True)
            if st.button("⚖️ ✨ Start Summary", type="primary", use_container_width=True):
                _run_analysis(combined, api_key, mode, page_from, page_to, book, output_mode)
            st.markdown("</div>", unsafe_allow_html=True)

    # ================================================================
    # Show Results if available
    # ================================================================
    pptx_file = st.session_state.get("pptx_file")
    if pptx_file:
        st.markdown("### 📋 Summary Result")
        processed_text = fix_text(st.session_state.get("summary_output", ""))
        if is_arabic_text(st.session_state.get("summary_output", "")):
            st.markdown(
                f'<div style="text-align: right; direction: rtl;">{processed_text}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(processed_text)

        safe_filename = re.sub(r"[^\w\s-]", "", st.session_state.get("file_name", "Summary")).strip() or "Summary"
        st.download_button(
            label="📊 Download PPTX",
            data=pptx_file,
            file_name=f"{safe_filename}.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
        )
    elif combined and len(combined.strip()) < 50:
        st.warning(f"⚠️ Text too short (minimum 50 characters). Current length: {len(combined.strip())}")
    else:
        st.info("💡 Tip: Paste book content or upload a PDF to begin analysis")


# ================================================================
# Core Analysis Runner
# ================================================================

def _run_analysis(
    combined_text: str,
    api_key: str,
    mode: str,
    page_from: int,
    page_to: int,
    book: dict,
    output_mode: str,
):
    """
    Execute the full analysis pipeline synchronously.
    Does NOT call st.rerun() on errors – just shows error messages.
    """
    # Validate API key
    if not api_key or not api_key.startswith("gsk_"):
        st.error("❌ Invalid API key. Must start with gsk_")
        return

    # Validate text
    if not combined_text or len(combined_text.strip()) < 50:
        st.error("❌ Text too short for analysis (minimum 50 characters)")
        return

    # Split text into chunks
    pages = split_text_by_pages(combined_text)
    total_pages = len(pages)

    if total_pages == 0:
        st.error("❌ No text chunks to process")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()

    sections_data = []
    for i, page in enumerate(pages):
        progress = int((i / total_pages) * 80)
        progress_bar.progress(progress)
        status_text.text(f"Analyzing chunk {i+1}/{total_pages}...")

        result = analyze_section(
            page["text"],
            i + 1,
            book,
            api_key,
            mode,
            (page_from, page_to),
        )
        if result:
            sections_data.append(result)

    if not sections_data:
        st.error("❌ AI analysis failed to return any valid content")
        progress_bar.empty()
        status_text.empty()
        return

    # ================================================================
    # Parse AI responses into structured sections
    # NEW: Uses markdown-heading-based parsing instead of [SECTION]
    # ================================================================
    progress_bar.progress(85)
    status_text.text("Processing results...")

    all_sections = []
    section_counter = 1

    for chunk_result in sections_data:
        if not isinstance(chunk_result, dict) or "content" not in chunk_result:
            continue

        content = chunk_result["content"]
        if len(content.strip()) < 10:
            continue

        # Check for API errors embedded in content
        if content.startswith("API Error:") or content.startswith("Error:"):
            continue

        # Use the new robust parser (markdown headings ##, then paragraph fallback)
        parsed = parse_content_into_sections(content)
        for sec in parsed:
            sec["section_num"] = section_counter
            all_sections.append(sec)
            section_counter += 1

    if not all_sections:
        st.error("❌ No content sections could be extracted from AI responses")
        progress_bar.empty()
        status_text.empty()
        return

    # ================================================================
    # Generate PPTX
    # ================================================================
    progress_bar.progress(95)
    status_text.text("Generating PPTX presentation...")

    try:
        pptx_file = create_creative_pptx(
            book_title=book.get("title", "Unknown"),
            sections_data=all_sections,
            output_mode=output_mode,
        )
    except Exception as e:
        st.error(f"❌ PPTX generation error: {str(e)}")
        progress_bar.empty()
        status_text.empty()
        return

    progress_bar.progress(100)
    status_text.text("✅ Complete!")

    # Store results
    st.session_state["pptx_file"] = pptx_file
    st.session_state["sections_data"] = all_sections
    st.session_state["file_name"] = st.session_state.get("file_name_input", "Summary")

    st.success(f"✅ Analysis complete! Generated {len(all_sections)} sections in PPTX.")

    # Clear progress
    progress_bar.empty()
    status_text.empty()

    # Single rerun to show the download button section
    st.rerun()


# ===================================================================
# Main App
# ===================================================================

def main():
    """Main entry point for the Hermes Streamlit app."""
    st.set_page_config(
        page_title="⚡Hermes\\ابو محسوب لعدم الرسوب💯",
        page_icon="⚖️",
        layout="centered",
    )

    # Load CSS
    st.markdown(HERMES_CSS, unsafe_allow_html=True)

    # Title
    st.markdown(
        """
        <div style="text-align: center; padding: 10px 0;">
            <h1 style="font-size: 2.5em !important;">⚡Hermes\ابو محسوب لعدم الرسوب💯</h1>
            <p style="font-family: 'Cinzel', serif; color: #D4AF37; font-size: 1.1em;">
                The Wisdom of Hermes • The Success of Abu Mahsoub
            </p>
        </div>
        <hr style="border-color: #D4AF37; opacity: 0.5;">
        """,
        unsafe_allow_html=True,
    )

    # Check for missing libraries
    missing = []
    try:
        from groq import Groq  # noqa: F401
    except ImportError:
        missing.append("groq")
    try:
        import arabic_reshaper  # noqa: F401
        from bidi.algorithm import get_display  # noqa: F401
    except ImportError:
        missing.append("arabic_reshaper, python-bidi")

    if missing:
        st.error(f"Missing libraries: {', '.join(missing)}. Run: pip install {' '.join(missing)}")

    st.title("📚 Book Analyzer Pro")
    st.caption("Creative & Comprehensive Mode")

    # Initialize session state
    init_session_state()

    # Sidebar
    api_key, mode, page_from, page_to, file_name_input = render_sidebar()
    st.session_state["file_name_input"] = file_name_input

    # Tabs
    tab1, tab2 = st.tabs(["🔍 Search Books", "📤 Upload PDF"])

    with tab1:
        render_search_tab()

    with tab2:
        render_upload_tab(page_from, page_to)

    # Processing section
    render_processing_section(api_key, mode, page_from, page_to)


if __name__ == "__main__":
    # Download font on startup
    download_amiri_font()
    main()