"""Live Copilot Studio chat via the Microsoft 365 Agents SDK.

Talks to a published Copilot Studio agent using
microsoft-agents-copilotstudio-client (the Python M365 Agents SDK).
Sign-in is a delegated MSAL flow: silent from the local token cache when
possible, otherwise a browser window opens once and the token is cached
in data/msal_token_cache.json — the same pattern as the SDK's own
copilotstudio-client sample.

One-time setup per tenant (the chat page shows these too):
- An Entra ID app registration with a "Mobile and desktop applications"
  platform using the http://localhost redirect URI, and the delegated
  Power Platform API permission CopilotStudio.Copilots.Invoke (consented).
- The agent published in Copilot Studio. Its Environment ID and schema
  name are under Settings > Advanced > Metadata in Copilot Studio.
"""
import asyncio
from pathlib import Path

try:
    import msal
    from microsoft_agents.copilotstudio.client import (
        AgentType,
        ConnectionSettings,
        CopilotClient,
        PowerPlatformCloud,
    )
    SDK_ERROR = None
except ImportError as exc:  # keep the app usable without the SDK installed
    msal = None
    SDK_ERROR = (
        f"Microsoft 365 Agents SDK not installed ({exc}). "
        "Run: pip3 install -r requirements.txt"
    )

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
TOKEN_CACHE = DATA_DIR / "msal_token_cache.json"
SCOPES = ["https://api.powerplatform.com/.default"]
SIGNIN_TIMEOUT = 180

# agent id -> Copilot Studio conversation id (in-memory; a restart simply
# starts a fresh conversation)
_conversations = {}


class CopilotError(Exception):
    """A connection/sign-in problem with a message meant for the tester."""


def _field(agent, key):
    return (agent.get(key) or "").strip()


def missing_config(agent):
    """Sign-in always needs tenant + client id; the agent address is either
    the Direct Connect URL or the Environment ID + schema name pair."""
    missing = [f for f in ("tenant_id", "app_client_id") if not _field(agent, f)]
    if not _field(agent, "direct_connect_url"):
        missing += [f for f in ("environment_id", "schema_name")
                    if not _field(agent, f)]
    return missing


def _require_ready(agent):
    if SDK_ERROR:
        raise CopilotError(SDK_ERROR)
    missing = missing_config(agent)
    if missing:
        raise CopilotError(
            "Agent is not fully configured — missing: " + ", ".join(missing)
            + ". Edit it on the Copilot Agents page.")


def _acquire_token(agent):
    cache = msal.SerializableTokenCache()
    if TOKEN_CACHE.exists():
        cache.deserialize(TOKEN_CACHE.read_text(encoding="utf-8"))
    app = msal.PublicClientApplication(
        client_id=agent["app_client_id"],
        authority=f"https://login.microsoftonline.com/{agent['tenant_id']}",
        token_cache=cache,
    )
    result = None
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
    if not result:
        # Local workstation: open the system browser once for sign-in.
        result = app.acquire_token_interactive(
            scopes=SCOPES, timeout=SIGNIN_TIMEOUT)
    if cache.has_state_changed:
        DATA_DIR.mkdir(exist_ok=True)
        TOKEN_CACHE.write_text(cache.serialize(), encoding="utf-8")
    if not result or "access_token" not in result:
        detail = (result or {}).get("error_description") \
            or (result or {}).get("error") or "sign-in was cancelled or timed out"
        raise CopilotError(f"Microsoft sign-in failed: {detail}")
    return result["access_token"]


def _client(agent, token):
    settings = ConnectionSettings(
        environment_id=_field(agent, "environment_id"),
        agent_identifier=_field(agent, "schema_name"),
        cloud=PowerPlatformCloud.PROD,
        copilot_agent_type=AgentType.PUBLISHED,
        direct_connect_url=_field(agent, "direct_connect_url") or None,
    )
    return CopilotClient(settings, token)


def _collect(activity, state, replies):
    """Pull the conversation id and human-readable text out of one activity."""
    conv = getattr(activity, "conversation", None)
    if conv is not None and getattr(conv, "id", None):
        state["conversation_id"] = conv.id
    if activity.type != "message":
        return
    if activity.text:
        replies.append(activity.text)
    suggested = getattr(activity, "suggested_actions", None)
    actions = getattr(suggested, "actions", None) if suggested else None
    if actions:
        titles = [a.title for a in actions if getattr(a, "title", None)]
        if titles:
            replies.append("Suggestions: " + " · ".join(titles))


async def _start_conversation(agent, token, state):
    client = _client(agent, token)
    replies = []
    async for activity in client.start_conversation():
        _collect(activity, state, replies)
    return replies


async def _ask_question(agent, token, conversation_id, message, state):
    client = _client(agent, token)
    replies = []
    async for activity in client.ask_question(message, conversation_id):
        _collect(activity, state, replies)
    return replies


def connect(agent):
    """Start (or restart) a conversation. Returns the greeting messages."""
    _require_ready(agent)
    token = _acquire_token(agent)
    state = {}
    try:
        replies = asyncio.run(_start_conversation(agent, token, state))
    except Exception as exc:
        raise CopilotError(f"Could not reach Copilot Studio: {exc}") from exc
    if not state.get("conversation_id"):
        raise CopilotError("Copilot Studio did not return a conversation id — "
                           "check the connection details (Direct Connect URL or "
                           "Environment ID + schema name).")
    _conversations[agent["id"]] = state["conversation_id"]
    return replies


def ask(agent, message):
    """Send one message; starts a conversation first if there is none yet."""
    _require_ready(agent)
    token = _acquire_token(agent)
    conversation_id = _conversations.get(agent["id"])
    greeting = []
    if not conversation_id:
        state = {}
        greeting = asyncio.run(_start_conversation(agent, token, state))
        conversation_id = state.get("conversation_id")
        if not conversation_id:
            raise CopilotError("Could not start a Copilot Studio conversation — "
                               "check the connection details (Direct Connect URL "
                               "or Environment ID + schema name).")
        _conversations[agent["id"]] = conversation_id
    state = {}
    try:
        replies = asyncio.run(
            _ask_question(agent, token, conversation_id, message, state))
    except Exception as exc:
        raise CopilotError(f"Copilot Studio request failed: {exc}") from exc
    return greeting + replies


def reset(agent_id):
    """Forget the current conversation so the next message starts fresh."""
    _conversations.pop(agent_id, None)
