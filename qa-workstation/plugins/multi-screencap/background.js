// QA Multi Screen Cap — service worker.
// Gallery (max 10 shots) lives in chrome.storage.local. Capture always
// targets the active tab of the last-focused NORMAL window, so it works
// from the popup and from the floating panel window alike. The last
// selected area is remembered and can be re-captured without dragging.

const MAX_SHOTS = 10;
let panelWindowId = null;

async function getShots() {
  const { shots = [] } = await chrome.storage.local.get("shots");
  return shots;
}

async function setShots(shots) {
  await chrome.storage.local.set({ shots });
  const text = shots.length ? String(shots.length) : "";
  await chrome.action.setBadgeText({ text });
  await chrome.action.setBadgeBackgroundColor({ color: "#2563eb" });
}

async function addShot(dataUrl, tab, kind) {
  if (!dataUrl) return;
  const shots = await getShots();
  shots.unshift({
    id: Date.now() + "-" + Math.random().toString(36).slice(2, 7),
    dataUrl,
    kind,
    ts: new Date().toISOString(),
    title: (tab && tab.title) || "",
    url: (tab && tab.url) || "",
  });
  await setShots(shots.slice(0, MAX_SHOTS)); // 10 max — oldest drops off
}

async function targetTab() {
  // The last-focused *normal* window — never the popup or the panel.
  const win = await chrome.windows.getLastFocused({ windowTypes: ["normal"] });
  if (!win) return {};
  const [tab] = await chrome.tabs.query({ active: true, windowId: win.id });
  return { win, tab };
}

async function captureVisible() {
  const { win, tab } = await targetTab();
  if (!tab) return;
  const dataUrl = await chrome.tabs.captureVisibleTab(win.id, { format: "png" });
  await addShot(dataUrl, tab, "visible");
}

async function cropInTab(tabId, dataUrl, rect, dpr) {
  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId },
    func: (dataUrl, rect, dpr) => new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        const c = document.createElement("canvas");
        c.width = Math.max(1, Math.round(rect.w * dpr));
        c.height = Math.max(1, Math.round(rect.h * dpr));
        c.getContext("2d").drawImage(
          img,
          Math.round(rect.x * dpr), Math.round(rect.y * dpr),
          c.width, c.height, 0, 0, c.width, c.height);
        resolve(c.toDataURL("image/png"));
      };
      img.onerror = () => resolve(null);
      img.src = dataUrl;
    }),
    args: [dataUrl, rect, dpr],
  });
  return result;
}

async function captureArea(rect) {
  const { win, tab } = await targetTab();
  if (!tab || !rect) return;
  const [{ result: dpr }] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => window.devicePixelRatio || 1,
  });
  const frame = await chrome.tabs.captureVisibleTab(win.id, { format: "png" });
  const cropped = await cropInTab(tab.id, frame, rect, dpr);
  await addShot(cropped, tab, "area");
  await chrome.storage.local.set({ lastArea: rect }); // reusable without dragging
}

async function startAreaSelect() {
  const { win, tab } = await targetTab();
  if (!tab || !/^https?:|^file:/.test(tab.url || "")) return;
  await chrome.windows.update(win.id, { focused: true });
  await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["select.js"] });
}

async function captureLastArea() {
  const { lastArea } = await chrome.storage.local.get("lastArea");
  if (lastArea) await captureArea(lastArea);
}

async function openPanel() {
  if (panelWindowId !== null) {
    try {
      await chrome.windows.update(panelWindowId, { focused: true, drawAttention: true });
      return;
    } catch (e) { panelWindowId = null; } // was closed
  }
  const win = await chrome.windows.create({
    url: chrome.runtime.getURL("panel.html"),
    type: "popup", width: 380, height: 560,
  });
  panelWindowId = win.id;
}

chrome.windows.onRemoved.addListener((id) => {
  if (id === panelWindowId) panelWindowId = null;
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    if (msg.type === "capture-visible") await captureVisible();
    else if (msg.type === "start-area") await startAreaSelect();
    else if (msg.type === "area-rect") await captureArea(msg.rect);
    else if (msg.type === "capture-last-area") await captureLastArea();
    else if (msg.type === "clear-shots") await setShots([]);
    else if (msg.type === "open-panel") await openPanel();
    else if (msg.type === "open-shortcuts") {
      const isEdge = msg.isEdge;
      await chrome.tabs.create({
        url: isEdge ? "edge://extensions/shortcuts" : "chrome://extensions/shortcuts",
      });
    }
    sendResponse({ ok: true });
  })();
  return true; // keep sendResponse alive for the async work
});

chrome.commands.onCommand.addListener((command) => {
  if (command === "capture-visible") captureVisible();
  if (command === "capture-area") startAreaSelect();
  if (command === "capture-last-area") captureLastArea();
});

chrome.runtime.onStartup.addListener(async () => setShots(await getShots()));
