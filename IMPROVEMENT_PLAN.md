# WAT Framework — Improvement Plan
**Created:** 2026-03-16
**Based on:** DEBUG_REPORT.md findings

Think of this like a to-do list for making the system stronger.
Each fix is explained simply, step by step.

---

## How to Use This Plan

- Work through the fixes **in order** — each one builds on the previous
- Each fix has a difficulty rating: 🟢 Easy | 🟡 Medium | 🔴 Harder
- Tell Claude "let's do Fix #1 from the improvement plan" and it will do the work for you
- Check off each box when done: change `[x]` to `[x]`

---

# HIGH PRIORITY FIXES

---

## Fix #1 — Token file uses the wrong kind of address 🟢 Easy
**From DEBUG_REPORT finding #1**

### What's the problem?
Imagine you wrote your home address as just "my house" instead of "123 Main Street."
That works fine when you're already home — but if someone tries to find you from
a different city, "my house" means nothing.

Right now, `token.json` (your Google login file) is found using a relative path,
which is like saying "my house." If the program is ever started from a different
folder, it can't find the file and Google login breaks.

### What we'll fix
We'll change two files to use the **full address** (absolute path) for `token.json`
and `credentials.json` so they can always be found, no matter where the program starts.

### Files to change
- `tools/google/write_to_sheets.py`
- `tools/google/read_from_sheets.py`

### Steps
- [x] Step 1: Tell Claude "Do Fix #1 from the improvement plan"
- [x] Step 2: Claude will update both files to use absolute paths
- [x] Step 3: Test by running: `python tools/google/write_to_sheets.py --help`
- [x] Step 4: If no error, the fix worked ✅

---

## Fix #2 — Stop copy-pasting the same login code in two places 🟡 Medium
**From DEBUG_REPORT finding #2**

### What's the problem?
Imagine you wrote your WiFi password on two sticky notes and put them in different
drawers. If you ever change your WiFi password, you have to remember to update
BOTH sticky notes. If you forget one, things break in a confusing way.

Right now, the Google login code (`get_sheets_service`) is written identically
in two files. If we ever need to update how Google login works, we have to change
it in both files — and it's easy to forget one.

### What we'll fix
We'll create **one shared file** that holds the login code.
Both tools will then pull from that one place.
Update it once → both tools use the new version automatically.

### Files to change
- **Create new:** `tools/google/auth.py` (the shared file)
- **Update:** `tools/google/write_to_sheets.py` (import from auth.py)
- **Update:** `tools/google/read_from_sheets.py` (import from auth.py)

### Steps
- [x] Step 1: Tell Claude "Do Fix #2 from the improvement plan"
- [x] Step 2: Claude creates `tools/google/auth.py` with the shared login code
- [x] Step 3: Claude updates both tools to import from `auth.py`
- [x] Step 4: Test read: `python tools/google/read_from_sheets.py --spreadsheet-id 1HYVpkLb_smXqcKrxPC1n-i1zH7mI-eTwFfi79MgW214 --range "Sheet1!A1:B2"`
- [x] Step 5: Test write: run a small write to the sheet
- [x] Step 6: If both work, Fix #2 is done ✅

---

## Fix #3 — Argument splitter breaks on names with spaces 🟡 Medium
**From DEBUG_REPORT finding #3**

### What's the problem?
Imagine asking someone to count the words in this sentence:
`"fix: update config, remove stale keys"`

A dumb counter would see the quotes as part of the text and count wrong.
A smart counter knows the quotes mean "treat this as one thing."

Right now, `mcp_server.py` uses a dumb splitter that breaks arguments by spaces.
So a commit message like `"fix: update the main file"` gets chopped into
5 separate pieces instead of staying as one message. This would cause silent
failures or garbled commit messages when using the MCP tool.

### What we'll fix
Replace the dumb splitter (`args.split()`) with a smart one (`shlex.split()`)
that understands quotes.

### Files to change
- `mcp_server.py` (line 204, one-line change)

### Steps
- [x] Step 1: Tell Claude "Do Fix #3 from the improvement plan"
- [x] Step 2: Claude changes `args.split()` to `shlex.split(args)` and adds the import
- [x] Step 3: Test by asking Claude to run a tool with a message containing spaces
- [x] Step 4: If the message stays intact, Fix #3 is done ✅

---

# MEDIUM PRIORITY FIXES

---

## Fix #4 — Remove packages we're not using 🟢 Easy
**From DEBUG_REPORT finding #4**

### What's the problem?
Imagine packing for a weekend trip, but you bring every piece of clothing you own
"just in case." Your suitcase is huge, heavy, and takes forever to pack and unpack.

Right now, `requirements.txt` lists ~12 packages that nothing in our code actually
uses. Every time someone installs this project, they download and install all of
them anyway — wasting time, disk space, and adding security risk.

### Packages to remove
These are not imported anywhere in the current code:

| Package | Why it's not needed yet |
|---------|------------------------|
| `selenium` | Browser automation — no scraping tools built yet |
| `beautifulsoup4` | HTML parsing — no scraping tools built yet |
| `lxml` | HTML parser — no scraping tools built yet |
| `pandas` | Data tables — not used in any current tool |
| `numpy` | Math operations — not used in any current tool |
| `openpyxl` | Excel files — not used in any current tool |
| `pytz` | Timezones — not used in any current tool |
| `python-dateutil` | Date parsing — not used in any current tool |
| `jsonschema` | JSON validation — not used in any current tool |
| `pyyaml` | YAML files — not used in any current tool |
| `colorlog` | Colored terminal output — not used |
| `openai` | OpenAI API — not used (we use Anthropic) |

### Files to change
- `requirements.txt`

### Steps
- [x] Step 1: Tell Claude "Do Fix #4 from the improvement plan"
- [x] Step 2: Claude removes the unused packages from `requirements.txt`
- [x] Step 3: Claude keeps a comment block at the bottom for packages to add later
- [x] Step 4: Verify nothing broke: `python tools/git_agent.py --action list-repos`
- [x] Step 5: Verify sheets still work: run a quick read from the sheet
- [x] Step 6: If both work, Fix #4 is done ✅

---

## Fix #5 — Add automatic retry when Google has a hiccup 🟡 Medium
**From DEBUG_REPORT finding #5**

### What's the problem?
Imagine you knock on someone's door, they don't answer, and you immediately give
up and go home. But what if they were just in the bathroom? If you had waited
10 seconds and knocked again, they would have answered.

We hit a `503 Service Unavailable` error from Google during this session.
The current code knocks once and gives up. A smarter version would wait a
moment and try again automatically — most 503s fix themselves in seconds.

### What we'll fix
Wrap the Google API call in a simple "try up to 3 times" loop with a short pause
between attempts. If it fails all 3 times, then show the error.

### Files to change
- `tools/google/write_to_sheets.py` (the `write_data` function)
- `tools/google/read_from_sheets.py` (the `read_data` function)

### Steps
- [x] Step 1: Complete Fix #2 first (shared auth module makes this easier)
- [x] Step 2: Tell Claude "Do Fix #5 from the improvement plan"
- [x] Step 3: Claude adds retry logic to both tools
- [x] Step 4: Test by running a normal write — it should work on the first try as usual
- [x] Step 5: The retry only kicks in during errors, so normal operation is unchanged ✅

---

## Fix #6 — Cell values with commas get split incorrectly 🟡 Medium
**From DEBUG_REPORT finding #6**

### What's the problem?
Our write tool uses commas to separate columns in a row.
So `"Hello,World"` means: put `Hello` in column A and `World` in column B.

But what if your data IS a sentence with a comma in it?
Like a commit message: `"fix: update config, remove old keys"`

The tool sees that comma and splits it into two cells: `fix: update config` and
`remove old keys`. Your data is now broken and spread across the wrong columns.

### What we'll fix
Add support for JSON-formatted data as an alternative input.
JSON uses `["cell1","cell2,with comma"]` syntax which handles commas inside values safely.
The simple comma format still works — this just adds a smarter option.

### Files to change
- `tools/google/write_to_sheets.py` (the `main` function)

### Steps
- [x] Step 1: Tell Claude "Do Fix #6 from the improvement plan"
- [x] Step 2: Claude adds a `--format` flag: `--format csv` (default) or `--format json`
- [x] Step 3: Test with a value containing a comma: `--data '[["hello, world","test"]]' --format json`
- [x] Step 4: Verify the comma stays inside the cell and doesn't split it ✅

---

## Fix #7 — Update the Anthropic package version 🟢 Easy
**From DEBUG_REPORT finding #7**

### What's the problem?
Imagine your phone is still running iOS from 2 years ago. Apps still work, but
newer features won't load and eventually things start breaking.

`requirements.txt` asks for `anthropic>=0.8.0` — a version from early 2024.
The current version is `0.40+` and has many improvements. The old minimum
means someone could install the outdated version and get errors when using
newer Claude API features.

### Files to change
- `requirements.txt` (one line change)

### Steps
- [x] Step 1: Tell Claude "Do Fix #7 from the improvement plan"
- [x] Step 2: Claude updates `anthropic>=0.8.0` to `anthropic>=0.40.0`
- [x] Step 3: Done ✅ (one line change, nothing to test unless you're calling the API directly)

---

# BONUS FIX (Low Priority)

---

## Fix #8 — Guard against empty directory path in read tool 🟢 Easy
**From DEBUG_REPORT finding #8**

### What's the problem?
A very small edge-case bug. If someone calls `read_from_sheets.py` with just a
plain filename (no folder), the code tries to create an empty folder name and crashes.

### Files to change
- `tools/google/read_from_sheets.py` (one line)

### Steps
- [x] Step 1: Tell Claude "Do Fix #8 from the improvement plan"
- [x] Step 2: Claude adds a one-line guard check
- [x] Step 3: Done ✅

---

# Summary Table

| Fix | Priority | Difficulty | Est. Time | Status |
|-----|----------|-----------|-----------|--------|
| #1 — Absolute token paths | 🔴 High | 🟢 Easy | 5 min | [x] |
| #2 — Shared auth module | 🔴 High | 🟡 Medium | 15 min | [x] |
| #3 — Fix arg splitter | 🔴 High | 🟢 Easy | 5 min | [x] |
| #4 — Trim requirements.txt | 🟡 Medium | 🟢 Easy | 5 min | [x] |
| #5 — Retry logic for Sheets | 🟡 Medium | 🟡 Medium | 15 min | [x] |
| #6 — Fix comma-in-values bug | 🟡 Medium | 🟡 Medium | 15 min | [x] |
| #7 — Update anthropic version | 🟡 Medium | 🟢 Easy | 2 min | [x] |
| #8 — Empty path guard | 🟢 Low | 🟢 Easy | 2 min | [x] |

**To start any fix:** Just tell Claude "Let's do Fix #[number] from the improvement plan."
