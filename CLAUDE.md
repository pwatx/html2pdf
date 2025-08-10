# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an HTML to PDF conversion tool that transforms multiple HTML files into a single PDF document with automatic bookmark generation. The project parses the table of contents from `src/index.html`, converts HTML files to PDF in order, and adds interactive bookmarks using a combination of Node.js and Python scripts.

This project was originally developed to convert the "SSH Tutorial" from WangDoc.com into a downloadable PDF format, and includes sample files from that tutorial.

## Common Commands

### Install Dependencies
```bash
npm install
```

### Install Python Dependencies (for bookmarks)
```bash
pip install PyPDF2
```

### Run HTML to PDF Conversion (Full)
```bash
node merge_by_toc.js
```

### Test Mode (Convert only first file)
```bash
node merge_by_toc.js --test
```

### Add Bookmarks to PDF
```bash
python add_bookmarks.py <pdf_file_path> [bookmarks_file_path] [output_file_path]
```

### Run Playwright Tests
```bash
npx playwright test
```

## Project Architecture

### Core Files
- `merge_by_toc.js` - Main conversion script using Playwright and pdf-lib
- `add_bookmarks.py` - Python script for adding PDF bookmarks using PyPDF2
- `toc_parser.py` - Python script for parsing hierarchical table of contents structure
- `playwright.config.ts` - Playwright test configuration

### Directory Structure
- `src/` - Source HTML files directory
  - `index.html` - Main page containing table of contents structure
  - `basic.html`, `client.html`, etc. - Individual chapter HTML files
  - `assets/` - Static resources (CSS, JS, images, fonts)
- `output/` - Output directory
  - `document_by_toc.pdf` - Generated PDF document
  - `document_by_toc_with_bookmarks.pdf` - PDF with bookmarks
  - `bookmarks.txt` - Bookmark information file

### Workflow
1. Parse `src/index.html` to extract table of contents and HTML file order
2. Use Playwright to convert each HTML file to PDF with print-optimized styling
3. Merge all PDFs using pdf-lib, adding cover page and hierarchical table of contents
4. Generate bookmark information file and use PyPDF2 to add interactive bookmarks

## Key Dependencies

### JavaScript Dependencies
- **@playwright/test** - Browser automation for HTML to PDF conversion
- **pdf-lib** - PDF manipulation and merging library
- **@pdf-lib/fontkit** - Font embedding support for Chinese characters
- **cheerio** - HTML parsing for table of contents extraction

### Python Dependencies
- **PyPDF2** - PDF bookmark manipulation (requires separate installation)
- **BeautifulSoup** - HTML parsing for hierarchical table of contents extraction

## Important Implementation Details

### Chinese Font Support
- Script automatically attempts to load Windows system fonts (SimHei, SimSun, Microsoft YaHei, KaiTi)
- Falls back to English text if Chinese fonts are unavailable
- Font loading happens at `merge_by_toc.js:207-236`

### Print Optimization
- Custom CSS injected during conversion hides navigation elements
- Code blocks and images optimized for print layout
- Print-specific styles applied at `merge_by_toc.js:420-466`

### Memory Management
- Playwright context memory released every 5 files processed
- Temporary files automatically cleaned up after conversion
- Memory management logic at `merge_by_toc.js:537-542`

### Bookmark Generation
- Two-step process: JavaScript generates bookmark info, Python adds to PDF
- Bookmark format: "序号. 章节标题 (第X页)"
- Supports cover page (page 1) and table of contents (page 2) bookmarks
- Table of contents page supports hierarchical structure and automatic pagination for large documents
- Bookmarks support multi-level hierarchy with proper parent-child relationships

### Error Handling
- Graceful handling of missing HTML files with warnings
- Automatic fallback for image format detection
- UTF-8 encoding support for Chinese characters in Python script

### Table of Contents Parsing
- Uses multiple CSS selectors to find TOC structure in `index.html`
- Supported selectors: `.panel-menu a`, `.menu-list a`, `.toc a`, `.sidebar a`, etc.
- Parsing logic at `merge_by_toc.js:126-159`
- Generates hierarchical table of contents with proper indentation and pagination
- Uses BeautifulSoup in `toc_parser.py` for more robust hierarchical parsing

### Cover Page Generation
- Automatically detects and embeds cover image (`fengmian.png`)
- Supports both PNG and JPG formats with automatic detection
- Adds title and author information from HTML metadata
- Cover generation logic at `merge_by_toc.js:202-341`

### Table of Contents Page Generation
- Dynamically generates table of contents page with hierarchical structure
- Automatically handles pagination for large tables of contents
- Properly accounts for additional TOC pages when calculating page numbers
- Uses indentation to represent hierarchical structure

## Development Notes

### HTML File Requirements
- All HTML files must be in `src/` directory
- `index.html` must contain proper table of contents with relative links
- Cover image should be named `fengmian.png` in `src/` directory

### PDF Output Specifications
- A4 paper format with 15mm top/bottom margins, 10mm left/right margins
- Automatic header (chapter title) and footer (page numbers)
- Background images and styles preserved during conversion

### Testing
- Use `--test` flag for quick validation with single file conversion
- Test files prefixed with `test_` to avoid conflicts with production files
- Playwright configuration supports multiple browsers (Chromium, Firefox, WebKit)

### File Naming Convention
- Output files are named using document title and author from HTML metadata
- Filenames are sanitized to remove invalid characters
- Test mode files use `test_` prefix to avoid conflicts

### Recent Improvements
- Enhanced table of contents page generation with hierarchical structure support
- Automatic pagination for large tables of contents
- Proper page number calculation that accounts for multiple TOC pages
- Improved bookmark generation with hierarchical support