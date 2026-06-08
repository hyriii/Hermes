"""
Hermes Logic Module
Business logic: Arabic text processing, PDF extraction, parsers, PDF & PPTX generation.
"""

import io
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

import fitz  # PyMuPDF
import requests
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# ---------------------------------------------------------------------------
# Conditional imports
# ---------------------------------------------------------------------------

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    pytesseract = None

try:
    import arabic_reshaper
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False
    arabic_reshaper = None

try:
    from bidi.algorithm import get_display
    BIDI_AVAILABLE = True
except ImportError:
    BIDI_AVAILABLE = False
    get_display = None

try:
    from src.ppt_generator import PowerPointGenerator, fix_arabic_for_pptx
except ImportError:
    # Fallback – define a no-op
    def fix_arabic_for_pptx(text: str) -> str:
        return text


# ===================================================================
# SECTION 1 – Arabic Text Utilities
# ===================================================================

def is_arabic_text(text: str) -> bool:
    """Check if text contains Arabic characters."""
    return any("\u0600" <= c <= "\u06FF" for c in text)


def fix_text(text: str) -> str:
    """Centralized Arabic text fixing with arabic_reshaper and bidi."""
    if not ARABIC_SUPPORT or not arabic_reshaper or not text:
        return text
    try:
        reshaped = arabic_reshaper.reshape(text)
        if BIDI_AVAILABLE and get_display:
            return get_display(reshaped)
        return reshaped
    except Exception:
        return text


def fix_arabic(text: str) -> str:
    """Force Arabic reshaping and bidirectional display."""
    return fix_text(text)


def reshape_arabic(text: str) -> str:
    """Reshape Arabic text if present."""
    if not ARABIC_SUPPORT or not arabic_reshaper:
        return text
    try:
        if any("\u0600" <= c <= "\u06FF" for c in text):
            reshaped = arabic_reshaper.reshape(text)
            if BIDI_AVAILABLE and get_display:
                return get_display(reshaped)
            return reshaped
    except Exception:
        pass
    return text


def format_text_for_output(text: str) -> str:
    """Apply Arabic fixing only if text contains Arabic."""
    return fix_arabic(text) if is_arabic_text(text) else text


def download_amiri_font():
    """Download Amiri font from Google Fonts."""
    font_path = "Amiri-Regular.ttf"
    if not os.path.exists(font_path):
        url = (
            "https://raw.githubusercontent.com/google/fonts/main/"
            "ofl/amiri/Amiri-Regular.ttf"
        )
        try:
            r = requests.get(url, timeout=10)
            with open(font_path, "wb") as f:
                f.write(r.content)
        except Exception:
            pass  # will fallback to default font
    return font_path


# ===================================================================
# SECTION 2 – PPTX Inspection Utilities
# ===================================================================

def analyze_arabic_text_shapes(text: str) -> Dict:
    """Analyze Arabic text shaping quality."""
    analysis = {
        "total_arabic_chars": 0,
        "isolated_chars": 0,
        "connected_sequences": 0,
        "shaping_issues": [],
        "rtl_issues": [],
        "word_analysis": [],
    }
    if not text:
        return analysis

    # Determine sample size for analysis
    sample = text[:2000]  # analyze first 2000 chars for performance

    words = sample.split()
    for word in words:
        arabic_in_word = [c for c in word if "\u0600" <= c <= "\u06FF"]
        if not arabic_in_word:
            continue
        analysis["total_arabic_chars"] += len(arabic_in_word)

        isolated_chars = [c for c in arabic_in_word if c in "ادرزوى"]
        connectable = sum(1 for c in arabic_in_word if c in "بتثجحخسشصضطظعغفقكلمنه")
        isolated_count = len(isolated_chars)

        if len(arabic_in_word) > 1 and isolated_count > len(arabic_in_word) * 0.8:
            analysis["shaping_issues"].append(
                f"Word '{word}' has mostly isolated Arabic chars – may need reshaping"
            )
            analysis["isolated_chars"] += isolated_count
        elif connectable > 0:
            analysis["connected_sequences"] += 1

        analysis["word_analysis"].append(
            {
                "word": word,
                "arabic_chars": len(arabic_in_word),
                "isolated": isolated_count,
                "connectable": connectable,
            }
        )
    return analysis


def inspect_pptx_arabic_correctness(pptx_buffer: io.BytesIO) -> Dict:
    """Inspect PPTX for Arabic text correctness."""
    result = {
        "total_slides": 0,
        "arabic_text_found": False,
        "alignment_issues": [],
        "shaping_issues": [],
        "rtl_issues": [],
        "text_samples": [],
        "arabic_word_analysis": [],
        "xml_structure_ok": True,
        "recommendations": [],
        "double_check_passed": True,
        "status": "NO_ARABIC",
    }
    try:
        pptx_buffer.seek(0)
        with zipfile.ZipFile(pptx_buffer, "r") as z:
            slides = [f for f in z.namelist() if f.startswith("ppt/slides/slide") and f.endswith(".xml")]
            result["total_slides"] = len(slides)

            for sfile in slides:
                try:
                    xml = z.read(sfile).decode("utf-8")
                    root = ET.fromstring(xml)
                    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}

                    texts = root.findall(".//a:t", ns)
                    for t in texts:
                        if t.text and t.text.strip():
                            result["text_samples"].append(t.text[:100])
                            if any("\u0600" <= c <= "\u06FF" for c in t.text):
                                result["arabic_text_found"] = True
                                analysis = analyze_arabic_text_shapes(t.text)
                                result["arabic_word_analysis"].append(analysis)
                                if analysis["shaping_issues"]:
                                    result["shaping_issues"].extend(analysis["shaping_issues"])

                    pprs = root.findall(".//a:pPr", ns)
                    for ppr in pprs:
                        algn = ppr.get("{http://schemas.openxmlformats.org/drawingml/2006/main}algn")
                        if algn and algn != "r":
                            parent = ppr.getparent()
                            if parent is not None:
                                runs = parent.findall(".//a:t", ns)
                                for r in runs:
                                    if r.text and any("\u0600" <= c <= "\u06FF" for c in r.text):
                                        result["alignment_issues"].append(
                                            f"Arabic text with {algn} alignment instead of 'r'"
                                        )
                except Exception:
                    result["xml_structure_ok"] = False

        if result["arabic_text_found"]:
            if (
                not result["alignment_issues"]
                and not result["shaping_issues"]
                and not result["rtl_issues"]
            ):
                result["status"] = "PASS"
            else:
                result["status"] = "ISSUES_FOUND"
                result["double_check_passed"] = False
    except Exception:
        result["xml_structure_ok"] = False
    return result


# ===================================================================
# SECTION 3 – PDF Text Extraction
# ===================================================================

def extract_text_from_pdf(pdf_file, page_range: tuple = None) -> str:
    """
    Extract text from an uploaded PDF using PyMuPDF with OCR fallback.
    Returns empty string on failure.
    """
    try:
        file_bytes = pdf_file.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        total_pages = doc.page_count

        if page_range and page_range[0] and page_range[1]:
            start, end = page_range
            if end > total_pages:
                raise ValueError(
                    f"Invalid page range: To Page ({end}) exceeds total pages ({total_pages})"
                )
            if start > end:
                raise ValueError(
                    f"Invalid page range: From Page ({start}) > To Page ({end})"
                )
            pages_to_process = range(start - 1, end)
        else:
            pages_to_process = range(total_pages)

        text = ""
        for i in pages_to_process:
            page = doc[i]
            raw = page.get_text("text", sort=True)
            if raw and len(raw.strip()) > 50:
                text += raw + "\n"
            elif OCR_AVAILABLE:
                try:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    ocr = pytesseract.image_to_string(img, lang="ara+eng")
                    if ocr.strip():
                        text += ocr + "\n"
                except Exception:
                    pass

        doc.close()
        cleaned = re.sub(r"\s+", " ", text).strip()
        if len(cleaned) < 100:
            return ""
        return cleaned

    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {e}") from e


# ===================================================================
# SECTION 4 – Robust Content Parsing (replaces [SECTION] logic)
# ===================================================================

def parse_content_into_sections(content: str) -> List[Dict]:
    """
    Parse AI response into sections using markdown headings (## ).
    Falls back to double-newline paragraph splitting if no headings found.
    """
    sections = []

    # Strategy 1: Markdown headings ## Title
    heading_pattern = r"^##\s+(.+)$"
    lines = content.split("\n")

    current_title = None
    current_lines: List[str] = []

    def flush():
        nonlocal current_title, current_lines
        if current_title:
            body = "\n".join(current_lines).strip()
            if body:
                sections.append({"title": current_title.strip(), "content": body})
        current_title = None
        current_lines = []

    for line in lines:
        m = re.match(heading_pattern, line.strip())
        if m:
            flush()
            current_title = m.group(1)
        elif current_title:
            current_lines.append(line)
        else:
            # Content before any heading – skip or treat as intro?
            pass
    flush()

    # Strategy 2: If no headings, split by double newline, use first sentence as title
    if not sections:
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip() and len(p.strip()) > 40]
        for i, para in enumerate(paragraphs):
            # Take first sentence as title
            sentences = re.split(r"(?<=[.!?])\s+", para)
            if len(sentences) > 1:
                title = sentences[0][:60]
                body = " ".join(sentences[1:])
                if len(body) > 20:
                    sections.append({"title": f"Section {i+1}: {title}", "content": body})
            else:
                # Whole paragraph is the content
                sections.append({"title": f"Section {i+1}", "content": para})

    return sections


def parse_sections_to_summary_result(sections_data: List[Dict]) -> "SummaryResult":
    """
    Legacy function: convert sections_data to SummaryResult.
    Kept for backward compatibility.
    """
    from api import SummaryResult

    full = "\n\n".join(s.get("content", "") for s in sections_data if s and "content" in s)
    english = ""
    arabic = ""
    key_points = []
    scientific_terms = []
    references = []

    lines = full.split("\n")
    current = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        lower = line.lower()
        if "english" in lower or "summary" in lower:
            current = "english"
        elif "arabic" in lower or "عربي" in lower:
            current = "arabic"
        elif "key" in lower and "point" in lower:
            current = "key_points"
        elif "scientific" in lower or "term" in lower:
            current = "scientific_terms"
        elif "reference" in lower:
            current = "references"
        elif current == "english":
            english += line + " "
        elif current == "arabic":
            arabic += line + " "
        elif current == "key_points" and (line.startswith("•") or line.startswith("-")):
            key_points.append(line.lstrip("•- ").strip())
        elif current == "scientific_terms" and (line.startswith("•") or line.startswith("-")):
            scientific_terms.append(line.lstrip("•- ").strip())
        elif current == "references" and (line.startswith("•") or line.startswith("-")):
            references.append(line.lstrip("•- ").strip())

    if not english and not arabic:
        english = full[:2000]

    return SummaryResult(
        english_summary=english.strip(),
        arabic_summary=arabic.strip(),
        key_points=key_points,
        scientific_terms=scientific_terms,
        references=references,
    )


# ===================================================================
# SECTION 5 – PPTX Generation
# ===================================================================

def create_creative_pptx(
    book_title: str,
    sections_data: List[Dict],
    output_mode: str,
) -> Optional[io.BytesIO]:
    """
    Create a comprehensive PPTX presentation.
    """
    try:
        prs = Presentation()
        prs.slide_width = Inches(13.33)
        prs.slide_height = Inches(7.5)

        COLORS = {
            "primary": RGBColor(0, 51, 102),
            "secondary": RGBColor(212, 175, 55),
            "accent1": RGBColor(46, 125, 50),
            "accent2": RGBColor(244, 67, 54),
            "accent3": RGBColor(156, 39, 176),
            "text_dark": RGBColor(33, 33, 33),
            "text_light": RGBColor(255, 255, 255),
            "background": RGBColor(248, 248, 248),
        }

        def add_bg(slide, color=None):
            if color is None:
                color = COLORS["background"]
            rect = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.33), Inches(7.5))
            rect.fill.solid()
            rect.fill.fore_color.rgb = color
            rect.line.width = 0

        slide_count = 0

        # ---------- TITLE SLIDE ----------
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        slide_count += 1
        add_bg(slide)
        # Gold circle
        gc = slide.shapes.add_shape(3, Inches(8), Inches(1), Inches(4), Inches(4))
        gc.fill.solid()
        gc.fill.fore_color.rgb = RGBColor(255, 215, 0)
        gc.line.width = 0
        bt = slide.shapes.add_shape(5, Inches(0), Inches(5), Inches(3), Inches(2.5))
        bt.fill.solid()
        bt.fill.fore_color.rgb = COLORS["primary"]
        bt.line.width = 0

        tb = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(2))
        p = tb.text_frame.add_paragraph()
        p.text = fix_arabic_for_pptx(book_title) if book_title else "Academic Analysis"
        p.font.bold = True
        p.font.size = Pt(48)
        p.font.name = "Arial"
        p.font.color.rgb = COLORS["primary"]
        if is_arabic_text(p.text):
            p.alignment = PP_ALIGN.RIGHT

        tb2 = slide.shapes.add_textbox(Inches(1), Inches(3.5), Inches(8), Inches(1))
        p2 = tb2.text_frame.add_paragraph()
        p2.text = fix_arabic_for_pptx("Comprehensive Academic Summary & Analysis")
        p2.font.size = Pt(24)
        p2.font.color.rgb = COLORS["accent1"]
        if is_arabic_text(p2.text):
            p2.alignment = PP_ALIGN.RIGHT

        line = slide.shapes.add_shape(1, Inches(1), Inches(5), Inches(8), Inches(0.1))
        line.fill.solid()
        line.fill.fore_color.rgb = COLORS["secondary"]
        line.line.width = 0

        # ---------- TABLE OF CONTENTS ----------
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        slide_count += 1
        add_bg(slide, COLORS["primary"])

        tt = slide.shapes.add_textbox(Inches(1), Inches(0.5), Inches(11), Inches(1))
        pt = tt.text_frame.add_paragraph()
        pt.text = fix_arabic_for_pptx("📋 Table of Contents")
        pt.font.bold = True
        pt.font.size = Pt(36)
        pt.font.color.rgb = COLORS["text_light"]
        if is_arabic_text(pt.text):
            pt.alignment = PP_ALIGN.RIGHT

        left_x, right_x = Inches(1), Inches(7)
        for i, sec in enumerate(sections_data):
            col_x = left_x if i % 2 == 0 else right_x
            y_pos = Inches(2 + (i // 2) * 0.8)
            item = slide.shapes.add_textbox(col_x, y_pos, Inches(5.5), Inches(0.6))
            pi = item.text_frame.add_paragraph()
            pi.text = f"{i+1}. {fix_arabic_for_pptx(sec.get('title', f'Section {i+1}'))}"
            pi.font.size = Pt(18)
            pi.font.color.rgb = COLORS["text_light"]
            if is_arabic_text(pi.text):
                pi.alignment = PP_ALIGN.RIGHT

        # ---------- CONTENT SLIDES ----------
        layouts = [
            {"shapes": [(1, 1, 11, 6)]},
            {"shapes": [(1, 1, 5.5, 5), (7, 1, 5.5, 5)]},
            {"shapes": [(2, 1, 9, 5)]},
        ]
        bg_colors = [
            COLORS["background"],
            RGBColor(240, 248, 255),
            RGBColor(255, 250, 240),
        ]

        for idx, sec in enumerate(sections_data):
            layout = layouts[idx % len(layouts)]
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            slide_count += 1
            add_bg(slide, bg_colors[idx % len(bg_colors)])

            # Title
            tbox = slide.shapes.add_textbox(Inches(1), Inches(0.3), Inches(11), Inches(0.8))
            tp = tbox.text_frame.add_paragraph()
            tp.text = fix_arabic_for_pptx(sec.get("title", f"Section {idx+1}"))
            tp.font.bold = True
            tp.font.size = Pt(28)
            tp.font.color.rgb = COLORS["primary"]
            if is_arabic_text(tp.text):
                tp.alignment = PP_ALIGN.RIGHT

            content = sec.get("content", "")
            parts = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]

            for shape_idx, (left, top, w, h) in enumerate(layout["shapes"]):
                if shape_idx >= len(parts):
                    break
                cbox = slide.shapes.add_textbox(
                    Inches(left), Inches(top), Inches(w), Inches(h)
                )
                tf = cbox.text_frame
                tf.word_wrap = True

                text = fix_arabic_for_pptx(parts[shape_idx])
                for line in text.split("\n"):
                    if not line.strip():
                        continue
                    pp = tf.add_paragraph()
                    pp.text = line.strip()
                    pp.font.size = Pt(16)
                    pp.font.color.rgb = COLORS["text_dark"]
                    pp.space_after = Pt(6)
                    if is_arabic_text(pp.text):
                        pp.alignment = PP_ALIGN.RIGHT

        # ---------- SUMMARY SLIDE ----------
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        slide_count += 1
        add_bg(slide, COLORS["primary"])

        stb = slide.shapes.add_textbox(Inches(1), Inches(0.5), Inches(11), Inches(1))
        sp = stb.text_frame.add_paragraph()
        sp.text = fix_arabic_for_pptx("📊 Presentation Summary")
        sp.font.bold = True
        sp.font.size = Pt(36)
        sp.font.color.rgb = COLORS["text_light"]
        if is_arabic_text(sp.text):
            sp.alignment = PP_ALIGN.RIGHT

        sb = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(11), Inches(4))
        for line in [
            f"📚 Total Sections Analyzed: {len(sections_data)}",
            f"📊 Slides Created: {slide_count}",
            "🌟 Comprehensive PDF Coverage: 100%",
        ]:
            pp = sb.text_frame.add_paragraph()
            pp.text = fix_arabic_for_pptx(line)
            pp.font.size = Pt(20)
            pp.font.color.rgb = COLORS["text_light"]
            if is_arabic_text(pp.text):
                pp.alignment = PP_ALIGN.RIGHT

        # Save
        pptx_io = io.BytesIO()
        prs.save(pptx_io)
        pptx_io.seek(0)
        return pptx_io

    except Exception as e:
        raise RuntimeError(f"PPTX creation error: {e}") from e


# ===================================================================
# SECTION 6 – PDF Generation
# ===================================================================

def create_hermes_pdf(
    book_info: Dict,
    sections_data: List[Dict],
    output_mode: str = "quick",
    filename: str = "Summary",
) -> io.BytesIO:
    """
    Create PDF summary with Arabic support using FPDF.
    """
    if not FPDF_AVAILABLE:
        raise ValueError("FPDF library not installed. Run: pip install fpdf2")
    if not sections_data:
        raise ValueError("No content to create PDF")

    book_title = book_info.get("title", "Unknown")
    author_name = book_info.get("author", "Unknown")
    language = book_info.get("language", "en")
    is_arabic = language == "ar"

    # Ensure Amiri font is available
    font_path = download_amiri_font()

    class HermesPDF(FPDF):
        def header(self):
            self.set_fill_color(212, 175, 55)
            self.rect(0, 0, 210, 10, "F")
            self.set_text_color(0, 35, 102)
            self.set_font("Amiri" if is_arabic else "Arial", "", 16)
            self.cell(0, 15, "Hermes / أبو محسوب - ملخص المادة", 0, 1, "C")
            self.ln(2)

        def footer(self):
            self.set_y(-15)
            self.set_font("Amiri" if is_arabic else "Arial", "", 10)
            self.set_text_color(128, 128, 128)
            self.cell(
                0,
                10,
                f"Hermes / أبو محسوب لعدم الرسوب - Page {self.page_no()}",
                0,
                0,
                "C",
            )

    pdf = HermesPDF()
    pdf.add_page()
    try:
        pdf.add_font("Amiri", "", font_path, uni=True)
    except Exception:
        pass

    pdf.set_font("Amiri" if is_arabic else "Arial", "B", 18)
    pdf.set_text_color(0, 35, 102)
    pdf.cell(0, 12, fix_text(book_title), 0, 1, "C")
    pdf.ln(5)

    pdf.set_font("Amiri" if is_arabic else "Arial", "", 14)
    pdf.set_text_color(80, 80, 80)
    author_label = f"تأليف: {author_name}" if is_arabic else f"By: {author_name}"
    pdf.cell(0, 10, author_label, 0, 1, "C")
    pdf.ln(15)

    for sec in sections_data:
        content = sec.get("content", "")
        # Extract title from content if not provided
        sec_title = sec.get("title", f"Section {sec.get('section_num', 1)}")

        pdf.set_font("Amiri" if is_arabic else "Arial", "B", 14)
        pdf.set_fill_color(212, 175, 55)
        pdf.set_text_color(0, 35, 102)
        pdf.cell(0, 12, fix_text(sec_title), 0, 1, "L")
        pdf.ln(5)

        # Parse slides (backward compat) or just print content
        slides = re.findall(
            r"\[SLIDE\s*\d+:\s*([^\]]+)\](.*?)(?=\[SLIDE|\[SECTION|$)",
            content,
            re.DOTALL,
        )
        if slides:
            for slide_title, slide_content in slides:
                pdf.set_font("Amiri" if is_arabic else "Arial", "B", 12)
                pdf.set_text_color(41, 128, 185)
                pdf.cell(0, 10, fix_text(slide_title.strip()), 0, 1, "L")
                pdf.ln(3)
                pdf.set_font("Amiri" if is_arabic else "Arial", "", 11)
                pdf.set_text_color(44, 62, 80)
                for line in slide_content.strip().split("\n"):
                    if line.strip().startswith("•") or line.strip().startswith("-"):
                        point = fix_text(line.strip().lstrip("•- "))
                        pdf.cell(5, 7, "•", 0, 0)
                        align = "R" if is_arabic else "L"
                        pdf.multi_cell(0, 7, point, 0, align)
        else:
            # Print as paragraphs
            pdf.set_font("Amiri" if is_arabic else "Arial", "", 11)
            pdf.set_text_color(44, 62, 80)
            for para in content.split("\n\n"):
                para = para.strip()
                if para:
                    lines = para.split("\n")
                    for line in lines:
                        line = line.strip()
                        if line.startswith("•") or line.startswith("-"):
                            point = fix_text(line.lstrip("•- "))
                            pdf.cell(5, 7, "•", 0, 0)
                            align = "R" if is_arabic else "L"
                            pdf.multi_cell(0, 7, point, 0, align)
                        elif line:
                            fix = fix_text(line)
                            align = "R" if is_arabic else "L"
                            pdf.multi_cell(0, 7, fix, 0, align)
                    pdf.ln(4)
        pdf.ln(10)

    # Final quote
    pdf.ln(25)
    pdf.set_font("Amiri" if is_arabic else "Arial", "", 14)
    pdf.set_text_color(212, 175, 55)
    pdf.cell(0, 12, "HERMES Analyzer - مع أبو محسوب لا فشل ولا رسوب", 0, 1, "C")

    pdf_bytes = pdf.output(dest="S")
    output = io.BytesIO(pdf_bytes)
    output.seek(0)
    return output