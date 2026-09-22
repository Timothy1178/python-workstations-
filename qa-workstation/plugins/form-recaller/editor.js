// QA Form Recaller — full-page recipe editor (editor.html?id=…).
const id = new URLSearchParams(location.search).get("id");
const rows = document.getElementById("rows");
const status = document.getElementById("status");
let recipe = null;
let dragRow = null;

async function load() {
  const { recipes = [] } = await chrome.storage.local.get("recipes");
  recipe = recipes.find((r) => r.id === id);
  if (!recipe) { document.querySelector("main").innerHTML = "<p>Recipe not found.</p>"; return; }
  document.getElementById("name").value = recipe.name;
  document.getElementById("url").value = recipe.url;
  document.getElementById("delay").value = recipe.delay ?? 60;
  document.getElementById("meta").textContent = `${recipe.title || ""} · created ${new Date(recipe.created).toLocaleString()} · updated ${new Date(recipe.updated).toLocaleString()}`;
  document.title = recipe.name + " · QA Form Recaller";
  rows.innerHTML = "";
  recipe.fields.forEach((f) => rows.appendChild(row(f)));
}

function valueEditor(f) {
  const t = f.type;
  if (t === "checkbox" || t === "radio") {
    const s = document.createElement("select");
    s.innerHTML = '<option value="1">☑ checked / selected</option><option value="0">☐ unchecked</option>';
    s.value = f.value ? "1" : "0";
    s.dataset.kind = "bool";
    return s;
  }
  if (t === "select-multiple") {
    const ta = document.createElement("textarea");
    ta.value = [].concat(f.value || []).join("\n");
    ta.dataset.kind = "multi";
    return ta;
  }
  if (t === "textarea" || t === "contenteditable" || String(f.value || "").length > 60) {
    const ta = document.createElement("textarea");
    ta.value = f.value ?? "";
    ta.dataset.kind = "text";
    return ta;
  }
  const inp = document.createElement("input");
  inp.value = f.value ?? "";
  inp.dataset.kind = "text";
  if (t === "number") inp.type = "text";
  return inp;
}

function row(f) {
  const tr = document.createElement("tr");
  tr._field = f;
  const grip = document.createElement("td");
  grip.className = "drag";
  grip.textContent = "⋮⋮";
  grip.draggable = true;
  grip.addEventListener("dragstart", () => { dragRow = tr; });
  tr.addEventListener("dragover", (e) => { e.preventDefault(); });
  tr.addEventListener("drop", (e) => {
    e.preventDefault();
    if (dragRow && dragRow !== tr) rows.insertBefore(dragRow, tr);
  });
  const label = document.createElement("td");
  const lab = document.createElement("input");
  lab.value = f.label || "";
  lab.placeholder = "label";
  lab.dataset.role = "label";
  const loc = document.createElement("div");
  loc.className = "loc";
  loc.textContent = [f.loc.id && "#" + f.loc.id, f.loc.name && "name=" + f.loc.name, f.loc.testid && "testid=" + f.loc.testid, f.loc.placeholder && "ph=" + f.loc.placeholder]
    .filter(Boolean).join(" · ") || f.loc.css;
  label.append(lab, loc);
  const type = document.createElement("td");
  type.innerHTML = `<span class="pill">${f.type}</span>`;
  const val = document.createElement("td");
  val.appendChild(valueEditor(f));
  const del = document.createElement("td");
  const x = document.createElement("button");
  x.className = "danger"; x.textContent = "✕"; x.title = "Remove field";
  x.onclick = () => tr.remove();
  del.appendChild(x);
  tr.append(grip, label, type, val, del);
  return tr;
}

function readRows() {
  return [...rows.querySelectorAll("tr")].map((tr) => {
    const f = { ...tr._field, loc: { ...tr._field.loc } };
    f.label = tr.querySelector('[data-role="label"]').value.trim() || f.label;
    const ed = tr.querySelector("td:nth-child(4) [data-kind]");
    if (ed.dataset.kind === "bool") f.value = ed.value === "1";
    else if (ed.dataset.kind === "multi") f.value = ed.value.split("\n").map((s) => s.trim()).filter(Boolean);
    else f.value = ed.value;
    return f;
  });
}

document.getElementById("save").onclick = async () => {
  const { recipes = [] } = await chrome.storage.local.get("recipes");
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
  await chrome.storage.local.set({ recipes });
  status.textContent = "✓ saved";
  status.className = "status ok";
  setTimeout(() => (status.textContent = ""), 1500);
};

document.getElementById("add").onclick = () => {
  rows.appendChild(row({ type: "text", label: "", loc: { id: "", name: "", css: "" }, value: "" }));
  const inp = rows.lastChild.querySelector('[data-role="label"]');
  inp.placeholder = "label text exactly as shown on the page";
  inp.focus();
};
document.getElementById("close").onclick = () => window.close();
load();
