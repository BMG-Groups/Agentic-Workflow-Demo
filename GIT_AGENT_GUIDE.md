# Git Agent — What It Does & How to Use It

## Overview

The Git Agent is an extension to the **WAT Framework** that gives Claude the ability to work with all the git repositories on your computer — the same ones you have open in VS Code. Instead of typing git commands yourself in a terminal, you simply tell Claude what you want in plain English and it handles the rest.

**Example conversations:**
- *"Show me the status of all my repos"*
- *"Commit my changes in git-practice with the message 'add homepage'"*
- *"Create a new branch called feature/login in my Skinny-Assessment project"*

---

## How It Works — The Big Picture

```
You (in Claude)
      |
      | plain English request
      v
  Claude AI
      |
      | calls MCP tools
      v
  WAT Framework MCP Server  (mcp_server.py)
      |
      | imports and calls functions
      v
  Git Agent  (tools/git_agent.py)
      |
      | reads                      | runs
      v                            v
VS Code storage.json          git commands
(finds your repos)            on your computer
```

1. You ask Claude something about your git repos
2. Claude calls one of the 6 git tools exposed by the MCP server
3. The MCP server calls the git agent functions
4. The git agent either reads VS Code's storage file to find repos, or runs a `git` command on your machine
5. The result comes back to Claude, who tells you in plain English

---

## Files Created

| File | Location | Purpose |
|------|----------|---------|
| `git_agent.py` | `tools/git_agent.py` | Core logic — repo discovery + all git operations |
| `mcp_server.py` | `mcp_server.py` | Updated — 6 new MCP tools added here |
| `git_agent.md` | `workflows/git_agent.md` | SOP / reference for the agent |

---

## The 6 MCP Tools (What Claude Can Do)

### 1. `git_list_repos`
**What it does:** Scans VS Code's local storage file and returns a list of every folder you've recently opened — flagging which ones are actual git repositories.

**When to use:** Always call this first. It shows you what's available.

**Example output:**
```
Repositories discovered from VS Code:

   1. C:\Users\wm119\OneDrive\...\Agentic Workflow Demo  [git repo]
   2. C:\Users\wm119\OneDrive\..._BenMare Agent Workflows  [not a git repo]
   3. C:\Users\wm119\git-practice  [git repo]
   ...
```

---

### 2. `git_status`
**What it does:** Shows you the current state of a repository — which files have been changed, added, or deleted, and what branch you're on.

**Input required:** The full path to the repo

**Example output:**
```
Branch: main

?? newfile.js
 M hello.md
```
The symbols mean:
- `??` = untracked (new file git doesn't know about yet)
- `M` = modified
- `A` = staged/added
- `D` = deleted

---

### 3. `git_log`
**What it does:** Shows the recent commit history for a repository — who committed what and when.

**Inputs:** Repo path, and optionally how many commits to show (default: 10)

**Example output:**
```
1496b1b initial comit
a3f92c1 add homepage layout
b81de04 fix: broken link on contact page
```

---

### 4. `git_commit`
**What it does:** Saves your changes permanently to the repository's history. Optionally stages everything first (equivalent to `git add .` + `git commit`).

**Inputs:**
- `repo_path` — the repository to commit in
- `message` — a short description of what changed (e.g. `"fix: update contact form"`)
- `add_all` — set to `True` to automatically stage all changed files before committing

**Example:** *"Commit all my changes in git-practice with the message 'add newfile'"*
→ Claude calls `git_commit` with `add_all=True`

---

### 5. `git_push_pull`
**What it does:** Syncs your local repository with a remote one (like GitHub).
- **Push** — sends your local commits up to GitHub
- **Pull** — downloads the latest commits from GitHub to your machine

**Inputs:**
- `repo_path` — the repository
- `action` — `"push"` or `"pull"`
- `remote` — the remote name (almost always `"origin"`)
- `branch` — branch name (auto-detected if left blank)

> **Note:** If a repository has no remote configured (like `git-practice` currently), this tool will tell you how to add one rather than crashing.

---

### 6. `git_branch`
**What it does:** Manages branches — the parallel lines of work in a git repository.

**Actions:**
| Action | What it does |
|--------|-------------|
| `list` | Show all branches (local and remote) |
| `create` | Create a new branch and switch to it |
| `switch` | Switch to an existing branch |
| `delete` | Delete a branch |

**Example:** *"Create a new branch called feature/login in my Skinny-Assessment project"*

---

## Step-by-Step: Common Tasks

### Task 1: See What Repos You Have
1. Tell Claude: *"List my git repositories"*
2. Claude calls `git_list_repos`
3. You get a numbered list of all your VS Code folders with git status

---

### Task 2: Check What You've Changed
1. Tell Claude: *"What's the git status of my git-practice repo?"*
2. Claude calls `git_status` with your repo path
3. You see which files are modified and what branch you're on

---

### Task 3: Save Your Work (Commit)
1. Tell Claude: *"Commit all my changes in git-practice with the message 'update hello page'"*
2. Claude calls `git_commit` with `add_all=True` and your message
3. Your changes are saved to git history

---

### Task 4: Upload to GitHub (Push)
> Prerequisite: You need a remote configured. See "Setting Up a Remote" below.

1. Tell Claude: *"Push my git-practice repo to GitHub"*
2. Claude calls `git_push_pull` with `action="push"`
3. Your commits appear on GitHub

---

### Task 5: Work on a New Feature (Branch)
1. Tell Claude: *"Create a new branch called feature/contact-form in git-practice"*
2. Claude calls `git_branch` with `action="create"` and `name="feature/contact-form"`
3. You're now on a new branch — your main branch stays untouched

---

### Task 6: Get the Latest Changes (Pull)
1. Tell Claude: *"Pull the latest changes for my Skinny-Assessment repo"*
2. Claude calls `git_push_pull` with `action="pull"`
3. Any new commits from the remote are merged into your local copy

---

## Setting Up a Remote (Connecting to GitHub)

Your `git-practice` repo currently has no remote — it only exists on your computer. To connect it to GitHub:

### Step 1: Create a repo on GitHub
1. Go to [github.com](https://github.com) and sign in
2. Click **New repository**
3. Name it (e.g. `git-practice`), leave it empty (no README), click **Create**
4. Copy the URL shown (e.g. `https://github.com/BMG-Groups/git-practice.git`)

### Step 2: Add the remote locally
Open a terminal and run:
```bash
git -C "C:\Users\wm119\git-practice" remote add origin https://github.com/BMG-Groups/git-practice.git
```

### Step 3: Push for the first time
```bash
git -C "C:\Users\wm119\git-practice" push -u origin main
```

After this, you can tell Claude *"push my git-practice repo"* and it will work.

---

## How Repo Discovery Works

The agent reads this file on your computer:
```
C:\Users\wm119\AppData\Roaming\Code\User\globalStorage\storage.json
```

VS Code automatically maintains this file — every time you open a folder in VS Code, it gets added. The agent reads the `profileAssociations.workspaces` section, decodes the file URIs (e.g. `file:///c%3A/Users/...` → `C:\Users\...`), and checks each path for a `.git` folder.

**Currently discovered repos on your machine:**
1. `Agentic Workflow Demo` — git repo (the WAT Framework itself)
2. `_BenMare Agent Workflows II` — git repo
3. `Skinny-Assessment` — git repo
4. `git-practice` — git repo (your learning repo)

---

## Activating / Restarting the Agent

The git tools are part of the WAT Framework MCP server. To activate them after this installation:

1. In VS Code, open the Command Palette (`Ctrl+Shift+P`)
2. Run **Claude: Restart MCP Servers** (or reload the window)
3. The next time you ask Claude a git question, the new tools will be available

You can verify they loaded by asking Claude: *"What MCP tools do you have available?"*

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `git_list_repos` returns empty | VS Code storage.json not found. Pass repo path directly to any tool. |
| "git executable not found" | Install git from [git-scm.com](https://git-scm.com) and restart your terminal |
| "No remotes configured" | See "Setting Up a Remote" section above |
| Merge conflict on pull | Resolve conflicts manually in VS Code, then commit |
| MCP tools not showing | Restart MCP server (reload VS Code window) |

---

*Built for Bill — WAT Framework Git Agent v1.0 — 2026-03-13*
