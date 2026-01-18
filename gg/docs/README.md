# ⚡ Hermes / أبو محسوب لعدم الرسوب 💯

**The Wisdom of Hermes • The Success of Abu Mahsoub**

An advanced AI-powered Research Assistant that transforms documents into comprehensive, visually stunning presentations with perfect Arabic text support.

## 🌟 Features

### 📚 **Comprehensive Document Processing**
- **Full PDF Coverage**: Processes entire documents using intelligent chunking logic
- **OCR Support**: Automatically handles scanned PDFs with Tesseract OCR
- **Multi-format Support**: Works with PDF uploads and Google Books integration
- **Language Detection**: Automatically detects and preserves document language

### 🎨 **Creative PPTX Generation**
- **Multiple Slide Layouts**: 4 different creative layouts per presentation
- **Visual Excellence**: Decorative elements, gradients, and professional styling
- **Arabic Perfection**: 100% correct Arabic text rendering with proper shaping
- **Responsive Design**: Modern 16:9 aspect ratio for all devices

### 🔍 **Advanced AI Analysis**
- **Chunking Logic**: Intelligent document segmentation for comprehensive coverage
- **Multi-Section Analysis**: Generates 4-8 detailed sections per document chunk
- **Language Preservation**: Maintains original document language in summaries
- **Context Awareness**: Considers page ranges and document structure

### 🛡️ **Quality Assurance**
- **Double-Checking Device**: Advanced Arabic text validation system
- **Self-Testing**: Automated PPTX inspection for Arabic correctness
- **Error Recovery**: Automatic regeneration with fixes when issues detected
- **Debug Logging**: Comprehensive logging for troubleshooting

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Groq API key (from [console.groq.com](https://console.groq.com))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/hyriii/Hermes.git
cd hermes-ai-assistant
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
export GROQ_API_KEY="your_groq_api_key_here"
```

4. **Run the application**
```bash
streamlit run app.py
```

## 📖 Usage

### 1. **Upload PDF Document**
- Upload any PDF file (text-based or scanned)
- Specify page ranges for targeted analysis
- Automatic OCR fallback for scanned documents

### 2. **Search Google Books**
- Search for books by title or author
- Select from search results for instant analysis
- Access book descriptions and metadata

### 3. **AI Analysis**
- Choose between "Quick Summary" or "Detailed Explanation"
- Hermes processes the entire document using chunking
- Generates comprehensive multi-section analysis

### 4. **Download Results**
- Beautiful PPTX presentation with creative layouts
- Perfect Arabic text rendering
- Self-tested for quality assurance

## 🏗️ Architecture

### Core Components

```
hermes-ai-assistant/
├── app.py                 # Main Streamlit application
├── src/
│   ├── __init__.py
│   ├── ppt_generator.py   # Creative PPTX generation
│   ├── pdf_processor.py   # PDF text extraction with OCR
│   ├── huggingface_engine.py
│   └── minimax_engine.py
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── client-instruction.md # AI behavior guidelines
```

### Key Technologies

- **Frontend**: Streamlit with custom CSS and glassmorphism design
- **AI Engine**: Groq API with Llama 3.3 70B model
- **Document Processing**: PyMuPDF + Tesseract OCR
- **Presentation Generation**: python-pptx with Arabic text support
- **Arabic Handling**: arabic-reshaper + python-bidi for perfect RTL rendering

## 🔧 Advanced Features

### Arabic Text Processing
- **Character Reshaping**: Proper Arabic ligature formation
- **Bidirectional Support**: Correct RTL text direction
- **Mixed Content**: Handles Arabic text mixed with numbers/symbols
- **Font Optimization**: Cairo font integration for Arabic display

### Quality Assurance
- **Double-Checking Device**: Validates Arabic text shaping and alignment
- **Self-Testing**: Automated PPTX XML inspection
- **Error Recovery**: Automatic regeneration when issues detected
- **Debug Logging**: Comprehensive troubleshooting information

### Performance Optimization
- **Intelligent Chunking**: 12000-character chunks for optimal processing
- **Memory Management**: Efficient PDF processing and cleanup
- **Caching**: Smart caching of processed content
- **Error Handling**: Robust exception handling throughout

## 🎨 Creative PPTX Features

### Slide Layouts
1. **Title Slide**: Large typography with decorative background elements
2. **Table of Contents**: Two-column layout with numbered sections
3. **Content Slides**: Cycling through 4 creative layouts:
   - Single content area
   - Two-column split
   - Title + bullet points
   - Centered content with decorations
4. **Summary Slide**: Statistics and completion metrics

### Visual Design
- **Color Palette**: Professional navy blue, gold, and accent colors
- **Typography**: Cairo font for Arabic, modern sans-serif for English
- **Decorative Elements**: Shapes, gradients, and visual separators
- **Responsive**: Optimized for 16:9 presentation format

## 🔒 Security & Privacy

- **API Key Protection**: Secure key management with environment variables
- **Local Processing**: All document processing happens locally
- **No Data Storage**: Documents are not stored on servers
- **Privacy First**: User content remains private and secure

## 🐛 Troubleshooting

### Common Issues

**ModuleNotFoundError: No module named 'src'**
- Solution: The `sys.path` logic in `app.py` handles this automatically

**Arabic text not displaying correctly**
- Solution: Ensure `arabic-reshaper` and `python-bidi` are installed
- Check that the PPTX is opened in PowerPoint (not other viewers)

**PDF extraction failing**
- Solution: For scanned PDFs, ensure Tesseract OCR is installed
- Check page range settings if using specific pages

**API quota exceeded**
- Solution: Check your Groq API usage and billing status

### Debug Mode
Enable debug logging by checking the debug output in the Streamlit interface for detailed processing information.

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Hermes**: Greek god of wisdom, commerce, and communication
- **Abu Mahsoub**: Arabic expression for "the one who doesn't fail"
- **Groq**: For providing fast and reliable AI inference
- **Streamlit**: For the amazing web app framework

## 📞 Support

For support, please:
- Check the troubleshooting section above
- Review the debug logs in the application
- Open an issue on GitHub with detailed information

---

**⚡ Hermes / أبو محسوب لعدم الرسوب 💯**
*Transforming documents into presentations with the wisdom of the gods and the success of champions*
