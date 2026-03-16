# Agent Instructions — n8n AI Agency

You help build, debug, and optimize n8n workflows for an AI agency. The WAT framework (Workflows, Agents, Tools) governs how this project is organized.

## The WAT Architecture

**Layer 1: Workflows (The Instructions)**
- Markdown SOPs stored in `workflows/`
- Each workflow defines objective, required inputs, which n8n workflow or tool to invoke, expected outputs, and edge case handling
- Don't create or overwrite workflows without asking — they're living instructions, not throwaway notes

**Layer 2: Agents (The Decision-Maker)**
- Your role: read the relevant workflow, orchestrate execution, handle failures, ask clarifying questions
- Don't try to do everything directly — offload to n8n workflows and Python tools

**Layer 3: Tools (The Execution)**
- Python scripts in `tools/` for deterministic tasks (Google Sheets, data transforms, file I/O)
- n8n handles automation, integrations, and AI orchestration
- Credentials and API keys live in `.env` — never anywhere else

## n8n Workflow Conventions

### Format
- Workflows are exported as JSON from n8n and stored in `workflows/n8n/` (create this dir as needed)
- Always keep a human-readable markdown SOP alongside the JSON (same base name)
- JSON filename pattern: `snake_case_workflow_name.json`

### Node naming
- Use descriptive names, not n8n defaults ("HTTP Request" → "Fetch Lead Data from Apollo")
- Prefix AI nodes: `AI: Classify Intent`, `AI: Draft Email`, `AI: Score Lead`
- Prefix utility nodes: `UTIL: Format Date`, `UTIL: Filter Empty Rows`

### Expressions
- n8n uses `{{ }}` for expressions. Key patterns:
  ```
  {{ $json.fieldName }}                          # current node output
  {{ $node["Node Name"].json.field }}            # reference another node
  {{ $items("Node Name") }}                      # all items from a node
  {{ $now.toISO() }}                             # current timestamp
  {{ $json.email.toLowerCase() }}                # transform inline
  ```
- For complex logic, use a Code node (JavaScript) rather than chaining expressions

### Error handling
- Every production workflow needs an Error Trigger workflow connected
- Use "Continue on Fail" on non-critical nodes, not as a blanket setting
- Log failures to a Google Sheet or send a Slack/email alert — never fail silently

### Sub-workflows
- Extract reusable logic into sub-workflows and call them via the Execute Workflow node
- Common sub-workflows to build: `normalize_contact`, `enrich_company`, `log_error`, `send_notification`

## AI Agency Workflow Patterns

### Lead generation
1. Trigger (webhook, schedule, or sheet watch)
2. Fetch leads from source (Apollo, Clay, LinkedIn scraper)
3. Enrich with AI (classify industry, score fit, extract intent signals)
4. Deduplicate against CRM
5. Write qualified leads to Google Sheets / CRM

### Outreach
1. Pull leads from pipeline sheet
2. AI: research company + personalize message
3. AI: draft email / LinkedIn message
4. Human approval step (wait for webhook or manual trigger) OR auto-send based on score threshold
5. Log sent + update CRM status

### Client reporting
1. Pull data from relevant sheets / APIs
2. Aggregate and compute KPIs
3. AI: write narrative summary
4. Populate Google Slides template or send formatted email

### Content creation
1. Input brief (webhook, sheet row, or form)
2. AI: expand outline → draft sections → review + refine
3. Format output
4. Push to destination (Notion, Google Docs, CMS API)

## Debugging n8n Workflows

**In n8n UI:**
- Use "Test Workflow" / "Execute Node" to run individual nodes with real data
- Pin node output data to test downstream nodes without re-running expensive steps
- Check execution logs at `/executions` — look at input/output of the failing node

**Common issues:**
| Problem | Likely cause | Fix |
|---|---|---|
| `Cannot read property X of undefined` | Node output is array, not object | Add an item loop or use `$items()` |
| Expression returns `[Object object]` | Missing `.json` accessor | Use `$node["X"].json.field` |
| Webhook not triggering | URL mismatch or missing activation | Check workflow is active, URL matches |
| Rate limit errors | No retry/backoff logic | Add Wait node + loop, or use queue mode |
| AI hallucinating wrong format | Prompt has no output schema | Add JSON schema to system prompt |
| Data lost between nodes | Wrong item index | Use `{{ $item(0).$node["X"].json }}` pattern |

**Before assuming n8n is broken:**
1. Check what data the previous node actually returned (click the node, inspect output)
2. Check credentials are valid and not expired (re-test the credential in n8n's credential manager)
3. On n8n Cloud, check execution logs at `/executions` — they show every node's input/output

## Working with This Codebase

### Python tools
- `tools/google/read_from_sheets.py` — pull data from Google Sheets
- `tools/google/write_to_sheets.py` — write data back
- `tools/example_tool.py` — template for new tools

### MCP servers
Two MCP servers are configured at user scope (`~/.claude.json`):

**WAT Framework** (`wat-framework`) — stdio transport
- Exposes Python tools and workflow docs to Claude directly
- Registered with: `claude mcp add --scope user wat-framework -- C:\Users\wm119\.local\bin\uv.exe run --with mcp[cli] python "C:\Users\wm119\OneDrive\Public\OneNote Documents\Agentic Workflow Demo\mcp_server.py"`
- Also defined in `.mcp.json` at project root as a fallback

**n8n Cloud** (`n8n`) — SSE transport
- Connects Claude directly to the n8n Cloud instance
- Endpoint: `https://gimbel.app.n8n.cloud/mcp-test/37562652-009e-444f-9577-427667bbb67e`
- Registered with: `claude mcp add --scope user --transport sse n8n <url>`
- Allows Claude to read and trigger n8n workflows from the conversation

To re-register either server if lost, run the commands above in a terminal.

### File structure
```
workflows/          # Markdown SOPs + n8n JSON exports
tools/              # Python execution scripts
.env                # API keys (never commit)
.tmp/               # Throwaway intermediates
mcp_server.py       # MCP server for WAT framework
```

## n8n Instance

- **Hosting**: n8n Cloud
- **Webhook base URL**: set in n8n Cloud dashboard under Settings → Webhook URL
- **Executions**: visible at `/executions` in the n8n UI; Cloud retains execution history per plan limits
- **Activation**: workflows must be **Active** (toggle top-right) for production triggers to fire; "Test Workflow" mode uses a different, temporary webhook URL

## Using Claude in n8n

Use **native Anthropic nodes** — not raw HTTP Request calls to the API.

**Setup (do this once):**
1. In n8n, go to **Credentials → New → Anthropic**
2. Paste the `ANTHROPIC_API_KEY` value
3. Save as "Anthropic account" (or any name you'll recognize)

**Nodes to use:**
| Goal | Node | Notes |
|---|---|---|
| Single prompt → response | **Basic LLM Chain** | Set model to `claude-sonnet-4-6` (latest capable) or `claude-haiku-4-5` (fast/cheap) |
| Multi-step reasoning + tools | **AI Agent** | Give it tools (HTTP Request, Google Sheets, etc.) and let it decide the steps |
| Classify / extract structured data | **Information Extractor** | Returns typed fields, not free text |
| Summarize / transform text | **Summarization Chain** | Good for long docs |
| Embed + search | **Vector Store nodes** | Pair with Pinecone or Supabase |

**Model selection guide:**
- `claude-sonnet-4-6` — default for most agency tasks (reasoning, drafting, analysis)
- `claude-haiku-4-5-20251001` — high-volume cheap steps (classification, scoring, formatting)
- `claude-opus-4-6` — complex reasoning or tasks where quality matters most

**Always set a system prompt** on any LLM node. Vague prompts produce inconsistent outputs at scale.

## Credentials Reference

Add keys to `.env` for Python tools. Common ones for AI agency work:
```
ANTHROPIC_API_KEY=
APOLLO_API_KEY=
INSTANTLY_API_KEY=
SLACK_WEBHOOK_URL=
GOOGLE_SHEETS_SPREADSHEET_ID=
```

n8n credentials (Anthropic, Google Sheets, Slack, etc.) are managed separately inside the n8n UI credential manager — not in `.env`. `.env` is only for the Python tools layer.

## Self-Improvement Loop

Every failure is a chance to make the system stronger:
1. Identify what broke (read the full error and node output)
2. Fix the workflow or tool
3. Verify the fix with test data
4. Update the relevant workflow SOP with what you learned
5. Move on with a more robust system

When you discover rate limits, API quirks, or n8n version-specific behavior — document it in the workflow. That's institutional memory.

## Bottom Line

You're the decision layer between what the agency needs and what actually gets executed. Read the workflow SOP first. Use existing tools before building new ones. Fix and document failures. Keep everything observable — no silent failures in production.
