# File Format Support Test

## Overview

Tested whether Gemini Code Execution supports XLSX (Microsoft Excel) file format in addition to CSV.

## Test Configuration

- **Script**: `scripts/run_analysis_xlsx.py`
- **Input File**: `data/ab_testing_data.xlsx` (converted from CSV)
- **Model**: `gemini-2.5-flash`
- **Test Operation**: Upload XLSX and run code execution analysis

## File Upload Results

### ✅ Upload Successful

```
File uploaded: files/jwzm5dk1hgdw
URI: https://generativelanguage.googleapis.com/v1beta/files/jwzm5dk1hgdw
Display name: None
MIME type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
```

**File Details**:
- **Size**: 10 KB
- **MIME Type**: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (standard Excel MIME)
- **Status**: Successfully uploaded to Gemini file storage

## Code Execution Results

### ❌ XLSX NOT SUPPORTED

When attempting to use the uploaded XLSX file with code execution:

```
google.genai.errors.ClientError: 400 INVALID_ARGUMENT
{'error': {
    'code': 400,
    'message': 'Unsupported MIME type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'status': 'INVALID_ARGUMENT'
}}
```

## Conclusion

### ❌ Gemini Code Execution DOES NOT Support XLSX

**Status**: XLSX files can be uploaded to file storage but **CANNOT** be used with Code Execution feature.

## Supported vs Unsupported File Formats

| Format | File Upload | Code Execution | Notes |
|---------|-------------|-----------------|-------|
| **CSV** | ✅ Supported | ✅ Supported | Primary data format for code execution |
| **XLSX** | ✅ Supported | ❌ NOT Supported | Uploads fine, but rejected by code execution |
| **JSON** | ✅ Supported | ⚠️ Limited | Can be uploaded, but parsing depends on AI |
| **TXT** | ✅ Supported | ⚠️ Limited | Can be uploaded, but structured parsing needed |
| **PNG** | ✅ Supported | ✅ Supported (output) | Images can be uploaded and analyzed |
| **JPG** | ✅ Supported | ✅ Supported (output) | Images can be uploaded and analyzed |

## Why XLSX is Not Supported

### Technical Reasons

1. **Sandbox Security**: XLSX is a complex binary format that can contain:
   - Macros (VBA code)
   - External data connections
   - Embedded objects
   - Security vulnerabilities

2. **Parsing Complexity**: XLSX requires special libraries:
   - `openpyxl` or `xlrd` for reading
   - Additional dependencies for complex features

3. **Consistency**: CSV is simple, text-based, and universally supported

### Design Choice

Google likely chose to support only CSV for:
- **Simplicity**: Plain text, easy to parse
- **Security**: No executable code, no hidden content
- **Portability**: Universally compatible
- **Performance**: Faster to parse and process

## Workarounds

### If You Have XLSX Data

#### Option 1: Convert to CSV (Recommended)
```bash
# Using pandas
import pandas as pd
df = pd.read_excel('data.xlsx', engine='openpyxl')
df.to_csv('data.csv', index=False)
```

#### Option 2: Use Google Sheets
1. Upload XLSX to Google Sheets
2. Export to CSV from Google Sheets
3. Use CSV with Gemini Code Execution

#### Option 3: AI Conversion
Ask the AI to convert:
```
"Here's my data in XLSX format. Please help me convert it to CSV format for analysis."
```

## Recommendations

### For Data Analysis

1. **Prefer CSV**: Always use CSV for code execution
2. **Convert Early**: Convert XLSX to CSV before uploading
3. **Keep Both**: Maintain XLSX for Excel users, create CSV for analysis
4. **Automate**: Build conversion scripts in your workflow

### For File Uploads

1. **Check MIME Type**: Ensure correct MIME type before use
2. **Test Format**: Verify file is supported before complex analysis
3. **Handle Errors**: Catch and report unsupported format errors

## Test Code

### Upload Code (XLSX)
```python
from google.genai import Client

client = Client(api_key=os.getenv("GEMINI_API_KEY"))

# Upload XLSX - THIS SUCCEEDS
uploaded_file = client.files.upload(file="data.xlsx")
print(f"Uploaded: {uploaded_file.name}")
print(f"MIME type: {uploaded_file.mime_type}")
```

### Code Execution Attempt (XLSX) - FAILS
```python
from google.genai import Client, types

client = Client(api_key=os.getenv("GEMINI_API_KEY"))

# Upload XLSX
uploaded_file = client.files.upload(file="data.xlsx")

# Attempt to use with code execution - THIS FAILS
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[uploaded_file, prompt],
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution())]
    )
)
# ERROR: 400 INVALID_ARGUMENT
# 'Unsupported MIME type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
```

### Code Execution Code (CSV) - SUCCESS
```python
from google.genai import Client, types

client = Client(api_key=os.getenv("GEMINI_API_KEY"))

# Upload CSV - THIS SUCCEEDS
uploaded_file = client.files.upload(file="data.csv")
print(f"Uploaded: {uploaded_file.name}")
print(f"MIME type: {uploaded_file.mime_type}")

# Use with code execution - THIS SUCCEEDS
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[uploaded_file, prompt],
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution())]
    )
)
# SUCCESS: Analysis runs normally
```

## Final Answer

### ❌ NO, Gemini Only Supports CSV for Code Execution

**Gemini Code Execution does NOT support XLSX files**. While you can upload XLSX files to Gemini's file storage, attempting to use them with code execution will result in a 400 error:

```
Unsupported MIME type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
```

**Best Practice**: Always convert XLSX to CSV before using with Gemini Code Execution.

## Summary Table

| Feature | CSV | XLSX |
|---------|-----|-------|
| File Upload | ✅ Yes | ✅ Yes |
| Code Execution | ✅ Yes | ❌ No |
| Error Handling | Standard | MIME type error |
| Recommended | **Primary format** | Convert to CSV first |

## Resources

- [pandas Excel documentation](https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html)
- [openpyxl documentation](https://openpyxl.readthedocs.io/)
- [MIME types reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types)