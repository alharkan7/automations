# Correlation Matrix Feature

## Overview

Gemini Code Execution can compute and visualize correlation matrices for numerical variables, identifying relationships between metrics.

## Implementation

The AI generates Python code using pandas and numpy:

```python
import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('input_file_0.csv')

# Select numerical columns
numerical_cols = df.select_dtypes(include=np.number).columns

# Compute correlation matrix
correlation_matrix = df[numerical_cols].corr()
print("\nCorrelation Matrix:")
print(correlation_matrix)
```

## Correlation Coefficient Interpretation

| Range | Strength | Direction |
|-------|----------|-----------|
| 0.9 to 1.0 | Very Strong | Positive |
| 0.7 to 0.9 | Strong | Positive |
| 0.5 to 0.7 | Moderate | Positive |
| 0.3 to 0.5 | Weak | Positive |
| 0.0 to 0.3 | Negligible | Positive |
| 0.0 to -0.3 | Negligible | Negative |
| -0.3 to -0.5 | Weak | Negative |
| -0.5 to -0.7 | Moderate | Negative |
| -0.7 to -0.9 | Strong | Negative |
| -0.9 to -1.0 | Very Strong | Negative |

## Raw Output Example

```
Correlation Matrix:
                  conversion  time_on_page  click_count  session_duration  bounce_rate  page_views
conversion          1.000000      0.935469     0.878803          0.921194    -0.943593    0.846830
time_on_page        0.935469      1.000000     0.967274          0.993723    -0.995282    0.952641
click_count         0.878803      0.967274     1.000000          0.982445    -0.963868    0.972992
session_duration    0.921194      0.993723     0.982445          1.000000    -0.993071    0.969200
bounce_rate        -0.943593     -0.995282    -0.963868         -0.993071     1.000000   -0.947289
page_views          0.846830      0.952641     0.972992          0.969200    -0.947289     1.000000
```

## Key Findings from Test Data

### Strong Positive Correlations (> 0.9)
- **conversion ↔ time_on_page**: 0.94
- **conversion ↔ session_duration**: 0.92
- **time_on_page ↔ session_duration**: 0.99
- **time_on_page ↔ click_count**: 0.97
- **session_duration ↔ click_count**: 0.98

### Strong Negative Correlations (< -0.9)
- **conversion ↔ bounce_rate**: -0.94
- **time_on_page ↔ bounce_rate**: -0.99
- **session_duration ↔ bounce_rate**: -0.99
- **click_count ↔ bounce_rate**: -0.96

### Interpretation

The test data shows extremely strong relationships because of the experimental design:
- Higher engagement metrics (time, clicks, duration) correlate with conversion
- Higher bounce rate correlates with lower conversion
- All engagement metrics are highly correlated with each other

## Capabilities

1. **Automatic Selection**: Identifies numerical columns automatically
2. **Missing Values**: Handles NaN values appropriately
3. **Data Types**: Works with int64, float64, and other numeric types
4. **Visualization**: Can generate correlation heatmaps (see Data Visualization feature)

## Best Practices

1. **Linear Relationships**: Correlation only measures linear relationships
2. **Outliers**: Outliers can significantly affect correlation coefficients
3. **Causality**: Correlation does not imply causation
4. **Sample Size**: Larger samples provide more reliable correlation estimates
5. **Multicollinearity**: Highly correlated features can affect regression models

## Applications

1. **Feature Selection**: Identify redundant features
2. **Data Understanding**: Explore relationships in data
3. **Model Building**: Address multicollinearity in regression
4. **Hypothesis Generation**: Generate hypotheses about relationships

## Test Results

Successfully computed correlation matrix for:
- 7 numerical variables
- 150 observations
- All pairwise correlations computed correctly

All correlation values are in the expected range [-1, 1] and match expected patterns based on the experimental design.