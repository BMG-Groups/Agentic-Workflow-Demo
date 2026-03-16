# Example Workflow - [Workflow Name]

## Objective
[Clear statement of what this workflow accomplishes]

## Required Inputs
- Input 1: [Description, format, where to get it]
- Input 2: [Description, format, where to get it]

## Tools Used
- `tools/example_tool.py` - [What it does]
- `tools/another_tool.py` - [What it does]

## Process

### Step 1: [Step Name]
**Action**: [What to do]

**Tool**: `python tools/example_tool.py --arg value`

**Expected Output**: [What should happen]

**Validation**: [How to verify success]

### Step 2: [Step Name]
**Action**: [What to do]

**Tool**: `python tools/another_tool.py --arg value`

**Expected Output**: [What should happen]

**Validation**: [How to verify success]

## Expected Outputs
- Deliverable 1: [Where it goes, format, who accesses it]
- Deliverable 2: [Where it goes, format, who accesses it]

## Edge Cases

### Case 1: [Scenario]
**Problem**: [What goes wrong]

**Solution**: [How to handle it]

**Prevention**: [How to avoid it]

### Case 2: Rate Limiting
**Problem**: API returns 429 Too Many Requests

**Solution**: Wait [X] minutes or use batch endpoint

**Prevention**: Implement exponential backoff in tool

## Learnings
[Document improvements discovered through use]

**Updated**: 2026-02-15
**Version**: 1.0
