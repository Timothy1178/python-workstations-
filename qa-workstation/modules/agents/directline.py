"""Direct Line fallback — connect with a Copilot Studio web-channel secret.

Alternative to the M365 Agents SDK path (copilot.py) for when there is no
Entra app registration: register the agent with the secret from Copilot
Studio > Settings > Security > Web channel security. The agent's
Authentication setting must be "No authentication" (and republished),
otherwise it still demands a Microsoft sign-in inside the conversation.

Talks Direct Line 3.0 REST: exchange the secret for a scoped token, open a
conversation, post the tester's message, poll for the agent's replies.
"""
import time

import requests

from .copilot import CopilotError

BASE = "https://directline.botframework.com/v3/directline"
USER_ID = "qa-workstation"
POLL_INTERVAL = 1.0
REPLY_TIMEOUT = 60      # seconds to wait for the first reply
SETTLE = 2.5            # keep polling this long after a reply, for multi-message turns
GREETING_TIMEOUT = 6

# agent id -> {token, conversation_id, watermark}
_sessions = {}


def missing_config(agent):
    # Presence of the secret is what routes an agent here; nothing else needed.
    return []


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _check(resp, doing):
    if resp.status_code in (401, 403):
        raise CopilotError(
            f"Direct Line rejected the secret while {doing} — check it against "
            "Copilot Studio > Settings > Security > Web channel security, and "
            "that the agent is published.")
    if resp.status_code == 404:
        raise CopilotError(f"Direct Line conversation not found while {doing} — "
                           "press ↺ New conversation and try again.")
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        raise CopilotError(f"Direct Line error while {doing}: {exc}") from exc
    return resp


def _start_session(secret):
    try:
        r = requests.post(f"{BASE}/tokens/generate",
                          headers=_headers(secret), timeout=30)
        _check(r, "signing in")
        token = r.json()["token"]
        r = requests.post(f"{BASE}/conversations",
                          headers=_headers(token), timeout=30)
        _check(r, "starting the conversation")
    except requests.RequestException as exc:
        raise CopilotError(f"Could not reach Direct Line: {exc}") from exc
    data = r.json()
    return {"token": data.get("token") or token,
            "conversation_id": data["conversationId"],
            "watermark": None}


def _fetch_new(session):
    url = f"{BASE}/conversations/{session['conversation_id']}/activities"
    params = {"watermark": session["watermark"]} if session["watermark"] else {}
    r = requests.get(url, headers=_headers(session["token"]),
                     params=params, timeout=30)
    _check(r, "reading replies")
    data = r.json()
    session["watermark"] = data.get("watermark") or session["watermark"]
    replies = []
    for a in data.get("activities", []):
        if a.get("type") != "message":
            continue
        if (a.get("from") or {}).get("id") == USER_ID:
            continue
        if a.get("text"):
            replies.append(a["text"])
        actions = ((a.get("suggestedActions") or {}).get("actions")) or []
        titles = [x.get("title") for x in actions if x.get("title")]
        if titles:
            replies.append("Suggestions: " + " · ".join(titles))
    return replies


def _poll(session, timeout):
    """Collect replies; once the first arrives, only wait SETTLE longer so
    multi-message turns come through without dragging out every request."""
    replies = []
    stop = time.time() + timeout
    while time.time() < stop:
        got = _fetch_new(session)
        if got:
            replies += got
            stop = min(stop, time.time() + SETTLE)
        time.sleep(POLL_INTERVAL)
    return replies


def _secret(agent):
    return (agent.get("directline_secret") or "").strip()


def connect(agent):
    """Open a fresh conversation; returns any greeting messages."""
    session = _start_session(_secret(agent))
    _sessions[agent["id"]] = session
    return _poll(session, GREETING_TIMEOUT)


def ask(agent, message):
    session = _sessions.get(agent["id"])
    greeting = []
    if session is None:
        session = _start_session(_secret(agent))
        _sessions[agent["id"]] = session
        greeting = _poll(session, GREETING_TIMEOUT)
    activity = {"type": "message", "from": {"id": USER_ID}, "text": message}
    try:
        r = requests.post(
            f"{BASE}/conversations/{session['conversation_id']}/activities",
            headers=_headers(session["token"]), json=activity, timeout=30)
        _check(r, "sending the message")
        replies = _poll(session, REPLY_TIMEOUT)
    except CopilotError:
        _sessions.pop(agent["id"], None)  # token/conversation likely expired
        raise
    except requests.RequestException as exc:
        raise CopilotError(f"Could not reach Direct Line: {exc}") from exc
    if not replies and not greeting:
        raise CopilotError("The agent did not reply within "
                           f"{REPLY_TIMEOUT}s — try again or press "
                           "↺ New conversation.")
    return greeting + replies


def reset(agent_id):
    _sessions.pop(agent_id, None)
