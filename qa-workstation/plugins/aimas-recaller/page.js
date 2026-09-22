// AIMAS Recaller — in-page helpers, injected on demand.
// window.__qaForm: collect(opts) → fields, fill(fields, opts) → report,
// startRecording()/stopRecording(). Understands three field flavours:
//   plain    — set the value with native setters + input/change events
//   combobox — searchable dropdowns: type the search text, wait for the
//              option list, click the matching option (keyboard fallback)
//   date     — fixed / today / today±N in a chosen format, set natively
//              or typed (for masked pickers), Enter/Escape closes popups
(() => {
  if (window.__qaForm) return;

  const FIELD_SEL = "input, select, textarea, [contenteditable=''], [contenteditable='true']";
  const SKIP_TYPES = new Set(["submit", "button", "reset", "image", "hidden", "file"]);
  const OPTION_SEL = '[role="option"], [role="listbox"] li, .select2-results__option, ' +
    '.selectize-dropdown .option, .ui-menu-item, .autocomplete-item, .ui-autocomplete li, ' +
    '[class*="__option"], [class*="-option"], [class*="option-"], [class*="MuiAutocomplete-option"], ' +
    '[class*="dropdown-item"], [class*="typeahead"] li, [class*="suggestion"]';
  const NATIVE_DATE = new Set(["date", "datetime-local", "month", "time", "week"]);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  function visible(el) {
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && st.visibility !== "hidden" && st.display !== "none";
  }
  function looksGenerated(s) {
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
      if (l) return l.textContent.trim().replace(/\s+/g, " ");
    }
    const wrap = el.closest("label");
    if (wrap) return wrap.textContent.trim().replace(/\s+/g, " ");
    const by = el.getAttribute("aria-labelledby");
    if (by) { const l = document.getElementById(by); if (l) return l.textContent.trim(); }
    return "";
  }
  function fieldType(el) {
    if (el.isContentEditable) return "contenteditable";
    if (el.tagName === "SELECT") return el.multiple ? "select-multiple" : "select";
    if (el.tagName === "TEXTAREA") return "textarea";
    return (el.type || "text").toLowerCase();
  }
  function isCombobox(el) {
    if (el.tagName !== "INPUT" && !el.isContentEditable) return false;
    if (el.getAttribute("role") === "combobox" || el.getAttribute("aria-autocomplete") || el.hasAttribute("list")) return true;
    const hint = [el.className, el.parentElement && el.parentElement.className,
      el.closest("[class]") && el.closest("[class]").className].join(" ");
    if (/select2|selectize|autocomplete|typeahead|combobox|react-select|chosen|MuiAutocomplete|searchable/i.test(hint)) return true;
    return Boolean(el.closest('[role="combobox"], .select2-container, [class*="react-select"], [class*="autocomplete"], [class*="typeahead"]'));
  }
  function isDateish(el) {
    const t = fieldType(el);
    if (NATIVE_DATE.has(t)) return true;
    if (t !== "text") return false;
    const box = el.closest("[class*='date'], [class*='Date'], [class*='calendar']");
    const hint = [el.id, el.name, el.placeholder, el.className, el.getAttribute("aria-label"),
      el.getAttribute("data-format"), box && box.className].join(" ").toLowerCase();
    return /date|dob|datepicker|calendar|dd\/mm|ddmmyyyy|yyyy/.test(hint);
  }
  function guessFormat(v) {
    v = String(v || "");
    if (/^\d{4}-\d{2}-\d{2}/.test(v)) return "YYYY-MM-DD";
    if (/^\d{2}-\d{2}-\d{4}/.test(v)) return "DD-MM-YYYY";
    if (/^\d{1,2} [A-Za-z]{3} \d{4}/.test(v)) return "DD MMM YYYY";
    if (/^\d{4}\/\d{2}\/\d{2}/.test(v)) return "YYYY/MM/DD";
    return "DD/MM/YYYY";
  }
  const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  function formatDate(d, fmt) {
    const p = (n) => String(n).padStart(2, "0");
    return (fmt || "DD/MM/YYYY")
      .replace("YYYY", d.getFullYear()).replace("MMM", MONTHS[d.getMonth()])
      .replace("MM", p(d.getMonth() + 1)).replace("DD", p(d.getDate()))
      .replace("HH", p(d.getHours())).replace("mm", p(d.getMinutes()));
  }
  function isoLocal(d) {
    const p = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
  }

  function locators(el) {
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
    if (fieldType(el) === "radio") loc.radioValue = el.value;
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
    const type = fieldType(el);
    const f = {
      type, tag: el.tagName.toLowerCase(),
      label: loc.label || loc.aria || loc.placeholder || loc.name || loc.id || loc.css,
      loc, value: currentValue(el), widget: "",
    };
    if (isCombobox(el)) {
      f.widget = "combobox";
      f.search = String(f.value || "");
      f.pick = String(f.value || "");
    } else if (isDateish(el)) {
      f.widget = "date";
      f.dateMode = "fixed";          // fixed | today | offset
      f.dateOffset = 0;
      f.dateFormat = NATIVE_DATE.has(type) ? "" : guessFormat(f.value);
      f.dateTyped = !NATIVE_DATE.has(type); // masked pickers want keystrokes
    }
    return f;
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
      : el instanceof HTMLSelectElement ? HTMLSelectElement.prototype : HTMLInputElement.prototype;
    const d = Object.getOwnPropertyDescriptor(proto, "value");
    if (d && d.set) d.set.call(el, value); else el.value = value;
  }
  function fire(el, names) { for (const n of names) el.dispatchEvent(new Event(n, { bubbles: true })); }
  function key(el, k) {
    const init = { key: k, code: k, bubbles: true, cancelable: true };
    el.dispatchEvent(new KeyboardEvent("keydown", init));
    el.dispatchEvent(new KeyboardEvent("keyup", init));
  }
  async function typeText(el, text, perChar = 25) {
    el.focus();
    if (el.isContentEditable) { el.innerText = ""; } else { nativeSet(el, ""); }
    fire(el, ["input"]);
    let cur = "";
    for (const ch of String(text)) {
      cur += ch;
      el.dispatchEvent(new KeyboardEvent("keydown", { key: ch, bubbles: true }));
      if (el.isContentEditable) el.innerText = cur; else nativeSet(el, cur);
      fire(el, ["input"]);
      el.dispatchEvent(new KeyboardEvent("keyup", { key: ch, bubbles: true }));
      if (perChar) await sleep(perChar);
    }
  }
  function visibleOptions(exclude) {
    let els;
    try { els = [...document.querySelectorAll(OPTION_SEL)]; } catch (e) { els = []; }
    return els.filter((o) => o !== exclude && !o.contains(exclude) && visible(o) && o.textContent.trim());
  }
  async function waitForOption(pick, exclude, timeout) {
    const want = String(pick || "").trim().toLowerCase();
    const end = Date.now() + timeout;
    while (Date.now() < end) {
      const opts = visibleOptions(exclude);
      if (opts.length) {
        if (!want) return opts[0];
        const exact = opts.find((o) => o.textContent.trim().toLowerCase() === want);
        if (exact) return exact;
        const partial = opts.find((o) => o.textContent.trim().toLowerCase().includes(want));
        if (partial) return partial;
      }
      await sleep(100);
    }
    return null;
  }
  function clickLike(el) {
    for (const n of ["pointerdown", "mousedown", "pointerup", "mouseup", "click"]) {
      el.dispatchEvent(new MouseEvent(n, { bubbles: true, cancelable: true, view: window }));
    }
  }

  async function fillCombobox(el, field, opts) {
    const search = field.search != null ? field.search : (field.pick || field.value || "");
    const pick = field.pick || search;
    el.focus();
    clickLike(el);
    await typeText(el, search);
    const opt = await waitForOption(pick, el, opts.optionWait || 1500);
    if (opt) { clickLike(opt); await sleep(80); return "ok"; }
    key(el, "ArrowDown"); key(el, "Enter");
    await sleep(80);
    const shown = String(el.value || el.innerText || "").trim();
    return shown ? "ok" : "no matching option appeared";
  }

  function resolveDate(field, opts) {
    const mode = field.dateMode || "fixed";
    if (mode === "fixed") return field.value;
    const d = new Date();
    if (mode === "offset") d.setDate(d.getDate() + (Number(field.dateOffset) || 0));
    if (field.type === "date") return isoLocal(d).slice(0, 10);
    if (field.type === "datetime-local") return isoLocal(d);
    if (field.type === "month") return isoLocal(d).slice(0, 7);
    return formatDate(d, field.dateFormat || opts.dateFormat || "DD/MM/YYYY");
  }
  async function fillDate(el, field, opts) {
    const value = resolveDate(field, opts);
    if (field.dateTyped && !NATIVE_DATE.has(fieldType(el))) {
      await typeText(el, value);
      fire(el, ["change"]);
      key(el, "Enter");
      key(el, "Escape");
    } else {
      nativeSet(el, String(value));
      fire(el, ["input", "change"]);
    }
    el.blur();
    return "ok";
  }

  async function setField(el, field, opts) {
    const type = fieldType(el);
    const want = field.value;
    if (field.widget === "combobox") return fillCombobox(el, field, opts);
    if (field.widget === "date") return fillDate(el, field, opts);
    el.focus();
    if (type === "checkbox" || type === "radio") {
      if (el.checked !== Boolean(want)) el.click();
    } else if (type === "select") {
      const opt = [...el.options].find((o) => o.value === String(want))
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
        if (type === "radio" && !f.value) continue;
        if (onlyFilled && empty) continue;
        out.push(f);
      }
      return out;
    },

    async fill(fields, opts = {}) {
      const delay = opts.delay == null ? 60 : opts.delay;
      const report = { filled: 0, missing: [], failed: [] };
      for (const field of fields) {
        const el = findElement(field);
        if (!el) { report.missing.push(field.label); continue; }
        try {
          const res = await setField(el, field, opts);
          if (res === "ok") report.filled++; else report.failed.push(`${field.label}: ${res}`);
        } catch (e) { report.failed.push(`${field.label}: ${e.message}`); }
        if (delay) await sleep(delay);
      }
      return report;
    },

    startRecording() {
      if (window.__qaFormRec) return;
      const seen = new Map();
      let lastCombo = null; // key of the combobox being searched, for the option click
      const badge = document.createElement("div");
      badge.style.cssText = "position:fixed;top:10px;right:10px;z-index:2147483647;background:#dc2626;color:#fff;" +
        "padding:6px 12px;border-radius:999px;font:13px -apple-system,'Segoe UI',sans-serif;box-shadow:0 4px 12px rgba(0,0,0,.3);cursor:pointer;";
      badge.textContent = "⏺ AIMAS Recaller recording — 0 fields · click to stop";
      badge.onclick = () => chrome.runtime.sendMessage({ type: "stop-recording" });
      document.documentElement.appendChild(badge);
      const push = () => {
        badge.textContent = `⏺ AIMAS Recaller recording — ${seen.size} field${seen.size === 1 ? "" : "s"} · click to stop`;
        chrome.runtime.sendMessage({ type: "recording-fields", fields: [...seen.values()] });
      };
      const keyOf = (f) => f.type === "radio" ? `radio:${f.loc.name}` : f.loc.css + "|" + f.loc.name;
      const onEvent = (e) => {
        const el = e.target;
        if (!el || !el.matches || !el.matches(FIELD_SEL)) return;
        const type = fieldType(el);
        if (SKIP_TYPES.has(type)) return;
        if (type === "password" && !window.__qaFormRecPw) return;
        const f = describe(el);
        if (type === "radio" && !f.value) return;
        const k = keyOf(f);
        const prev = seen.get(k);
        if (f.widget === "combobox") {
          // keep the text the tester typed as the search; the click on an
          // option (below) records what was chosen
          f.search = String(f.value || "");
          f.pick = prev && prev.pick && e.type !== "input" ? prev.pick : f.search;
          lastCombo = k;
        }
        seen.set(k, prev ? { ...prev, ...f, search: f.search ?? prev.search, pick: f.pick ?? prev.pick } : f);
        push();
      };
      const onClick = (e) => {
        if (!lastCombo || !seen.has(lastCombo)) return;
        const opt = e.target.closest && e.target.closest(OPTION_SEL);
        if (!opt) return;
        const f = seen.get(lastCombo);
        f.pick = opt.textContent.trim();
        seen.set(lastCombo, f);
        push();
      };
      document.addEventListener("change", onEvent, true);
      document.addEventListener("input", onEvent, true);
      document.addEventListener("click", onClick, true);
      window.__qaFormRec = { badge, onEvent, onClick };
    },

    stopRecording() {
      const rec = window.__qaFormRec;
      if (!rec) return;
      document.removeEventListener("change", rec.onEvent, true);
      document.removeEventListener("input", rec.onEvent, true);
      document.removeEventListener("click", rec.onClick, true);
      rec.badge.remove();
      window.__qaFormRec = null;
    },
  };
})();
