// QA Multi Screen Cap — area selection overlay.
// Injected on demand; drag to select, Esc to cancel. The overlay removes
// itself before the capture so it never appears in the shot, then crops the
// captured frame here (the page has a DOM canvas; the worker does not).
(() => {
  if (window.__qaCapSelecting) return;
  window.__qaCapSelecting = true;

  const overlay = document.createElement("div");
  overlay.style.cssText =
    "position:fixed;inset:0;z-index:2147483647;cursor:crosshair;" +
    "background:rgba(15,23,42,.25);user-select:none;";
  const box = document.createElement("div");
  box.style.cssText =
    "position:fixed;border:2px solid #2563eb;background:rgba(37,99,235,.15);" +
    "z-index:2147483647;display:none;pointer-events:none;";
  const hint = document.createElement("div");
  hint.textContent = "Drag to select the capture area — Esc to cancel";
  hint.style.cssText =
    "position:fixed;top:12px;left:50%;transform:translateX(-50%);" +
    "background:#111827;color:#fff;padding:6px 14px;border-radius:999px;" +
    "font:13px -apple-system,'Segoe UI',sans-serif;z-index:2147483647;";
  document.documentElement.append(overlay, box, hint);

  let startX = 0, startY = 0, rect = null;

  function cleanup() {
    overlay.remove(); box.remove(); hint.remove();
    document.removeEventListener("keydown", onKey, true);
    window.__qaCapSelecting = false;
  }

  function onKey(e) {
    if (e.key === "Escape") { e.preventDefault(); cleanup(); }
  }
  document.addEventListener("keydown", onKey, true);

  overlay.addEventListener("mousedown", (e) => {
    e.preventDefault();
    startX = e.clientX; startY = e.clientY;
    box.style.display = "block";
    const move = (ev) => {
      const x = Math.min(startX, ev.clientX), y = Math.min(startY, ev.clientY);
      const w = Math.abs(ev.clientX - startX), h = Math.abs(ev.clientY - startY);
      rect = { x, y, w, h };
      box.style.left = x + "px"; box.style.top = y + "px";
      box.style.width = w + "px"; box.style.height = h + "px";
    };
    const up = () => {
      document.removeEventListener("mousemove", move, true);
      document.removeEventListener("mouseup", up, true);
      const chosen = rect;
      cleanup();
      if (!chosen || chosen.w < 4 || chosen.h < 4) return;
      // Two frames so the overlay is really gone before the capture.
      requestAnimationFrame(() => requestAnimationFrame(() => {
        chrome.runtime.sendMessage({
          type: "area-rect", rect: chosen, dpr: window.devicePixelRatio || 1,
        });
      }));
    };
    document.addEventListener("mousemove", move, true);
    document.addEventListener("mouseup", up, true);
  });

  if (!window.__qaCapCropListener) {
    window.__qaCapCropListener = true;
    chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
      if (msg.type !== "crop") return;
      const img = new Image();
      img.onload = () => {
        const { rect: r, dpr } = msg;
        const canvas = document.createElement("canvas");
        canvas.width = Math.round(r.w * dpr);
        canvas.height = Math.round(r.h * dpr);
        canvas.getContext("2d").drawImage(
          img,
          Math.round(r.x * dpr), Math.round(r.y * dpr),
          canvas.width, canvas.height,
          0, 0, canvas.width, canvas.height);
        chrome.runtime.sendMessage({
          type: "area-cropped", dataUrl: canvas.toDataURL("image/png"),
        });
      };
      img.src = msg.dataUrl;
      sendResponse({ ok: true });
      return true;
    });
  }
})();
