// QA Form Recaller — in-page helpers, injected on demand.
// Exposes window.__qaForm with: collect(opts) → fields, fill(fields, opts)
// → report, startRecording()/stopRecording(). Nothing runs until called.
(() => {
  if (window.__qaForm) return;

  const FIELD_SEL = "input, select, textarea, [contenteditable=''], [contenteditable='true']";
  const SKIP_TYPES = new Set(["submit", "button", "reset", "image", "hidden", "file"]);

  function visible(el) {
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && st.visibility !== "hidden" && st.display !== "none";
  }

  function looksGenerated(s) {
    // ids like "input-4821" or ":r3:" change between page loads
    return !s || /\d{3,}/.test(s) || /^:/.test(s) || /^[a-f0-9-]{20,}$/i.test(s);
  }

  function cssPath(el) {
    const parts = [];
    let node = el;
    while (node && node.nodeType === 1 && parts.length < 6) {
      let part = node.tagName.toLowerCase();
      if (node.id && !looksGenerated(node.id)) { parts.unshift("#" + CSS.escape(node.id)); break; }
      const parent = node.parentElement;
      if (parent) {
        const same = [...parent.children].filter((c) => c.tagName === node.tagName);
        if (same.length > 1) part += `:nth-of-type(${same.indexOf(node) + 1})`;
      }
      parts.unshift(part);
      node = parent;
    }
    return parts.join(" > ");
  }

  function labelText(el) {
    if (el.id) {
      const l = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (l) return l.textContent.trim();
    }
    const wrap = el.closest("label");
    if (wrap) return wrap.textContent.trim().replace(/\s+/g, " ");
    if (el.getAttribute("aria-labelledby")) {
      const l = document.getElementById(el.getAttribute("aria-labelledby"));
      if (l) return l.textContent.trim();
    }
    return "";
  }

  function fieldType(el) {
    if (el.isContentEditable) return "contenteditable";
    if (el.tagName === "SELECT") return el.multiple ? "select-multiple" : "select";
    if (el.tagName === "TEXTAREA") return "textarea";
    return (el.type || "text").toLowerCase();
  }

  function locators(el) {
    const type = fieldType(el);
    const loc = {
      id: el.id && !looksGenerated(el.id) ? el.id : "",
      name: el.getAttribute("name") || "",
      testid: el.getAttribute("data-testid") || el.getAttribute("data-test") || el.getAttribute("data-cy") || "",
      aria: el.getAttribute("aria-label") || "",
      placeholder: el.getAttribute("placeholder") || "",
      label: labelText(el).slice(0, 80),
      css: cssPath(el),
      formIndex: [...document.querySelectorAll("form")].indexOf(el.closest("form")),
    };
    if (type === "radio") loc.radioValue = el.value;
    return loc;
  }

  function currentValue(el) {
    const type = fieldType(el);
    if (type === "checkbox" || type === "radio") return el.checked;
    if (type === "select-multiple") return [...el.selectedOptions].map((o) => o.value);
    if (type === "contenteditable") return el.innerText;
    return el.value;
  }

  function describe(el) {
    const loc = locators(el);
    return {
      type: fieldType(el),
      tag: el.tagName.toLowerCase(),
      label: loc.label || loc.aria || loc.placeholder || loc.name || loc.id || loc.css,
      loc,
      value: currentValue(el),
    };
  }

  function candidates(loc, type) {
    const list = [];
    if (loc.id) list.push(`#${CSS.escape(loc.id)}`);
    if (loc.testid) list.push(`[data-testid="${loc.testid}"], [data-test="${loc.testid}"], [data-cy="${loc.testid}"]`);
    if (loc.name) {
      const base = `[name="${loc.name}"]`;
      list.push(type === "radio" && loc.radioValue !== undefined
        ? `input[type="radio"]${base}[value="${loc.radioValue}"]` : base);
    }
    if (loc.aria) list.push(`[aria-label="${loc.aria}"]`);
    if (loc.placeholder) list.push(`[placeholder="${loc.placeholder}"]`);
    if (loc.css) list.push(loc.css);
    return list;
  }

  function findElement(field) {
    const { loc, type } = field;
    for (const sel of candidates(loc, type)) {
      let els;
      try { els = [...document.querySelectorAll(sel)]; } catch (e) { continue; }
      els = els.filter((el) => el.matches(FIELD_SEL));
      if (loc.formIndex >= 0 && els.length > 1) {
        const forms = document.querySelectorAll("form");
        const inForm = els.filter((el) => el.closest("form") === forms[loc.formIndex]);
        if (inForm.length) els = inForm;
      }
      if (els.length) return els[0];
    }
    if (loc.label) {
      for (const l of document.querySelectorAll("label")) {
        if (l.textContent.trim().replace(/\s+/g, " ") === loc.label) {
          const target = l.control || l.querySelector(FIELD_SEL);
          if (target) return target;
        }
      }
    }
    return null;
  }

  function nativeSet(el, value) {
    const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype
      : el instanceof HTMLSelectElement ? HTMLSelectElement.prototype
      : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, "value");
    if (setter && setter.set) setter.set.call(el, value); else el.value = value;
  }

  function fire(el, names) {
    for (const n of names) el.dispatchEvent(new Event(n, { bubbles: true }));
  }

  function setField(el, field) {
    const type = fieldType(el);
    const want = field.value;
    el.focus();
    if (type === "checkbox" || type === "radio") {
      if (el.checked !== Boolean(want)) el.click();
    } else if (type === "select") {
      let opt = [...el.options].find((o) => o.value === String(want))
        || [...el.options].find((o) => o.textContent.trim() === String(want).trim());
      if (!opt) return "option not found";
      nativeSet(el, opt.value);
      fire(el, ["input", "change"]);
    } else if (type === "select-multiple") {
      const wanted = new Set([].concat(want).map(String));
      [...el.options].forEach((o) => { o.selected = wanted.has(o.value) || wanted.has(o.textContent.trim()); });
      fire(el, ["input", "change"]);
    } else if (type === "contenteditable") {
      el.innerText = String(want);
      fire(el, ["input"]);
    } else {
      nativeSet(el, String(want));
      fire(el, ["keydown", "keyup", "input", "change"]);
    }
    el.blur();
    return "ok";
  }

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  window.__qaForm = {
    collect({ onlyFilled = true, includePasswords = false } = {}) {
      const out = [];
      for (const el of document.querySelectorAll(FIELD_SEL)) {
        const type = fieldType(el);
        if (SKIP_TYPES.has(type) || el.disabled || el.readOnly) continue;
        if (type === "password" && !includePasswords) continue;
        if (!visible(el)) continue;
        const f = describe(el);
        const empty = f.value === "" || f.value === false || (Array.isArray(f.value) && !f.value.length);
        if (type === "radio" && !f.value) continue; // only the chosen radio
        if (onlyFilled && empty) continue;
        out.push(f);
      }
      return out;
    },

    async fill(fields, { delay = 60 } = {}) {
      const report = { filled: 0, missing: [], failed: [] };
      for (const field of fields) {
        const el = findElement(field);
        if (!el) { report.missing.push(field.label); continue; }
        try {
          const res = setField(el, field);
          if (res === "ok") report.filled++; else report.failed.push(`${field.label}: ${res}`);
        } catch (e) { report.failed.push(`${field.label}: ${e.message}`); }
        if (delay) await sleep(delay);
      }
      return report;
    },

    startRecording() {
      if (window.__qaFormRec) return;
      const seen = new Map();
      const badge = document.createElement("div");
      badge.style.cssText = "position:fixed;top:10px;right:10px;z-index:2147483647;background:#dc2626;color:#fff;" +
        "padding:6px 12px;border-radius:999px;font:13px -apple-system,'Segoe UI',sans-serif;box-shadow:0 4px 12px rgba(0,0,0,.3);cursor:pointer;";
      badge.textContent = "⏺ Recording form — 0 fields · click to stop";
      badge.onclick = () => chrome.runtime.sendMessage({ type: "stop-recording" });
      document.documentElement.appendChild(badge);
      const onEvent = (e) => {
        const el = e.target;
        if (!el || !el.matches || !el.matches(FIELD_SEL)) return;
        const type = fieldType(el);
        if (SKIP_TYPES.has(type)) return;
        if (type === "password" && !window.__qaFormRecPw) return;
        const f = describe(el);
        if (type === "radio" && !f.value) return;
        const key = type === "radio" ? `radio:${f.loc.name}` : f.loc.css + "|" + f.loc.name;
        if (seen.has(key)) seen.set(key, { ...seen.get(key), value: f.value });
        else seen.set(key, f);
        badge.textContent = `⏺ Recording form — ${seen.size} field${seen.size === 1 ? "" : "s"} · click to stop`;
        chrome.runtime.sendMessage({ type: "recording-fields", fields: [...seen.values()] });
      };
      document.addEventListener("change", onEvent, true);
      document.addEventListener("input", onEvent, true);
      window.__qaFormRec = { badge, onEvent };
    },

    stopRecording() {
      const rec = window.__qaFormRec;
      if (!rec) return;
      document.removeEventListener("change", rec.onEvent, true);
      document.removeEventListener("input", rec.onEvent, true);
      rec.badge.remove();
      window.__qaFormRec = null;
    },
  };
})();
