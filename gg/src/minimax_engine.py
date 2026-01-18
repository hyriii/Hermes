import requests
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class SummaryResult:
    english_summary: str
    arabic_summary: str
    key_points: List[str]
    scientific_terms: List[str]
    references: List[str]

class MiniMaxEngine:
    """MiniMax API engine for scientific text summarization"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def generate_scientific_summary(self, text: str, metadata: Dict) -> SummaryResult:
        """Generate scientific summary with strict academic constraints using MiniMax API"""
        
        # Scientific prompt template with academic constraints
        scientific_prompt = f"""
        You are a scientific researcher. Provide a STRICTLY ACADEMIC summary following these SCIENTIFIC CONSTRAINTS:

        1. USE ONLY SCIENTIFIC AND ACADEMIC LANGUAGE - no casual or conversational tone
        2. BASE SUMMARY EXCLUSIVELY ON THE PROVIDED TEXT - no external information
        3. BEGIN with book title and author: "{metadata.get('title', 'Unknown')}" by {metadata.get('author', 'Unknown')}
        4. MAINTAIN OBJECTIVE, IMPERSONAL ACADEMIC TONE throughout
        5. IDENTIFY and highlight key scientific concepts and terminology
        6. STRUCTURE summary with clear academic sections: Introduction, Methodology, Findings, Conclusions
        7. CITE specific page numbers when referencing content
        8. USE FORMAL CITATION FORMAT for any references mentioned

        DOCUMENT METADATA:
        - Title: {metadata.get('title', 'Unknown')}
        - Author: {metadata.get('author', 'Unknown')}
        - Total Pages: {metadata.get('total_pages', 0)}
        - Number of Chapters: {metadata.get('number_of_chapters', 0)}
        - Chapters: {', '.join([ch.get('title', 'Untitled') for ch in metadata.get('chapters', [])])}

        TEXT TO SUMMARIZE:
        {text[:6000]}  # Limit text length for API constraints

        Provide your response in this exact format:
        
        ENGLISH SUMMARY:
        [Academic summary in English with scientific terminology]
        
        ARABIC SUMMARY:
        [Academic summary in Arabic with scientific terminology]
        
        KEY SCIENTIFIC POINTS:
        - [List 5-7 key scientific findings/concepts]
        
        SCIENTIFIC TERMINOLOGY:
        - [List 5-10 key scientific terms with brief definitions]
        
        ACADEMIC REFERENCES:
        - [List any academic references mentioned in text]
        """
        
        try:
            response = self._call_minimax_api(scientific_prompt)
            if response:
                return self._parse_scientific_response(response, metadata)
            else:
                return self._create_fallback_summary(text, metadata)
        except Exception as e:
            print(f"Error generating summary with MiniMax: {e}")
            return self._create_fallback_summary(text, metadata)
    
    def _call_minimax_api(self, prompt: str) -> Optional[str]:
        """Call MiniMax API for text generation"""
        
        payload = {
            "model": "abab6.5s-chat",  # MiniMax chat model
            "messages": [
                {
                    "role": "system",
                    "content": "You are a scientific researcher specializing in academic document analysis. You must use only formal scientific language, cite sources from the provided text only, and maintain academic objectivity throughout your responses."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4000,
            "top_p": 0.95
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
            else:
                print(f"MiniMax API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"MiniMax API exception: {e}")
            return None
        
        return None
    
    def _parse_scientific_response(self, response_text: str, metadata: Dict) -> SummaryResult:
        """Parse the MiniMax response into structured format"""
        
        lines = response_text.split('\n')
        english_summary = ""
        arabic_summary = ""
        key_points = []
        scientific_terms = []
        references = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if 'ENGLISH SUMMARY:' in line.upper():
                current_section = 'english'
                continue
            elif 'ARABIC SUMMARY:' in line.upper():
                current_section = 'arabic'
                continue
            elif 'KEY SCIENTIFIC POINTS:' in line.upper():
                current_section = 'key_points'
                continue
            elif 'SCIENTIFIC TERMINOLOGY:' in line.upper():
                current_section = 'terms'
                continue
            elif 'ACADEMIC REFERENCES:' in line.upper():
                current_section = 'references'
                continue
            
            if current_section == 'english':
                english_summary += line + " "
            elif current_section == 'arabic':
                arabic_summary += line + " "
            elif current_section == 'key_points' and line.startswith('-'):
                key_points.append(line[1:].strip())
            elif current_section == 'terms' and line.startswith('-'):
                scientific_terms.append(line[1:].strip())
            elif current_section == 'references' and line.startswith('-'):
                references.append(line[1:].strip())
        
        # Ensure we have content even if parsing fails
        if not english_summary:
            english_summary = self._generate_basic_english_summary(metadata)
        if not arabic_summary:
            arabic_summary = self._generate_basic_arabic_summary(metadata)
        
        return SummaryResult(
            english_summary=english_summary.strip(),
            arabic_summary=arabic_summary.strip(),
            key_points=key_points if key_points else self._extract_key_points_from_metadata(metadata),
            scientific_terms=scientific_terms if scientific_terms else [],
            references=references if references else metadata.get('references', [])[:5]
        )
    
    def _create_fallback_summary(self, text: str, metadata: Dict) -> SummaryResult:
        """Create a basic summary if MiniMax API fails"""
        
        # Basic English summary
        english_summary = f"Scientific document: {metadata.get('title', 'Unknown')} by {metadata.get('author', 'Unknown')}. "
        english_summary += f"This document contains {metadata.get('total_pages', 0)} pages and {metadata.get('number_of_chapters', 0)} chapters. "
        english_summary += "The content focuses on scientific research and academic findings."
        
        # Basic Arabic summary
        arabic_summary = f"المستند العلمي: {metadata.get('title', 'غير معروف')} بقلم {metadata.get('author', 'غير معروف')}. "
        arabic_summary += f"يحتوي هذا المستند على {metadata.get('total_pages', 0)} صفحة و{metadata.get('number_of_chapters', 0)} فصول. "
        arabic_summary += "يركز المحتوى على البحث العلمي والنتائج الأكاديمية."
        
        return SummaryResult(
            english_summary=english_summary,
            arabic_summary=arabic_summary,
            key_points=self._extract_key_points_from_metadata(metadata),
            scientific_terms=[],
            references=metadata.get('references', [])[:5]
        )
    
    def _generate_basic_english_summary(self, metadata: Dict) -> str:
        """Generate basic English summary"""
        return f"Scientific document: {metadata.get('title', 'Unknown')} by {metadata.get('author', 'Unknown')}. Contains {metadata.get('total_pages', 0)} pages and {metadata.get('number_of_chapters', 0)} chapters of academic research content."
    
    def _generate_basic_arabic_summary(self, metadata: Dict) -> str:
        """Generate basic Arabic summary"""
        return f"المستند العلمي: {metadata.get('title', 'غير معروف')} بقلم {metadata.get('author', 'غير معروف')}. يحتوي على {metadata.get('total_pages', 0)} صفحة و{metadata.get('number_of_chapters', 0)} فصول من محتوى البحث الأكاديمي."
    
    def _extract_key_points_from_metadata(self, metadata: Dict) -> List[str]:
        """Extract key points from metadata"""
        chapters = metadata.get('chapters', [])
        key_points = []
        
        if chapters:
            key_points.append(f"Document structured in {len(chapters)} chapters")
            for i, chapter in enumerate(chapters[:3]):  # First 3 chapters
                key_points.append(f"Chapter {i+1}: {chapter.get('title', 'Untitled')}")
        
        key_points.append(f"Total pages: {metadata.get('total_pages', 0)}")
        key_points.append("Academic and scientific content")
        
        return key_points
    
    def generate_citation(self, metadata: Dict, summary_text: str) -> str:
        """Generate academic citation for the document"""
        
        citation_prompt = f"""
        Generate a PROPER ACADEMIC CITATION for this scientific document:
        
        Title: {metadata.get('title', 'Unknown')}
        Author: {metadata.get('author', 'Unknown')}
        Pages: {metadata.get('total_pages', 0)}
        
        Summary excerpt: {summary_text[:500]}
        
        Provide citation in APA format for academic use.
        """
        
        try:
            response = self._call_minimax_api(citation_prompt)
            if response:
                return response.strip()
        except:
            pass
        
        # Fallback citation
        return f"{metadata.get('author', 'Unknown')}. ({metadata.get('title', 'Unknown')}). Academic Press, {metadata.get('total_pages', 0)} pages."
