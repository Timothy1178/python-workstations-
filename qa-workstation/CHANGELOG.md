# Changelog

Version lives in `version.py` and shows in the sidebar footer.
Bump rule: every **main update adds 0.1** (1.1.0 → 1.2.0); every
**bug fix adds 0.0.1** (1.1.0 → 1.1.1). Update this file in the same
change.

## 1.3.0 — 2026-09-14

- **Attachments in every chat box** (📎): attach documents (txt, md,
  csv, json, logs…), Excel workbooks (sheets are read inline), and
  images. Images are analysed by the local Claude CLI provider;
  Copilot agents are told what was attached. Unsupported binaries get
  a clear note instead of failing.
- **CSV Reader chat bot**: a Data Analyst chat box in the file viewer —
  counts, duplicates, anomalies, summaries over the open file, with
  🔎 Data quality check and 📊 Summarise quick actions.
- **QA Wiki chat bot**: an Ask-the-wiki chat box on the wiki index that
  answers from all pages and names the pages it used.
- New seeded wiki page + doc: **CSV Data Analyst Agent — setup guide**
  (`docs/copilot-csv-agent-setup.md`), the Copilot Studio role prompt
  for analysing tabular QA data.

## 1.2.0 — 2026-09-14

- **QA Wiki**: new module for the team's QA knowledge — Markdown pages
  organised by category and tags, full-text search, recently-updated
  list, live preview editor, and the shared agent chat box in the
  editor (paste a real document and the agent drafts the page; quick
  actions to organise a draft or list what's missing).
- Ships with a seeded page: the **Copilot Wiki Agent setup guide**
  (also in `docs/copilot-wiki-agent-setup.md`) — the role prompt for a
  Copilot Studio agent that creates wiki documentation from real
  documents and studies new ones to stay current.

## 1.1.0 — 2026-09-14

- **Copilot Agents**: live chat with Copilot Studio agents — via the
  Microsoft 365 Agents SDK (Direct Connect URL or Environment ID +
  schema name, Microsoft sign-in with optional tenant ID) or via a
  Direct Line web-channel secret (no Entra setup).
- **Test case builder**: chat box gets an agent selector (local Claude
  CLI or any connected Copilot agent, remembered across pages), a
  one-click **Review test cases** action, and auto-growing cells so
  long wording shows in full while editing.
- **Shared chat component**: any module can add an agent-assisted chat
  box with one `initChatBox()` call backed by
  `modules/agents/service.py`.
- **CSV reader**: paste text (comma / tab / semicolon / pipe separated,
  auto-detected) and convert it to a CSV file.
- **Fixed**: the builder's assistant chat box could not be closed
  (`display: flex` overrode the `hidden` attribute); Escape now also
  closes it.

## 1.0.0

- Initial QA workstation: test case builder and run viewer with Claude
  CLI assist and Excel export, CSV record reader, Copilot agent roster.
