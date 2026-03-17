#!/usr/bin/env python3
"""
WAT Framework MCP Server

Exposes the WAT (Workflows, Agents, Tools) framework via the
Model Context Protocol, enabling AI assistants to:
- Execute tools (example tool, Google Sheets read/write)
- Read workflows and tool source code
- Browse project structure
- Run arbitrary tools by path
"""

import os
import sys
import shlex
import subprocess
import glob
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Git agent and Google Sheets tools — imported once at startup
sys.path.insert(0, str(Path(__file__).parent / "tools"))
import git_agent
from tools.google.write_to_sheets import write_data as _sheets_write
from tools.google.read_from_sheets import read_data as _sheets_read

# Project root directory
PROJECT_ROOT = Path(__file__).parent.resolve()

# Create the MCP server
mcp = FastMCP(
    "WAT Framework",
    instructions=(
        "This MCP server exposes the WAT (Workflows, Agents, Tools) framework. "
        "Use tools to execute Python scripts, resources to read workflows and "
        "tool source code, and prompts for guided workflow execution."
    ),
)


# ---------------------------------------------------------------------------
# MCP TOOLS - Executable actions
# ---------------------------------------------------------------------------


@mcp.tool()
def list_tools() -> str:
    """List all available Python tools in the tools/ directory."""
    tools_dir = PROJECT_ROOT / "tools"
    tool_files = []

    for py_file in sorted(tools_dir.rglob("*.py")):
        if py_file.name == "__init__.py":
            continue
        relative = py_file.relative_to(PROJECT_ROOT)
        tool_files.append(str(relative))

    if not tool_files:
        return "No tools found in tools/ directory."

    return "Available tools:\n" + "\n".join(f"  - {t}" for t in tool_files)


@mcp.tool()
def list_workflows() -> str:
    """List all available workflow SOPs in the workflows/ directory."""
    workflows_dir = PROJECT_ROOT / "workflows"
    workflow_files = []

    for md_file in sorted(workflows_dir.glob("*.md")):
        # Read first line to get the title
        try:
            first_line = md_file.read_text(encoding="utf-8").split("\n")[0]
            title = first_line.lstrip("# ").strip()
        except Exception:
            title = md_file.stem

        relative = md_file.relative_to(PROJECT_ROOT)
        workflow_files.append(f"  - {relative} — {title}")

    if not workflow_files:
        return "No workflows found in workflows/ directory."

    return "Available workflows:\n" + "\n".join(workflow_files)


@mcp.tool()
def run_example_tool(input_text: str, output_path: str = ".tmp/output.txt") -> str:
    """
    Run the example tool with the given input.

    Args:
        input_text: The input string to process.
        output_path: Where to write the output file (default: .tmp/output.txt).
    """
    script = PROJECT_ROOT / "tools" / "example_tool.py"
    result = subprocess.run(
        [sys.executable, str(script), "--input", input_text, "--output", output_path],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=60,
    )

    output = ""
    if result.stdout:
        output += f"STDOUT:\n{result.stdout}\n"
    if result.stderr:
        output += f"STDERR:\n{result.stderr}\n"
    output += f"Exit code: {result.returncode}"
    return output


@mcp.tool()
def read_google_sheet(
    spreadsheet_id: str,
    range: str,
    output: str = ".tmp/sheet_data.csv",
) -> str:
    """
    Read data from a Google Sheet and save to a local CSV file.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID (from the URL).
        range: The range in A1 notation (e.g., 'Sheet1!A:Z').
        output: Where to save the CSV file (default: .tmp/sheet_data.csv).
    """
    try:
        success = _sheets_read(spreadsheet_id, range, output)
        return f"Read complete. Data saved to {output}" if success else "Read failed — no data found in range."
    except Exception as exc:
        return f"Error reading sheet: {exc}"


@mcp.tool()
def write_google_sheet(
    spreadsheet_id: str,
    range: str,
    data: str,
) -> str:
    """
    Write data to a Google Sheet.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID (from the URL).
        range: The range in A1 notation (e.g., 'Sheet1!A1').
        data: Semicolon-separated rows with comma-separated values (e.g., "A1,B1;A2,B2"),
              or a JSON 2D array (e.g., '[["hello, world","test"]]') when values contain commas.
    """
    import json as _json
    try:
        values = _json.loads(data)
    except (_json.JSONDecodeError, ValueError):
        values = [row.split(',') for row in data.split(';')]
    try:
        success = _sheets_write(spreadsheet_id, range, values)
        return "Write complete." if success else "Write failed — check logs."
    except Exception as exc:
        return f"Error writing sheet: {exc}"


@mcp.tool()
def run_tool(tool_path: str, args: str = "") -> str:
    """
    Run any tool by its relative path with optional arguments.

    Args:
        tool_path: Relative path to the tool script (e.g., 'tools/example_tool.py').
        args: Space-separated arguments to pass to the tool (e.g., '--input hello --output .tmp/out.txt').
    """
    script = PROJECT_ROOT / tool_path

    if not script.exists():
        return f"Error: Tool not found at {tool_path}"
    if not str(script.resolve()).startswith(str(PROJECT_ROOT)):
        return "Error: Tool path must be within the project directory."
    if not script.suffix == ".py":
        return "Error: Only Python (.py) tools can be executed."

    cmd = [sys.executable, str(script)]
    if args:
        cmd.extend(shlex.split(args))

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=60,
    )

    output_text = ""
    if result.stdout:
        output_text += f"STDOUT:\n{result.stdout}\n"
    if result.stderr:
        output_text += f"STDERR:\n{result.stderr}\n"
    output_text += f"Exit code: {result.returncode}"
    return output_text


# ---------------------------------------------------------------------------
# GIT TOOLS - Operate on local git repositories
# ---------------------------------------------------------------------------


@mcp.tool()
def git_list_repos() -> str:
    """
    Discover all git repositories from VS Code recently opened workspaces.
    Returns a numbered list with paths and whether each folder is a git repo.
    Always call this first to find available repos before running other git operations.
    """
    repos = git_agent.discover_repos()
    return git_agent.format_repos(repos)


@mcp.tool()
def git_status(repo_path: str) -> str:
    """
    Show the working tree status of a git repository.

    Args:
        repo_path: Absolute path to the git repository (e.g. C:\\Users\\wm119\\git-practice).
    """
    return git_agent.git_status(repo_path)


@mcp.tool()
def git_log(repo_path: str, count: int = 10) -> str:
    """
    Show recent commit history for a repository.

    Args:
        repo_path: Absolute path to the git repository.
        count: Number of commits to show (default: 10).
    """
    return git_agent.git_log(repo_path, count)


@mcp.tool()
def git_commit(repo_path: str, message: str, add_all: bool = False) -> str:
    """
    Commit changes in a repository.

    Args:
        repo_path: Absolute path to the git repository.
        message: Commit message.
        add_all: If True, stage all changes with 'git add .' before committing (default: False).
    """
    return git_agent.git_commit(repo_path, message, add_all)


@mcp.tool()
def git_push_pull(
    repo_path: str,
    action: str,
    remote: str = "origin",
    branch: str = "",
) -> str:
    """
    Push or pull from a remote repository.

    Args:
        repo_path: Absolute path to the git repository.
        action: Either 'push' or 'pull'.
        remote: Remote name (default: 'origin').
        branch: Branch name. If empty, uses the current branch.
    """
    if action.lower() == "push":
        return git_agent.git_push(repo_path, remote, branch)
    elif action.lower() == "pull":
        return git_agent.git_pull(repo_path, remote, branch)
    else:
        return f"Unknown action '{action}'. Use 'push' or 'pull'."


@mcp.tool()
def git_branch(repo_path: str, action: str, name: str = "") -> str:
    """
    Manage branches in a repository.

    Args:
        repo_path: Absolute path to the git repository.
        action: One of 'list', 'create', 'switch', 'delete'.
        name: Branch name (required for create, switch, delete).
    """
    return git_agent.git_branch(repo_path, action, name)


@mcp.tool()
def git_diff(repo_path: str, staged: bool = False) -> str:
    """
    Show line-by-line file changes in a repository.

    Args:
        repo_path: Absolute path to the git repository.
        staged: If True, show staged (cached) changes. Default shows unstaged changes.
    """
    return git_agent.git_diff(repo_path, staged=staged)


@mcp.tool()
def git_check_all() -> str:
    """
    Scan all VS Code repositories and report which ones have uncommitted changes.
    Use this as a morning check or before starting work to see pending state across all repos.
    """
    return git_agent.check_all_repos()


@mcp.tool()
def git_smart_sync(repo_path: str, commit_message: str,
                   remote: str = "origin", branch: str = "") -> str:
    """
    One-shot GitHub sync: stage all changes, commit with a message, and push.
    Use git_check_all first to identify repos with pending changes.
    If no remote is configured, commits locally and explains how to connect to GitHub.

    Args:
        repo_path: Absolute path to the git repository.
        commit_message: Commit message describing the changes.
        remote: Remote name (default: 'origin').
        branch: Branch to push to. If empty, uses the current branch.
    """
    return git_agent.git_smart_sync(repo_path, commit_message, remote=remote, branch=branch)


@mcp.tool()
def git_fetch(repo_path: str, remote: str = "origin") -> str:
    """
    Fetch from a remote without merging. Safe — does not change your local branch.
    Use before git_push_pull(action='pull') to preview what's incoming.

    Args:
        repo_path: Absolute path to the git repository.
        remote: Remote name (default: 'origin').
    """
    return git_agent.git_fetch(repo_path, remote=remote)


@mcp.tool()
def git_merge(repo_path: str, branch: str) -> str:
    """
    Merge a branch into the current branch.
    Automatically detects conflicts and returns a resolution checklist if they occur.

    Args:
        repo_path: Absolute path to the git repository.
        branch: Name of the branch to merge into the current branch.
    """
    return git_agent.git_merge(repo_path, branch)


@mcp.tool()
def git_rebase(repo_path: str, onto_branch: str, confirm: bool = False) -> str:
    """
    Rebase the current branch onto another branch.
    GUARDRAIL: Returns a warning and does NOT run unless confirm=True is explicitly passed.
    On conflict, automatically aborts the rebase to restore a clean state.

    Args:
        repo_path: Absolute path to the git repository.
        onto_branch: Branch to rebase onto (e.g. 'main').
        confirm: Must be True to proceed. Default False shows a warning instead.
    """
    return git_agent.git_rebase(repo_path, onto_branch, confirm=confirm)


@mcp.tool()
def git_conflict_status(repo_path: str) -> str:
    """
    List all files currently in a merge conflict state and provide resolution steps.
    Call this after any merge, pull, or rebase that reports conflicts.

    Args:
        repo_path: Absolute path to the git repository.
    """
    return git_agent.git_conflict_status(repo_path)


@mcp.tool()
def git_generate_message(repo_path: str) -> str:
    """
    Return the current diff (staged and unstaged) so a commit message can be proposed.
    Use this when the user says 'commit my changes' without providing a message.
    After reviewing the diff, propose a message using conventional commits format, then call git_commit.

    Args:
        repo_path: Absolute path to the git repository.
    """
    return git_agent.git_generate_message(repo_path)


# ---------------------------------------------------------------------------
# MCP RESOURCES - Read-only data
# ---------------------------------------------------------------------------


@mcp.resource("workflow://{name}")
def get_workflow(name: str) -> str:
    """Read a workflow SOP by name (without .md extension)."""
    workflow_path = PROJECT_ROOT / "workflows" / f"{name}.md"

    if not workflow_path.exists():
        available = [f.stem for f in (PROJECT_ROOT / "workflows").glob("*.md")]
        return f"Workflow '{name}' not found. Available: {', '.join(available)}"

    return workflow_path.read_text(encoding="utf-8")


@mcp.resource("tool-info://{path}")
def get_tool_info(path: str) -> str:
    """
    Read a tool's source code. Use forward slashes for nested paths
    (e.g., 'google/read_from_sheets' for tools/google/read_from_sheets.py).
    """
    tool_path = PROJECT_ROOT / "tools" / f"{path}.py"

    if not tool_path.exists():
        return f"Tool not found at tools/{path}.py"

    return tool_path.read_text(encoding="utf-8")


@mcp.resource("project://structure")
def get_project_structure() -> str:
    """Get the full project directory tree (excluding .git, __pycache__, venv)."""
    exclude_dirs = {".git", "__pycache__", "venv", ".venv", "node_modules", ".tmp"}
    lines = []

    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Filter out excluded directories
        dirs[:] = [d for d in sorted(dirs) if d not in exclude_dirs]

        level = Path(root).relative_to(PROJECT_ROOT).parts
        indent = "  " * len(level)
        folder_name = Path(root).name if level else PROJECT_ROOT.name
        lines.append(f"{indent}{folder_name}/")

        sub_indent = "  " * (len(level) + 1)
        for f in sorted(files):
            lines.append(f"{sub_indent}{f}")

    return "\n".join(lines)


@mcp.resource("project://env-template")
def get_env_template() -> str:
    """Read the .env.template file to see required configuration variables."""
    template_path = PROJECT_ROOT / ".env.template"

    if not template_path.exists():
        return ".env.template not found."

    return template_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# MCP PROMPTS - Reusable templates
# ---------------------------------------------------------------------------


@mcp.prompt()
def execute_workflow(workflow_name: str) -> str:
    """
    Generate a prompt for executing a workflow step-by-step.

    Args:
        workflow_name: Name of the workflow to execute (without .md extension).
    """
    workflow_path = PROJECT_ROOT / "workflows" / f"{workflow_name}.md"

    if not workflow_path.exists():
        available = [f.stem for f in (PROJECT_ROOT / "workflows").glob("*.md")]
        return f"Workflow '{workflow_name}' not found. Available: {', '.join(available)}"

    content = workflow_path.read_text(encoding="utf-8")

    return (
        f"Execute the following WAT framework workflow step-by-step. "
        f"For each step, use the appropriate MCP tool to run the required script. "
        f"Report the result of each step before proceeding to the next. "
        f"If any step fails, follow the Edge Cases section for recovery.\n\n"
        f"---\n\n{content}"
    )


@mcp.prompt()
def create_new_tool(tool_name: str, description: str) -> str:
    """
    Generate a prompt for creating a new tool following the WAT framework pattern.

    Args:
        tool_name: Name for the new tool (e.g., 'scrape_single_site').
        description: What the tool should do.
    """
    example_path = PROJECT_ROOT / "tools" / "example_tool.py"
    example_code = ""
    if example_path.exists():
        example_code = example_path.read_text(encoding="utf-8")

    return (
        f"Create a new WAT framework tool called '{tool_name}' that: {description}\n\n"
        f"Follow the standard tool pattern shown in the example below. The tool must:\n"
        f"1. Use argparse for command-line arguments\n"
        f"2. Load environment variables with python-dotenv\n"
        f"3. Use logging (not print) for output\n"
        f"4. Return exit code 0 on success, 1 on failure\n"
        f"5. Use utilities from tools/utils/common.py where applicable\n"
        f"6. Save the tool to tools/{tool_name}.py\n\n"
        f"Example tool pattern:\n```python\n{example_code}\n```"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
