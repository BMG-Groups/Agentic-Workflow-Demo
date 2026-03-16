# Monitor Gmail — Diane DeVito

## Objective
Poll Gmail every 15 minutes for emails from Diane DeVito (diane@RogerGimbel.com) and append a row to a Google Sheet log for each one found.

## Required Inputs
- **Gmail account**: OAuth2 credentials connected in n8n (must have access to the monitored inbox)
- **Google Sheets account**: OAuth2 credentials connected in n8n
- **Spreadsheet ID**: The Google Sheet to log emails into (see Setup below)
- **Sheet tab name**: `Diane Emails` (must match exactly)

## Setup (one-time)

### 1. Create the Google Sheet
1. Create a new Google Sheet
2. Rename the first tab to `Diane Emails`
3. Add this header row in row 1:

   | A | B | C | D | E | F |
   |---|---|---|---|---|---|
   | Date Logged | Date Received | From Name | From Email | Subject | Body Preview |

4. Copy the Spreadsheet ID from the URL:
   `https://docs.google.com/spreadsheets/d/**YOUR_ID_HERE**/edit`

### 2. Configure n8n credentials
- **Gmail**: Credentials → New → Gmail OAuth2 → authenticate with the monitored account
- **Google Sheets**: Credentials → New → Google Sheets OAuth2 → authenticate

### 3. Import and configure the workflow
1. In n8n: Workflows → Import → select `workflows/n8n/monitor_gmail_diane.json`
2. Open the `Google Sheets: Append Email Row` node
3. Replace `YOUR_SPREADSHEET_ID` with the actual Spreadsheet ID from step 1
4. Connect credentials to both the Gmail Trigger and Google Sheets nodes
5. Toggle the workflow to **Active**

## Tools Used
- `n8n-nodes-base.gmailTrigger` — polls Gmail API on a schedule with search filter
- `n8n-nodes-base.set` — extracts and formats fields from raw email data
- `n8n-nodes-base.googleSheets` — appends a row to the log sheet

## Process

### Step 1: Gmail Trigger: Watch Diane
**Action**: Poll Gmail every 15 minutes using the search query:
```
from:diane@rogergimbel.com OR from:"Diane DeVito"
```
**Expected Output**: One item per matching email, containing raw Gmail fields (`subject`, `date`, `from`, `text`, `id`, `threadId`)
**Validation**: In n8n "Test Workflow" mode, send a test email from diane@rogergimbel.com — the trigger should return it within the test window

### Step 2: UTIL: Extract Email Fields
**Action**: Set node maps raw Gmail data to clean, sheet-ready fields:

| Field | Source Expression |
|---|---|
| Date Logged | `{{ $now.toISO() }}` |
| Date Received | `{{ $json.date }}` |
| From Name | `{{ $json.from.value[0].name }}` |
| From Email | `{{ $json.from.value[0].address }}` |
| Subject | `{{ $json.subject }}` |
| Body Preview | `{{ ($json.text \|\| '').substring(0, 500) }}` |

**Expected Output**: Single item with all 6 fields populated as strings
**Validation**: Click the node after a test run — inspect Output tab to confirm all fields have values

### Step 3: Google Sheets: Append Email Row
**Action**: Append one row to the `Diane Emails` tab using `autoMapInputData` — field names from Step 2 map to column headers automatically
**Expected Output**: New row visible in the sheet within seconds
**Validation**: Open the Google Sheet and confirm the row was added with correct data in all 6 columns

## Expected Outputs
- **Google Sheet (`Diane Emails` tab)**: One row per email from Diane, with 6 fields populated
- **n8n Execution log** (`/executions`): Shows each successful run; inspect for errors

## Edge Cases

### No emails found in a poll cycle
**Problem**: Gmail Trigger returns nothing if no matching emails arrived since the last check
**Solution**: Normal behavior — n8n does not execute downstream nodes when the trigger has no results
**Prevention**: No action needed; this is expected for quiet periods

### Email body is `null` or empty (HTML-only email)
**Problem**: `$json.text` is undefined for HTML-only emails, causing Body Preview to be blank
**Solution**: The expression `($json.text || '').substring(0, 500)` safely falls back to empty string
**Prevention**: If HTML body is needed, switch to `$json.html` and use a Code node to strip tags

### From field has unexpected structure
**Problem**: `$json.from.value[0].name` throws if the sender has no display name
**Solution**: Add fallback: `{{ $json.from.value[0].name || $json.from.value[0].address }}`
**Prevention**: Use a Code node for more robust parsing if Diane's email client ever changes

### Duplicate emails logged
**Problem**: n8n Cloud restart or workflow re-activation may re-process recently seen emails
**Solution**: The Gmail Trigger tracks processed message IDs internally — duplicates are rare but not impossible
**Prevention**: Add a Google Sheets lookup node to check for existing Message ID before appending (future enhancement)

### Google Sheets API quota exceeded
**Problem**: 429 error if too many appends are made in a short window
**Solution**: Add a Wait node before the Sheets append if processing bulk emails; Sheets API limit is 300 writes/min
**Prevention**: At 15-minute polling intervals, this should never be an issue for a single sender

## Error Handling
Per agency conventions, connect this workflow to an Error Trigger workflow that sends a notification on failure:
1. Create a companion workflow with the Error Trigger node
2. Add a Slack or email node to alert on errors
3. Connect via: Settings → Error Workflow → select the error workflow

## Learnings
*(Document issues and fixes discovered in production here)*

**Created**: 2026-02-24
**Version**: 1.0
