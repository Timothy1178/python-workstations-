// QA Form Recaller — service worker. Recipes live in chrome.storage.local:
// {id, name, url, created, updated, delay, fields:[{type, label, loc, value}]}
// Page work is done by page.js injected on demand into the active tab.

async function activeTab() {
  const win = await chrome.windows.getLastFocused({ windowTypes: ["normal"] });
  const [tab] = await chrome.tabs.query({ active: true, windowId: win.id });
  return tab;
}

async function ensurePage(tabId) {
  await chrome.scripting.executeScript({ target: { tabId }, files: ["page.js"] });
}

async function inPage(tabId, func, args = []) {
  await ensurePage(tabId);
  const [{ result }] = await chrome.scripting.executeScript({ target: { tabId }, func, args });
  return result;
}

async function getRecipes() {
  const { recipes = [] } = await chrome.storage.local.get("recipes");
  return recipes;
}
async function setRecipes(recipes) {
  await chrome.storage.local.set({ recipes });
}

function pageKey(url) {
  try { const u = new URL(url); return u.origin + u.pathname; } catch (e) { return url || ""; }
}

function newRecipe(tab, fields, name) {
  const now = new Date().toISOString();
  return {
    id: Date.now() + "-" + Math.random().toString(36).slice(2, 7),
    name: name || `${(tab.title || "Form").slice(0, 40)} — ${new Date().toLocaleString()}`,
    url: pageKey(tab.url),
    title: tab.title || "",
    created: now, updated: now,
    delay: 60,
    fields,
  };
}

async function snapshot(includePasswords) {
  const tab = await activeTab();
  if (!tab || !/^https?:|^file:/.test(tab.url || "")) return { ok: false, error: "open a normal web page first" };
  const fields = await inPage(tab.id, (pw) => window.__qaForm.collect({ onlyFilled: true, includePasswords: pw }), [Boolean(includePasswords)]);
  if (!fields || !fields.length) return { ok: false, error: "no filled fields found on this page" };
  const recipe = newRecipe(tab, fields);
  const recipes = await getRecipes();
  recipes.unshift(recipe);
  await setRecipes(recipes);
  return { ok: true, recipe };
}

let recording = null; // {tabId, tab, fields}

async function startRecording(includePasswords) {
  const tab = await activeTab();
  if (!tab || !/^https?:|^file:/.test(tab.url || "")) return { ok: false, error: "open a normal web page first" };
  recording = { tabId: tab.id, tab, fields: [] };
  await inPage(tab.id, (pw) => { window.__qaFormRecPw = pw; window.__qaForm.startRecording(); return true; }, [Boolean(includePasswords)]);
  await chrome.action.setBadgeText({ text: "REC" });
  await chrome.action.setBadgeBackgroundColor({ color: "#dc2626" });
  return { ok: true };
}

async function stopRecording() {
  if (!recording) return { ok: false, error: "not recording" };
  const rec = recording;
  recording = null;
  await chrome.action.setBadgeText({ text: "" });
  try { await inPage(rec.tabId, () => { window.__qaForm.stopRecording(); return true; }); } catch (e) {}
  if (!rec.fields.length) return { ok: false, error: "nothing was filled while recording" };
  const recipe = newRecipe(rec.tab, rec.fields);
  const recipes = await getRecipes();
  recipes.unshift(recipe);
  await setRecipes(recipes);
  return { ok: true, recipe };
}

async function play(recipeId) {
  const recipes = await getRecipes();
  const recipe = recipes.find((r) => r.id === recipeId);
  if (!recipe) return { ok: false, error: "recipe not found" };
  const tab = await activeTab();
  if (!tab || !/^https?:|^file:/.test(tab.url || "")) return { ok: false, error: "open the form's page first" };
  const report = await inPage(tab.id, (fields, delay) => window.__qaForm.fill(fields, { delay }), [recipe.fields, recipe.delay || 60]);
  const { lastPlayed = {} } = await chrome.storage.local.get("lastPlayed");
  lastPlayed[pageKey(tab.url)] = recipe.id;
  await chrome.storage.local.set({ lastPlayed });
  return { ok: true, report, recipe };
}

async function playLast() {
  const tab = await activeTab();
  if (!tab) return;
  const { lastPlayed = {} } = await chrome.storage.local.get("lastPlayed");
  const id = lastPlayed[pageKey(tab.url)];
  if (id) await play(id);
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    if (msg.type === "snapshot") sendResponse(await snapshot(msg.includePasswords));
    else if (msg.type === "start-recording") sendResponse(await startRecording(msg.includePasswords));
    else if (msg.type === "stop-recording") sendResponse(await stopRecording());
    else if (msg.type === "recording-fields") { if (recording) recording.fields = msg.fields; sendResponse({ ok: true }); }
    else if (msg.type === "recording-state") sendResponse({ recording: Boolean(recording), count: recording ? recording.fields.length : 0 });
    else if (msg.type === "play") sendResponse(await play(msg.id));
    else if (msg.type === "active-page") { const t = await activeTab(); sendResponse({ url: t ? pageKey(t.url) : "", title: t ? t.title : "" }); }
    else if (msg.type === "open-editor") {
      await chrome.tabs.create({ url: chrome.runtime.getURL("editor.html" + (msg.id ? "?id=" + encodeURIComponent(msg.id) : "")) });
      sendResponse({ ok: true });
    }
    else sendResponse({ ok: false, error: "unknown message" });
  })();
  return true;
});

chrome.commands.onCommand.addListener((command) => {
  if (command === "snapshot-form") snapshot(false);
  if (command === "play-last") playLast();
});
