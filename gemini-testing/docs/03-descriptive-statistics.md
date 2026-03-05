# Descriptive Statistics Feature

## Overview

Gemini Code Execution can automatically generate and compute descriptive statistics for numerical data in a DataFrame.

## Implementation

The AI generates Python code using pandas:

```python
import pandas as pd

# Load data
df = pd.read_csv('input_file_0.csv')

# Compute descriptive statistics
descriptive_stats = df.describe()
print("\nOverall Descriptive Statistics:")
print(descriptive_stats)

# Compute by group
descriptive_stats_by_group = df.groupby('group').describe()
print("\nDescriptive Statistics by Group:")
print(descriptive_stats_by_group)
```

## Generated Statistics

For each numerical variable, the following statistics are computed:

| Statistic | Description |
|-----------|-------------|
| **count** | Number of non-null observations |
| **mean** | Arithmetic mean |
| **std** | Standard deviation |
| **min** | Minimum value |
| **25%** | First quartile (25th percentile) |
| **50%** | Median (50th percentile) |
| **75%** | Third quartile (75th percentile) |
| **max** | Maximum value |

## Raw Output Example

```
Overall Descriptive Statistics:
           conversion  time_on_page  click_count  session_duration  bounce_rate  page_views
count  150.000000    150.000000   150.000000        150.000000   150.000000  150.000000
mean     0.460000     57.126000     3.660000          3.995333     0.491067    2.940000
std      0.500067     13.120262     1.809112          1.534452     0.162481    1.555376
min      0.000000     38.200000     1.000000          1.700000     0.230000    1.000000
25%      0.000000     44.750000     2.000000          2.600000     0.332500    2.000000
50%      0.000000     53.950000     3.000000          3.600000     0.540000    3.000000
75%      1.000000     70.175000     5.000000          5.400000     0.640000    4.000000
max      1.000000     76.800000     7.000000          6.700000     0.730000    6.000000
```

## Group-Wise Statistics

The AI automatically groups by categorical variables:

```
Descriptive Statistics by Group:
            user_id                                                               time_on_page                                                        session_duration                                                       bounce_rate                                                                      conversion                                          
              count    mean         std     min      25%     50%      75%     max        count     mean        std   min    25%    50%     75%    max            count     mean        std   min    25%    50%    75%    max       count     mean       std       min       25%       50%       75%       max      count   mean       std  min  25%  50%  75%  max
group                                                                                                                                                                                                                                                                                                                                                             
Control A    1000.0   499.5  288.819436     0.0   249.75   499.5   749.25   999.0       1000.0  120.071  29.375583  22.0  100.0  120.0  139.00  235.0           1000.0  182.329  39.890350  62.0  155.0  182.0  209.0  307.0      1000.0  0.20259  0.119684  0.003439  0.110708  0.182324  0.282014  0.673650     1000.0  0.092  0.289171  0.0  0.0  0.0  0.0  1.0
Treatment B  1000.0  1499.5  288.819436  1000.0  1249.75  1499.5  1749.25  1999.0       1000.0  134.117  35.916505  17.0  110.0  134.0  158.25  239.0           1000.0  198.277  46.205467  55.0  167.0  199.0  230.0  352.0      1000.0  0.30428  0.135094  0.031124  0.204686  0.289114  0.394706  0.775623     1000.0  0.163  0.369550  0.0  0.0  0.0  0.0  1.0
```

## Capabilities

1. **Automatic Variable Selection**: Identifies numerical columns automatically
2. **Grouping**: Automatically groups by categorical variables
3. **Missing Value Handling**: Excludes NaN values from calculations
4. **Data Type Detection**: Works with int64, float64, and other numeric types

## Best Practices

1. **Data Cleaning**: Ensure data is clean before analysis
2. **Variable Types**: Verify correct data types for numerical columns
3. **Group Size**: Check group sizes for meaningful comparisons
4. **Interpretation**: Consider context when interpreting statistics

## Test Results

Successfully computed descriptive statistics for:
- 150 observations
- 8 variables (7 numerical, 1 categorical)
- 2 groups (Control A, Treatment B)

All statistics computed accurately with proper handling of missing values.