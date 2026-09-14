// QA Multi Screen Cap — popup gallery.
const grid = document.getElementById("grid");
const empty = document.getElementById("empty");
const count = document.getElementById("count");

function stamp(iso) {
  return iso.replace(/[-:]/g, "").replace("T", "-").slice(0, 15);
}

async function shots() {
  const { shots = [] } = await chrome.storage.local.get("shots");
  return shots;
}

function download(shot, index) {
  chrome.downloads.download({
    url: shot.dataUrl,
    filename: `screencaps/qa-cap-${stamp(shot.ts)}${index != null ? "-" + (index + 1) : ""}.png`,
  });
}

async function render() {
  const list = await shots();
  count.textContent = list.length ? list.length + " capture" + (list.length > 1 ? "s" : "") : "";
  empty.hidden = list.length > 0;
  grid.innerHTML = "";
  list.forEach((s) => {
    const card = document.createElement("div");
    card.className = "shot";
    const img = document.createElement("img");
    img.src = s.dataUrl;
    img.title = (s.title || "") + "\n" + new Date(s.ts).toLocaleString();
    img.onclick = () => chrome.tabs.create({ url: s.dataUrl });
    const bar = document.createElement("div");
    bar.className = "bar";
    const meta = document.createElement("span");
    meta.className = "meta";
    meta.textContent = (s.kind === "area" ? "✂️ " : "📸 ") + new Date(s.ts).toLocaleTimeString();
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
    bar.append(meta, save, del);
    card.append(img, bar);
    grid.appendChild(card);
  });
}

document.getElementById("cap-visible").onclick = () =>
  chrome.runtime.sendMessage({ type: "capture-visible" });

document.getElementById("cap-area").onclick = () => {
  chrome.runtime.sendMessage({ type: "start-area" });
  window.close(); // hand the page over to the selection overlay
};

document.getElementById("save-all").onclick = async () => {
  (await shots()).forEach((s, i) => download(s, i));
};

document.getElementById("clear-all").onclick = () =>
  chrome.runtime.sendMessage({ type: "clear-shots" });

chrome.storage.onChanged.addListener((changes) => {
  if (changes.shots) render();
});

render();
