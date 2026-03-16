# WAT Framework — Debug & Best Practices Report
**Generated:** 2026-03-16
**Reviewed by:** Claude Sonnet 4.6
**Scope:** `git_agent.py`, `mcp_server.py`, `write_to_sheets.py`, `read_from_sheets.py`, `requirements.txt`, `.gitignore`

---

## Overall Verdict

The system is **working well and production-ready for its current scope**. All 4 repos are synced to GitHub, Google Sheets integration is functional, and the MCP server is wired up correctly. The findings below are improvements — none of them are currently breaking anything.

---

## 🔴 High Priority

### 1. Token and credentials files use relative paths
**File:** `write_to_sheets.py` and `read_from_sheets.py` (lines 36–52 in each)

Both files look for `token.json` and `credentials.json` using relative paths (`os.path.exists('token.json')`). This means they only work when run from the project root directory. When called from a different working directory, they silently fail to find the files.

**Why it matters:** The MCP server launches these as subprocesses. If the working directory ever shifts, Google auth breaks.

**Fix:** Replace `'token.json'` with an absolute path:
```python
TOKEN_PATH = Path(__file__).parent.parent.parent / "token.json"
CREDS_PATH = Path(__file__).parent.parent.parent / "credentials.json"
```

---

### 2. `get_sheets_service()` is copy-pasted in two files
**Files:** `write_to_sheets.py:26–58` and `read_from_sheets.py:32–64`

The exact same 30-line authentication function exists in both files. If you ever need to update the auth logic (e.g., token refresh, new scopes), you have to change it in two places and it's easy to get them out of sync.

**Fix:** Move `get_sheets_service()` into `tools/google/__init__.py` or a new `tools/google/auth.py` and import it in both files.

---

### 3. `run_tool` in MCP server splits arguments naively
**File:** `mcp_server.py:204`

```python
cmd.extend(args.split())  # ← breaks on quoted args with spaces
```

If you ever call `run_tool` with an argument containing spaces (e.g., a commit message or file path), `args.split()` will break it into pieces incorrectly.

**Fix:** Use `shlex.split(args)` instead, which correctly handles quoted strings.

---

## 🟡 Medium Priority

### 4. `requirements.txt` has many unused packages
**File:** `requirements.txt`

The following packages are listed but not imported anywhere in the current codebase:

| Package | Status |
|---------|--------|
| `selenium` | Not used |
| `beautifulsoup4` | Not used |
| `lxml` | Not used |
| `pandas` | Not used |
| `numpy` | Not used |
| `openpyxl` | Not used |
| `pytz` | Not used |
| `python-dateutil` | Not used |
| `jsonschema` | Not used |
| `pyyaml` | Not used |
| `colorlog` | Not used |
| `openai` | Not used |

These add ~500MB to installs, slow down setup, and create unnecessary security surface area.

**Fix:** Trim `requirements.txt` to only what's actually imported. Keep commented-out entries for packages you plan to add soon.

---

### 5. No retry logic on Google Sheets API calls
**Files:** `write_to_sheets.py`, `read_from_sheets.py`

We hit a `503 Service Unavailable` error from Google during this session. There is no retry logic — one transient network hiccup fails the whole operation.

**Fix:** Wrap the `.execute()` calls in a simple retry loop (2–3 attempts, 2-second wait). The `google-api-python-client` library also supports `HttpRequest` retries natively.

---

### 6. `write_to_sheets.py` data format can't handle commas or semicolons in values
**File:** `write_to_sheets.py:114`

```python
values = [row.split(',') for row in args.data.split(';')]
```

If any cell value contains a comma (e.g., a commit message like `"fix: update config, remove stale keys"`), it gets split into two separate cells. The current workaround is to replace commas with semicolons in the data, but that's fragile.

**Fix:** Accept JSON-encoded data as an alternative input format for complex payloads.

---

### 7. `anthropic` package version is outdated
**File:** `requirements.txt:24`

```
anthropic>=0.8.0
```

Version `0.8.0` is from early 2024. The current version is `0.40+` and includes major API changes. Any code that tries to use Claude through this package with the old interface will fail silently or throw errors.

**Fix:** Update to `anthropic>=0.40.0`.

---

## 🟢 Low Priority / Nice to Have

### 8. `read_from_sheets.py` has a potential path bug
**File:** `read_from_sheets.py:96`

```python
os.makedirs(os.path.dirname(output_path), exist_ok=True)
```

If `output_path` is a plain filename with no directory (e.g., `output.csv`), `os.path.dirname()` returns an empty string `''`, and `os.makedirs('')` raises an error.

**Fix:** Add a guard: `if dir_path: os.makedirs(dir_path, exist_ok=True)`

---

### 9. Scope mismatch between read and write tools
**Files:** `read_from_sheets.py:29`, `write_to_sheets.py:23`

- Read tool uses: `spreadsheets.readonly`
- Write tool uses: `spreadsheets` (full access)

The `token.json` on disk was created with full access (write scope). When `read_from_sheets.py` loads it, the token has broader access than the script declares. This works fine right now, but if the token is ever regenerated using the read tool first, write operations will fail until the token is regenerated again.

**Fix:** Use a single shared `SCOPES` constant with full access (`spreadsheets`) in the shared auth module (see Finding #2).

---

### 10. `GIT_LOG_SHEET_ID` missing from `.env` file
**File:** `.env` (not committed, but based on `.env.template`)

The `.env.template` shows `GIT_LOG_SHEET_ID=your_google_sheet_id_here`. The actual sheet ID (`1HYVpkLb_smXqcKrxPC1n-i1zH7mI-eTwFfi79MgW214`) needs to be set in your `.env` file for the git activity log to work automatically after every commit/push.

**Fix:** Open `.env` and set:
```
GIT_LOG_SHEET_ID=1HYVpkLb_smXqcKrxPC1n-i1zH7mI-eTwFfi79MgW214
```

---

## ✅ What's Working Well

| Area | Status |
|------|--------|
| Secret protection | `.env`, `token.json`, `credentials.json` all gitignored |
| Error handling in git operations | Timeouts, missing git, conflict detection all handled |
| Rebase safety guardrail | Requires `confirm=True` — good protection |
| MCP server path traversal protection | `run_tool` checks path stays within project root |
| Activity logging | `git_log_entry` fails silently — correct, non-critical path |
| `.claude/worktrees/` gitignored | Fixed during this session |
| `GIT_AGENT_ENHANCEMENT_PLAN.md` in repo | Fine to have — useful planning doc |

---

## Recommended Action Order

1. **Do now:** Set `GIT_LOG_SHEET_ID` in your `.env` (5 minutes, unlocks automatic activity logging)
2. **Next session:** Fix the relative `token.json` paths to absolute (prevents future auth breakage)
3. **When time allows:** Trim `requirements.txt` to used packages only
4. **Future enhancement:** Shared `auth.py` module + retry logic for Sheets API
