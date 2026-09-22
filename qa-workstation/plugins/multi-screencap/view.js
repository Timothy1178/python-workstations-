// QA Multi Screen Cap — full-size viewer for one capture (view.html?id=…).
const id = new URLSearchParams(location.search).get("id");
const img = document.getElementById("img");
const info = document.getElementById("info");
let shot = null;

(async () => {
  const { shots = [] } = await chrome.storage.local.get("shots");
  shot = shots.find((s) => s.id === id);
  if (!shot) { info.textContent = "This capture is no longer in the gallery."; return; }
  img.src = shot.dataUrl;
  img.onload = () => {
    info.textContent = `${img.naturalWidth}×${img.naturalHeight}px · ${new Date(shot.ts).toLocaleString()}`;
  };
  document.title = (shot.title || "Capture") + " · QA Screen Cap";
})();

document.getElementById("fit").onclick = (e) => {
  img.classList.toggle("actual");
  e.target.textContent = img.classList.contains("actual") ? "🔍 Fit to window" : "🔍 Actual size";
};
document.getElementById("save").onclick = () => {
  if (!shot) return;
  const stamp = shot.ts.replace(/[-:]/g, "").replace("T", "-").slice(0, 15);
  chrome.downloads.download({ url: shot.dataUrl, filename: `screencaps/qa-cap-${stamp}.png` });
};
document.getElementById("copy").onclick = async (e) => {
  if (!shot) return;
  const blob = await (await fetch(shot.dataUrl)).blob();
  await navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]);
  e.target.textContent = "✓ Copied";
  setTimeout(() => (e.target.textContent = "📋 Copy"), 1200);
};
