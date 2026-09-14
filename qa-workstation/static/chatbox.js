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
    <div class="chat-input">
      <textarea rows="3" placeholder="${opts.placeholder || "Ask the agent…"}"></textarea>
      <button class="btn primary">Send</button>
    </div>`;
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

  async function send() {
    const message = chatText.value.trim();
    if (!message || chatSend.disabled) return;
    chatText.value = "";
    addMsg("user", message);
    history.push({ role: "user", text: message });
    chatSend.disabled = true;
    const thinking = addMsg("agent thinking", "Thinking…");
    try {
      const context = opts.buildContext ? opts.buildContext() : {};
      const res = await fetch(opts.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          history: history.slice(0, -1),
          provider: providerSel.value || null,
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

  chatSend.onclick = send;
  chatText.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  });

  return { addMsg, open: () => { panel.hidden = false; chatText.focus(); } };
}
