# Automations

A collection of Python scripts, Chrome extensions, and tools for personal productivity and automation.

## Projects

| Project | Description | Language |
|---------|-------------|----------|
| **al-library** | Local ebook inventory, Google Books enrichment, and HTML viewer with macOS Books-style grid | Python |
| **github-stars** | Sync categorized GitHub stars to GitHub Lists via GraphQL | Python |
| **chrome_reading_list_extension** | Chrome extension that syncs Reading List to Supabase PostgreSQL | JavaScript |
| **linkedin-connections** | Automated LinkedIn connection removal using Playwright | Python |
| **cloudflare-crawl** | Web crawling using Cloudflare's Browser Rendering API | Bash |
| **reference-agent** | Intelligent autonomous literature review system using OpenAlex and Gemini | Python |
| **git_dailies** | Daily git commit automation and bookmark update scripts | Python |
| **code-execution-analysis** | A/B testing data analysis using Gemini Code Execution | Python |
| **compress** | Image compression utilities with intelligent resizing | Python |
| **conversion** | PDF compression with quality control | Python |
| **cv-review** | CV evaluation using Gemini 2.5 Pro with resume capability | Python |
| **prisma** | Systematic Literature Review (SLR) tool with PRISMA workflow | Python |
| **to-markdown** | PDF to Markdown batch converter using markitdown | Python |
| **twitter-alhrkn** | Streamlit app to fetch X (Twitter) bookmarks via API v2 | Python |

## Getting Started

Each project is self-contained with its own dependencies and setup instructions. Navigate to the project directory and refer to its README for detailed setup and usage instructions.

### Prerequisites

Most Python projects require:
- Python 3.10 or later
- Virtual environment (recommended)

```bash
cd <project-directory>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment Variables

Some projects require environment variables. Create a `.env` file in the project root or at the repository level:

```bash
# Example .env file
GOOGLE_BOOKS_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here
SUPABASE_URL=your_url_here
SUPABASE_ANON_KEY=your_key_here
```

## Project Highlights

### al-library
Manages a personal ebook library with:
- File discovery and inventory generation from `~/Downloads/Lib*`
- Filename normalization (typos, publisher tails, underscore cleanup)
- Google Books metadata enrichment via API
- Static HTML viewer with search, filtering, and macOS Finder integration
- CSV-based scan with incremental resume support

### github-stars
Synchronizes locally categorized GitHub stars to GitHub Lists:
- Reads from `github_stars_categorized.json`
- Creates missing lists via GraphQL
- Assigns repositories to appropriate lists
- Supports dry-run mode and batch operations

### chrome_reading_list_extension
Chrome extension (Chrome 120+) that:
- Auto-syncs Reading List to Supabase PostgreSQL on browser startup (once per day)
- Provides statistics (total, read, unread)
- Supports manual export to JSON
- Uses Row Level Security (RLS) on database

### reference-agent
Academic literature review tool featuring:
- Iterative OpenAlex search for academic papers
- Gemini-powered relevance evaluation
- Streamlit UI for interactive queries
- Configurable target paper counts and API limits

### git_dailies
Daily automation scripts for git workflows:
- Automated daily git commits with timestamp logging
- Chrome bookmarks and liked videos sync to GitHub Pages
- Cloudflare Worker deployment for scheduled tasks

### code-execution-analysis
A/B testing data analysis using Gemini Code Execution:
- Statistical analysis of conversion data
- Automated visualization generation
- Correlation matrices and regression analysis
- Supports both CSV and XLSX formats

### compress
Image compression utilities with intelligent resizing:
- Scales images down to max 2000px while maintaining aspect ratio
- Multiple compression strategies (size-based, optimized)
- Preserves original format and filenames

### conversion
PDF compression with quality control:
- Multiple compression strategies (pypdf, Ghostscript)
- Quality presets: high, medium, low
- Minimal text quality loss

### cv-review
CV evaluation using Gemini 2.5 Pro:
- Resume-capable processing
- JSON-structured evaluation output
- Scoring against job descriptions
- Batch processing of multiple CVs

### linkedin-connections
Automated LinkedIn connection removal:
- Playwright-based browser automation
- Resumable processing from CSV
- Human-like delays and batch pauses
- Safe error handling with backup creation

### cloudflare-crawl
Web crawling using Cloudflare's Browser Rendering API:
- Crawl websites and convert to markdown, HTML, or JSON
- Support for AI extraction with custom prompts
- Include/exclude pattern matching
- Job status polling and result retrieval

### prisma
Systematic Literature Review (SLR) tool with PRISMA workflow:
- Duplicate detection (DOI, title, fuzzy matching)
- Complete screening workflow with tracking
- PRISMA flow diagram generation based on actual decisions
- Data persistence with JSON state management
- Export capability for included studies

### to-markdown
Simple batch PDF to Markdown converter:
- Uses Microsoft's `markitdown`
- Handles tables and text formatting
- Supports batch directory processing

### twitter-alhrkn
Streamlit app to fetch X (Twitter) bookmarks:
- OAuth 2.0 authentication with X API v2
- Requires X API Basic tier or higher
- Saves bookmarks to JSON format

## License

This collection of personal automation scripts is provided as-is for reference and personal use.
