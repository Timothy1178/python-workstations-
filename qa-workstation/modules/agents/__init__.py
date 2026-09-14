"""Copilot Agents module — Copilot Studio agents with live chat.

Stage 1 registered agents (name, QA role, connection details); this stage
wires the live connection through the Microsoft 365 Agents SDK
(microsoft-agents-copilotstudio-client): each registered agent gets a chat
page that talks to the published Copilot Studio agent.
"""
from flask import Blueprint, jsonify, render_template, request, redirect, url_for

from . import copilot, directline, service, store

_provider = service.agent_backend

bp = Blueprint("agents", __name__, url_prefix="/agents")

MODULE_INFO = {
    "name": "Copilot Agents",
    "url": "/agents",
    "desc": "Copilot Studio agents with live chat via the M365 Agents SDK.",
    "icon": "🤖",
}


@bp.route("/api/providers")
def providers():
    """Chat providers for the shared chat box (static/chatbox.js)."""
    return jsonify({"providers": service.list_providers()})


@bp.route("/")
def index():
    return render_template(
        "agents/index.html",
        agents=store.load_agents(),
        sdk_error=copilot.SDK_ERROR,
    )


@bp.route("/add", methods=["POST"])
def add():
    name = request.form.get("name", "").strip()
    if name:
        store.add_agent(
            name=name,
            role=request.form.get("role", "").strip(),
            notes=request.form.get("notes", "").strip(),
            environment_id=request.form.get("environment_id", "").strip(),
            schema_name=request.form.get("schema_name", "").strip(),
            tenant_id=request.form.get("tenant_id", "").strip(),
            app_client_id=request.form.get("app_client_id", "").strip(),
            direct_connect_url=request.form.get("direct_connect_url", "").strip(),
            directline_secret=request.form.get("directline_secret", "").strip(),
        )
    return redirect(url_for("agents.index"))


@bp.route("/<agent_id>/delete", methods=["POST"])
def delete(agent_id):
    copilot.reset(agent_id)
    directline.reset(agent_id)
    store.delete_agent(agent_id)
    return redirect(url_for("agents.index"))


@bp.route("/<agent_id>/chat")
def chat(agent_id):
    agent = store.get_agent(agent_id)
    if agent is None:
        return redirect(url_for("agents.index"))
    provider = _provider(agent)
    return render_template(
        "agents/chat.html",
        agent=agent,
        missing=provider.missing_config(agent),
        sdk_error=copilot.SDK_ERROR if provider is copilot else None,
    )


@bp.route("/<agent_id>/connect", methods=["POST"])
def connect(agent_id):
    """Start a fresh Copilot Studio conversation (also used as 'reconnect')."""
    agent = store.get_agent(agent_id)
    if agent is None:
        return jsonify({"error": "unknown agent"}), 404
    provider = _provider(agent)
    provider.reset(agent_id)
    try:
        replies = provider.connect(agent)
    except copilot.CopilotError as exc:
        store.set_status(agent_id, "error")
        return jsonify({"error": str(exc)})
    store.set_status(agent_id, "connected")
    return jsonify({"replies": replies})


@bp.route("/<agent_id>/send", methods=["POST"])
def send(agent_id):
    agent = store.get_agent(agent_id)
    if agent is None:
        return jsonify({"error": "unknown agent"}), 404
    message = (request.get_json(silent=True) or {}).get("message", "").strip()
    if not message:
        return jsonify({"error": "empty message"})
    try:
        replies = _provider(agent).ask(agent, message)
    except copilot.CopilotError as exc:
        store.set_status(agent_id, "error")
        return jsonify({"error": str(exc)})
    store.set_status(agent_id, "connected")
    return jsonify({"replies": replies})
