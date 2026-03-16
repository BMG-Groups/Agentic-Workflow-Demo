# WAT Framework - Workflows, Agents, Tools

A reliable agentic architecture that separates probabilistic AI reasoning from deterministic code execution.

## Architecture Overview

The WAT framework consists of three layers:

1. **Workflows** (The Instructions) - Markdown SOPs in [workflows/](workflows/)
2. **Agents** (The Decision-Maker) - AI coordination and orchestration
3. **Tools** (The Execution) - Python scripts in [tools/](tools/)

## Why This Architecture?

When AI handles every step directly, accuracy compounds negatively. At 90% accuracy per step, five steps = 59% success rate. WAT solves this by:
- AI handles reasoning and coordination (what it's good at)
- Deterministic scripts handle execution (what computers are good at)
- Workflows capture and evolve best practices

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
copy .env.template .env
# Edit .env with your API keys
```

### 2. Google Workspace Setup (if using Google APIs)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable required APIs (Sheets, Slides, Drive, etc.)
4. Create OAuth 2.0 credentials (Desktop application)
5. Download credentials.json to project root
6. First run will prompt for authorization and create token.json

### 3. Create Your First Workflow

See [workflows/example_workflow.md](workflows/example_workflow.md) for template and structure.

## Project Structure

```
.
├── CLAUDE.md           # Agent instructions (framework philosophy)
├── README.md           # This file
├── .env                # Environment variables (not committed)
├── .env.template       # Template for required variables
├── requirements.txt    # Python dependencies
├── workflows/          # Markdown SOPs defining processes
├── tools/              # Python scripts for execution
│   ├── api/           # API integrations
│   ├── data/          # Data transformations
│   ├── google/        # Google Workspace tools
│   └── utils/         # Shared utilities
└── .tmp/              # Temporary files (not committed)
```

## Core Principles

1. **Deliverables go to cloud services** - Google Sheets, Slides, etc.
2. **Local files are for processing only** - Everything in `.tmp/` is disposable
3. **Workflows evolve** - Update them as you learn better approaches
4. **Tools are deterministic** - They do one thing reliably
5. **Self-improvement loop** - Every failure strengthens the system

## Creating New Tools

Tools should:
- Do one thing well
- Accept inputs via command-line arguments or environment variables
- Return clear success/failure status codes
- Log operations for debugging
- Be idempotent when possible

Template:
```python
#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def main():
    # Your tool logic here
    pass

if __name__ == "__main__":
    main()
```

## Creating New Workflows

Workflows should include:
- **Objective**: What this workflow accomplishes
- **Required Inputs**: What information/files are needed
- **Tools Used**: Which scripts in `tools/` are called
- **Expected Outputs**: What gets delivered and where
- **Edge Cases**: Known issues and how to handle them

See [workflows/example_workflow.md](workflows/example_workflow.md) for full template.

## Available Tools

### Google Workspace Tools
- [tools/google/write_to_sheets.py](tools/google/write_to_sheets.py) - Write data to Google Sheets
- [tools/google/read_from_sheets.py](tools/google/read_from_sheets.py) - Read data from Google Sheets

### Utilities
- [tools/utils/common.py](tools/utils/common.py) - Shared utility functions

### Examples
- [tools/example_tool.py](tools/example_tool.py) - Reference implementation showing best practices

## Available Workflows

- [workflows/example_workflow.md](workflows/example_workflow.md) - Template for creating new workflows
- [workflows/scrape_website.md](workflows/scrape_website.md) - Web scraping to Google Sheets workflow
- [workflows/analyze_data.md](workflows/analyze_data.md) - Data analysis to Google Slides workflow

## Contributing

When improving the framework:
1. Test the change thoroughly
2. Update relevant workflows with new learnings
3. Document any new dependencies
4. Commit with clear messages about what improved

## Troubleshooting

### Common Issues

**Import errors**: Ensure virtual environment is activated and dependencies installed
```bash
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

**Google API errors**: Check credentials.json exists and token.json has valid scopes
- Delete token.json to re-authenticate if scopes changed
- Ensure required APIs are enabled in Google Cloud Console

**Rate limiting**: See workflow documentation for API-specific rate limits
- Most APIs require delays between requests
- Implement exponential backoff in tools

**Module not found**: Ensure __init__.py files exist in package directories
```bash
# Check package structure
ls tools/__init__.py tools/google/__init__.py
```

## The Self-Improvement Loop

The framework gets better over time:

1. **Identify what broke** - Read error messages and traces carefully
2. **Fix the tool** - Update Python scripts with better error handling or logic
3. **Verify the fix works** - Test thoroughly before committing
4. **Update the workflow** - Document learnings and new approaches
5. **Move on with a more robust system** - Next time will be smoother

This loop transforms failures into permanent improvements.

## License

[Your License Here]
