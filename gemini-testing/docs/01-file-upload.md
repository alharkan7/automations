# File Upload Feature

## Overview

Gemini Code Execution supports uploading local files to Google's cloud storage for use during code execution.

## How It Works

Using the `google-genai` SDK:

```python
from google.genai import Client

client = Client(api_key=os.getenv("GEMINI_API_KEY"))

# Upload local file
uploaded_file = client.files.upload(file="data/ab_testing_data.csv")
```

## Upload Response

The upload returns a file object with the following properties:

```python
{
    "name": "files/91a0fnuudwti",
    "uri": "https://generativelanguage.googleapis.com/v1beta/files/91a0fnuudwti",
    "display_name": None,
    "mime_type": "text/csv"
}
```

## Supported File Types

Based on testing, the following file types are supported:
- **CSV files** (`text/csv`) - Tabular data
- **Images** (`image/png`, `image/jpeg`) - For analysis
- **JSON files** (`application/json`) - Structured data
- Other types may be supported but not yet tested

## Usage in Code Execution

Once uploaded, the file is accessible in the code execution environment as `input_file_0.csv` (or similar auto-generated name):

```python
# In the generated Python code
import pandas as pd
df = pd.read_csv('input_file_0.csv')
```

## Raw Output

The file upload process creates:
1. A unique file ID (e.g., `91a0fnuudwti`)
2. A URI for accessing the file
3. MIME type detection based on file content

## Limitations

1. **File Size**: Large files may exceed upload limits
2. **Storage Duration**: Uploaded files are temporary and expire after a period
3. **Network Dependency**: Requires internet connection to upload
4. **Privacy**: Files are uploaded to Google's cloud storage

## Test Results

Successfully uploaded a 3,881-byte CSV file with 150 rows of A/B testing data.

```bash
File uploaded: files/91a0fnuudwti
  URI: https://generativelanguage.googleapis.com/v1beta/files/91a0fnuudwti
  Display name: None
  MIME type: text/csv
```

## Best Practices

1. Always check file existence before uploading
2. Handle upload errors gracefully
3. Use appropriate file paths (relative to script location)
4. Clean up old files if storage limits are a concern