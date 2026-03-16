# Data Analysis Workflow

## Objective
Fetch data from Google Sheets, perform analysis, and generate insights in a new Slides presentation.

## Required Inputs
- Google Sheets ID with source data
- Analysis type (summary statistics, trends, correlations, etc.)
- Output Google Slides ID (or create new presentation)

## Tools Used
- `tools/google/read_from_sheets.py` - Fetches data from Sheets
- `tools/data/analyze.py` - Performs statistical analysis (to be created)
- `tools/google/create_slides.py` - Generates presentation (to be created)

## Process

### Step 1: Fetch Data
**Action**: Download data from Google Sheets

**Tool**: `python tools/google/read_from_sheets.py --spreadsheet-id <ID> --range 'Sheet1!A:Z' --output .tmp/data.csv`

**Expected Output**: CSV file in .tmp/

**Validation**: Verify CSV has expected columns and row count using `head .tmp/data.csv`

### Step 2: Analyze Data
**Action**: Generate statistics and insights

**Tool**: `python tools/data/analyze.py --input .tmp/data.csv --output .tmp/analysis.json`

**Expected Output**: JSON with analysis results, charts saved to .tmp/

**Validation**: Check that analysis.json contains expected metrics and chart files exist

### Step 3: Create Presentation
**Action**: Build Google Slides with insights

**Tool**: `python tools/google/create_slides.py --analysis .tmp/analysis.json --charts .tmp/ --output <SLIDES_ID>`

**Expected Output**: Google Slides with charts and insights

**Validation**: Open Slides URL and verify all charts and text appear correctly

## Expected Outputs
- Google Slides presentation with analysis results
- Charts and visualizations embedded in slides
- Temporary analysis files in .tmp/ (can be deleted after presentation is created)

## Edge Cases

### Case 1: Missing Data
**Problem**: Source Sheets has empty cells or columns

**Solution**: Handle NaN values in analysis tool
- Skip rows with missing critical data
- Fill with mean/median for numerical columns
- Document assumptions in analysis output

**Prevention**: Validate data quality before analysis, add data validation rules in source Sheet

### Case 2: Large Datasets
**Problem**: Memory issues with >100k rows

**Solution**:
- Use pandas chunking: `pd.read_csv('file.csv', chunksize=10000)`
- Sample data if full analysis isn't required
- Consider aggregating data before analysis

**Prevention**: Add data size check before loading, warn user if dataset is very large

### Case 3: API Quota Exceeded
**Problem**: Google API quota limits reached

**Solution**:
- Wait for quota reset (usually daily at midnight Pacific Time)
- Request quota increase in Google Cloud Console
- Batch operations where possible

**Prevention**:
- Cache intermediate results
- Use batch API methods instead of individual calls
- Monitor quota usage in Google Cloud Console

### Case 4: Invalid Data Types
**Problem**: Non-numeric data in columns expected to be numbers

**Solution**:
- Clean data during import: `pd.to_numeric(df['column'], errors='coerce')`
- Log cleaning operations for transparency
- Report data quality issues to user

**Prevention**: Add data type validation in the data collection tool

## Learnings
- Pandas handles CSV files more reliably than manual parsing
- Google Slides API has a 500 requests per 100 seconds limit
- Charts should be generated as PNG files (easier to embed than SVG)
- Always validate data quality before running expensive analyses

**Updated**: 2026-02-15
**Version**: 1.0

## Notes
This workflow template provides the structure. You'll need to build:
- `tools/data/analyze.py` - Your specific analysis logic (pandas, numpy, matplotlib)
- `tools/google/create_slides.py` - Slides generation tool

The Google Sheets reader is already implemented. Follow the pattern in `tools/example_tool.py` for creating the remaining tools.
