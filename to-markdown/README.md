# PDF to Markdown Converter

A simple utility to batch convert PDF files into Markdown using Microsoft's `markitdown` library.

## Setup

1. Ensure you have a virtual environment active.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script and provide the source directory containing PDF files:

```bash
python convert.py "/path/to/your/pdfs" [output_directory]
```

By default, it will save the converted files to an `output/` directory within this folder.

### Example

```bash
python convert.py "/Users/alharkan/Documents/Drive/Study/Seminar Proposal Disertasi"
```
