# HTML to PDF Converter

A powerful tool that reads the index.html file (must use this name) from the src folder, parses the table of contents from the index page, matches it with HTML files in the src folder, and generates a bookmark.txt file. The program then converts HTML files to a single PDF document in order according to the table of contents using Node.js's Playwright library, and uses Python's PyPDF2 library to convert bookmark.txt into PDF bookmarks.

This project can convert multiple HTML files into a single PDF document with automatic bookmark generation. It was originally developed to convert the "SSH Tutorial" from WangDoc.com into a downloadable PDF format. Therefore, this project includes sample files from the "SSH Tutorial".

Original sample file website: https://wangdoc.com/ssh/
Sample files on Github: https://github.com/wangdoc/ssh-tutorial

## Features

- 📄 Convert multiple HTML files to a single PDF document
- 📖 Automatic table of contents generation based on index.html
- 🔖 Interactive PDF bookmarks with hierarchical structure
- 🎨 Customizable cover page with image support
- 🌐 Multi-language support (Chinese/English)
- 🧪 Test mode for quick validation
- 📱 Responsive design preservation

## Prerequisites

- Node.js (v14 or higher)
- Python 3.11.x以上 (for bookmark functionality)
- npm or yarn

## Installation

1. Clone this repository
```bash
git clone <repository-url>
cd html2pdf
```

2. Install Node.js dependencies
```bash
npm install
```

3. Install Python dependencies (for bookmark generation)
```bash
pip install PyPDF2
```

## Usage
- Place all HTML files of your static web pages in the `/src` folder, which must include an `index.html` file containing the table of contents.
- CSS style files should be placed in the `/src/assets` folder. Refer to the sample for folder structure.
- The cover page can be customized. The cover image must be located in the `/src` folder and named `fengmian.png`.

### Full Conversion
Convert all HTML files according to the table of contents:
```bash
node merge_by_toc.js
```

### Test Mode
Convert only the first file in the table of contents for testing to avoid long conversion time:
```bash
node merge_by_toc.js --test
```

### Add Bookmarks to PDF
Add interactive bookmarks to an existing PDF:
```bash
# Bookmark file defaults to bookmarks.txt, output file defaults to "original_filename_with_bookmarks.pdf"
python add_bookmarks.py <pdf-file> [bookmarks-file] [output-file]
```

### Examples
```bash
# Full conversion, automatically generates bookmarks.txt based on index.html content, and automatically adds bookmarks to PDF files.
node merge_by_toc.js

# Test mode
node merge_by_toc.js --test

# Manually add bookmarks to existing PDF, normally not necessary.
python add_bookmarks.py output/document_by_toc.pdf
python add_bookmarks.py output/document_by_toc.pdf output/bookmarks.txt output/final_document.pdf
```

## Project Structure

```
html2pdf/
├── src/                    # Source HTML files
│   ├── index.html         # Main page with table of contents
│   ├── basic.html         # Chapter files
│   ├── client.html
│   ├── assets/           # Static resources
│   │   ├── css/          # Stylesheets
│   │   ├── js/           # JavaScript files
│   │   ├── icons/        # Favicons and app icons
│   │   └── fonts/        # Font files
├── output/               # Generated files
│   ├── document_by_toc.pdf              # Main PDF output
│   ├── document_by_toc_with_bookmarks.pdf  # PDF with bookmarks
│   └── bookmarks.txt     # Bookmark information
├── merge_by_toc.js       # Main conversion script
├── add_bookmarks.py      # Bookmark generation script
└── playwright.config.ts  # Playwright configuration
```

## How It Works

1. **Parse Table of Contents**: The script reads `src/index.html` and extracts the table of contents structure
2. **HTML to PDF Conversion**: Uses Playwright to convert each HTML file to PDF
3. **PDF Merging**: Combines all PDFs using pdf-lib with cover page and table of contents
4. **Bookmark Generation**: Uses PyPDF2 to add interactive bookmarks to the final PDF

## Configuration

### Cover Page Customization
- Replace `src/fengmian.png` with your own cover image
- The script automatically detects image format (PNG/JPG)
- Supports Chinese fonts for cover text

### Styling
- Print-specific CSS is automatically injected during conversion
- Navigation elements are hidden in the PDF output
- Code blocks and images are optimized for print

## Output Files

- `document_by_toc.pdf` - Main PDF document
- `document_by_toc_with_bookmarks.pdf` - PDF with interactive bookmarks
- `bookmarks.txt` - Text file containing bookmark information
- `test_*.*` - Test mode files (when using --test flag)

## Dependencies

### JavaScript
- **@playwright/test** - Browser automation for HTML to PDF conversion
- **pdf-lib** - PDF manipulation and merging
- **@pdf-lib/fontkit** - Font embedding support
- **cheerio** - HTML parsing for table of contents extraction

### Python
- **PyPDF2** - PDF bookmark generation

## Browser Support

The tool uses Playwright and supports all modern browsers:
- Chromium-based browsers
- Firefox
- WebKit (Safari)

## Troubleshooting

### Font Issues
- The script automatically tries to load Chinese fonts from the system
- If fonts are not available, it falls back to English text
- Supported fonts: SimHei, SimSun, Microsoft YaHei, KaiTi

### Memory Management
- The script automatically releases memory every 3 files processed
- Temporary files are cleaned up after conversion

### Common Issues
- Ensure all HTML files exist in the `src/` directory
- Check that `index.html` contains proper table of contents links
- Verify Python and PyPDF2 are installed for bookmark functionality

## License

This project is for educational and personal use. Please respect the original content license.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Original Content

The original content follows the Creative Commons Attribution-ShareAlike 3.0 License.