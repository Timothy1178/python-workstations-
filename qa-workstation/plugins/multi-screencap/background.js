// QA Multi Screen Cap — service worker.
// Holds the shot gallery in chrome.storage.local and orchestrates the two
// capture flows: visible page, and area selection (select.js overlay in the
// page picks the rect and crops the capture, since the worker has no DOM).

const MAX_SHOTS = 100;

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
  const shots = await getShots();
  shots.unshift({
    id: Date.now() + "-" + Math.random().toString(36).slice(2, 7),
    dataUrl,
    kind,
    ts: new Date().toISOString(),
    title: (tab && tab.title) || "",
    url: (tab && tab.url) || "",
  });
  await setShots(shots.slice(0, MAX_SHOTS));
}

async function activeTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function captureVisible() {
  const tab = await activeTab();
  if (!tab) return;
  const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: "png" });
  await addShot(dataUrl, tab, "visible");
}

async function startAreaSelect() {
  const tab = await activeTab();
  if (!tab || !/^https?:|^file:/.test(tab.url || "")) return;
  await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["select.js"] });
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    if (msg.type === "capture-visible") {
      await captureVisible();
      sendResponse({ ok: true });
    } else if (msg.type === "start-area") {
      await startAreaSelect();
      sendResponse({ ok: true });
    } else if (msg.type === "area-rect") {
      // Overlay is gone; grab the frame and hand it back for cropping.
      const dataUrl = await chrome.tabs.captureVisibleTab(sender.tab.windowId, { format: "png" });
      await chrome.tabs.sendMessage(sender.tab.id, {
        type: "crop", dataUrl, rect: msg.rect, dpr: msg.dpr,
      });
      sendResponse({ ok: true });
    } else if (msg.type === "area-cropped") {
      await addShot(msg.dataUrl, sender.tab, "area");
      sendResponse({ ok: true });
    } else if (msg.type === "clear-shots") {
      await setShots([]);
      sendResponse({ ok: true });
    }
  })();
  return true; // keep sendResponse alive for the async work
});

chrome.commands.onCommand.addListener((command) => {
  if (command === "capture-visible") captureVisible();
  if (command === "capture-area") startAreaSelect();
});

chrome.runtime.onStartup.addListener(async () => setShots(await getShots()));
