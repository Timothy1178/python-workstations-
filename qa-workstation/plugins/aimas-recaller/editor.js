// AIMAS Recaller — full-page recipe editor (editor.html?id=…).
const id = new URLSearchParams(location.search).get("id");
const rows = document.getElementById("rows");
const status = document.getElementById("status");
const FORMATS = ["DD/MM/YYYY", "YYYY-MM-DD", "MM/DD/YYYY", "DD-MM-YYYY", "DD MMM YYYY", "YYYY/MM/DD"];
const NATIVE_DATE = new Set(["date", "datetime-local", "month", "time", "week"]);
let recipe = null;
let dragRow = null;

async function load() {
  const { recipes = [], settings = {} } = await chrome.storage.local.get(["recipes", "settings"]);
  recipe = recipes.find((r) => r.id === id);
  if (!recipe) { document.querySelector("main").innerHTML = "<p>Recipe not found.</p>"; return; }
  document.getElementById("name").value = recipe.name;
  document.getElementById("url").value = recipe.url;
  document.getElementById("delay").value = recipe.delay ?? 60;
  document.getElementById("date-format").value = settings.dateFormat || "DD/MM/YYYY";
  document.getElementById("option-wait").value = settings.optionWait || 1500;
  document.getElementById("meta").textContent = `${recipe.title || ""} · created ${new Date(recipe.created).toLocaleString()} · updated ${new Date(recipe.updated).toLocaleString()}`;
  document.title = recipe.name + " · AIMAS Recaller";
  rows.innerHTML = "";
  recipe.fields.forEach((f) => rows.appendChild(row(f)));
}

function el(tag, props = {}, children = []) {
  const n = document.createElement(tag);
  Object.assign(n, props);
  children.forEach((c) => n.append(c));
  return n;
}
function opts(select, values, current) {
  values.forEach(([v, t]) => select.append(el("option", { value: v, textContent: t })));
  select.value = current;
}

function valueEditor(f) {
  const box = el("div", { className: "vbox" });
  const t = f.type;
  if (f.widget === "combobox") {
    const search = el("input", { value: f.search ?? f.value ?? "", placeholder: "text to type in the search box" });
    search.dataset.role = "search";
    const pick = el("input", { value: f.pick ?? f.value ?? "", placeholder: "option to choose (exact or partial text)" });
    pick.dataset.role = "pick";
    box.append(el("label", { className: "mini", textContent: "🔎 type" }), search,
               el("label", { className: "mini", textContent: "✔ choose" }), pick);
    return box;
  }
  if (f.widget === "date") {
    const mode = el("select"); mode.dataset.role = "dateMode";
    opts(mode, [["fixed", "fixed date"], ["today", "today (at replay)"], ["offset", "today ± N days"]], f.dateMode || "fixed");
    const fixed = el("input", { value: f.value ?? "", placeholder: "date value" }); fixed.dataset.role = "value";
    const offset = el("input", { type: "number", value: f.dateOffset ?? 0, style: "width:80px" }); offset.dataset.role = "dateOffset";
    const fmt = el("select"); fmt.dataset.role = "dateFormat";
    opts(fmt, [["", "(default format)"], ...FORMATS.map((x) => [x, x])], f.dateFormat || "");
    const typed = el("input", { type: "checkbox", checked: f.dateTyped !== false }); typed.dataset.role = "dateTyped";
    const native = NATIVE_DATE.has(t);
    const sync = () => {
      fixed.hidden = mode.value !== "fixed";
      offset.hidden = mode.value !== "offset";
      fmt.hidden = native;
      typed.parentElement.hidden = native;
    };
    mode.onchange = sync;
    box.append(el("label", { className: "mini", textContent: "📅 when" }), mode, fixed, offset,
               el("label", { className: "mini", textContent: "format" }), fmt,
               el("label", { className: "check", textContent: " type keystrokes + Enter (masked pickers)" }));
    box.lastChild.prepend(typed);
    sync();
    return box;
  }
  if (t === "checkbox" || t === "radio") {
    const s = el("select"); s.dataset.role = "bool";
    opts(s, [["1", "☑ checked / selected"], ["0", "☐ unchecked"]], f.value ? "1" : "0");
    box.append(s); return box;
  }
  if (t === "select-multiple") {
    const ta = el("textarea", { value: [].concat(f.value || []).join("\n") }); ta.dataset.role = "multi";
    box.append(ta); return box;
  }
  if (t === "textarea" || t === "contenteditable" || String(f.value || "").length > 60) {
    const ta = el("textarea", { value: f.value ?? "" }); ta.dataset.role = "value";
    box.append(ta); return box;
  }
  const inp = el("input", { value: f.value ?? "" }); inp.dataset.role = "value";
  box.append(inp); return box;
}

function row(f) {
  const tr = document.createElement("tr");
  tr._field = f;
  const grip = el("td", { className: "drag", textContent: "⋮⋮", draggable: true });
  grip.addEventListener("dragstart", () => { dragRow = tr; });
  tr.addEventListener("dragover", (e) => e.preventDefault());
  tr.addEventListener("drop", (e) => { e.preventDefault(); if (dragRow && dragRow !== tr) rows.insertBefore(dragRow, tr); });

  const lab = el("input", { value: f.label || "", placeholder: "label text exactly as shown on the page" });
  lab.dataset.role = "label";
  const locText = [f.loc.id && "#" + f.loc.id, f.loc.name && "name=" + f.loc.name, f.loc.testid && "testid=" + f.loc.testid,
    f.loc.placeholder && "ph=" + f.loc.placeholder].filter(Boolean).join(" · ") || f.loc.css || "";
  const label = el("td", {}, [lab, el("div", { className: "loc", textContent: locText })]);

  const kind = el("select"); kind.dataset.role = "widget";
  const kinds = [["", "plain"], ["combobox", "search-select"], ["date", "date"]];
  opts(kind, kinds, f.widget || "");
  const typeCell = el("td", {}, [kind, el("div", { className: "pill", textContent: f.type })]);

  const val = el("td", {}, [valueEditor(f)]);
  kind.onchange = () => {
    // switching kind rebuilds the value editor with sensible defaults
    const cur = readRow(tr);
    cur.widget = kind.value;
    if (cur.widget === "combobox") { cur.search = cur.search || cur.value || ""; cur.pick = cur.pick || cur.value || ""; }
    if (cur.widget === "date") { cur.dateMode = cur.dateMode || "fixed"; cur.dateTyped = cur.dateTyped !== false; }
    tr._field = cur;
    val.innerHTML = "";
    val.appendChild(valueEditor(cur));
  };

  const x = el("button", { className: "danger", textContent: "✕", title: "Remove field" });
  x.onclick = () => tr.remove();
  tr.append(grip, label, typeCell, val, el("td", {}, [x]));
  return tr;
}

function readRow(tr) {
  const f = { ...tr._field, loc: { ...tr._field.loc } };
  const get = (role) => tr.querySelector(`[data-role="${role}"]`);
  f.label = get("label").value.trim() || f.label;
  f.widget = get("widget").value;
  const bool = get("bool"), multi = get("multi"), value = get("value");
  if (f.widget === "combobox") {
    f.search = get("search").value;
    f.pick = get("pick").value;
    f.value = f.pick;
  } else if (f.widget === "date") {
    f.dateMode = get("dateMode").value;
    f.value = value ? value.value : f.value;
    f.dateOffset = Number(get("dateOffset").value) || 0;
    f.dateFormat = get("dateFormat").value;
    f.dateTyped = get("dateTyped").checked;
  } else if (bool) f.value = bool.value === "1";
  else if (multi) f.value = multi.value.split("\n").map((s) => s.trim()).filter(Boolean);
  else if (value) f.value = value.value;
  return f;
}
function readRows() { return [...rows.querySelectorAll("tr")].map(readRow); }

document.getElementById("save").onclick = async () => {
  const { recipes = [], settings = {} } = await chrome.storage.local.get(["recipes", "settings"]);
  const i = recipes.findIndex((r) => r.id === id);
  if (i < 0) return;
  recipes[i] = {
    ...recipes[i],
    name: document.getElementById("name").value.trim() || recipes[i].name,
    url: document.getElementById("url").value.trim() || recipes[i].url,
    delay: Math.max(0, Number(document.getElementById("delay").value) || 0),
    fields: readRows(),
    updated: new Date().toISOString(),
  };
  settings.dateFormat = document.getElementById("date-format").value;
  settings.optionWait = Math.max(200, Number(document.getElementById("option-wait").value) || 1500);
  await chrome.storage.local.set({ recipes, settings });
  status.textContent = "✓ saved";
  status.className = "status ok";
  setTimeout(() => (status.textContent = ""), 1500);
};

document.getElementById("add").onclick = () => {
  rows.appendChild(row({ type: "text", widget: "", label: "", loc: { id: "", name: "", css: "" }, value: "" }));
  rows.lastChild.querySelector('[data-role="label"]').focus();
};
document.getElementById("close").onclick = () => window.close();
load();
