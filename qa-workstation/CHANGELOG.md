# Changelog

Version lives in `version.py` and shows in the sidebar footer.
Bump rule: every **main update adds 0.1** (1.1.0 → 1.2.0); every
**bug fix adds 0.0.1** (1.1.0 → 1.1.1). Update this file in the same
change.

## 1.1.0 — 2026-09-14

- **Copilot Agents**: live chat with Copilot Studio agents — via the
  Microsoft 365 Agents SDK (Direct Connect URL or Environment ID +
  schema name, Microsoft sign-in with optional tenant ID) or via a
  Direct Line web-channel secret (no Entra setup).
- **Test case builder**: chat box gets an agent selector (local Claude
  CLI or any connected Copilot agent, remembered across pages), a
  one-click **Review test cases** action, and auto-growing cells so
  long wording shows in full while editing.
- **Shared chat component**: any module can add an agent-assisted chat
  box with one `initChatBox()` call backed by
  `modules/agents/service.py`.
- **CSV reader**: paste text (comma / tab / semicolon / pipe separated,
  auto-detected) and convert it to a CSV file.
- **Fixed**: the builder's assistant chat box could not be closed
  (`display: flex` overrode the `hidden` attribute); Escape now also
  closes it.

## 1.0.0

- Initial QA workstation: test case builder and run viewer with Claude
  CLI assist and Excel export, CSV record reader, Copilot agent roster.
