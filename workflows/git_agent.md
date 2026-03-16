# Git Agent Workflow

## Objective
Perform git operations across all VS Code repositories using Claude as the operator.
Repositories are discovered automatically from VS Code's recently opened workspaces.

## Required Inputs
- **Repository path**: discovered automatically via `git_list_repos`, or provide an absolute path directly
- **For commits**: a meaningful commit message
- **For push/pull**: a remote must be configured on the repository

## Tools Used
- `git_list_repos` — discovers all repos from VS Code; call this first
- `git_status` — shows working tree status and current branch (always call before write ops)
- `git_log` — shows commit history
- `git_diff` — shows line-by-line changes (staged or unstaged)
- `git_check_all` — scans all repos at once; use as morning check
- `git_commit` — stages and commits changes
- `git_smart_sync` — one-shot: stage + commit + push
- `git_push_pull` — push or pull to/from a remote
- `git_fetch` — fetch from remote without merging (safe preview)
- `git_branch` — lists, creates, switches, or deletes branches
- `git_merge` — merges a branch; auto-detects conflicts
- `git_rebase` — rebases current branch; guardrail requires confirm=True
- `git_conflict_status` — lists conflicted files with resolution steps
- `git_generate_message` — returns diff for Claude to propose a commit message

## Process

### Step 1: Discover Available Repositories
**Action**: Call `git_list_repos` (no arguments needed)

**Expected Output**: Numbered list of paths with `[git repo]` or `[not a git repo]` tags

**Validation**: Confirm your target repository appears in the list; note its full path

---

### Step 2: Check Repository Status
**Action**: Call `git_status` with the full repo path

**Expected Output**: Current branch name and a list of modified/untracked files

**Validation**: Understand what changes exist before taking any action

---

### Step 3: Perform the Desired Operation

#### Commit changes
**Action**: Call `git_commit` with `repo_path`, `message`, and `add_all=True` to stage everything

**Expected Output**: Commit hash and summary line

**Validation**: Follow up with `git_log` to confirm the commit appears

#### Push to GitHub / remote
**Action**: Call `git_push_pull` with `action="push"` (and optionally `remote` and `branch`)

**Expected Output**: Lines showing objects written and branch tracking info

**Validation**: Visit the remote (e.g. GitHub) to confirm the branch is updated

#### Pull latest changes
**Action**: Call `git_push_pull` with `action="pull"`

**Expected Output**: "Already up to date." or a list of merged commits

#### Create a new branch
**Action**: Call `git_branch` with `action="create"` and `name="your-branch-name"`

**Expected Output**: "Switched to a new branch 'your-branch-name'"

---

## Expected Outputs
- `git_list_repos`: numbered table of discovered paths
- `git_status`: branch + short-format file list
- `git_log`: one commit per line (hash + message)
- `git_commit`: confirmation with commit hash
- `git_push_pull`: remote sync result
- `git_branch`: branch listing or operation confirmation

---

## Edge Cases

### No Remotes Configured
**Problem**: `git_push_pull` returns "No remotes configured"

**Solution**: Add a remote in a terminal:
```
git remote add origin https://github.com/your-username/your-repo.git
```
Then retry. This is normal for brand-new local repositories (e.g. git-practice).

**Prevention**: Initialize repos on GitHub first and clone, rather than init locally.

---

### VS Code Storage Not Found
**Problem**: `git_list_repos` returns an empty list

**Solution**: Pass the repo path directly to any tool — they all work with absolute paths:
```
git_status("C:\\Users\\wm119\\my-project")
```
**Prevention**: N/A — VS Code discovery is a convenience, not a requirement.

---

### Merge Conflicts
**Problem**: `git_push_pull` (pull) fails with conflict messages

**Solution**: Claude cannot resolve conflicts interactively. Inform the user to:
1. Open VS Code Source Control panel
2. Resolve each conflicted file manually
3. Stage resolved files and commit

**Prevention**: Pull before making changes; use feature branches.

---

### Windows Paths With Spaces
**Problem**: Path contains spaces (e.g. `Agentic Workflow Demo`)

**Solution**: Always pass the full path as a single quoted string. The tools handle quoting internally — no extra escaping needed from the caller.

---

### Nothing to Commit
**Problem**: `git_commit` returns "nothing to commit"

**Solution**: Check `git_status` first. If the working tree is clean, there is nothing to commit. Use `add_all=True` only when there are actual changes.

---

## Morning Scan Workflow

**When to use:** Start of the day to see what repos have pending changes.

1. **Scan all repos** — `git_check_all` (no arguments)
   Shows CLEAN or CHANGES PENDING for every VS Code repo at a glance.

2. **Preview changes** (optional) — `git_diff(repo_path)`
   Review the exact lines changed before committing.

3. **Sync to GitHub** — `git_smart_sync(repo_path, "your message")`
   Stages everything, commits, and pushes in one call.
   If no GitHub remote is configured, commits locally and explains how to add one.

---

## Commit Without a Message

**When to use:** User says "commit my changes" without specifying a message.

1. Call `git_generate_message(repo_path)` — returns the current diff
2. Read the diff and propose a commit message in conventional commits format:
   `feat:`, `fix:`, `docs:`, `refactor:`, or `chore:`
3. Confirm the message with the user
4. Call `git_commit(repo_path, message, add_all=True)`

---

## Fetch + Pull Workflow

**When to use:** User wants to get the latest changes from GitHub.

1. `git_fetch(repo_path)` — safely checks what's incoming (read-only)
2. `git_push_pull(repo_path, action="pull")` — merges remote changes locally
3. If pull returns conflict markers → `git_conflict_status(repo_path)` is called automatically

---

## Merge Workflow

**When to use:** User wants to merge a feature branch into main.

1. `git_branch(repo_path, action="switch", name="main")` — ensure you're on the target branch
2. `git_merge(repo_path, branch="feature/x")` — merge the feature branch
3. On conflict: `git_conflict_status` is called automatically — follow the resolution checklist
4. After resolving: `git_commit(repo_path, "merge feature/x", add_all=True)`

---

## Rebase Workflow

**When to use:** User explicitly requests a rebase.

1. Call `git_rebase(repo_path, onto_branch="main")` — this returns a warning, does NOT run yet
2. Present the warning to the user and ask for explicit confirmation
3. If confirmed: call `git_rebase(repo_path, onto_branch="main", confirm=True)`
4. On conflict: rebase is automatically aborted and clean state is restored

---

## Conflict Resolution Checklist

When `git_conflict_status` reports conflicts:

1. Open VS Code Source Control panel (`Ctrl+Shift+G`)
2. Click each file marked with `⚠️` and resolve the conflict markers (`<<<<`, `====`, `>>>>`)
3. Stage each resolved file in VS Code
4. Call `git_commit(repo_path, "resolve merge conflicts")` to complete

---

## Activity Logging

Every write operation (commit, push, pull, merge, smart_sync, branch create/delete) is automatically
logged to the **"Git Activity Log"** Google Sheet with:
- Timestamp, Repo, Branch, Action, Message, Result

**Setup required:** Set `GIT_LOG_SHEET_ID` in `.env` to the ID of your "Git Activity Log" sheet.
The sheet ID is found in the Google Sheets URL: `.../spreadsheets/d/<SHEET_ID>/edit`.

---

## Learnings
- `git -C <path>` is used internally so paths with spaces work reliably on Windows
- `add_all=True` on `git_commit` runs `git add .` before committing — covers 80% of use cases
- Repos with no remote (local-only) will gracefully tell you to add one rather than erroring
- VS Code storage.json is read-only by this tool; no VS Code state is modified
- `git_pull` automatically calls `git_conflict_status` on conflict — no manual check needed
- `git_rebase` with `confirm=False` (default) is a no-op safety gate — always shows warning first
- `git_generate_message` returns the raw diff; Claude composes the message (no API call inside tool)

**Version**: 2.0
**Updated**: 2026-03-15
