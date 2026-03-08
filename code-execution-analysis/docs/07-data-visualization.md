# Data Visualization Feature

## Overview

Gemini Code Execution can create various types of data visualizations using matplotlib and seaborn libraries.

## Implementation

### Basic Plotting (matplotlib)

```python
import matplotlib.pyplot as plt

# Create bar chart
plt.figure(figsize=(8, 6))
plt.bar(['Control A', 'Treatment B'], [rate_control, rate_treatment])
plt.title('Conversion Rate by Group')
plt.xlabel('Group')
plt.ylabel('Conversion Rate')
plt.savefig('output/conversion_rate_by_group.png')
plt.close()
```

### Advanced Plotting (seaborn)

```python
import seaborn as sns
import matplotlib.pyplot as plt

# Set style
sns.set_style("whitegrid")

# Create histogram with KDE
plt.figure(figsize=(10, 7))
sns.histplot(
    data=df, 
    x='time_on_page', 
    hue='group', 
    kde=True, 
    palette='magma', 
    multiple="stack"
)
plt.title('Distribution of Time on Page by Group')
plt.savefig('output/time_on_page_distribution_by_group.png')
plt.close()
```

## Types of Visualizations Created

### 1. Bar Charts
**Purpose**: Compare categorical data

```python
sns.barplot(
    x='group', 
    y='conversion', 
    data=df, 
    errorbar=None, 
    palette='viridis'
)
```

**Use Cases**:
- Conversion rates by group
- Average metrics by category
- Frequency comparison

### 2. Histograms with KDE
**Purpose**: Show distribution of numerical data

```python
sns.histplot(
    data=df, 
    x='time_on_page', 
    hue='group', 
    kde=True
)
```

**Use Cases**:
- Distribution of time metrics
- User engagement patterns
- Outlier detection

### 3. Violin Plots
**Purpose**: Show distribution shape and statistics

```python
sns.violinplot(
    data=df, 
    x='group', 
    y='time_on_page', 
    palette='magma'
)
```

**Use Cases**:
- Distribution comparison between groups
- Probability density visualization
- Multiple distribution comparison

### 4. Correlation Heatmaps
**Purpose**: Visualize correlation matrix

```python
sns.heatmap(
    correlation_matrix, 
    annot=True, 
    cmap='coolwarm', 
    fmt=".2f"
)
```

**Use Cases**:
- Identify variable relationships
- Feature selection
- Multicollinearity detection

### 5. Scatter Plots
**Purpose**: Show relationship between two variables

```python
sns.scatterplot(
    data=df, 
    x='time_on_page', 
    y='session_duration', 
    hue='group', 
    alpha=0.6
)
```

**Use Cases**:
- Variable relationships
- Outlier identification
- Clustering visualization

### 6. Box Plots
**Purpose**: Show distribution statistics

```python
sns.boxplot(
    x='conversion', 
    y='bounce_rate', 
    data=df, 
    palette='pastel'
)
```

**Use Cases**:
- Distribution comparison
- Outlier identification
- Statistical summary visualization

## Generated Visualizations

### From Test Data

1. **conversion_rate_by_group.png** (50,127 bytes)
   - Bar chart showing 0% vs 100% conversion rates
   - Clear visual of treatment effectiveness

2. **time_on_page_distribution_by_group_hist.png** (40,633 bytes)
   - Histogram with KDE overlay
   - Shows distinct distributions for each group

3. **correlation_heatmap.png** (64,035 bytes)
   - Heatmap of correlation matrix
   - Color-coded correlation coefficients

4. **time_on_page_vs_click_count_by_group.png** (50,127 bytes)
   - Scatter plot showing relationship
   - Points colored by group

5. **session_duration_vs_bounce_rate_by_conversion.png** (19,006 bytes)
   - Scatter plot colored by conversion
   - Shows relationship patterns

## Visualization Features

### Styling Options
- **Color Palettes**: viridis, magma, pastel, coolwarm
- **Figure Size**: Customizable dimensions
- **Labels**: Titles, axis labels, legends
- **Annotations**: Correlation coefficients, significance markers

### File Formats
- **PNG**: Default format for plots
- **DPI**: Standard 100-150 DPI
- **Size**: Typically 20-65 KB per plot

### Design Patterns
- Clean, publication-quality styling
- Appropriate color choices for accessibility
- Clear labels and titles
- Professional appearance

## Capabilities

1. **Multiple Plot Types**: Bar, histogram, violin, heatmap, scatter, box
2. **Grouping**: Automatic grouping by categorical variables
3. **Color Coding**: Color by different variables
4. **Statistical Overlay**: KDE curves, error bars
5. **File Output**: Saves to specified directory

## Best Practices

1. **Figure Size**: Use appropriate sizes for readability
2. **Color Choice**: Consider color-blind friendly palettes
3. **Labels**: Always include clear labels and titles
4. **Aspect Ratio**: Maintain appropriate aspect ratios
5. **File Size**: Balance quality with file size

## Limitations

1. **Static Plots**: Only generates static images (no interactivity)
2. **Format**: Limited to PNG (no SVG, PDF support in current implementation)
3. **Complexity**: May struggle with very complex visualizations
4. **Customization**: Limited customization compared to manual coding
5. **File Access**: Generated files are in remote environment

## Applications

1. **Exploratory Analysis**: Understand data distributions
2. **Presentation**: Create figures for reports
3. **Communication**: Visualize findings for stakeholders
4. **Debugging**: Identify data issues
5. **Model Interpretation**: Visualize model results

## Test Results

Successfully generated 5 visualizations:
- All plots created without errors
- Appropriate file sizes (20-65 KB)
- High visual quality
- Correct data representation
- Professional appearance

All visualizations match expected patterns based on the test data characteristics.