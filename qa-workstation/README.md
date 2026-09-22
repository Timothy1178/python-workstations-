# QA Workstation

A local Python (Flask) workstation for day-to-day QA testing. Each tool is a
module under `modules/` — any folder exposing a Flask blueprint (`bp`) and a
`MODULE_INFO` dict is auto-registered on the sidebar and home page, so new
functions plug in without touching the core.

## Run it

```bash
cd qa-workstation
pip3 install -r requirements.txt
python3 app.py
```

Open **http://127.0.0.1:5010**.

## Versioning

The version lives in `version.py` and shows in the sidebar footer
(currently starting from 1.1.0). Every **main update adds 0.1**
(1.1.0 → 1.2.0); every **bug fix adds 0.0.1** (1.1.0 → 1.1.1). Each
bump gets an entry in [CHANGELOG.md](CHANGELOG.md).

## Modules

- **Test Cases** (`modules/testcases/`) — template-driven test case builder
  and a test-run viewer. The columns come from `data/template.json`; replace
  it with your own template to change the layout, no code changes needed.
- **QA Wiki** (`modules/wiki/`) — the team's knowledge base: Markdown
  pages with categories, tags and search, plus an agent-assisted editor
  (paste a real document, the agent drafts the page). See
  [docs/copilot-wiki-agent-setup.md](docs/copilot-wiki-agent-setup.md)
  for the wiki-librarian agent prompt.
- **Web Plugins** (`modules/plugins/`) — browser extensions for QA work,
  downloadable as zips and loaded unpacked into Chrome/Edge. Extensions
  live under `plugins/<slug>/`: **QA Multi Screen Cap** (multi-shot
  screenshots with area selection, sends evidence to the current test
  case) and **AIMAS Recaller** (record, edit and replay web form
  fill-ins, incl. search-select dropdowns and date pickers).
- **Copilot Agents** (`modules/agents/`) — roster of Copilot Studio agents
  with live chat through the Microsoft 365 Agents SDK
  (`microsoft-agents-copilotstudio-client`). Each registered agent gets a
  💬 Chat page that talks to the published agent.

## Connecting a Copilot Studio agent

### Option A — web channel secret (Direct Line, no Entra setup)

1. In **Copilot Studio**: *Settings → Security → Authentication* →
   **No authentication**, then republish the agent.
2. Copy **Secret 1** from *Settings → Security → Web channel security*.
3. Paste it into the secret field when registering the agent — done.
   Note: anyone holding the secret can chat with the agent, and it no
   longer knows who the tester is.

### Option B — M365 Agents SDK (Microsoft sign-in, authenticated agents)

One-time setup per tenant, then fill the connection fields on the
Copilot Agents page:

1. In **Copilot Studio**, publish the agent, then either copy its
   **Direct Connect URL** (the
   `…environment.api.powerplatform.com/copilotstudio/…/conversations…`
   link — paste it as-is), or the **Environment ID** and **schema name**
   from *Settings → Advanced → Metadata*.
2. In **Entra ID**, create (or reuse) an app registration:
   - platform *Mobile and desktop applications* with the
     `http://localhost` redirect URI;
   - delegated **Power Platform API** permission
     `CopilotStudio.Copilots.Invoke`, admin-consented.
   Copy the app's **client ID** (and optionally the **tenant ID** — leave
   it blank to sign in with any work/school account).
3. Open the agent's 💬 Chat page. On first use a browser window opens for
   Microsoft sign-in; the token is cached in
   `data/msal_token_cache.json` after that.

## Data

Everything is stored as JSON under `data/` — the folder is the app *and*
your data; copy it to move machines.

- `data/template.json` — test case template (builder columns + run fields)
- `data/plans/*.json` — test plans and their cases/results
- `data/agents.json` — registered Copilot agents

## Agent-assisted chat box in any module

The assistant chat box is a shared component, used in the test case
builder, the CSV viewer, and the QA Wiki. The dropdown in its header
picks who answers: the local Claude CLI or any connected Copilot agent.
The 📎 button attaches files: documents and Excel workbooks are read
into the conversation for every provider; images are analysed by the
Claude CLI provider (Copilot agents are told what was attached).
To add the same chat box to a new tool:

1. Backend: build a prompt and call
   `modules.agents.service.complete(provider_id, prompt)` from your
   route (see `modules/testcases/assist.py`), passing through the
   `provider` field of the request body.
2. Frontend: include `static/chatbox.js` and call
   `initChatBox({title, greeting, endpoint, buildContext, onReply})`
   (see `templates/testcases/builder.html`). The provider dropdown,
   history, and open/close handling come for free.

## Adding a new module

1. Create `modules/<name>/__init__.py` with a Flask `Blueprint` named `bp`
   and a `MODULE_INFO = {"name", "url", "desc", "icon"}` dict.
2. Put its pages in `templates/<name>/`.
3. Restart the app — it appears on the sidebar automatically.
