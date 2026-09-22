// QA Multi Screen Cap — shared gallery UI for the popup and the floating
// panel (body.className says which). Thumbnails can be dragged straight
// into Excel / the workstation chat box / a folder, or copied to the
// clipboard for pasting.
const MODE = document.body.classList.contains("panel") ? "panel" : "popup";
const IS_EDGE = navigator.userAgent.includes("Edg/");
const grid = document.getElementById("grid");
const empty = document.getElementById("empty");
const count = document.getElementById("count");
const lastAreaBtn = document.getElementById("cap-last-area");
const scaleSel = document.getElementById("scale");

async function loadSettings() {
  const { settings = {} } = await chrome.storage.local.get("settings");
  scaleSel.value = String(settings.scale || 1);
}
scaleSel.onchange = async () => {
  const { settings = {} } = await chrome.storage.local.get("settings");
  settings.scale = Number(scaleSel.value) || 1;
  await chrome.storage.local.set({ settings });
};

function dataUrlToFile(dataUrl, name) {
  const [head, b64] = dataUrl.split(",");
  const type = (head.match(/data:([^;]+)/) || [, "image/png"])[1];
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new File([bytes], name, { type });
}

function stamp(iso) {
  return iso.replace(/[-:]/g, "").replace("T", "-").slice(0, 15);
}

async function shots() {
  const { shots = [] } = await chrome.storage.local.get("shots");
  return shots;
}

function fileName(shot, index) {
  return `qa-cap-${stamp(shot.ts)}${index != null ? "-" + (index + 1) : ""}.png`;
}

function download(shot, index) {
  chrome.downloads.download({
    url: shot.dataUrl,
    filename: `screencaps/${fileName(shot, index)}`,
  });
}

async function copyToClipboard(shot, el) {
  const blob = await (await fetch(shot.dataUrl)).blob();
  await navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]);
  el.classList.add("copied");
  setTimeout(() => el.classList.remove("copied"), 900);
}

function preview(shot) {
  // A page of our own: blob URLs made here die when the popup closes.
  chrome.tabs.create({ url: chrome.runtime.getURL("view.html?id=" + encodeURIComponent(shot.id)) });
}

async function refreshLastAreaBtn() {
  const { lastArea } = await chrome.storage.local.get("lastArea");
  lastAreaBtn.disabled = !lastArea;
  lastAreaBtn.title = lastArea
    ? `Capture the saved area again (${Math.round(lastArea.w)}×${Math.round(lastArea.h)}) — no dragging needed`
    : "No saved area yet — use ✂️ Select area once";
}

async function render() {
  const list = await shots();
  count.textContent = `${list.length}/10`;
  empty.hidden = list.length > 0;
  grid.innerHTML = "";
  list.forEach((s) => {
    const card = document.createElement("div");
    card.className = "shot";
    const img = document.createElement("img");
    img.src = s.dataUrl;
    img.title = "Drag me into Excel or a chat box · click to preview\n"
      + (s.title || "") + "\n" + new Date(s.ts).toLocaleString();
    img.draggable = true;
    img.addEventListener("dragstart", (e) => {
      // Drops as a real .png everywhere: DownloadURL for the desktop/Excel,
      // a File item for web pages (the workstation's evidence cells), and
      // the data URL as text as a last resort.
      e.dataTransfer.setData("DownloadURL", `image/png:${fileName(s)}:${s.dataUrl}`);
      try { e.dataTransfer.items.add(dataUrlToFile(s.dataUrl, fileName(s))); } catch (err) {}
      e.dataTransfer.setData("text/uri-list", s.dataUrl);
      e.dataTransfer.effectAllowed = "copy";
    });
    img.onclick = () => preview(s);
    const bar = document.createElement("div");
    bar.className = "bar";
    const meta = document.createElement("span");
    meta.className = "meta";
    meta.textContent = (s.kind === "area" ? "✂️" : "📸") + " " + new Date(s.ts).toLocaleTimeString();
    const copy = document.createElement("button");
    copy.textContent = "📋";
    copy.title = "Copy — then paste into Excel or the workstation";
    copy.onclick = () => copyToClipboard(s, card);
    const save = document.createElement("button");
    save.textContent = "💾";
    save.title = "Save this capture";
    save.onclick = () => download(s);
    const del = document.createElement("button");
    del.textContent = "✕";
    del.title = "Delete";
    del.onclick = async () => {
      const list = (await shots()).filter((x) => x.id !== s.id);
      await chrome.storage.local.set({ shots: list });
      chrome.action.setBadgeText({ text: list.length ? String(list.length) : "" });
    };
    bar.append(meta, copy, save, del);
    card.append(img, bar);
    grid.appendChild(card);
  });
}

document.getElementById("cap-visible").onclick = () =>
  chrome.runtime.sendMessage({ type: "capture-visible" });

document.getElementById("cap-area").onclick = () => {
  chrome.runtime.sendMessage({ type: "start-area" });
  if (MODE === "popup") window.close(); // hand the page to the overlay
};

lastAreaBtn.onclick = () =>
  chrome.runtime.sendMessage({ type: "capture-last-area" });

document.getElementById("save-all").onclick = async () => {
  (await shots()).forEach((s, i) => download(s, i));
};

document.getElementById("clear-all").onclick = () =>
  chrome.runtime.sendMessage({ type: "clear-shots" });

document.getElementById("shortcuts").onclick = () =>
  chrome.runtime.sendMessage({ type: "open-shortcuts", isEdge: IS_EDGE });

const openPanelBtn = document.getElementById("open-panel");
if (openPanelBtn) {
  openPanelBtn.onclick = () => {
    chrome.runtime.sendMessage({ type: "open-panel" });
    if (MODE === "popup") window.close();
  };
}

chrome.storage.onChanged.addListener((changes) => {
  if (changes.shots) render();
  if (changes.lastArea) refreshLastAreaBtn();
});

render();
refreshLastAreaBtn();
loadSettings();
