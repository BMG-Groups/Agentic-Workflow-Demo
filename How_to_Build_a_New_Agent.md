# How to Build a New Agent Using the WAT Framework
**Created:** 2026-03-16
**For:** BMG-Groups AI Agency

---

## Before You Start — What You Have

Your `Agentic Workflow Demo` folder is your **lab**. It has:
- A fully working **Git Agent** that tracks and syncs all your repos
- **Google Sheets** read/write tools
- A running **MCP server** that connects everything to Claude

When you build a new agent, you build it in a **brand new isolated folder** — not inside this lab.

---

## Phase 1 — Create Your New Project

### Step 1 — Create a new folder
1. Open **File Explorer** (Windows key + E)
2. Go to: `C:\Users\wm119\OneDrive\Public\OneNote Documents\`
3. Right-click → **New Folder**
4. Name it after your agent (no spaces — use dashes). Example: `BMG-Lead-Agent`

---

### Step 2 — Open ONLY that folder in VS Code
1. Open VS Code
2. Click **File → Open Folder**
3. Select your new folder
4. Click **Select Folder**

> ⚠️ This is critical. VS Code must open the **new folder directly** — not a parent folder. This keeps Claude isolated to only that project.

---

### Step 3 — Open Claude Code in that folder
In the VS Code terminal (Ctrl + `), type:
```
claude
```
Claude will now be working exclusively inside your new project folder.

---

## Phase 2 — Initialize Git and GitHub

### Step 4 — Initialize Git
In the terminal:
```
git init
git branch -M main
```

---

### Step 5 — Create the GitHub repo
Decide which account owns this agent:
- **BMG-Groups** account → use for agency/client work
- **wm1199** account → use for personal/Gimbel work

Then run (replace `BMG-Lead-Agent` with your project name):
```
gh repo create BMG-Groups/BMG-Lead-Agent --public
git remote add origin https://github.com/BMG-Groups/BMG-Lead-Agent.git
```

> Make sure `gh` is logged in as the right account first:
> ```
> gh auth status
> ```
> It should say `Logged in as BMG-Groups`. If not, run `gh auth login`.

---

### Step 6 — Protect your secrets
```
echo ".env" > .gitignore
echo ".tmp/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "token.json" >> .gitignore
echo "credentials.json" >> .gitignore
```

Then create your `.env` file:
```
echo "" > .env
```
Open `.env` and add your API keys. This file **never** goes to GitHub.

---

### Step 7 — Make your first commit
```
git add .gitignore
git commit -m "chore: initialize project"
git push -u origin main
```

---

## Phase 3 — Connect the Git Agent

The Git Agent in `Agentic Workflow Demo` **automatically discovers** your new repo — no extra setup needed. As long as:
1. Your new folder is a git repo (`git init` was run)
2. You've opened it in VS Code at least once

The next time you ask Claude to run `git_check_all` in the Agentic Workflow Demo context, your new repo will appear in the list automatically.

---

## Phase 4 — Set Up Your New Agent's Structure

### Step 8 — Create the standard folder structure
In the terminal inside your new project:
```
mkdir tools
mkdir workflows
mkdir tests
mkdir .tmp
```

---

### Step 9 — Create a CLAUDE.md file
This tells Claude what your project does and how to behave.
Ask Claude:
> *"Please write a CLAUDE.md for my new agent project. The agent will [describe what it does]."*

Claude will write it for you. This file is the brain of your project.

---

### Step 10 — Create a requirements.txt
Start lean — only add what you need. A good starting point:
```
python-dotenv>=1.0.0
requests>=2.31.0
anthropic>=0.40.0
pytest>=7.4.0
mcp[cli]>=1.0.0
```

---

### Step 11 — Install dependencies
```
uv pip install -r requirements.txt
```

---

## Phase 5 — Build Your Agent

### Step 12 — Create your first tool
Copy the pattern from the example tool:
```
copy "C:\Users\wm119\OneDrive\Public\OneNote Documents\Agentic Workflow Demo\tools\example_tool.py" tools\my_first_tool.py
```
Then edit it to do what your agent needs.

**Every tool should:**
- Use `argparse` for arguments
- Use `logging` (not `print`) for output
- Load `.env` with `python-dotenv`
- Return exit code `0` on success, `1` on failure

---

### Step 13 — Write a workflow SOP
Create a markdown file in `workflows/` that describes:
- What the agent does step by step
- What inputs it needs
- What outputs it produces
- What to do if something goes wrong

Example: `workflows/lead_generation.md`

---

### Step 14 — Test your tool
```
python tools/my_first_tool.py --help
python tools/my_first_tool.py --input "test data"
```

---

## Phase 6 — Sync with the Git Agent

### Step 15 — Switch back to the Agentic Workflow Demo context
1. In VS Code, click **File → Open Recent** and select `Agentic Workflow Demo`
2. Open Claude Code: type `claude` in the terminal

### Step 16 — Run the Git Agent to sync your new repo
Tell Claude:
> *"Run git_check_all and sync my new BMG-Lead-Agent repo"*

Claude will:
1. Detect your new repo
2. Show you what's uncommitted
3. Commit and push with a meaningful message
4. Log it to the Google Sheets report

---

## Quick Reference — Key Commands

| Task | Command |
|------|---------|
| Check git login | `gh auth status` |
| Switch to BMG-Groups | `gh auth login` (use william@bennmar.com) |
| Switch to wm1199 | `gh auth login` (use william@gimbelsignagegroup.com) |
| Check all repos | Ask Claude: *"run git_check_all"* |
| Sync a repo | Ask Claude: *"smart sync [repo name]"* |
| Run git report | Ask Claude: *"run a git report to Google Sheets"* |

---

## Quick Reference — Account Guide

| Account | Email | Use for |
|---------|-------|---------|
| `BMG-Groups` | william@bennmar.com | Agency work, client agents, BMG projects |
| `wm1199` | william@gimbelsignagegroup.com | Gimbel/personal projects |

---

## Checklist — New Agent Setup

- [ ] New folder created (no spaces in name)
- [ ] Folder opened directly in VS Code
- [ ] `git init` + `git branch -M main` run
- [ ] GitHub repo created under correct account
- [ ] Remote URL connected
- [ ] `.gitignore` created (protects `.env`)
- [ ] `.env` created with API keys
- [ ] First commit pushed to GitHub
- [ ] `CLAUDE.md` written
- [ ] `requirements.txt` created (lean)
- [ ] Folder structure created (`tools/`, `workflows/`, `tests/`)
- [ ] First tool built and tested
- [ ] Git Agent synced from Agentic Workflow Demo context

---

*Generated by Claude Code — 2026-03-16*
*WAT Framework — Agentic Workflow Demo*
