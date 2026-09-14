"""Shared chat-provider service.

One place other modules go to get an AI completion, so any tool in the
workstation can offer an agent-assisted chat box: call
`service.complete(provider_id, prompt)` and pair it with the front-end
component in static/chatbox.js (which lists these providers in its
dropdown via /agents/api/providers).

Providers:
- "claude-cli" — the locally installed Claude Code CLI (`claude -p`),
  using the user's existing login; the default.
- any registered Copilot agent id — routed live to Copilot Studio over
  the M365 Agents SDK or Direct Line, whichever the agent is set up for.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

from . import copilot, directline, store

CLAUDE_CLI = "claude-cli"
CLAUDE_PATHS = ["claude", "/opt/homebrew/bin/claude", "/usr/local/bin/claude"]
CLI_TIMEOUT = 240
DEBUG_LOG = Path(__file__).resolve().parents[2] / "data" / "assist_debug.log"


class ProviderError(Exception):
    """Completion failed; str() is a message meant for the tester."""

    def __init__(self, message, code="provider_failed"):
        super().__init__(message)
        self.code = code


def list_providers():
    """Providers a chat box can offer, default first."""
    providers = [{"id": CLAUDE_CLI, "name": "Claude CLI (local)",
                  "kind": "cli", "status": ""}]
    for a in store.load_agents():
        providers.append({"id": a["id"], "name": a["name"], "kind": "copilot",
                          "status": a.get("status", "")})
    return providers


def agent_backend(agent):
    """Direct Line when the agent was registered with a web-channel secret,
    otherwise the M365 Agents SDK (Entra sign-in) path."""
    if (agent.get("directline_secret") or "").strip():
        return directline
    return copilot


def complete(provider_id, prompt):
    """Send `prompt` to the chosen provider and return its raw text reply."""
    if not provider_id or provider_id == CLAUDE_CLI:
        return _run_claude_cli(prompt)
    agent = store.get_agent(provider_id)
    if agent is None:
        raise ProviderError("The selected agent no longer exists — pick "
                            "another one in the chat box.", "no_provider")
    try:
        replies = agent_backend(agent).ask(agent, prompt)
    except copilot.CopilotError as exc:
        store.set_status(agent["id"], "error")
        raise ProviderError(str(exc), "agent_failed") from exc
    store.set_status(agent["id"], "connected")
    return "\n\n".join(replies) if replies else ""


def extract_json(text):
    """Parse a model's JSON reply, tolerating code fences or stray prose."""
    for candidate in (text, text.strip("`").lstrip("json")):
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            return None
    return None


# ---------- Claude CLI backend ----------

def _clean_env():
    """Minimal environment for the CLI.

    If this server was launched from inside a Claude Code session, the
    inherited CLAUDE_*/ANTHROPIC_* variables point the nested CLI at that
    session's plumbing and it hangs — so start from scratch instead.
    """
    keep = ("PATH", "HOME", "USER", "SHELL", "TERM", "LANG", "TMPDIR")
    return {k: os.environ[k] for k in keep if k in os.environ}


def _claude_bin():
    for p in CLAUDE_PATHS:
        found = shutil.which(p) if "/" not in p else (p if shutil.which(p) else None)
        if found:
            return found
    return None


def _run_claude_cli(prompt):
    binary = _claude_bin()
    if not binary:
        raise ProviderError(
            "Claude CLI not found on this machine — install Claude Code, or "
            "pick a Copilot agent in the chat box instead.", "no_provider")
    try:
        proc = subprocess.run(
            [binary, "-p", prompt],
            capture_output=True, text=True, timeout=CLI_TIMEOUT,
            stdin=subprocess.DEVNULL, env=_clean_env(),
            cwd=os.path.expanduser("~"))
    except subprocess.TimeoutExpired:
        raise ProviderError("The agent took too long to answer — try again.",
                            "timeout")
    raw = (proc.stdout or "").strip()
    _log_debug(proc.returncode, raw, proc.stderr)
    if proc.returncode != 0:
        detail = (raw or proc.stderr or "unknown error").strip()
        if "authenticate" in detail.lower() or "401" in detail:
            raise ProviderError(
                "The Claude CLI on this Mac is not logged in. Open Terminal, "
                "run `claude`, and complete the login once — then I'll be "
                "able to answer here.", "auth")
        raise ProviderError(f"Agent error: {detail[:300]}", "cli_failed")
    return raw


def _log_debug(rc, stdout, stderr):
    DEBUG_LOG.parent.mkdir(exist_ok=True)
    DEBUG_LOG.write_text(f"rc={rc}\n--- stdout ---\n{stdout[:4000]}\n"
                         f"--- stderr ---\n{(stderr or '')[:2000]}\n",
                         encoding="utf-8")
