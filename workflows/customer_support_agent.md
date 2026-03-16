# Customer Support Agent — Gadgets & More Electronics

## Objective
Poll the support Gmail inbox every 15 minutes, classify each new email using AI to determine if it's a customer support question (returns, warranties, repairs, exchanges, billing, shipping, or store policies), then use the embedded Gadgets & More policy knowledge base to generate a draft reply — placed in Gmail Drafts for human review before sending.

## Required Inputs
- **Gmail account**: OAuth2 credential authenticated to the support inbox
- **Anthropic account**: API key credential (for classification + draft generation)

## Tools Used
- `n8n-nodes-base.gmailTrigger` — polls Gmail inbox for unread emails every 15 minutes
- `@n8n/n8n-nodes-langchain.chainLlm` — AI classification and draft generation
- `@n8n/n8n-nodes-langchain.lmChatAnthropic` — Anthropic model sub-nodes
- `n8n-nodes-base.code` — parses classification JSON and extracts email fields
- `n8n-nodes-base.if` — routes support emails vs. unrelated emails
- `n8n-nodes-base.gmail` — creates draft reply in Gmail

## Policy Knowledge Base

Policies are embedded directly in the AI draft node's combined prompt (sourced from `faqs.pdf` and `policies .pdf`):

| Topic | Key Details |
|---|---|
| Returns | 30-day window; FREE shipping if wrong/defective/damaged; customer pays for change-of-mind; 15% restocking fee on non-defective |
| Refunds | 5–10 business days to original payment method |
| Warranties | New: 1-yr manufacturer + 30-day GadgetHub guarantee; Refurbished: 90-day GadgetHub only; void if misused |
| Shipping | Standard 3–7 days (free on $99+); Express 1–3 days (fee); tracking within 24 hrs |
| Billing | Rewards $9.99/mo, cancel anytime; duplicate charges refunded in 48 hrs |
| Gift Cards | Never expire; no cash value |
| Pricing | No post-purchase price matching; promo codes + gift cards usually can't be combined |

## Setup (one-time)

### 1. Configure n8n credentials
- **Gmail**: Credentials → New → Gmail OAuth2 → authenticate with the support inbox account
- **Anthropic**: Credentials → New → Anthropic → paste the `ANTHROPIC_API_KEY` value from `.env`

### 2. Import the workflow
1. In n8n: Workflows → Import → select `workflows/n8n/customer_support_agent.json`

### 3. Fix the AI nodes manually (required after every import)
n8n does not reliably import prompts or sub-node connections for LangChain nodes. After importing, you must fix these manually:

**AI: Classify Support Topic — set the prompt:**
1. Double-click the node → Source for Prompt → select **"Define below"**
2. Paste this into the prompt field:
   ```
   ={{ 'Subject: ' + ($json['Subject'] || '') + '\n\nBody:\n' + ($json['snippet'] || '').substring(0, 1000) }}
   ```
3. Delete any entries in the Chat Messages section — leave it empty

**AI: Draft Customer Reply — set the combined prompt:**
1. Double-click the node → Source for Prompt → select **"Define below"**
2. Paste this into the prompt field:
   ```
   You are a friendly customer support agent for Gadgets & More Electronics. Use only these policies to answer — never invent policies not listed:

   RETURNS: 30-day window. Free shipping if wrong/defective/damaged. Customer pays for change-of-mind returns. Refund in 5-10 business days. 15% restocking fee on non-defective returns.
   WARRANTIES: New items: 1-year manufacturer + 30-day GadgetHub guarantee. Refurbished: 90-day only. Void if misused.
   SHIPPING: Standard 3-7 days (free over $99). Express 1-3 days (extra fee). Tracking within 24 hours.
   BILLING: Rewards $9.99/month, cancel anytime. Duplicate charges refunded in 48 hours.
   GIFT CARDS: Never expire. No cash value.
   PRICING: No price matching after purchase.

   Be warm, concise (under 200 words), and sign off as "The Gadgets & More Support Team".

   Customer: {{ $json['From Name'] }}
   Topic: {{ $json['topic'] }}
   Email: {{ $json['Body'] }}
   ```
3. Delete any entries in the Chat Messages section — leave it empty

**Reconnect both Anthropic Chat Model sub-nodes:**
1. Delete the "Anthropic Chat Model (Classify)" circle on the canvas
2. Hover over **"AI: Classify Support Topic"** on the canvas → click the **"Model\*"** dot at the bottom → select "Anthropic Chat Model" → set credential and model
3. Repeat for **"AI: Draft Customer Reply"** using "Anthropic Chat Model (Draft)"
4. Use the same model for both — whichever is available on your Anthropic account

### 4. Connect credentials on each node
- Gmail Trigger → Gmail account
- Anthropic Chat Model (Classify) → Anthropic account
- Anthropic Chat Model (Draft) → Anthropic account
- Gmail: Create Draft Reply → Gmail account

### 5. Test and activate
1. Open the Gmail Trigger node → click **"Fetch Test Event"** → send a test email to yourself ("I want to return my headphones")
2. Click **"Test Workflow"** — confirm a draft appears in Gmail Drafts
3. Toggle the workflow to **Active**

## Process

### Step 1: Gmail Trigger: Customer Support Inbox
**Action**: Poll Gmail every 15 minutes using filter `in:inbox is:unread`. Each new email becomes one workflow item.
**Key output fields** (Simplify ON):
- `Subject` — email subject line (capital S)
- `From` — sender as plain string e.g. `"William Martin <william@example.com>"`
- `snippet` — first ~200 chars of email body (NOT `text` — that field is absent when Simplify is ON)
- `threadId` — for reply threading
- `id` — unique message ID

### Step 2: AI: Classify Support Topic
**Action**: Send subject + first 1,000 chars of snippet to Claude (haiku-class model). Prompt instructs model to respond with ONLY a JSON object:
```json
{"is_support_topic": true, "topic": "return"}
```
Valid topics: `return`, `warranty`, `repair`, `exchange`, `billing`, `shipping`, `policy`, `unrelated`
**Important**: No system messages — put all instructions in the single user prompt field

### Step 3: UTIL: Parse Classification
**Action**: Code node extracts the JSON from the LLM response and pulls all email fields directly from the Gmail Trigger node output:
```javascript
const raw = $input.first().json.text;
const match = raw.match(/\{[\s\S]*?\}/);
if (!match) throw new Error('Could not parse JSON. LLM returned: ' + raw);
const parsed = JSON.parse(match[0]);

const gmailData = $node['Gmail Trigger: Customer Support Inbox'].json;
const fromStr = gmailData['From'] || '';
const fromEmailMatch = fromStr.match(/<(.+)>/);
const fromNameMatch = fromStr.match(/^(.+?)\s*</);

return [{ json: {
  ...parsed,
  'From Email': fromEmailMatch ? fromEmailMatch[1] : fromStr,
  'From Name': fromNameMatch ? fromNameMatch[1].trim() : fromStr,
  'Subject': gmailData['Subject'] || '',
  'Body': gmailData['snippet'] || '',
  'Thread ID': gmailData['threadId'] || '',
  'Message ID': gmailData['id'] || ''
}}];
```

### Step 4: UTIL: Route Support Emails
**Action**: IF node checks `$json.is_support_topic === true`
- True → draft generation
- False → workflow ends silently

### Step 5: AI: Draft Customer Reply
**Action**: Single combined prompt (policies + instructions + customer data) sent to Claude sonnet-class model. Everything in one user message — no separate system message.
**Output**: `$json.text` = ready-to-send email reply body

### Step 6: Gmail: Create Draft Reply
**Action**: Creates a Gmail draft threaded to the original email
- To: `$node['UTIL: Parse Classification'].json['From Email']`
- Subject: `Re: [original subject]`
- Body: `$json.text` (AI-generated reply)
- Thread: linked via threadId

## Expected Outputs
- **Gmail Drafts**: One draft per qualifying support email, ready for human review
- **Unrelated emails**: Silently skipped
- **n8n Execution log** (`/executions`): Full node-by-node input/output for debugging

## Edge Cases

### HTML-only email (no plain text)
**Problem**: `snippet` may be empty for some email types
**Solution**: The `|| ''` fallback prevents errors; AI will draft a generic response asking the customer to resend their question
**Prevention**: No action needed — snippet is almost always populated

### LLM returns malformed JSON
**Problem**: Classification step returns JSON wrapped in markdown or with extra text
**Solution**: The regex `/{[\s\S]*?}/` extracts the first JSON object found regardless of surrounding text
**Prevention**: System prompt explicitly says "respond with ONLY a JSON object"

### Unrelated emails processed unnecessarily
**Problem**: Newsletters, promotions, and spam all trigger the workflow
**Solution**: IF node filters them at Step 4 — no draft is created
**Prevention**: Add a Gmail label or upstream filter (e.g. only process "Support" labeled emails) to reduce noise and API costs

### Anthropic model not available (404 error)
**Problem**: Selected model returns "The resource you are requesting could not be found"
**Solution**: Delete the Anthropic Chat Model sub-node and re-add it from the Model* canvas connection point; try a different model from the dropdown
**Prevention**: Use whichever model shows no error when you click "Test credential" — do not type model IDs manually

### Duplicate model fields after editing
**Problem**: Editing an Anthropic sub-node after import can create duplicate Model fields, causing 404 errors
**Solution**: Delete the sub-node entirely and re-add it fresh from the canvas
**Prevention**: Always add sub-nodes from the canvas Model* connection point rather than relying on JSON import

### System message ordering error
**Problem**: "System messages are only permitted as the first passed message"
**Solution**: Delete all entries from the Chat Messages section; put system instructions directly into the user prompt field as one combined message
**Prevention**: Never use the Chat Messages section for system prompts in chainLlm nodes

## Error Handling
Per agency conventions, connect a companion Error Trigger workflow:
1. Create a new n8n workflow → add Error Trigger node
2. Add a Slack or email notification node
3. In this workflow: Settings → Error Workflow → select the error workflow

## Learnings

**Gmail Trigger Simplify=ON output format**: The `From` field is a plain string like `"Name <email@domain.com>"` — not a structured object. Use regex to extract name and email. The body field is `snippet`, not `text`. `text` is absent when Simplify is ON.

**LangChain node JSON import limitations**: Prompt fields, Chat Messages, and sub-node connections do not import reliably from JSON. Always set prompts manually via "Define below" after import. Always delete and re-add sub-nodes from the canvas.

**System message ordering**: n8n's chainLlm node sends the user prompt before chat messages, causing "system messages only permitted as first" errors. Solution: put all instructions (system + user) into a single combined user prompt. No separate system messages needed.

**Sub-node connection corruption**: Editing Anthropic sub-nodes after import can create duplicate parameter fields. If you see duplicate Model fields or persistent 404 errors on a sub-node, delete it and recreate it fresh from the canvas Model* connection point.

**Model availability**: Not all Anthropic models are available on all account tiers. If a model returns 404, try another from the dropdown. The model that works for the Classify node will work for the Draft node too.

**Updated**: 2026-02-26
**Version**: 1.1
