# Git Agent Enhancement Plan — GitHub Sync Feature

## What We're Adding

The git agent already has 6 working tools (list repos, status, log, commit, push/pull, branch). This plan adds **3 new tools** to make transferring your VS Code files to GitHub faster and easier.

---

## The 3 New Tools

### Tool 1: `git_diff`
**What it does:** Shows you the exact line-by-line changes in a file *before* you commit — so you can review what's about to go to GitHub.

**Example:**
> *"Show me what changed in git-practice"*
> → Claude displays every added/removed line

---

### Tool 2: `git_check_all`
**What it does:** Scans **all** your VS Code repositories at once and tells you which ones have pending changes. Great as a morning check.

**Example output:**
```
Repository scan:

  [CHANGES PENDING]  git-practice  (branch: main)
               ?? newfile.js
               M  hello.md

  [clean]  Skinny-Assessment  (branch: main)
  [clean]  Agentic Workflow Demo  (branch: main)
```

---

### Tool 3: `git_smart_sync` ⭐ (The Main Addition)
**What it does:** A single command that does the full GitHub transfer in one shot:

```
1. Detect what changed
2. Stage everything  (git add .)
3. Commit with your message
4. Push to GitHub
```

**Example:**
> *"Push my latest changes in git-practice with the message 'update homepage'"*
> → Done in one step, no manual git commands needed

**If no GitHub remote is configured** (like `git-practice` currently), it still commits your changes successfully and then explains exactly how to connect it to GitHub — it won't crash.

---

## How the Workflow Will Look

```
You:    "Which of my repos have pending changes?"
Claude: calls git_check_all → shows you the scan

You:    "Show me what changed in git-practice"
Claude: calls git_diff → shows line-by-line changes

You:    "Push those changes to GitHub with the message 'add new homepage'"
Claude: calls git_smart_sync → stages + commits + pushes → done
```

---

## Files to Modify

| File | What Changes |
|------|-------------|
| `tools/git_agent.py` | Add 2 new functions: `check_all_repos()` and `git_smart_sync()` |
| `mcp_server.py` | Add 3 new MCP tool wrappers (git_diff, git_check_all, git_smart_sync) |
| `workflows/git_agent.md` | Add a "Push to GitHub" step-by-step SOP section |
| `GIT_AGENT_GUIDE.md` | Document the 3 new tools in the tools table |

All files are in:
`C:\Users\wm119\OneDrive\Public\OneNote Documents\Agentic Workflow Demo\`

---

## Code to Add — `tools/git_agent.py`

Add these two functions before the CLI entry point at the bottom of the file:

```python
def check_all_repos() -> str:
    """Check every VS Code repo for uncommitted changes."""
    repos = discover_repos()
    if not repos:
        return "No repositories found."
    lines = []
    for r in repos:
        if not r["is_git"]:
            continue
        status = _run_git(r["path"], ["status", "--short"])
        branch = _current_branch(r["path"])
        has_changes = bool(status["stdout"].strip())
        label = "CHANGES PENDING" if has_changes else "clean"
        lines.append(f"  [{label}]  {r['name']}  (branch: {branch})")
        if has_changes:
            for line in status["stdout"].strip().splitlines():
                lines.append(f"             {line}")
    return "Repository scan:\n\n" + "\n".join(lines)


def git_smart_sync(repo_path: str, commit_message: str,
                   remote: str = "origin", branch: str = "") -> str:
    """One-shot GitHub sync: stage all changes, commit, and push."""
    log = []

    # Step 1 — Check for changes
    status = _run_git(repo_path, ["status", "--short"])
    if not status["stdout"].strip():
        return "Nothing to sync — working tree is clean."
    log.append(f"Changes detected:\n{status['stdout'].rstrip()}")

    # Step 2 — Stage all
    add_result = _run_git(repo_path, ["add", "."])
    if add_result["returncode"] != 0:
        return f"Stage failed:\n{add_result['stderr']}"
    log.append("Staged all changes.")

    # Step 3 — Commit
    commit_result = _run_git(repo_path, ["commit", "-m", commit_message])
    if commit_result["returncode"] != 0:
        return f"Commit failed:\n{commit_result['stderr']}"
    log.append(f"Committed: \"{commit_message}\"")

    # Step 4 — Push
    if not _has_remotes(repo_path):
        log.append(
            "No remote configured — skipping push.\n"
            "To connect to GitHub: git remote add origin <your-github-url>"
        )
        return "\n".join(log)

    push_branch = branch or _current_branch(repo_path)
    push_result = _run_git(repo_path, ["push", remote, push_branch])
    if push_result["returncode"] != 0:
        log.append(f"Push failed:\n{push_result['stderr']}")
    else:
        log.append(f"Pushed to {remote}/{push_branch} on GitHub.")

    return "\n".join(log)
```

---

## Code to Add — `mcp_server.py`

Add these 3 tool wrappers after the existing `git_log` tool (around line 258):

```python
@mcp.tool()
def git_diff(repo_path: str, staged: bool = False) -> str:
    """Show line-by-line file changes. Use staged=True to see what's staged for commit."""
    return git_agent.git_diff(repo_path, staged=staged)

@mcp.tool()
def git_check_all() -> str:
    """Scan all VS Code repositories and report which ones have uncommitted changes."""
    return git_agent.check_all_repos()

@mcp.tool()
def git_smart_sync(repo_path: str, commit_message: str,
                   remote: str = "origin", branch: str = "") -> str:
    """
    One-shot GitHub sync: stage all changes, commit with message, push to GitHub.
    Use git_check_all first to identify repos with pending changes.
    """
    return git_agent.git_smart_sync(
        repo_path, commit_message, remote=remote, branch=branch
    )
```

---

## Section to Append — `workflows/git_agent.md`

```markdown
## Push-to-GitHub Workflow

**When to use:** You've been working in VS Code and want to save your changes to GitHub.

### Steps

1. **Scan all repos** — `git_check_all`
   See every repo and which ones have pending changes at a glance.

2. **Preview changes** (optional) — `git_diff(repo_path)`
   Review exactly what lines changed before committing.

3. **Sync to GitHub** — `git_smart_sync(repo_path, "your message")`
   Stages everything, commits, and pushes in one call.

### Prerequisites
- The repo must have a GitHub remote configured.
- If no remote: smart_sync will commit locally and explain how to add one.

### Example
User: "Push my latest changes in git-practice to GitHub"
→ git_check_all → git_smart_sync("C:\Users\wm119\git-practice", "update hello page")
```

---

## Verification Steps

After the code is added:

1. **Diff test**: *"Show me what changed in git-practice"*
   → Should show line-by-line changes for `newfile.js` and `hello.md`

2. **Check-all test**: *"Which of my repos have pending changes?"*
   → Should list all 4 repos with CLEAN or CHANGES PENDING status

3. **Smart sync test**: *"Push my changes in git-practice with message 'add newfile'"*
   → Should stage + commit + attempt push (graceful no-remote message expected)

4. **Restart MCP** after changes: `Ctrl+Shift+P` → "Claude: Restart MCP Servers"

---

## Design Notes

- The 6 existing tools are **not changed** — this is purely additive
- `git_smart_sync` handles the no-remote case gracefully (commits locally, skips push, gives instructions)
- `check_all_repos` only scans actual git folders — skips VS Code workspaces that aren't repos
- `git_diff` is read-only and safe to call any time

---

*Enhancement plan for WAT Framework Git Agent — 2026-03-13*
