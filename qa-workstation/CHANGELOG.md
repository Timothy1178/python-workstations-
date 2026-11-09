# Changelog

Version lives in `version.py` and shows in the sidebar footer.
Bump rule: every **main update adds 0.1** (1.1.0 → 1.2.0); every
**bug fix adds 0.0.1** (1.1.0 → 1.1.1). Update this file in the same
change.

## 1.22.1 — 2026-11-09

- **TLog CSV set: output now matches the valid WTCID batch set byte for
  byte** (`ORDER_WTCID_202604281544`), so the batch import accepts it.
  What was wrong and is fixed: file names now carry a 12-digit
  `YYYYMMDDHHMM` stamp with no sequence (`{TYPE}_{BU}_{YYYYMMDDHHMM}`;
  8- and 14-digit stamps and `_SEQ` still import), the marker files are
  `.OK` (upper case, configurable), **empty files are 0 bytes** instead
  of a CRLF, the default column set is the batch one — ORDER 30 columns
  (no X_STF_DISCNT_PROCESS_FLG / SubClub block), ORDERITEMS 26 (no staff
  discount / tax columns), ORDER_PAYMENT 12, ORDERITEMS_PROMOTION 14 —
  amounts are written with 2 decimals and quantities as typed (no more
  `1.000000000` / `0E-9`), and Order Number for Conversion (all files)
  and External Transaction Key default to the ERP Order Number instead of
  a reference-base counter. The full spec v1.3 layout (55 / 29 columns,
  4-decimal amounts) is kept as a preset in ⚙️ Layout, which also gets
  the `.OK` extension and empty-file options. A layout saved with the old
  defaults is migrated automatically; customised layouts are kept.

## 1.22.0 — 2026-11-08

- **Test Cases · 🎛 Studio** — a second editor for the same plans at
  `/testcases/plan/<id>/studio`, now the default when a plan is created or
  imported (the ☰ Table builder stays one click away, and both export the
  unchanged Excel template). One case at a time: a grouped case list by
  Testing BU with search, drag-to-reorder, checklist dots, evidence counts
  and run results; a focused form with a big case title, BU with
  suggestions, a **step editor** (one box per step, Enter adds the next,
  Backspace removes an empty one, Alt+↑/↓ reorders, Text mode for free
  typing, numbering added on save), a "1-2-3 number lines" helper for
  expected results, auto-growing fields and an evidence gallery that takes
  paste / drop / picker and the screen-cap plugin; an inspector with a
  **quality checklist** (BU, name, steps present and concrete, expected
  result, test data / campaign ID when the steps call for them — click an
  unticked item to jump to the field), position controls, the run result
  and shortcuts; plan stats (cases, BUs, % complete, evidence, executed);
  **autosave** 1.5 s after a change (toggle) plus Ctrl+S; **🧰 Tools**
  with find & replace (per field or all, match case, count first), fill
  / set Testing BU, renumber all steps, sort by BU, remove empty cases;
  the same Import Excel / CSV dialog and the assistant with
  case-aware quick actions (review this case, add negative cases, review
  the whole plan). Case numbering, saving and the export are the same
  code paths as the table builder.

## 1.21.0 — 2026-11-05

- **TLog editor built on the full Sales_Transactions v1.3 workbook.**
  `modules/tlog/tlog_spec.json` is regenerated from the spec: every column
  now carries the sheet's comments, the WTCCN mapping guidance, the POS
  source field and the Retail HK sample value (shown on hover and in the
  new **📖 Spec** panel, which lists each file's fields next to the
  editor's column name, default, auto rule and LOV, plus a *Rules &
  formats* tab, the *Payment mapping* tables from the Order Payment sheet
  and the *Cancel Order* feed for reference).
- **ORDER_XM** (TSR / Lucky Draw account values, sheet *Order XM*) is the
  optional 5th file: an *Account values* table per transaction; the file
  and its `.ok` are added to the zip when a transaction has account lines
  or the toggle in *File set* is on; import accepts it.
- **Tender ↦ picker** on payment lines: pick a POS tender from the WTCTW /
  WTCCN mapping tables (or a common pair) and Payment Method + Payment
  Type are filled with LOV-valid values.
- **Spec business rules in Validation**: member cards must carry the 991
  prefix and non-member orders leave the four member fields empty
  (programme names are now derived only when a card is present); Points
  Earned ≥ Bonus Points Earned; Customer / Business Order Date not in the
  future (they are UTC); Total Amount vs item net prices; unique Order
  Line Numbers and payment Sequence Numbers (1, 2, 3 …); positive
  quantities, no negative cancelled quantity or discounts; fixed values
  (`=PromotionID`, `=Account`) as inline LOVs usable in the Layout editor;
  promotion lines that do not match an item line are listed as a note.

## 1.20.1 — 2026-11-05

- **TLog CSV set: imports sets without a sequence number.** A WTCID set
  named `ORDER_WTCID_20261102.csv` (no `_SEQ`) was rejected with
  "no ORDER_<BU>_<YYYYMMDD>_<SEQ>.csv in the upload" because the file-name
  parser insisted on the `_SEQ` part even though export had already made
  it optional. `_SEQ` is now optional on import too; the WTCID set loads
  as 1 transaction (2 items, 3 payments, 24 promotions), all four files
  match the spec column counts (55 / 29 / 12 / 14) and the zip
  round-trips byte for byte.

## 1.20.0 — 2026-11-04

- **Timestamp Converter** (`/timestamp`, ⏱ in the sidebar). UTC+8 ⇄ UTC ⇄
  epoch in one page: paste an epoch in seconds / milliseconds /
  microseconds / nanoseconds (auto-detected by digit count, overridable),
  an ISO 8601 string, `YYYY-MM-DD HH:mm[:ss]`, `YYYY/MM/DD …`, or a compact
  `YYYYMMDD[HHmmss]`, and every form is listed with a copy button: local
  zone, UTC, epoch s / ms / µs, ISO (+08:00 and Z), the TLog CSV
  `YYYY/MM/DD HH:MM:SS` UTC form, date / time only, compact, weekday / ISO
  week / day of year and "relative to now". **Quick buttons**: Now (with a
  live, ticking mode), Today 00:00, Today 23:59:59, Tomorrow, Yesterday,
  this Monday, month start / end, ±1 d / ±1 h / ±15 m / ±1 m nudges and
  round to second / minute / hour / day; a date-time picker in the local
  zone. **Display settings** with presets — with / without seconds, with
  milliseconds, TLog style (slashes), ISO 8601 style, 12-hour — plus
  separator, "T", zone suffix, weekday, local zone (UTC+8 / +7 / +9 /
  +5:30 / UTC) and how zone-less typed dates are read. **Custom formats**
  (token patterns, local or UTC) and a **Batch** tab that converts one
  value per line, log lines included, into any output form. Settings,
  formats and the recent list live in the browser's localStorage; nothing
  is written on the server.

## 1.19.0 — 2026-11-02

- **TLog CSV set rebuilt on the real spec.** Columns now follow
  *RetailHK – Sales_Transactions v1.3* (field names, types, max lengths,
  required flags, LOVs) in the column order of the sample files
  (`modules/tlog/tlog_spec.json`, editable in ⚙️ Layout): ORDER 55
  columns incl. the SubClub block, ORDERITEMS 29, ORDER_PAYMENT 12,
  ORDERITEMS_PROMOTION 14. Shared per transaction: Card Number,
  Customer Order Date, Store ID, POS Number, Customer / ERP Order
  Number, Organization (BU) Name. **Derived values fill blank cells**
  and typed values always win: BU → Organization (BU) Name / for
  Member, Program Name = BU + " Membership", Member Number = card
  without the 991 prefix, Store Name = "05" + Store ID, Tax Exempt /
  X_STF flags = N, totals, line numbers, references. Every input shows
  the spec hint and type / length / LOV on hover. **Validation card**:
  required fields, number and `YYYY/MM/DD HH:MM:SS` (UTC) formats, max
  lengths, Payment Method / Payment Type LOVs (spelling warnings), empty
  item / payment lines and payments ≠ items net, with click-to-jump and
  red / amber field marks; the zip warns before exporting with errors.
  BU picker with the known BU codes, sequence optional in file names,
  Msg5 fill converts HK times to UTC (−8 h) and maps Business Date.
  The sample set still round-trips byte for byte.

## 1.18.0 — 2026-11-01

- **Msg5 Json merged into TLog Handler.** The two pages overlapped; the
  only feature the TLog Msg5 request tab lacked — 📂 **Load from file**
  (open a message from an Excel cell, CSV, Word doc, .json or .txt
  without saving it, with a chooser when a file holds several and
  "Save all as templates") — is now on the TLog tab. The Msg5 Json page
  is retired: `/msg5` redirects to `/tlog`, and on first visit its
  saved messages become TLog library requests and its custom edit-box
  fields join the TLog config (group "Msg5"), together with the
  auto-increment toggle. Note: an Excel cell holds at most 32,767
  characters, so longer messages (e.g. the WTCID / WTCTH samples) must
  be kept in .docx / .json / .txt rather than Excel.
- **New module — 📑 Doc & PPT Templates**: a file holder for Word,
  PowerPoint, Excel, PDF and text templates. Drag-and-drop upload with
  tags and notes, kind filter and search, cards with open / download /
  rename / tags / notes / delete. Files live flat in `data/templates/`
  (gitignored) and the folder is scanned on every view, so templates
  the assistant generates — via `modules.doctemplates.store_file()` or
  by writing into the folder — appear without an upload.

## 1.17.0 — 2026-11-01

- **TLog Handler — 🗂 TLog CSV set** (second tab): one editor for the
  four TLog files ORDER / ORDER_PAYMENT / ORDERITEMS /
  ORDERITEMS_PROMOTION. A **transaction** is entered once: the shared
  fields (member card, date-time, store, till, transaction number,
  receipt, BU) are copied into every row of every file; the ORDER-only
  fields, item lines, payment lines and promotion lines sit under it.
  Auto columns: line numbers, order / line references (reference base
  + type code + transaction index), order total = Σ item net, item
  count, net = price × qty when blank, payment amount = total when
  blank; number formats per column (3 / 4 / 9 decimals). **📨 Add from
  Msg5** builds a transaction from a library message or a pasted JSON
  through the layout's Msg5 mapping (shared fields, items from Item,
  payments from Tender, promotions from TransactionDetailLine).
  **📦 Download zip** writes the 4 CSVs in the template format (every
  field quoted, CRLF rows, empty file = one CRLF) plus the 4 same-named
  empty `.ok` files, named `{TYPE}_{BU}_{YYYYMMDD}_{SEQ}`; the
  reference set round-trips byte for byte. Live per-file preview with
  copy, import an existing set (4 CSVs or a zip) into transactions,
  save / update / delete named sets. **⚙️ Layout**: the template has no
  header row, so the column names are best guesses — rename, set
  defaults, formats, auto rules, reference codes and Msg5 tags per
  column, add / remove / reorder columns, reset to defaults; saved in
  `data/tlog/csv_layout.json`.

## 1.16.0 — 2026-11-01

- **Msg5 Json — 📂 Load from file**: open the message straight from an
  Excel workbook (every text cell of every sheet is scanned, the name
  comes from the row's title cell), a CSV, a Word doc, .json or .txt.
  One message loads directly; several open a chooser (name, sheet /
  cell, BU · type · id, size) with ⬇ Load per row and 💾 Save all to
  library.
- **Msg5 Json — message keys as fields**: the ⚙️ Edit box fields picker
  now lists the JSON's own keys (type, buCode, timestamp…) beside the
  payload tags; a key field edits the JSON directly, with an `epochms`
  type that shows a 13-digit timestamp as a date-time picker. Source
  (key / tag) is shown and editable in the fields table.
- **TLog Handler import** accepts .xlsx / .xlsm / .csv too (same shared
  reader, `modules/msgfiles.py`).

## 1.15.0 — 2026-11-01

- **New module — 📨 TLog Handler (create msg5)**: editor for the
  `UPDATE_TRANSACTION_STOCK_FROM_MSG5` function-call messages sent
  through Offset Explorer. **BU library**: drop the BU documents
  (.docx / .json / .txt, several at once) and each message becomes a
  template, grouped by BU code read from the message; saved requests
  live beside them (save as new / update / delete / filter). **Fields**
  grouped as Message (type, BU code, timestamp as a date-time picker),
  Transaction (store, retailer incl. the element attribute, business /
  period dates, transaction number, external reference, till, cashier,
  start / end, LPE server), Customer (club card, club id) and Flags
  (0/1 selects); ⚙️ Edit box fields adds any message key or payload tag
  (picked from the loaded message) with label / type / group, saved in
  `data/tlog/config.json`. **Items & tenders** tables: edit item ID,
  unit price, quantity (extended amount follows), tender ID and amount,
  add or remove lines (sequence numbers renumbered), Σ Recalculate sets
  ExtendedAmount, TotalAmount, ItemsNumber and a single tender amount.
  Toggles: New UUID → transaction number +1, Generate → timestamp now,
  Generate → recalc totals; 📅 Dates → today. Output is the one-line
  string for Offset Explorer with Copy / Download / Use as source and
  the decoded XML preview. All data under `data/tlog/` (gitignored).

## 1.14.0 — 2026-10-21

- **New module — 🧾 Msg5 Json**: the Transaction String Editor as a
  workstation page. Paste the transaction JSON (`playloadJson` XML
  payload), load its fields, edit, generate the updated string, copy /
  download / decoded-XML preview, "use as source" to keep iterating.
  **Auto +1**: with the 🔢 toggle on (saved in the config), pressing
  New UUID also raises the transaction number by one. **Saved
  messages**: name and save any JSON (the generated one if present),
  reload it later, update in place or save as a copy, notes, filter,
  delete — stored in `data/msg5/messages/`. **Edit box fields**: pick
  any tag from the loaded payload (listed with its value) or type one,
  give it a label / type (text, number, date, datetime) / required /
  every-occurrence / insert-after-tag, and it becomes an input in the
  Fields box from then on; reorder, edit or remove fields, reset to
  the defaults — all saved in `data/msg5/config.json` (gitignored).

## 1.13.0 — 2026-10-13

- **Test case builder — 📂 Import Excel / CSV**: bring test cases in
  from any workbook. The import dialog picks the sheet and header row
  automatically (the workstation's own exported plan round-trips as is,
  SIT sheet / row 8), suggests a column → field mapping from the header
  names (Test Steps, Expected Result, Scenario, Status, Comments… all
  recognised; custom templates match on their own labels) and shows a
  preview before anything lands. Options: fill blank Testing BU / Case
  from the row above (Excel merged cells), append or replace, and
  "Status"-style columns become run results (passed/FAIL/n.a. normalised).
  Imported rows are highlighted and saved only when you press Save. The
  Test Cases page also gets **Import from Excel** → new plan.
- **Builder UI redesign**: sticky header bar with case count and a
  live save-state pill (saved / unsaved / saving / error); 🔍 filter
  rows by any text; ☰ Full text / ≡ Compact density (remembered);
  sticky column headers inside a scrolling table; the active row is
  highlighted and the BU/Case group breaks are visible; per-row tools
  on hover (⧉ duplicate, ＋ insert below, ↑ ↓ move, ✕ remove with
  confirm); row number plus overall position; placeholders in empty
  cells; cleaner borderless cells that outline on hover/focus; footer
  summary (cases · BUs · evidence images); an empty-state card with
  Add / Import / Draft-with-assistant shortcuts; Ctrl+S hint.

## 1.12.0 — 2026-09-22

- **New module — 📧 Mailer** + **new plugin — QA Table Mailer**
  (v1.0.0): email Excel tables through Outlook. In Excel Online (or any
  spreadsheet) select the cells and Ctrl+C; the plugin's 📋 Grab copied
  table reads them into an editable grid (edit cells, add/remove rows
  and columns), then 📧 Send now or 💾 Save as job. The workstation
  sends through your **desktop Outlook** (Windows via COM, macOS via
  AppleScript — no app registration, mails land in Sent Items) or SMTP,
  with an optional review-in-Outlook step. **Templates**: HTML with
  `{{table}}` `{{date}}` `{{job}}` `{{rows}}` placeholders, saved and
  edited with live preview. **Receiver groups**: To/Cc/Bcc lists.
  **Jobs** with a **schedule** (time + weekdays) run on your PC while
  the workstation is open; data comes from the saved table, a
  OneDrive-synced `.xlsx` path or a download URL (sheet + range) read
  live at send time. Every send is logged; configuration lives in
  `data/mailer/` (gitignored).

## 1.11.0 — 2026-09-22

- **AIMAS Recaller v1.1.0** (renamed from QA Form Recaller): two new
  field kinds, detected automatically and switchable per field in the
  editor. 🔎 **Search-select**: for searchable dropdowns (Select2,
  react-select, autocomplete, comboboxes) the recipe stores the text you
  typed and the option you clicked; replay types the search, waits for
  the option list, and clicks the match (partial-text match, keyboard
  fallback; wait time adjustable). 📅 **Date**: per-field setting —
  fixed date, today, or today ± N days computed at replay time — with
  a format choice (DD/MM/YYYY, YYYY-MM-DD, DD MMM YYYY…) and a "type
  keystrokes + Enter" mode for masked date pickers (native value set for
  `<input type=date>`); a default format lives in the editor header.

## 1.10.0 — 2026-09-22

- **New plugin — QA Form Recaller** (v1.0.0, Chrome & Edge): record
  what you fill into any web form and replay it later. 📥 Snapshot
  captures every filled field on the page (Alt+Shift+R); ⏺ Record
  watches the form as you fill it and keeps the order you touched
  fields; ▶ Play refills the form in one click (Alt+Shift+P replays the
  page's last recipe) and reports filled / not-found fields. Handles
  text, number, date, email, textarea, select, multi-select, checkbox,
  radio and contenteditable rich-text fields, firing real input/change
  events so React/Angular/Vue forms accept the values. Full-page
  editor: rename, edit values, remove/reorder fields, add a field by
  label, set the per-field delay, duplicate for variants. Robust field
  matching (id → data-testid → name → aria-label → placeholder → label
  text → CSS path); recipes grouped by page URL; passwords skipped
  unless opted in; JSON export/import to share with the team.

## 1.9.0 — 2026-09-22

- **Screen cap plugin ↔ workstation link** (plugin v1.3.0): the
  workstation now tracks the **current test case** — the row you last
  clicked in the builder, or the case open in the run viewer
  (`/testcases/api/current`). The plugin's popup and floating panel
  show it live ("Current case: DEMO-001 · #2 Login with wrong
  password · 3 images so far") and a **📤 Send all to case** button
  uploads every capture into it in the order they were taken; each
  thumbnail also has its own 📤. Gallery clears after a successful send
  (toggle in ⚙️, along with the workstation URL). The builder and run
  viewer refresh their evidence thumbnails automatically, so sent
  images appear without a reload.

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
