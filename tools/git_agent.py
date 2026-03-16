#!/usr/bin/env python3
"""
Git Agent - Discover and operate on git repositories from VS Code

Discovers repositories by reading VS Code's storage.json (recently opened
workspaces), then provides git operations on any of them.

Usage:
    python tools/git_agent.py --action list-repos
    python tools/git_agent.py --action status --repo "C:\\Users\\wm119\\git-practice"
    python tools/git_agent.py --action log --repo "C:\\Users\\wm119\\git-practice" --count 5
    python tools/git_agent.py --action commit --repo "..." --message "fix: update" --add-all
    python tools/git_agent.py --action push --repo "..." --remote origin --branch main
    python tools/git_agent.py --action pull --repo "..." --remote origin --branch main
    python tools/git_agent.py --action branch --repo "..." --branch-action list
    python tools/git_agent.py --action branch --repo "..." --branch-action create --name feature/x
    python tools/git_agent.py --action diff --repo "..." --staged
"""

import os
import sys
import subprocess
import argparse
import logging
import json
from pathlib import Path
from urllib.parse import unquote

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# VS Code stores recently opened workspaces here on Windows
VSCODE_STORAGE = Path(
    os.environ.get(
        "VSCODE_STORAGE_PATH",
        r"C:\Users\wm119\AppData\Roaming\Code\User\globalStorage\storage.json",
    )
)


# ---------------------------------------------------------------------------
# Repo Discovery
# ---------------------------------------------------------------------------

def _uri_to_path(uri: str) -> str | None:
    """Convert a VS Code file URI to a Windows absolute path.

    Examples:
        file:///c%3A/Users/wm119/git-practice  ->  C:\\Users\\wm119\\git-practice
        file:///c%3A/Users/wm119/Agentic%20Workflow%20Demo -> C:\\Users\\...\\Agentic Workflow Demo
    """
    if not uri.startswith("file:///"):
        return None
    raw = uri[len("file:///"):]          # strip  file:///
    decoded = unquote(raw)               # %3A -> :   %20 -> space
    # Normalize slashes and capitalise drive letter
    path = decoded.replace("/", "\\")
    if len(path) >= 2 and path[1] == ":":
        path = path[0].upper() + path[1:]
    return path


def discover_repos() -> list[dict]:
    """Return a list of repos discovered from VS Code's storage.json.

    Each entry is:
        {
            "index": int,
            "path": str,          # absolute Windows path
            "name": str,          # last path component
            "is_git": bool,       # True if <path>/.git exists
        }
    """
    if not VSCODE_STORAGE.exists():
        logger.warning("VS Code storage.json not found at %s", VSCODE_STORAGE)
        return []

    try:
        data = json.loads(VSCODE_STORAGE.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error("Failed to read storage.json: %s", exc)
        return []

    uris: list[str] = []

    # Primary source: profileAssociations.workspaces (keys are URIs)
    profile_assoc = data.get("profileAssociations", {}).get("workspaces", {})
    uris.extend(profile_assoc.keys())

    # Secondary source: backupWorkspaces.folders
    for entry in data.get("backupWorkspaces", {}).get("folders", []):
        uri = entry.get("folderUri") or entry.get("uri", "")
        if uri:
            uris.append(uri)

    # Tertiary: windowsState last active window folder
    last_folder = (
        data.get("windowsState", {})
        .get("lastActiveWindow", {})
        .get("folder", "")
    )
    if last_folder:
        uris.append(last_folder)

    # Deduplicate while preserving order
    seen: set[str] = set()
    repos: list[dict] = []
    for uri in uris:
        path = _uri_to_path(uri)
        if not path or path in seen:
            continue
        seen.add(path)
        p = Path(path)
        repos.append(
            {
                "index": len(repos) + 1,
                "path": path,
                "name": p.name,
                "is_git": (p / ".git").exists(),
            }
        )

    return repos


def format_repos(repos: list[dict]) -> str:
    if not repos:
        return (
            "No workspaces found in VS Code storage.\n"
            "Tip: You can pass a repo path directly to any git_ tool."
        )
    lines = ["Repositories discovered from VS Code:\n"]
    for r in repos:
        tag = "[git repo]" if r["is_git"] else "[not a git repo]"
        lines.append(f"  {r['index']:>2}. {r['path']}  {tag}")
    lines.append(
        "\nPass the full path to other git tools (e.g. git_status, git_commit)."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core git runner
# ---------------------------------------------------------------------------

def _run_git(repo_path: str, git_args: list[str], timeout: int = 30) -> dict:
    """Run a git command inside repo_path. Uses 'git -C <path>' so it works
    reliably even when paths contain spaces.

    Returns:
        {"success": bool, "stdout": str, "stderr": str, "returncode": int}
    """
    cmd = ["git", "-C", repo_path] + git_args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "stdout": "",
            "stderr": "git executable not found. Make sure git is installed and on PATH.",
            "returncode": -1,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"git command timed out after {timeout}s.",
            "returncode": -1,
        }


def _fmt(result: dict, label: str = "") -> str:
    """Format a _run_git result as a human-readable string."""
    parts = []
    if label:
        parts.append(label)
    if result["stdout"]:
        parts.append(result["stdout"])
    if result["stderr"] and not result["success"]:
        parts.append(f"Error: {result['stderr']}")
    if not parts:
        parts.append("(no output)")
    return "\n".join(parts)


def _current_branch(repo_path: str) -> str:
    r = _run_git(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])
    return r["stdout"] if r["success"] else "unknown"


def _has_remotes(repo_path: str) -> bool:
    r = _run_git(repo_path, ["remote"])
    return bool(r["stdout"].strip())


# ---------------------------------------------------------------------------
# Activity logging (appends a row to Google Sheets after every write op)
# ---------------------------------------------------------------------------

def git_log_entry(repo_name: str, branch: str, action: str, message: str, result: str) -> None:
    """Append one row to the Git Activity Log Google Sheet. Fails silently."""
    sheet_id = os.environ.get("GIT_LOG_SHEET_ID", "")
    if not sheet_id:
        logger.warning("GIT_LOG_SHEET_ID not set — activity log skipped.")
        return
    try:
        from datetime import datetime
        from tools.google.write_to_sheets import get_sheets_service
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [[timestamp, repo_name, branch, action, message, result]]
        service = get_sheets_service()
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range="Sheet1!A:F",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": row},
        ).execute()
        logger.info("Activity log: %s on %s/%s → %s", action, repo_name, branch, result)
    except Exception as exc:
        logger.warning("Activity log failed (non-fatal): %s", exc)


# ---------------------------------------------------------------------------
# Git operation functions (these are imported by mcp_server.py)
# ---------------------------------------------------------------------------

def git_status(repo_path: str) -> str:
    """Show the working tree status of a git repository."""
    branch = _current_branch(repo_path)
    r = _run_git(repo_path, ["status", "--short"])
    status_lines = r["stdout"] if r["success"] else f"Error: {r['stderr']}"
    if not status_lines:
        status_lines = "  (nothing to commit, working tree clean)"
    return f"Branch: {branch}\n\n{status_lines}"


def git_log(repo_path: str, n: int = 10) -> str:
    """Show the last N commits (oneline format)."""
    r = _run_git(repo_path, ["log", "--oneline", f"-{n}"])
    if not r["success"]:
        return f"Error: {r['stderr']}"
    return r["stdout"] or "(no commits yet)"


def git_diff(repo_path: str, staged: bool = False) -> str:
    """Show unstaged (or staged) changes."""
    args = ["diff"]
    if staged:
        args.append("--cached")
    r = _run_git(repo_path, args)
    if not r["success"]:
        return f"Error: {r['stderr']}"
    return r["stdout"] or "(no changes)"


def git_commit(repo_path: str, message: str, add_all: bool = False) -> str:
    """Stage all changes (optional) and create a commit."""
    if add_all:
        add_r = _run_git(repo_path, ["add", "."])
        if not add_r["success"]:
            return f"git add failed: {add_r['stderr']}"

    r = _run_git(repo_path, ["commit", "-m", message])
    result_str = "✅ success" if r["success"] else f"❌ failed: {r['stderr'][:80]}"
    git_log_entry(Path(repo_path).name, _current_branch(repo_path), "commit", message, result_str)
    return _fmt(r, f"Commit in {Path(repo_path).name}:")


def git_push(repo_path: str, remote: str = "origin", branch: str = "") -> str:
    """Push the current branch to a remote."""
    if not _has_remotes(repo_path):
        return (
            "No remotes configured for this repository.\n"
            "To add one:\n"
            "  git remote add origin https://github.com/your-username/your-repo.git\n"
            "Then retry the push."
        )
    if not branch:
        branch = _current_branch(repo_path)
    r = _run_git(repo_path, ["push", remote, branch])
    result_str = "✅ success" if r["success"] else f"❌ failed: {r['stderr'][:80]}"
    git_log_entry(Path(repo_path).name, branch, "push", f"push to {remote}/{branch}", result_str)
    return _fmt(r, f"Push {branch} -> {remote}:")


def git_pull(repo_path: str, remote: str = "origin", branch: str = "") -> str:
    """Pull from a remote into the current branch."""
    if not _has_remotes(repo_path):
        return (
            "No remotes configured for this repository.\n"
            "Nothing to pull."
        )
    if not branch:
        branch = _current_branch(repo_path)
    r = _run_git(repo_path, ["pull", remote, branch])
    if not r["success"] and "CONFLICT" in (r["stdout"] + r["stderr"]):
        git_log_entry(Path(repo_path).name, branch, "pull", f"pull from {remote}/{branch}", "❌ conflict")
        return f"Pull produced merge conflicts:\n\n{git_conflict_status(repo_path)}"
    result_str = "✅ success" if r["success"] else f"❌ failed: {r['stderr'][:80]}"
    git_log_entry(Path(repo_path).name, branch, "pull", f"pull from {remote}/{branch}", result_str)
    return _fmt(r, f"Pull {remote}/{branch}:")


def git_branch(repo_path: str, action: str, name: str = "") -> str:
    """Manage branches. action: list | create | switch | delete."""
    action = action.lower()
    if action == "list":
        r = _run_git(repo_path, ["branch", "-a"])
        return _fmt(r, "Branches:")
    elif action == "create":
        if not name:
            return "Error: --name is required for branch create."
        r = _run_git(repo_path, ["checkout", "-b", name])
        result_str = "✅ success" if r["success"] else f"❌ failed: {r['stderr'][:80]}"
        git_log_entry(Path(repo_path).name, name, "branch_create", f"create {name}", result_str)
        return _fmt(r, f"Created and switched to branch '{name}':")
    elif action == "switch":
        if not name:
            return "Error: --name is required for branch switch."
        r = _run_git(repo_path, ["checkout", name])
        return _fmt(r, f"Switched to branch '{name}':")
    elif action == "delete":
        if not name:
            return "Error: --name is required for branch delete."
        r = _run_git(repo_path, ["branch", "-d", name])
        result_str = "✅ success" if r["success"] else f"❌ failed: {r['stderr'][:80]}"
        git_log_entry(Path(repo_path).name, _current_branch(repo_path), "branch_delete", f"delete {name}", result_str)
        return _fmt(r, f"Deleted branch '{name}':")
    else:
        return f"Unknown branch action '{action}'. Use: list, create, switch, delete."


# ---------------------------------------------------------------------------
# Extended git operations (Phase 1 enhancements + Phase 2 new capabilities)
# ---------------------------------------------------------------------------

def check_all_repos() -> str:
    """Scan every VS Code repo and report which ones have uncommitted changes."""
    repos = discover_repos()
    if not repos:
        return "No repositories found."
    lines = ["Repository scan:\n"]
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
    return "\n".join(lines)


def git_smart_sync(repo_path: str, commit_message: str,
                   remote: str = "origin", branch: str = "") -> str:
    """One-shot GitHub sync: stage all changes, commit with message, push."""
    log = []

    status = _run_git(repo_path, ["status", "--short"])
    if not status["stdout"].strip():
        return "Nothing to sync — working tree is clean."
    log.append(f"Changes detected:\n{status['stdout'].rstrip()}")

    add_result = _run_git(repo_path, ["add", "."])
    if add_result["returncode"] != 0:
        return f"Stage failed:\n{add_result['stderr']}"
    log.append("Staged all changes.")

    commit_result = _run_git(repo_path, ["commit", "-m", commit_message])
    if commit_result["returncode"] != 0:
        return f"Commit failed:\n{commit_result['stderr']}"
    log.append(f"Committed: \"{commit_message}\"")

    repo_name = Path(repo_path).name
    cur_branch = branch or _current_branch(repo_path)

    if not _has_remotes(repo_path):
        git_log_entry(repo_name, cur_branch, "smart_sync", commit_message,
                      "✅ committed (no remote)")
        log.append(
            "No remote configured — skipping push.\n"
            "To connect to GitHub: git remote add origin <your-github-url>"
        )
        return "\n".join(log)

    push_result = _run_git(repo_path, ["push", remote, cur_branch])
    if push_result["returncode"] != 0:
        git_log_entry(repo_name, cur_branch, "smart_sync", commit_message,
                      f"❌ push failed: {push_result['stderr'][:80]}")
        log.append(f"Push failed:\n{push_result['stderr']}")
    else:
        git_log_entry(repo_name, cur_branch, "smart_sync", commit_message, "✅ success")
        log.append(f"Pushed to {remote}/{cur_branch}.")

    return "\n".join(log)


def git_fetch(repo_path: str, remote: str = "origin") -> str:
    """Fetch from a remote without merging (safe, read-only locally)."""
    if not _has_remotes(repo_path):
        return "No remotes configured. Nothing to fetch."
    r = _run_git(repo_path, ["fetch", remote])
    return _fmt(r, f"Fetch from {remote}:")


def git_conflict_status(repo_path: str) -> str:
    """List files with merge conflicts and provide resolution guidance."""
    r = _run_git(repo_path, ["diff", "--name-only", "--diff-filter=U"])
    conflicted = r["stdout"].strip().splitlines() if r["success"] else []
    if not conflicted:
        return "No merge conflicts detected."
    lines = [f"Merge conflicts in {len(conflicted)} file(s):\n"]
    for f in conflicted:
        lines.append(f"  ⚠️  {f}")
    lines.append("\nResolution steps:")
    lines.append("  1. Open VS Code Source Control panel (Ctrl+Shift+G)")
    lines.append("  2. Click each conflicted file and resolve the conflict markers (<<<<, ====, >>>>)")
    lines.append("  3. Stage each resolved file")
    lines.append("  4. Call git_commit to complete the merge")
    return "\n".join(lines)


def git_merge(repo_path: str, branch: str) -> str:
    """Merge a branch into the current branch."""
    check = _run_git(repo_path, ["rev-parse", "--verify", branch])
    if not check["success"]:
        return (
            f"Branch '{branch}' does not exist.\n"
            f"Available branches:\n{git_branch(repo_path, 'list')}"
        )
    r = _run_git(repo_path, ["merge", branch])
    repo_name = Path(repo_path).name
    cur_branch = _current_branch(repo_path)
    if not r["success"] and "CONFLICT" in (r["stdout"] + r["stderr"]):
        git_log_entry(repo_name, cur_branch, "merge", f"merge {branch}", "❌ conflict")
        return f"Merge conflict detected:\n\n{git_conflict_status(repo_path)}"
    result_str = "✅ success" if r["success"] else f"❌ failed: {r['stderr'][:80]}"
    git_log_entry(repo_name, cur_branch, "merge", f"merge {branch}", result_str)
    return _fmt(r, f"Merge '{branch}':")


def git_rebase(repo_path: str, onto_branch: str, confirm: bool = False) -> str:
    """Rebase current branch onto another. Requires confirm=True to run."""
    if not confirm:
        return (
            f"⚠️  Rebase warning: rebasing onto '{onto_branch}' rewrites your commit history.\n"
            "This is safe for local branches that haven't been pushed, but can cause\n"
            "problems if others have based work on your current branch.\n\n"
            "To proceed, call git_rebase again with confirm=True."
        )
    r = _run_git(repo_path, ["rebase", onto_branch])
    if not r["success"]:
        _run_git(repo_path, ["rebase", "--abort"])
        return (
            f"Rebase failed — automatically aborted to restore a clean state.\n"
            f"Details:\n{r['stdout']}\n{r['stderr']}\n\n"
            "Suggestion: use git_merge instead, or resolve conflicts manually before rebasing."
        )
    repo_name = Path(repo_path).name
    cur_branch = _current_branch(repo_path)
    git_log_entry(repo_name, cur_branch, "rebase", f"rebase onto {onto_branch}", "✅ success")
    return _fmt(r, f"Rebase onto '{onto_branch}':")


def git_generate_message(repo_path: str) -> str:
    """Return the current diff so Claude can propose a commit message."""
    staged = _run_git(repo_path, ["diff", "--cached"])
    unstaged = _run_git(repo_path, ["diff"])
    staged_out = staged["stdout"].strip()
    unstaged_out = unstaged["stdout"].strip()
    if not staged_out and not unstaged_out:
        return "No changes detected. Nothing to generate a message for."
    parts = []
    if staged_out:
        parts.append(f"=== STAGED CHANGES ===\n{staged_out}")
    if unstaged_out:
        parts.append(f"=== UNSTAGED CHANGES ===\n{unstaged_out}")
    diff_text = "\n\n".join(parts)
    MAX_CHARS = 3000
    if len(diff_text) > MAX_CHARS:
        diff_text = diff_text[:MAX_CHARS] + f"\n\n... (truncated — {len(diff_text) - MAX_CHARS} chars omitted)"
    return (
        f"Diff for commit message generation:\n\n{diff_text}\n\n"
        "Based on the diff above, propose a commit message using conventional commits format:\n"
        "  feat: <description>      — new feature\n"
        "  fix: <description>       — bug fix\n"
        "  docs: <description>      — documentation only\n"
        "  refactor: <description>  — code restructuring, no behaviour change\n"
        "  chore: <description>     — maintenance, tooling, dependencies"
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Git agent — discover and operate on VS Code repositories"
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["list-repos", "status", "log", "diff", "commit", "push", "pull", "branch"],
        help="Action to perform",
    )
    parser.add_argument("--repo", type=str, help="Absolute path to the git repository")
    parser.add_argument("--message", "-m", type=str, help="Commit message")
    parser.add_argument("--count", type=int, default=10, help="Number of log entries (default: 10)")
    parser.add_argument("--remote", type=str, default="origin", help="Remote name (default: origin)")
    parser.add_argument("--branch", type=str, default="", help="Branch name")
    parser.add_argument("--add-all", action="store_true", help="Stage all changes before committing")
    parser.add_argument("--staged", action="store_true", help="Show staged diff (for diff action)")
    parser.add_argument("--branch-action", type=str, default="list",
                        choices=["list", "create", "switch", "delete"],
                        help="Branch sub-action (default: list)")
    parser.add_argument("--name", type=str, help="Branch name for create/switch/delete")
    return parser.parse_args()


def main():
    args = parse_arguments()

    if args.action == "list-repos":
        repos = discover_repos()
        print(format_repos(repos))
        sys.exit(0)

    # All other actions require --repo
    if not args.repo:
        print("Error: --repo is required for this action.")
        sys.exit(1)

    repo = args.repo

    if args.action == "status":
        print(git_status(repo))
    elif args.action == "log":
        print(git_log(repo, args.count))
    elif args.action == "diff":
        print(git_diff(repo, args.staged))
    elif args.action == "commit":
        if not args.message:
            print("Error: --message is required for commit.")
            sys.exit(1)
        print(git_commit(repo, args.message, args.add_all))
    elif args.action == "push":
        print(git_push(repo, args.remote, args.branch))
    elif args.action == "pull":
        print(git_pull(repo, args.remote, args.branch))
    elif args.action == "branch":
        print(git_branch(repo, args.branch_action, args.name or ""))

    sys.exit(0)


if __name__ == "__main__":
    main()
