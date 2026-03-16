# Web Scraping Workflow

## Objective
Extract structured data from websites and save to Google Sheets for analysis.

## Required Inputs
- Target URL
- CSS selectors or XPath for data extraction
- Google Sheets ID for output
- Sheet range (e.g., 'Sheet1!A1')

## Tools Used
- `tools/scrape_single_site.py` - Fetches and parses HTML (to be created)
- `tools/google/write_to_sheets.py` - Writes data to Google Sheets

## Process

### Step 1: Scrape Website
**Action**: Extract data from target URL

**Tool**: `python tools/scrape_single_site.py --url <URL> --output .tmp/scraped_data.json`

**Expected Output**: JSON file in .tmp/ with extracted data

**Validation**: Check that .tmp/scraped_data.json exists and contains expected fields

### Step 2: Transform Data (if needed)
**Action**: Convert JSON to format suitable for Sheets

**Tool**: `python tools/data/json_to_csv.py --input .tmp/scraped_data.json --output .tmp/data.csv`

**Expected Output**: CSV file ready for Sheets import

**Validation**: Verify CSV has correct columns and row count

### Step 3: Write to Google Sheets
**Action**: Upload processed data to Sheets

**Tool**: `python tools/google/write_to_sheets.py --spreadsheet-id <ID> --range 'Sheet1!A1' --data <CSV>`

**Expected Output**: Data visible in Google Sheets

**Validation**: Open Sheets URL and verify data appears correctly

## Expected Outputs
- Google Sheets with scraped data
- Temporary files in .tmp/ (can be deleted after successful upload)

## Edge Cases

### Case 1: Website Blocks Scraping
**Problem**: 403 Forbidden or CAPTCHA

**Solution**:
- Add User-Agent header from .env (USER_AGENT variable)
- Implement rate limiting (sleep between requests)
- Consider using Selenium for JavaScript-heavy sites

**Prevention**: Respect robots.txt, add delays between requests

### Case 2: Data Structure Changes
**Problem**: CSS selectors no longer match

**Solution**:
- Inspect page source to find new selectors
- Update tool with new selectors
- Consider making selectors configurable via arguments

**Prevention**: Build robust selectors that don't rely on fragile classes

### Case 3: Rate Limiting
**Problem**: Too many requests in short time

**Solution**: Implement exponential backoff in scraping tool

**Prevention**: Add configurable delay between requests (e.g., --delay 2 for 2 second delay)

### Case 4: Malformed HTML
**Problem**: BeautifulSoup fails to parse page

**Solution**: Try different parsers (lxml, html5lib)

**Prevention**: Use BeautifulSoup's built-in error recovery

## Learnings
- BeautifulSoup handles malformed HTML better than lxml in most cases
- Always check robots.txt before scraping
- Rate limits vary by site - start with 1-2 second delays
- JavaScript-heavy sites require Selenium, which is slower but more reliable

**Updated**: 2026-02-15
**Version**: 1.0

## Notes
This workflow template assumes you'll create the scraping tool. The framework is set up - just build the specific scraper for your use case following the pattern in `tools/example_tool.py`.
