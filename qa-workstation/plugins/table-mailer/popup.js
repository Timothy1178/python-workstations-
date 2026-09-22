// QA Table Mailer — popup. Reads the table you copied from Excel Online
// (HTML on the clipboard, TSV as fallback), lets you edit it, and hands it
// to the workstation Mailer to send through Outlook or keep as a job.
const $ = (id) => document.getElementById(id);
const DEFAULT_WS = "http://127.0.0.1:5010";
let table = { headers: [], rows: [] };
let ws = DEFAULT_WS;

function say(el, text, cls = "") { el.textContent = text; el.className = "status " + cls; }

async function settings() {
  const { settings = {} } = await chrome.storage.local.get("settings");
  return settings;
}

function parseHtmlTable(html) {
  const doc = new DOMParser().parseFromString(html, "text/html");
  const t = doc.querySelector("table");
  if (!t) return null;
  const rows = [...t.querySelectorAll("tr")].map((tr) =>
    [...tr.querySelectorAll("th,td")].map((c) => c.textContent.replace(/\s+/g, " ").trim()));
  return rows.filter((r) => r.some((v) => v));
}
function parseTsv(text) {
  return text.replace(/\r/g, "").split("\n").filter((l) => l.trim()).map((l) => l.split("\t"));
}

function renderGrid() {
  const grid = $("grid");
  grid.innerHTML = "";
  const width = Math.max(table.headers.length, ...table.rows.map((r) => r.length), 0);
  while (table.headers.length < width) table.headers.push("");
  table.rows.forEach((r) => { while (r.length < width) r.push(""); });
  $("dims").textContent = width ? `${table.rows.length} × ${width}` : "";
  if (!width) { grid.innerHTML = '<tr><td class="empty">Select cells in Excel Online, press Ctrl+C, then click 📋 Grab copied table.</td></tr>'; return; }
  const head = document.createElement("tr");
  const corner = document.createElement("th"); corner.className = "num"; head.appendChild(corner);
  table.headers.forEach((h, c) => {
    const th = document.createElement("th"); th.contentEditable = true; th.textContent = h;
    th.oninput = () => (table.headers[c] = th.textContent);
    th.title = "Header — right-click to delete the column";
    th.oncontextmenu = (e) => { e.preventDefault(); if (confirm("Delete this column?")) { table.headers.splice(c, 1); table.rows.forEach((r) => r.splice(c, 1)); renderGrid(); } };
    head.appendChild(th);
  });
  grid.appendChild(head);
  table.rows.forEach((row, ri) => {
    const tr = document.createElement("tr");
    const num = document.createElement("th"); num.className = "num"; num.textContent = ri + 1;
    num.title = "Right-click to delete the row";
    num.oncontextmenu = (e) => { e.preventDefault(); if (confirm("Delete this row?")) { table.rows.splice(ri, 1); renderGrid(); } };
    tr.appendChild(num);
    row.forEach((v, c) => {
      const td = document.createElement("td"); td.contentEditable = true; td.textContent = v;
      td.oninput = () => (table.rows[ri][c] = td.textContent);
      tr.appendChild(td);
    });
    grid.appendChild(tr);
  });
  chrome.storage.local.set({ draft: table });
}

$("grab").onclick = async () => {
  let rows = null;
  try {
    const items = await navigator.clipboard.read();
    for (const it of items) {
      if (it.types.includes("text/html")) rows = parseHtmlTable(await (await it.getType("text/html")).text());
      if (!rows && it.types.includes("text/plain")) rows = parseTsv(await (await it.getType("text/plain")).text());
    }
  } catch (e) {
    say($("result"), "✕ Clipboard read was blocked: " + e.message, "off");
    return;
  }
  if (!rows || !rows.length) return say($("result"), "✕ No table in the clipboard — select the cells in Excel and press Ctrl+C first.", "off");
  table = { headers: rows[0], rows: rows.slice(1) };
  renderGrid();
  say($("result"), `✓ Grabbed ${table.rows.length} rows × ${table.headers.length} columns — edit cells if needed, then send or save.`, "on");
};
$("add-row").onclick = () => { table.rows.push(table.headers.map(() => "")); renderGrid(); };
$("add-col").onclick = () => { table.headers.push("New"); table.rows.forEach((r) => r.push("")); renderGrid(); };
$("clear").onclick = () => { table = { headers: [], rows: [] }; renderGrid(); };

async function loadOptions() {
  const s = await settings();
  ws = (s.workstation || DEFAULT_WS).replace(/\/+$/, "");
  $("ws-url").value = ws;
  try {
    const res = await fetch(`${ws}/mailer/api/options`, { cache: "no-store" });
    if (!res.ok) throw new Error("answered " + res.status);
    const d = await res.json();
    const fill = (sel, items, label) => {
      [...sel.options].slice(1).forEach((o) => o.remove());
      items.forEach((it) => { const o = document.createElement("option"); o.value = it.id; o.textContent = label(it); sel.appendChild(o); });
    };
    fill($("template"), d.templates, (t) => "🧾 " + t.name);
    fill($("receivers"), d.receivers, (g) => `👥 ${g.name} (${g.to.length})`);
    fill($("job"), d.jobs, (j) => "↻ update table of: " + j.name);
    if (s.template) $("template").value = s.template;
    if (s.receivers) $("receivers").value = s.receivers;
    say($("ws-status"), `🧪 Workstation connected · sending via ${d.transport === "smtp" ? "SMTP" : "desktop Outlook"} · ${d.templates.length} template(s), ${d.receivers.length} receiver group(s)`, "on");
    $("send").disabled = false; $("save-job").disabled = false;
  } catch (e) {
    say($("ws-status"), `🧪 Workstation not reachable at ${ws} — start the QA Workstation (python3 app.py) and open its 📧 Mailer page once.`, "off");
    $("send").disabled = true; $("save-job").disabled = true;
  }
}

function payload() {
  return {
    table, template_id: $("template").value, receivers_id: $("receivers").value,
    subject: $("subject").value.trim(), to: $("to").value.trim(),
    name: $("job-name").value.trim() || "Table from Excel", review: $("review").checked,
  };
}

$("send").onclick = async () => {
  if (!table.rows.length) return say($("result"), "✕ Grab a table first.", "off");
  if (!$("receivers").value && !$("to").value.trim()) return say($("result"), "✕ Pick a receiver group or type an address.", "off");
  $("send").disabled = true; say($("result"), "⏳ Sending through the workstation…");
  try {
    const res = await fetch(`${ws}/mailer/api/send`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload()) });
    const d = await res.json();
    if (d.ok) say($("result"), `✓ ${d.message} — "${d.subject}" to ${d.to.join(", ")}`, "on");
    else say($("result"), "✕ " + d.error, "off");
  } catch (e) { say($("result"), "✕ " + e.message, "off"); }
  $("send").disabled = false;
};

$("save-job").onclick = async () => {
  if ($("job-row").hidden) { $("job-row").hidden = false; $("job-name").focus(); return; }
  if (!table.rows.length) return say($("result"), "✕ Grab a table first.", "off");
  const body = { ...payload(), job_id: $("job").value || undefined };
  try {
    const res = await fetch(`${ws}/mailer/api/jobs`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const d = await res.json();
    if (!d.ok) return say($("result"), "✕ " + d.error, "off");
    say($("result"), `✓ Saved job "${d.job.name}" — set its schedule and receivers on the workstation.`, "on");
    chrome.tabs.create({ url: d.url });
  } catch (e) { say($("result"), "✕ " + e.message, "off"); }
};

$("open-ws").onclick = () => chrome.tabs.create({ url: `${ws}/mailer/` });
$("ws-url").onchange = async () => {
  const s = await settings(); s.workstation = $("ws-url").value.trim(); await chrome.storage.local.set({ settings: s }); loadOptions();
};
$("template").onchange = async () => { const s = await settings(); s.template = $("template").value; chrome.storage.local.set({ settings: s }); };
$("receivers").onchange = async () => { const s = await settings(); s.receivers = $("receivers").value; chrome.storage.local.set({ settings: s }); };

(async () => {
  const { draft } = await chrome.storage.local.get("draft");
  if (draft && draft.headers) table = draft;
  renderGrid();
  loadOptions();
})();
