"""Msg5 Json — transaction string editor.

Paste a transaction JSON (an object whose "playloadJson" holds an
XML-entity-encoded payload), edit its fields, generate the updated
string. The editing itself runs in the browser (XML DOM, like the
original Transaction String Editor); this module stores the named
messages and the editor's field configuration under data/msg5/.
"""
import json

from flask import Blueprint, render_template, request, jsonify

from . import store

bp = Blueprint("msg5", __name__, url_prefix="/msg5")

MODULE_INFO = {
    "name": "Msg5 Json",
    "url": "/msg5",
    "desc": "Transaction string editor: load, edit, regenerate and save Msg5 JSON payloads.",
    "icon": "🧾",
}


@bp.route("/")
def index():
    return render_template("msg5/index.html",
                           config=store.load_config(),
                           messages=store.list_messages(),
                           field_types=store.FIELD_TYPES,
                           default_fields=store.DEFAULT_FIELDS)


# ---------- config (fields + toggles) ----------

@bp.route("/api/config", methods=["GET", "POST"])
def config():
    if request.method == "POST":
        data = request.get_json(force=True) or {}
        cfg = store.load_config()
        if data.get("reset_fields"):
            cfg["fields"] = json.loads(json.dumps(store.DEFAULT_FIELDS))
        for k in ("auto_increment", "pretty", "increment_tag", "fields"):
            if k in data:
                cfg[k] = data[k]
        return jsonify({"ok": True, "config": store.save_config(cfg)})
    return jsonify({"ok": True, "config": store.load_config()})


# ---------- saved messages ----------

@bp.route("/api/messages", methods=["GET", "POST"])
def messages():
    if request.method == "POST":
        data = request.get_json(force=True) or {}
        text = data.get("json", "")
        if not isinstance(text, str) or not text.strip():
            return jsonify({"ok": False, "error": "nothing to save — load or generate a JSON first"}), 400
        try:
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise ValueError("must be one JSON object")
        except ValueError as e:
            return jsonify({"ok": False, "error": f"not valid JSON: {e}"}), 400
        m = store.save_message(data.get("id", ""), data.get("name", ""), text, data.get("notes", ""))
        return jsonify({"ok": True, "message": {k: m[k] for k in ("id", "name", "notes", "updated")},
                        "messages": store.list_messages()})
    return jsonify({"ok": True, "messages": store.list_messages()})


@bp.route("/api/messages/<mid>", methods=["GET", "DELETE"])
def message(mid):
    if request.method == "DELETE":
        if not store.delete_message(mid):
            return jsonify({"ok": False, "error": "not found"}), 404
        return jsonify({"ok": True, "messages": store.list_messages()})
    m = store.get_message(mid)
    if m is None:
        return jsonify({"ok": False, "error": "not found"}), 404
    return jsonify({"ok": True, "message": m})
