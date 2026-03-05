# Gemini Code Execution Testing

## Overview

This project tests the capabilities of Gemini's Code Execution feature for data analysis and statistical computing using the `google-genai` Python SDK. The testing covers file upload, code execution, statistical analysis, and data visualization.

## Quick Start

```bash
cd gemini-testing
source ../venv/bin/activate
python scripts/run_analysis.py
```

## Directory Structure

```
gemini-testing/
├── .env                          # API key configuration
├── data/
│   ├── ab_testing_data.csv       # Raw A/B testing data (150 rows)
│   └── raw_output/              # Raw outputs from Gemini
│       ├── full_text_response.txt
│       ├── code_block_*.py
│       ├── execution_result_*.txt
│       └── inline_data_*.*
├── scripts/
│   └── run_analysis.py          # Main analysis script
├── output/
│   └── ab_testing_data_raw.csv  # Copy of raw data
└── docs/
    ├── 00-overview.md               # This file
    ├── 01-file-upload.md            # File upload feature
    ├── 02-code-execution.md          # Code execution feature
    ├── 03-descriptive-statistics.md  # Statistical summaries
    ├── 04-correlation-matrix.md       # Correlation analysis
    ├── 05-group-comparisons.md        # T-tests, chi-square
    ├── 06-regression-analysis.md       # Regression modeling
    ├── 07-data-visualization.md      # Plotting capabilities
    ├── 08-visualization-stress-test.md # Stress test results
    ├── 09-histogram-test.md          # Histogram test results
    └── 10-xlsx-support-test.md       # XLSX support test (NOT SUPPORTED)
```

## Tested Features

| # | Feature | Status | Documentation |
|---|---------|--------|---------------|
| 1 | File Upload | ✅ Working | [01-file-upload.md](01-file-upload.md) |
| 2 | Code Execution | ✅ Working | [02-code-execution.md](02-code-execution.md) |
| 3 | Descriptive Statistics | ✅ Working | [03-descriptive-statistics.md](03-descriptive-statistics.md) |
| 4 | Correlation Matrix | ✅ Working | [04-correlation-matrix.md](04-correlation-matrix.md) |
| 5 | Group Comparisons | ✅ Working | [05-group-comparisons.md](05-group-comparisons.md) |
| 6 | Regression Analysis | ✅ Working | [06-regression-analysis.md](06-regression-analysis.md) |
| 7 | Data Visualization | ✅ Working | [07-data-visualization.md](07-data-visualization.md) |
| 8 | Visualization Stress Test | ✅ Working | [08-visualization-stress-test.md](08-visualization-stress-test.md) |
| 9 | Histogram Test | ✅ Working | [09-histogram-test.md](09-histogram-test.md) |
| 10 | XLSX Support Test | ❌ Not Supported | [10-xlsx-support-test.md](10-xlsx-support-test.md) |

## Test Dataset

The A/B testing dataset contains **150 rows** with the following variables:

| Variable | Type | Description |
|----------|------|-------------|
| `user_id` | int | Unique user identifier |
| `group` | string | Test group (A = control, B = treatment) |
| `conversion` | int | Binary conversion status (0 or 1) |
| `time_on_page` | float | Time spent on page (seconds) |
| `click_count` | int | Number of clicks |
| `session_duration` | float | Total session duration (minutes) |
| `bounce_rate` | float | Bounce rate (0-1 scale) |
| `page_views` | int | Number of pages viewed |

### Dataset Characteristics

- **Perfect Separation**: Group A has 0% conversion, Group B has 100% conversion
- **High Correlations**: Variables are highly correlated (|r| > 0.9)
- **Distinct Groups**: Clear separation between control and treatment groups
- **No Missing Values**: Complete dataset with no nulls

## Key Findings

### Statistical Results

1. **Conversion Rates**:
   - Control A: 0.00% (0/81)
   - Treatment B: 100.00% (69/69)
   - Chi-square: p < 0.0001 (highly significant)

2. **Numerical Metrics** (Treatment B vs Control A):
   - Time on page: +24.5 seconds (p < 0.0001)
   - Click count: +3.2 clicks (p < 0.0001)
   - Session duration: +2.8 minutes (p < 0.0001)
   - Bounce rate: -0.31 (p < 0.0001)
   - Page views: +2.6 pages (p < 0.0001)

### Correlation Patterns

- Strong positive correlations between engagement metrics (> 0.9)
- Strong negative correlations with bounce rate (< -0.9)
- Perfect correlation between conversion and group in test data

## Technical Details

### Supported Models

The following models support code execution:
- ✅ `gemini-2.5-flash` (tested, recommended)
- ✅ `gemini-2.5-pro`
- ✅ `gemini-2.0-flash`
- ❌ `gemini-2.0-flash-exp` (not supported)

### Available Libraries

- **Data Manipulation**: pandas, numpy, os
- **Statistics**: scipy.stats, statsmodels
- **Visualization**: matplotlib, seaborn

### API Usage

```python
from google.genai import Client, types

client = Client(api_key=os.getenv("GEMINI_API_KEY"))

# Upload file
uploaded_file = client.files.upload(file="data/ab_testing_data.csv")

# Generate content with code execution
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[uploaded_file, prompt],
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution())]
    )
)
```

## Raw Output Structure

The response contains multiple parts:

1. **Executable Code**: Python code blocks generated by AI
2. **Code Execution Result**: Output from code execution (stdout/stderr)
3. **Inline Data**: Binary data (images, CSVs) generated during execution
4. **Text**: Explanatory text from the model

All raw outputs are saved to `data/raw_output/` for inspection.

## Limitations

1. **Remote Execution**: Code runs in Google's cloud environment, not locally
2. **Output Location**: Generated files are stored remotely, not in local output folder
3. **File Access**: Must upload files to cloud before use
4. **Model Selection**: Some models don't support code execution
5. **Data Size Limits**: Very large datasets may exceed file upload limits
6. **Perfect Separation**: Logistic regression fails when predictors perfectly separate outcomes

## Setup Instructions

### 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install google-genai python-dotenv
```

### 2. Configure API Key

Create a `.env` file in the `gemini-testing` directory:

```bash
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Run Analysis

```bash
cd gemini-testing
source ../venv/bin/activate
python scripts/run_analysis.py
```

## Output Files

### Script Outputs
- `data/raw_output/full_text_response.txt` - Complete AI response
- `data/raw_output/code_block_*.py` - Generated Python code
- `data/raw_output/execution_result_*.txt` - Code execution output
- `data/raw_output/inline_data_*.*` - Generated files (CSVs, PNGs)

### Documentation
- Comprehensive documentation for each feature in `docs/`
- Code examples and interpretation guidance
- Best practices and limitations

## Notes

- The script handles errors gracefully (e.g., perfect separation in logistic regression)
- Statistical tests include both parametric and non-parametric checks
- Visualizations use publication-quality styling
- All analysis follows best practices for A/B testing
- Raw outputs are preserved for detailed inspection

## Future Enhancements

Potential improvements:
1. Download generated files from remote environment to local
2. Support for larger datasets
3. Custom statistical test configurations
4. Interactive plotting (plotly, bokeh)
5. Automated report generation (PDF, HTML)
6. Batch processing of multiple datasets
7. Model comparison and selection
8. Advanced regression techniques (regularization, ensemble methods)

## Additional Resources

- [Google Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Code Execution Feature Guide](https://ai.google.dev/gemini-api/docs/code-execution)
- [google-genai Python SDK](https://pypi.org/project/google-genai/)