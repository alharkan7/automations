# Group Comparisons Feature

## Overview

Gemini Code Execution can perform statistical comparisons between groups, including conversion rate analysis and t-tests for numerical metrics.

## Implementation

### Conversion Rate Comparison (Chi-Square Test)

```python
import pandas as pd
from scipy.stats import chi2_contingency

# Group data
control_group = df[df['group'] == 'Control A']
treatment_group = df[df['group'] == 'Treatment B']

# Calculate conversion rates
conv_control = control_group['conversion'].sum()
total_control = len(control_group)
rate_control = conv_control / total_control

conv_treatment = treatment_group['conversion'].sum()
total_treatment = len(treatment_group)
rate_treatment = conv_treatment / total_treatment

# Create contingency table
contingency_table = pd.DataFrame({
    'Converted': [conv_control, conv_treatment],
    'Not Converted': [total_control - conv_control, total_treatment - conv_treatment]
}, index=['Control A', 'Treatment B'])

# Perform Chi-square test
chi2, p_value, _, _ = chi2_contingency(contingency_table)
```

### T-Tests for Numerical Metrics

```python
from scipy.stats import ttest_ind, levene

# Check for equal variances using Levene's test
stat_levene, p_levene = levene(
    control_group[metric].dropna(),
    treatment_group[metric].dropna()
)
equal_var = p_levene > 0.05

# Perform t-test
t_stat, p_value = ttest_ind(
    control_group[metric].dropna(),
    treatment_group[metric].dropna(),
    equal_var=equal_var
)
```

## Raw Output Example

### Conversion Rate Comparison

```
--- Conversion Rate Comparison ---
Control A Conversion Rate: 0.0920 (92/1000)
Treatment B Conversion Rate: 0.1630 (163/1000)

Chi-square Test for Conversion Rates:
Chi-square Statistic: 22.0237
P-value: 0.0000
Conclusion: There is a statistically significant difference in conversion rates between Control A and Treatment B.
```

### Mean Comparison and T-Tests

```
--- Mean Comparison and T-tests for Key Metrics ---

--- Metric: time_on_page ---
Control A Mean time_on_page: 120.0710
Treatment B Mean time_on_page: 134.1170
Levene's Test (for equal variances): stat=33.7562, p=0.0000 (Equal variances assumed: False)
T-test Statistic: -9.5728
T-test P-value: 0.0000
Conclusion: There is a statistically significant difference in time_on_page between Control A and Treatment B.
```

## Statistical Tests Used

### Chi-Square Test
- **Purpose**: Test for independence between categorical variables
- **Use Case**: Comparing conversion rates between groups
- **Assumptions**:
  - Observations are independent
  - Expected frequency in each cell ≥ 5

### Independent T-Test
- **Purpose**: Compare means between two independent groups
- **Use Case**: Comparing numerical metrics between groups
- **Assumptions**:
  - Normal distribution (approximately)
  - Independent samples
  - Homogeneity of variances (optional - checked with Levene's test)

### Levene's Test
- **Purpose**: Test for equality of variances
- **Use Case**: Determine which t-test variant to use
- **Result**: If p > 0.05, assume equal variances (Student's t-test); otherwise, use Welch's t-test

## Key Findings from Test Data

### Conversion Rates
| Group | Conversions | Total | Rate | Significance |
|-------|-----------|-------|------|--------------|
| Control A | 0 | 81 | 0.00% | p < 0.0001 |
| Treatment B | 69 | 69 | 100.00% | p < 0.0001 |

### Numerical Metrics Comparison

| Metric | Mean (A) | Mean (B) | Difference | p-value | Significance |
|--------|----------|----------|-------------|---------|--------------|
| time_on_page | 45.84 | 70.38 | +24.54 | < 0.0001 | Yes |
| click_count | 2.20 | 5.38 | +3.18 | < 0.0001 | Yes |
| session_duration | 2.70 | 5.52 | +2.83 | < 0.0001 | Yes |
| bounce_rate | 0.63 | 0.33 | -0.31 | < 0.0001 | Yes |
| page_views | 1.73 | 4.36 | +2.63 | < 0.0001 | Yes |

## Capabilities

1. **Automatic Grouping**: Identifies categorical variables for grouping
2. **Variance Testing**: Automatically checks variance assumptions
3. **Test Selection**: Chooses appropriate test based on assumptions
4. **Multiple Metrics**: Can test multiple numerical variables
5. **Interpretation**: Provides interpretation of statistical significance

## Best Practices

1. **Sample Size**: Ensure adequate sample size for each group
2. **Assumption Checking**: Verify test assumptions are met
3. **Multiple Comparisons**: Consider adjusting for multiple comparisons
4. **Effect Size**: Report effect size along with p-values
5. **Practical Significance**: Distinguish between statistical and practical significance

## Applications

1. **A/B Testing**: Compare performance of different treatments
2. **Marketing Analysis**: Compare campaign effectiveness
3. **User Research**: Compare user segments
4. **Quality Control**: Compare production batches
5. **Medical Research**: Compare treatment groups

## Test Results

Successfully performed:
- 1 chi-square test (conversion rate)
- 5 t-tests with Levene's test (numerical metrics)
- Automatic variance assumption checking
- Proper test selection based on assumptions

All tests executed correctly with appropriate interpretations.