import fitz  # PyMuPDF
import re
from typing import Dict, List, Optional

class PDFProcessor:
    def __init__(self):
        self.pdf_document = None
        self.metadata = {}
        
    def load_pdf(self, file_path: str) -> bool:
        """Load PDF file and extract basic metadata"""
        try:
            self.pdf_document = fitz.open(file_path)
            self.metadata = {
                'total_pages': len(self.pdf_document),
                'title': self.pdf_document.metadata.get('title', 'Unknown'),
                'author': self.pdf_document.metadata.get('author', 'Unknown')
            }
            return True
        except Exception as e:
            print(f"Error loading PDF: {e}")
            return False
    
    def extract_chapters(self) -> List[Dict[str, str]]:
        """Extract chapters/TOC from PDF using multiple methods"""
        chapters = []
        
        # Method 1: Try to get from PDF outline/TOC
        try:
            toc = self.pdf_document.get_toc()
            if toc:
                for item in toc:
                    level, title, page = item
                    chapters.append({
                        'title': title.strip(),
                        'page': page,
                        'level': level
                    })
        except:
            pass
        
        # Method 2: Detect chapters using pattern matching if TOC not available
        if not chapters:
            chapters = self._detect_chapters_from_text()
            
        return chapters
    
    def _detect_chapters_from_text(self) -> List[Dict[str, str]]:
        """Detect chapters using text patterns"""
        chapters = []
        chapter_patterns = [
            r'Chapter\s+\d+[:.]?\s*(.+)',  # Chapter 1: Title
            r'CHAPTER\s+\d+[:.]?\s*(.+)',  # CHAPTER 1: TITLE
            r'\d+[:.]?\s*(.+)',  # 1: Title
            r'(?:الفصل|باب|مقدمة|خاتمة)\s+\d*[:.]?\s*(.+)'
        ]
        
        for page_num in range(min(10, len(self.pdf_document))):  # Check first 10 pages
            page = self.pdf_document[page_num]
            text = page.get_text()
            
            for pattern in chapter_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.UNICODE)
                for match in matches:
                    title = match.group(1).strip()
                    if len(title) > 10 and len(title) < 100:  # Reasonable chapter title length
                        chapters.append({
                            'title': title,
                            'page': page_num + 1,
                            'level': 1
                        })
        
        # Remove duplicates and sort
        seen = set()
        unique_chapters = []
        for chapter in chapters:
            key = (chapter['title'].lower(), chapter['page'])
            if key not in seen:
                seen.add(key)
                unique_chapters.append(chapter)
        
        return sorted(unique_chapters, key=lambda x: x['page'])
    
    def extract_text(self, start_page: int = 0, end_page: Optional[int] = None) -> str:
        """Extract text from PDF pages"""
        if not self.pdf_document:
            return ""
        
        if end_page is None:
            end_page = len(self.pdf_document)
        
        text = ""
        for page_num in range(start_page, min(end_page, len(self.pdf_document))):
            page = self.pdf_document[page_num]
            text += page.get_text() + "\n"
        
        return text
    
    def extract_references(self) -> List[str]:
        """Extract references/bibliography from PDF"""
        references = []
        reference_patterns = [
            r'References[\s\S]*?(?=(?:Appendix|Index|$))',
            r'Bibliography[\s\S]*?(?=(?:Appendix|Index|$))',
            r'المراجع[\s\S]*?(?=(?:ملحق|فهرس|$))',
            r'\[\d+\].*?(?=\[\d+\]|$)'  # [1] Author, Title...
        ]
        
        # Check last 20 pages for references
        start_page = max(0, len(self.pdf_document) - 20)
        end_page = len(self.pdf_document)
        
        full_text = self.extract_text(start_page, end_page)
        
        for pattern in reference_patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE | re.UNICODE | re.DOTALL)
            for match in matches:
                ref_text = match.group(0)
                # Split individual references
                if '[' in ref_text:
                    individual_refs = re.findall(r'\[\d+\].*?(?=\[\d+\]|$)', ref_text, re.DOTALL)
                    references.extend(individual_refs)
                else:
                    references.append(ref_text)
        
        return [ref.strip() for ref in references if ref.strip()]
    
    def get_metadata(self) -> Dict:
        """Get PDF metadata including page count and chapters"""
        chapters = self.extract_chapters()
        references = self.extract_references()
        
        return {
            'total_pages': self.metadata.get('total_pages', 0),
            'title': self.metadata.get('title', 'Unknown'),
            'author': self.metadata.get('author', 'Unknown'),
            'number_of_chapters': len(chapters),
            'chapters': chapters,
            'references': references[:20]  # Limit to first 20 references
        }
    
    def extract_metadata(self, file_path: str) -> Dict:
        """Load PDF and extract all metadata in one step"""
        if not self.load_pdf(file_path):
            return {
                'total_pages': 0,
                'title': 'Unknown',
                'author': 'Unknown',
                'number_of_chapters': 0,
                'chapters': [],
                'references': []
            }
        return self.get_metadata()
    
    def close(self):
        """Close the PDF document"""
        if self.pdf_document:
            self.pdf_document.close()