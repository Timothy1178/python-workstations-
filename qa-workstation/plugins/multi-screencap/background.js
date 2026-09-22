// QA Multi Screen Cap — service worker.
// Gallery (max 10 shots) lives in chrome.storage.local. Capture always
// targets the active tab of the last-focused NORMAL window, so it works
// from the popup and from the floating panel window alike. The last
// selected area is remembered and can be re-captured without dragging.

const MAX_SHOTS = 10;
let panelWindowId = null;

async function getScale() {
  const { settings = {} } = await chrome.storage.local.get("settings");
  const s = Number(settings.scale) || 1;
  return s > 1 ? s : 1;
}

async function pageMetrics(tabId) {
  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId },
    func: () => ({
      dpr: window.devicePixelRatio || 1,
      scrollX: window.scrollX, scrollY: window.scrollY,
      width: window.innerWidth, height: window.innerHeight,
    }),
  });
  return result;
}

// High-resolution capture: the DevTools protocol renders the clip at
// `scale` CSS-pixel multiples, independent of the screen's own scaling —
// so 2× on a normal monitor is as sharp as a Retina capture, and 3× stays
// crisp when the image is enlarged in Excel. Chrome shows an "is
// debugging this browser" bar while attached; we detach immediately.
async function captureHD(tabId, clipCss, scale) {
  const target = { tabId };
  await chrome.debugger.attach(target, "1.3");
  try {
    const { data } = await chrome.debugger.sendCommand(target, "Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
      clip: { x: clipCss.x, y: clipCss.y, width: clipCss.w, height: clipCss.h, scale },
    });
    return "data:image/png;base64," + data;
  } finally {
    await chrome.debugger.detach(target).catch(() => {});
  }
}

// ---------- workstation connection ----------
const DEFAULT_WS = "http://127.0.0.1:5010";

async function getSettings() {
  const { settings = {} } = await chrome.storage.local.get("settings");
  return { workstation: DEFAULT_WS, clearAfterSend: true, ...settings };
}

function wsBase(settings) {
  return (settings.workstation || DEFAULT_WS).replace(/\/+$/, "");
}

async function workstationCurrent() {
  const settings = await getSettings();
  try {
    const res = await fetch(`${wsBase(settings)}/testcases/api/current`, { cache: "no-store" });
    if (!res.ok) return { ok: false, error: `workstation answered ${res.status}` };
    const data = await res.json();
    return { ok: true, current: data.current, workstation: wsBase(settings) };
  } catch (e) {
    return { ok: false, error: "workstation not reachable at " + wsBase(settings) };
  }
}

function dataUrlToBlob(dataUrl) {
  const [head, b64] = dataUrl.split(",");
  const type = (head.match(/data:([^;]+)/) || [, "image/png"])[1];
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new Blob([bytes], { type });
}

// Upload gallery shots (all, or the given ids) to the workstation's
// current case — oldest first so the evidence numbering follows the
// order they were taken. Runs here so a closing popup can't cut it off.
async function sendToWorkstation(ids) {
  const state = await workstationCurrent();
  if (!state.ok) return state;
  if (!state.current) return { ok: false, error: "no current case — click a case in the workstation builder or run viewer first" };
  const settings = await getSettings();
  let list = await getShots();
  if (ids && ids.length) list = list.filter((s) => ids.includes(s.id));
  if (!list.length) return { ok: false, error: "nothing to send" };
  const fd = new FormData();
  [...list].reverse().forEach((s) => {
    const stamp = s.ts.replace(/[-:]/g, "").replace("T", "-").slice(0, 15);
    fd.append("shots", dataUrlToBlob(s.dataUrl), `qa-cap-${stamp}.png`);
  });
  const cur = state.current;
  const url = `${state.workstation}/testcases/plan/${encodeURIComponent(cur.plan_id)}/shots/${encodeURIComponent(cur.case_uid)}`;
  try {
    const res = await fetch(url, { method: "POST", body: fd });
    if (!res.ok) return { ok: false, error: `upload failed (${res.status})` };
    const data = await res.json();
    if (settings.clearAfterSend) {
      const sentIds = new Set(list.map((s) => s.id));
      await setShots((await getShots()).filter((s) => !sentIds.has(s.id)));
    }
    return { ok: true, sent: list.length, total: (data.shots || []).length, current: cur };
  } catch (e) {
    return { ok: false, error: "upload failed: " + e.message };
  }
}

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
  const scale = await getScale();
  if (scale > 1) {
    try {
      const m = await pageMetrics(tab.id);
      // CDP clips are page coordinates (scroll included), in CSS px.
      const clip = { x: m.scrollX, y: m.scrollY, w: m.width, h: m.height };
      await addShot(await captureHD(tab.id, clip, scale), tab, "visible");
      return;
    } catch (e) { /* debugger unavailable on this page — fall back */ }
  }
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
  await chrome.storage.local.set({ lastArea: rect }); // reusable without dragging
  const scale = await getScale();
  const m = await pageMetrics(tab.id);
  if (scale > 1) {
    try {
      const clip = { x: rect.x + m.scrollX, y: rect.y + m.scrollY, w: rect.w, h: rect.h };
      await addShot(await captureHD(tab.id, clip, scale), tab, "area");
      return;
    } catch (e) { /* debugger unavailable on this page — fall back */ }
  }
  const frame = await chrome.tabs.captureVisibleTab(win.id, { format: "png" });
  const cropped = await cropInTab(tab.id, frame, rect, m.dpr);
  await addShot(cropped, tab, "area");
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
    else if (msg.type === "ws-current") { sendResponse(await workstationCurrent()); return; }
    else if (msg.type === "send-to-workstation") { sendResponse(await sendToWorkstation(msg.ids)); return; }
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
