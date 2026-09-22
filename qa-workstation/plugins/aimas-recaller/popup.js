// AIMAS Recaller — popup: list recipes (this page first), play, record.
const status = document.getElementById("status");
const hereList = document.getElementById("here");
const allList = document.getElementById("all");
const recordBtn = document.getElementById("record");
const pw = document.getElementById("pw");
let pageUrl = "";

function say(text, cls = "") { status.textContent = text; status.className = "status " + cls; }

async function recipes() {
  const { recipes = [] } = await chrome.storage.local.get("recipes");
  return recipes;
}

function card(r) {
  const el = document.createElement("div");
  el.className = "recipe";
  const name = document.createElement("div");
  name.className = "name";
  name.textContent = r.name;
  const meta = document.createElement("div");
  meta.className = "muted";
  meta.textContent = `${r.fields.length} field${r.fields.length === 1 ? "" : "s"} · ${r.url.replace(/^https?:\/\//, "").slice(0, 48)}`;
  const bar = document.createElement("div");
  bar.className = "bar";
  const play = document.createElement("button");
  play.className = "primary";
  play.textContent = "▶ Play";
  play.onclick = async () => {
    play.disabled = true; play.textContent = "⏳";
    const res = await chrome.runtime.sendMessage({ type: "play", id: r.id });
    play.disabled = false; play.textContent = "▶ Play";
    if (!res.ok) return say("✕ " + res.error, "bad");
    const rep = res.report;
    let msg = `✓ Filled ${rep.filled} of ${r.fields.length} fields`;
    if (rep.missing.length) msg += ` · not found: ${rep.missing.slice(0, 4).join(", ")}${rep.missing.length > 4 ? "…" : ""}`;
    if (rep.failed.length) msg += ` · failed: ${rep.failed.slice(0, 3).join("; ")}`;
    say(msg, rep.missing.length || rep.failed.length ? "" : "ok");
  };
  const edit = document.createElement("button");
  edit.textContent = "✏️ Edit";
  edit.onclick = () => chrome.runtime.sendMessage({ type: "open-editor", id: r.id });
  const dup = document.createElement("button");
  dup.textContent = "⧉";
  dup.title = "Duplicate — make a variant with different values";
  dup.onclick = async () => {
    const list = await recipes();
    const copy = { ...r, id: Date.now() + "-" + Math.random().toString(36).slice(2, 7), name: r.name + " (copy)", created: new Date().toISOString(), updated: new Date().toISOString(), fields: r.fields.map((f) => ({ ...f })) };
    list.unshift(copy);
    await chrome.storage.local.set({ recipes: list });
    chrome.runtime.sendMessage({ type: "open-editor", id: copy.id });
  };
  const del = document.createElement("button");
  del.className = "danger";
  del.textContent = "🗑";
  del.onclick = async () => {
    if (!confirm(`Delete recipe "${r.name}"?`)) return;
    await chrome.storage.local.set({ recipes: (await recipes()).filter((x) => x.id !== r.id) });
  };
  bar.append(play, edit, dup, del);
  el.append(name, meta, bar);
  return el;
}

async function render() {
  const list = await recipes();
  const here = list.filter((r) => r.url === pageUrl);
  const rest = list.filter((r) => r.url !== pageUrl);
  hereList.innerHTML = ""; allList.innerHTML = "";
  if (!here.length) hereList.innerHTML = '<div class="empty">No recipe for this page yet — snapshot or record one.</div>';
  here.forEach((r) => hereList.appendChild(card(r)));
  if (!rest.length) allList.innerHTML = '<div class="empty">' + (list.length ? "All recipes belong to this page." : "No recipes saved yet.") + '</div>';
  rest.forEach((r) => allList.appendChild(card(r)));
}

async function refreshRecordBtn() {
  const st = await chrome.runtime.sendMessage({ type: "recording-state" });
  if (st && st.recording) {
    recordBtn.textContent = `⏹ Stop (${st.count})`;
    recordBtn.className = "rec";
  } else {
    recordBtn.textContent = "⏺ Record";
    recordBtn.className = "";
  }
}

document.getElementById("snapshot").onclick = async () => {
  say("Capturing…");
  const res = await chrome.runtime.sendMessage({ type: "snapshot", includePasswords: pw.checked });
  if (!res.ok) return say("✕ " + res.error, "bad");
  say(`✓ Saved "${res.recipe.name}" with ${res.recipe.fields.length} fields — ✏️ Edit to rename or adjust values.`, "ok");
};

recordBtn.onclick = async () => {
  const st = await chrome.runtime.sendMessage({ type: "recording-state" });
  if (st && st.recording) {
    const res = await chrome.runtime.sendMessage({ type: "stop-recording" });
    if (!res.ok) say("✕ " + res.error, "bad");
    else say(`✓ Recorded "${res.recipe.name}" with ${res.recipe.fields.length} fields.`, "ok");
  } else {
    const res = await chrome.runtime.sendMessage({ type: "start-recording", includePasswords: pw.checked });
    if (!res.ok) return say("✕ " + res.error, "bad");
    say("⏺ Recording — fill in the form, then click Stop here or the red badge on the page.");
    window.close(); // let the tester get to the form
  }
  refreshRecordBtn();
};

document.getElementById("export").onclick = async () => {
  const blob = new Blob([JSON.stringify(await recipes(), null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  chrome.downloads.download({ url, filename: "qa-form-recipes.json", saveAs: true });
};
document.getElementById("import").onclick = () => document.getElementById("import-file").click();
document.getElementById("import-file").onchange = async (e) => {
  const f = e.target.files[0];
  if (!f) return;
  try {
    const incoming = JSON.parse(await f.text());
    if (!Array.isArray(incoming)) throw new Error("expected a list of recipes");
    const list = await recipes();
    const ids = new Set(list.map((r) => r.id));
    const added = incoming.filter((r) => r && r.fields && !ids.has(r.id));
    await chrome.storage.local.set({ recipes: [...added, ...list] });
    say(`✓ Imported ${added.length} recipe${added.length === 1 ? "" : "s"}.`, "ok");
  } catch (err) { say("✕ Import failed: " + err.message, "bad"); }
};

chrome.storage.onChanged.addListener((c) => { if (c.recipes) render(); });

(async () => {
  const p = await chrome.runtime.sendMessage({ type: "active-page" });
  pageUrl = (p && p.url) || "";
  document.getElementById("page").textContent = pageUrl.replace(/^https?:\/\//, "").slice(0, 40);
  render();
  refreshRecordBtn();
})();
