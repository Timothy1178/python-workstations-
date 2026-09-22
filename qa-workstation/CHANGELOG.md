# Changelog

Version lives in `version.py` and shows in the sidebar footer.
Bump rule: every **main update adds 0.1** (1.1.0 → 1.2.0); every
**bug fix adds 0.0.1** (1.1.0 → 1.1.1). Update this file in the same
change.

## 1.8.0 — 2026-09-22

- **Test case builder — 🖼 Evidence column**: attach multiple images to
  any case by pasting (Ctrl/Cmd+V — e.g. straight from the screen cap
  plugin's 📋), dropping files or plugin thumbnails onto the row, or
  picking several files. Thumbnail strip with hover-delete and a
  lightbox (←/→ to browse, Esc to close). Images are stored with the
  case and shared with the run viewer.
- **Excel export — clearer evidence worksheet**: the ScreenCap sheet
  gets a shaded band per case with the image count, numbered captions
  under each image, and each SIT row's Case ID is a hyperlink to its
  evidence block, with an "↑ back to SIT" link beside it. Display size
  capped at 1000 px wide; embedded pixels stay full resolution.
- **Multi Screen Cap v1.2.0 — clearer captures**: 🔍 quality setting
  (Auto / 2× HD / 3× Ultra) renders captures at higher resolution via
  the browser's DevTools screenshot API, so they stay crisp when
  enlarged in Excel or the test plan (Chrome shows a brief "debugging"
  bar during HD capture; falls back to normal capture where the API is
  unavailable). Thumbnails now drop into web pages as real files (the
  builder's Evidence cell accepts them), and previews open in a proper
  viewer page with actual-size / copy / save.

## 1.7.2 — 2026-09-14

- **Privacy fix**: the whole `data/` folder is now gitignored and the
  previously committed demo data (test plans, screenshots, CSV samples,
  CSV settings, seeded wiki JSON) is untracked — no test case data,
  wiki content, settings or secrets can be pushed to GitHub. The two
  starter wiki guides are auto-seeded from the tracked `docs/` files on
  first run (delete `data/wiki/.seeded` to re-seed).

## 1.7.1 — 2026-09-14

- **Security fix**: `data/agents.json` (which holds Direct Line
  web-channel secrets for registered agents) and
  `data/chat_assignments.json` are now gitignored, so agent secrets can
  never be committed and pushed to GitHub by accident. Nothing secret
  was ever in the repository's history — this closes the future risk.

## 1.7.0 — 2026-09-14

- **Per-page agent assignments**: the Copilot Agents page gets a "Chat
  box assignments" table — pick which agent answers each chat box
  (builder, CSV viewer/index, wiki index/editor) and it is applied
  automatically when that chat box opens; testers can still switch in
  the dropdown for one session.
- **CSV Reader reads JSON**: upload a .json file (array of objects, or
  one object) and browse it as records; nested values stay as JSON
  text; export back with the new 📥 JSON button. New ⤢ **preview
  editor** on every text field: edit long values in a large window,
  pretty-print JSON, and decode/re-encode XML-entity payloads (e.g.
  `playloadJson` transaction strings) — modelled on the old
  Transaction String Editor.
- **Dark mode**: 🌓 toggle in the sidebar, remembered per browser and
  defaulting to the OS preference; the whole UI (cards, tables, chat
  boxes, wiki content, editors) is themed via CSS variables.

## 1.6.0 — 2026-09-14

- **Multi Screen Cap v1.1.0**: 🗔 floating capture window that stays
  open while you work — drag thumbnails straight into Excel, a folder,
  or the workstation's 📎 chat box, or 📋 copy & paste them; the
  selected capture area is saved, so ↻ / Alt+Shift+A re-captures the
  same spot without dragging; gallery keeps the last 10 captures
  (oldest drops off); ⌨️ button opens the browser's shortcut settings
  to rebind the keys.

## 1.5.0 — 2026-09-14

- **Web Plugins**: new module listing browser extensions (Chrome & Edge)
  with feature lists, install steps, and one-click .zip download; each
  plugin is an unpacked MV3 extension under `plugins/<slug>/` with a
  `plugin.json` describing it.
- First plugin — **QA Multi Screen Cap**: capture the visible page or a
  drag-selected area (Esc cancels; Alt+Shift+F / Alt+Shift+S), collect
  up to 100 captures in a popup gallery across pages and tabs, save one
  or all at once into Downloads/screencaps/, toolbar badge shows the
  count.

## 1.4.0 — 2026-09-14

- **CSV cleaning agent**: ask the viewer's Data Analyst chat to clean a
  file (🧹 quick action) — the cleaned table is saved as a new
  `<name>-cleaned.csv` next to the original, never overwriting it. The
  CSV Reader index gets its own assistant that cleans pasted or
  attached data straight into a new CSV file. Visible 🤖 chat buttons
  on both pages; cleaning contract added to the CSV agent wiki guide.
- **Fixed**: the 📎 button did not open the file explorer (the Send
  handler was bound to the wrong button in the chat input row).
- **Fixed**: layout now fits the browser window — content uses the full
  width (1300px cap removed), wide tables scroll inside their cards
  instead of stretching the page, and narrow windows get a top-bar
  layout with a full-width chat panel.

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
