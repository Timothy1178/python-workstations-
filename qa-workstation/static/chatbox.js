/* Reusable agent chat box.
 *
 * Any page gets a floating assistant wired to the shared providers
 * (local Claude CLI + every registered Copilot agent) with one call:
 *
 *   const chat = initChatBox({
 *     title: "Test Case Assistant",
 *     greeting: "Hi! ...",
 *     endpoint: "/testcases/plan/x/assist",   // POST target
 *     buildContext: () => ({table: [...]}),   // extra body fields (optional)
 *     onReply: (data, api) => {...},          // page-specific result handling (optional)
 *     quickActions: [{label: "🔍 Review", message: "Review the table…"}], // one-click prompts (optional)
 *   });
 *
 * Each request POSTs JSON: {message, history, provider, ...buildContext()}.
 * The response's `reply` (or `error`) is shown automatically; onReply then
 * runs for module-specific effects (api.addMsg posts extra notes).
 * The provider dropdown is filled from /agents/api/providers and the
 * choice is remembered in localStorage across pages.
 */
function initChatBox(opts) {
  const PROVIDER_KEY = "qa-chat-provider";

  const fab = document.createElement("button");
  fab.className = "fab";
  fab.title = "AI assistant";
  fab.textContent = "🤖";

  const panel = document.createElement("div");
  panel.className = "chat-panel";
  panel.hidden = true;
  panel.innerHTML = `
    <div class="chat-head">
      <strong>🤖 ${opts.title || "Assistant"}</strong>
      <span class="chat-head-tools">
        <select class="chat-provider" title="Which agent answers this chat"></select>
        <button class="btn small chat-close-btn">✕</button>
      </span>
    </div>
    <div class="chat-msgs"></div>
    <div class="chat-quick"></div>
    <div class="chat-files"></div>
    <div class="chat-input">
      <button class="btn chat-attach" title="Attach files — documents, Excel, images">📎</button>
      <textarea rows="3" placeholder="${opts.placeholder || "Ask the agent…"}"></textarea>
      <button class="btn primary">Send</button>
    </div>
    <input type="file" multiple hidden class="chat-file-input"
           accept=".txt,.md,.csv,.tsv,.json,.log,.xml,.yml,.yaml,.html,.sql,.xlsx,.xlsm,.png,.jpg,.jpeg,.gif,.webp,.bmp,.pdf,.docx">`;
  document.body.append(fab, panel);

  const msgs = panel.querySelector(".chat-msgs");
  const providerSel = panel.querySelector(".chat-provider");
  const chatText = panel.querySelector("textarea");
  const chatSend = panel.querySelector(".chat-input button");
  const history = [];

  function addMsg(role, text) {
    const div = document.createElement("div");
    div.className = "chat-msg " + role;
    div.textContent = text;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    return div;
  }
  if (opts.greeting) addMsg("agent", opts.greeting);

  // ---------- attachments ----------
  const TEXT_EXT = ["txt","md","csv","tsv","json","log","xml","yml","yaml","html","htm","sql","py","js","ini","cfg"];
  const MAX_FILE_MB = 6;
  const fileInput = panel.querySelector(".chat-file-input");
  const fileChips = panel.querySelector(".chat-files");
  let pendingFiles = [];

  panel.querySelector(".chat-attach").onclick = () => fileInput.click();
  fileInput.onchange = () => {
    for (const f of fileInput.files) {
      if (f.size > MAX_FILE_MB * 1024 * 1024) {
        addMsg("agent error", `${f.name} is larger than ${MAX_FILE_MB} MB — attach a smaller file.`);
        continue;
      }
      pendingFiles.push(f);
    }
    fileInput.value = "";
    renderChips();
  };

  function renderChips() {
    fileChips.innerHTML = "";
    fileChips.hidden = !pendingFiles.length;
    pendingFiles.forEach((f, i) => {
      const chip = document.createElement("span");
      chip.className = "file-chip";
      chip.textContent = "📎 " + f.name + " ";
      const x = document.createElement("button");
      x.textContent = "✕";
      x.title = "Remove";
      x.onclick = () => { pendingFiles.splice(i, 1); renderChips(); };
      chip.appendChild(x);
      fileChips.appendChild(chip);
    });
  }
  renderChips();

  function readAttachment(f) {
    const ext = (f.name.split(".").pop() || "").toLowerCase();
    return new Promise(resolve => {
      const r = new FileReader();
      if (TEXT_EXT.includes(ext) || f.type.startsWith("text/")) {
        r.onload = () => resolve({ name: f.name, text: String(r.result).slice(0, 300000) });
        r.onerror = () => resolve(null);
        r.readAsText(f);
      } else {
        r.onload = () => resolve({ name: f.name, data: String(r.result).split(",")[1] || "" });
        r.onerror = () => resolve(null);
        r.readAsDataURL(f);
      }
    });
  }

  const quick = panel.querySelector(".chat-quick");
  for (const qa of opts.quickActions || []) {
    const b = document.createElement("button");
    b.className = "btn small";
    b.textContent = qa.label;
    b.onclick = () => send(qa.message, qa.label);
    quick.appendChild(b);
  }
  if (!(opts.quickActions || []).length) quick.remove();

  async function loadProviders() {
    try {
      const res = await fetch("/agents/api/providers");
      const data = await res.json();
      providerSel.innerHTML = "";
      let remembered = null;
      try { remembered = localStorage.getItem(PROVIDER_KEY); } catch (e) {}
      for (const p of data.providers || []) {
        const o = document.createElement("option");
        o.value = p.id;
        o.textContent = (p.kind === "copilot" ? "🤖 " : "💻 ") + p.name;
        providerSel.appendChild(o);
      }
      if (remembered && [...providerSel.options].some(o => o.value === remembered))
        providerSel.value = remembered;
    } catch (e) { /* dropdown stays empty → server default provider */ }
  }
  loadProviders();
  providerSel.onchange = () => {
    try { localStorage.setItem(PROVIDER_KEY, providerSel.value); } catch (e) {}
    const name = providerSel.selectedOptions[0]?.textContent || providerSel.value;
    addMsg("agent note", `Now chatting with ${name}.`);
  };

  fab.onclick = () => {
    panel.hidden = !panel.hidden;
    if (!panel.hidden) chatText.focus();
  };
  panel.querySelector(".chat-close-btn").onclick = () => panel.hidden = true;
  document.addEventListener("keydown", e => {
    if (e.key === "Escape" && !panel.hidden) panel.hidden = true;
  });

  async function send(override, label) {
    const message = (override || chatText.value).trim();
    if ((!message && !pendingFiles.length) || chatSend.disabled) return;
    if (!override) chatText.value = "";
    const files = pendingFiles;
    pendingFiles = [];
    renderChips();
    const fileNote = files.length ? ` 📎(${files.map(f => f.name).join(", ")})` : "";
    addMsg("user", (label || message || "(files attached)") + fileNote);
    history.push({ role: "user", text: message || "(files attached)" });
    chatSend.disabled = true;
    const thinking = addMsg("agent thinking", "Thinking…");
    try {
      const attachments = (await Promise.all(files.map(readAttachment))).filter(Boolean);
      const context = opts.buildContext ? opts.buildContext() : {};
      const res = await fetch(opts.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: message || "See the attached files.",
          history: history.slice(0, -1),
          provider: providerSel.value || null,
          attachments,
          ...context,
        }),
      });
      const data = await res.json();
      thinking.remove();
      const text = data.reply || data.error || "(no reply)";
      addMsg(data.error ? "agent error" : "agent", text);
      history.push({ role: "assistant", text });
      if (opts.onReply) opts.onReply(data, { addMsg });
    } catch (err) {
      thinking.remove();
      addMsg("agent error", "Request failed: " + err.message);
    } finally {
      chatSend.disabled = false;
    }
  }

  chatSend.onclick = () => send();
  chatText.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  });

  return { addMsg, open: () => { panel.hidden = false; chatText.focus(); } };
}
