# Regression Analysis Feature

## Overview

Gemini Code Execution can perform regression analysis to model relationships between variables and make predictions.

## Implementation

### Logistic Regression (for binary outcomes)

```python
import pandas as pd
import statsmodels.api as sm

# Prepare data
df_reg = df.copy()

# Encode categorical variables
df_reg['group_encoded'] = df_reg['group'].apply(
    lambda x: 1 if x == 'Treatment B' else 0
)

# Define predictors and response
X = df_reg[['time_on_page', 'session_duration', 'bounce_rate', 'group_encoded']]
y = df_reg['conversion']

# Add intercept
X = sm.add_constant(X)

# Fit logistic regression model
logit_model = sm.Logit(y, X)
result = logit_model.fit()

# Print summary
print(result.summary())
```

### Linear Regression (for continuous outcomes)

```python
import statsmodels.formula.api as smf

# Fit linear regression model
model = smf.ols(
    'conversion ~ time_on_page + session_duration + bounce_rate + group',
    data=df
).fit()

# Print summary
print(model.summary())
```

## Raw Output Example

```
Logistic Regression Model Summary:
                           Logit Regression Results                           
==============================================================================
Dep. Variable:             conversion   No. Observations:                 2000
Model:                          Logit   Df Residuals:                     1995
Method:                           MLE   Df Model:                            4
Date:                Thu, 05 Mar 2026   Pseudo R-squ.:                 0.01554
Time:                        22:45:21   Log-Likelihood:                -751.35
converged:                       True   LL-Null:                       -763.21
Covariance Type:            nonrobust   LLR p-value:                 9.095e-05
====================================================================================
                       coef    std err          z      P>|z|      [0.025      0.975]
------------------------------------------------------------------------------------
const               -2.1699      0.400     -5.429      0.000      -2.953      -1.387
time_on_page         0.0002      0.002      0.084      0.933      -0.004       0.004
session_duration    -0.0011      0.002     -0.706      0.480      -0.004       0.002
bounce_rate          0.2812      0.518      0.543      0.587      -0.734       1.296
group_encoded        0.6396      0.153      4.175      0.000       0.339       0.940
====================================================================================
```

## Model Interpretation

### Coefficients
| Variable | Coefficient | Interpretation |
|----------|-------------|----------------|
| const | -2.17 | Baseline log-odds when all predictors are 0 |
| time_on_page | 0.0002 | Small positive effect (not significant) |
| session_duration | -0.0011 | Small negative effect (not significant) |
| bounce_rate | 0.2812 | Moderate positive effect (not significant) |
| group_encoded | 0.6396 | Strong positive effect (significant) |

### Model Fit Statistics
| Statistic | Value | Interpretation |
|-----------|-------|----------------|
| Pseudo R-squared | 0.0155 | Low explanatory power |
| LLR p-value | < 0.001 | Overall model is significant |
| Log-Likelihood | -751.35 | Model fit metric |

## Error Handling

### Perfect Separation Error

When a predictor perfectly separates the outcome:

```
PerfectSeparationError: Perfect separation detected, results not available
```

**Cause**: One or more predictors perfectly predict the outcome (e.g., all group A users have 0 conversion, all group B users have 1 conversion).

**Handling**:
- The AI detects the error and skips the regression
- Provides explanation of why it occurred
- Continues with other analyses (e.g., visualization)

**Alternatives**:
- Firth logistic regression (penalized likelihood)
- Remove the separating variable
- Combine categories
- Use regularization

## Types of Regression Available

1. **Logistic Regression**: For binary outcomes
2. **Linear Regression**: For continuous outcomes
3. **Poisson Regression**: For count data
4. **Multinomial Logistic**: For categorical outcomes (>2 categories)

## Capabilities

1. **Variable Encoding**: Automatically encodes categorical variables
2. **Intercept Handling**: Adds intercept term automatically
3. **Model Diagnostics**: Provides comprehensive model summary
4. **Error Detection**: Handles common regression errors
5. **Interpretation**: Provides interpretation of coefficients

## Best Practices

1. **Assumption Checking**: Verify regression assumptions
2. **Multicollinearity**: Check for highly correlated predictors
3. **Sample Size**: Ensure adequate sample size relative to predictors
4. **Feature Engineering**: Consider transformations, interactions
5. **Model Validation**: Use cross-validation when possible

## Applications

1. **Conversion Prediction**: Predict likelihood of conversion
2. **Customer Scoring**: Score customers by propensity
3. **Risk Assessment**: Assess risk of adverse events
4. **Price Optimization**: Model price-demand relationships
5. **Churn Prediction**: Predict customer churn

## Test Results

### Successful Execution
- Logistic regression model fitted successfully on dummy data (2000 observations)
- Model converged with appropriate coefficients
- Comprehensive summary generated

### Error Handling Test
- Perfect separation error correctly detected on test data
- Error handled gracefully with explanation
- Analysis continued without regression results

## Limitations

1. **Perfect Separation**: Cannot handle perfectly separating predictors
2. **Small Samples**: Requires adequate sample size
3. **Assumptions**: Relies on statistical assumptions
4. **Complexity**: Limited to basic regression models (no advanced techniques)
5. **Model Selection**: Does not automatically select best model