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
| **git_dailies** | Daily git commit automation scripts | Python |
| **code-execution-analysis** | Analysis of code execution patterns | Python |
| **compress** | Image compression utilities | Python |
| **prisma** | Prisma ORM related tools | TypeScript |
| **to-markdown** | PDF to Markdown batch converter | Python |

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
- File discovery and inventory generation
- Filename normalization
- Google Books metadata enrichment
- Static HTML viewer with search and filtering

### github-stars
Synchronizes locally categorized GitHub stars to GitHub Lists:
- Reads from `github_stars_categorized.json`
- Creates missing lists via GraphQL
- Assigns repositories to appropriate lists

### chrome_reading_list_extension
Chrome extension (Chrome 120+) that:
- Auto-syncs Reading List to Supabase on browser startup
- Provides statistics (total, read, unread)
- Supports manual export to JSON

### reference-agent
Academic literature review tool featuring:
- Iterative OpenAlex search
- Gemini-powered relevance evaluation
- Streamlit UI for interactive queries

### to-markdown
Simple batch PDF to Markdown converter:
- Uses Microsoft's `markitdown`
- Handles tables and text formatting
- Supports batch directory processing

## License

This collection of personal automation scripts is provided as-is for reference and personal use.
