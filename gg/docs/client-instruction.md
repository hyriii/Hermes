<<<<<<< HEAD
# Hermes Project Rules (Strict Instructions)

1. **NO EXTERNAL KNOWLEDGE:** You are a strict summarizer. Use ONLY the text provided in the current input. If the input is about "Cooking", do not mention "Psychology".
2. **DYNAMIC SYSTEM PROMPT:** The System Prompt must be: "You are a professional academic assistant. Summarize the provided text accurately. Use ONLY the provided information. Do not add outside information or hallucinations."
3. **ARABIC RENDERING RULE:** - Never use `fix_text` or `arabic_reshaper` on the text before sending it to the API.
   - Use `fix_text` ONLY at the last millisecond before `st.write` or saving to PDF/PPTX.
4. **SPACING FIX:** In `fix_text`, ensure words are not merged. If merging occurs, reshape word by word.
5. **PPTX FIX:** Every slide title and content MUST be wrapped in `fix_text()` before being added to the slide.
6. **ZERO TEMPERATURE:** Always set `temperature=0.1` in Groq API calls to prevent creativity and hallucinations.
=======
# Hermes Project Rules (Strict Instructions)

1. **NO EXTERNAL KNOWLEDGE:** You are a strict summarizer. Use ONLY the text provided in the current input. If the input is about "Cooking", do not mention "Psychology".
2. **DYNAMIC SYSTEM PROMPT:** The System Prompt must be: "You are a professional academic assistant. Summarize the provided text accurately. Use ONLY the provided information. Do not add outside information or hallucinations."
3. **ARABIC RENDERING RULE:** - Never use `fix_text` or `arabic_reshaper` on the text before sending it to the API.
   - Use `fix_text` ONLY at the last millisecond before `st.write` or saving to PDF/PPTX.
4. **SPACING FIX:** In `fix_text`, ensure words are not merged. If merging occurs, reshape word by word.
5. **PPTX FIX:** Every slide title and content MUST be wrapped in `fix_text()` before being added to the slide.
6. **ZERO TEMPERATURE:** Always set `temperature=0.1` in Groq API calls to prevent creativity and hallucinations.
>>>>>>> d302dd273f4fe90bec842c8a7efcbd901d2ad035
