from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Dict, List, Optional
import torch
from dataclasses import dataclass

@dataclass
class SummaryResult:
    english_summary: str
    arabic_summary: str
    key_points: List[str]
    scientific_terms: List[str]
    references: List[str]

class HuggingFaceEngine:
    def __init__(self, model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct"):
        """Initialize Hugging Face model for scientific summarization"""
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading model {model_name} on {self.device}...")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )
        
        # Set pad token if not present
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        print(f"Model {model_name} loaded successfully!")
        
    def generate_scientific_summary(self, text: str, metadata: Dict) -> SummaryResult:
        """Generate scientific summary with strict academic constraints using Qwen 2.5 Coder"""
        
        # Scientific prompt template with academic constraints
        scientific_prompt = f"""You are a scientific researcher. Provide a STRICTLY ACADEMIC summary following these SCIENTIFIC CONSTRAINTS:

1. USE ONLY SCIENTIFIC AND ACADEMIC LANGUAGE - no casual or conversational tone
2. BASE SUMMARY EXCLUSIVELY ON THE PROVIDED TEXT - no external information
3. BEGIN with book title and author: "{metadata.get('title', 'Unknown')}" by {metadata.get('author', 'Unknown')}
4. MAINTAIN OBJECTIVE, IMPERSONAL ACADEMIC TONE throughout
5. IDENTIFY and highlight key scientific concepts and terminology
6. STRUCTURE summary with clear academic sections: Introduction, Methodology, Findings, Conclusions
7. CITE specific page numbers when referencing content
8. USE FORMAL CITATION FORMAT for any references mentioned

TEXT TO SUMMARIZE:
{text[:4000]}  # Limit text length for model constraints

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
- [List any academic references mentioned in text]"""

        try:
            # Tokenize input
            inputs = self.tokenizer(scientific_prompt, return_tensors="pt", truncation=True, max_length=2048)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=1024,
                    temperature=0.3,  # Low temperature for more focused academic output
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract the generated part (after the prompt)
            generated_text = response_text[len(self.tokenizer.decode(inputs['input_ids'][0], skip_special_tokens=True)):]
            
            return self._parse_scientific_response(generated_text, metadata)
            
        except Exception as e:
            print(f"Error generating summary with Hugging Face: {e}")
            return self._create_fallback_summary(text, metadata)
    
    def _parse_scientific_response(self, response_text: str, metadata: Dict) -> SummaryResult:
        """Parse the Hugging Face response into structured format"""
        
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
                
            if 'ENGLISH SUMMARY:' in line:
                current_section = 'english'
                continue
            elif 'ARABIC SUMMARY:' in line:
                current_section = 'arabic'
                continue
            elif 'KEY SCIENTIFIC POINTS:' in line:
                current_section = 'key_points'
                continue
            elif 'SCIENTIFIC TERMINOLOGY:' in line:
                current_section = 'terms'
                continue
            elif 'ACADEMIC REFERENCES:' in line:
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
        """Create a basic summary if Hugging Face model fails"""
        
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
        
        citation_prompt = f"""Generate a PROPER ACADEMIC CITATION for this scientific document:

Title: {metadata.get('title', 'Unknown')}
Author: {metadata.get('author', 'Unknown')}
Pages: {metadata.get('total_pages', 0)}

Summary excerpt: {summary_text[:500]}

Provide citation in APA format for academic use."""

        try:
            inputs = self.tokenizer(citation_prompt, return_tensors="pt", truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=150,
                    temperature=0.3,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated_citation = response_text[len(self.tokenizer.decode(inputs['input_ids'][0], skip_special_tokens=True)):]
            
            return generated_citation.strip()
            
        except:
            # Fallback citation
            return f"{metadata.get('author', 'Unknown')}. ({metadata.get('title', 'Unknown')}). Academic Press, {metadata.get('total_pages', 0)} pages."