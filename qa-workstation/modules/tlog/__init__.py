"""TLog Handler — editor for the "create msg5" function call messages.

Import the BU documents (one UPDATE_TRANSACTION_STOCK_FROM_MSG5 message
each) as templates, pick one, edit the fields / items / tenders, and
copy the one-line string to send through Offset Explorer. Editing runs
in the browser; this module keeps the library and the field config
under data/tlog/ (gitignored).
"""
import json

from flask import Blueprint, render_template, request, jsonify

from . import store

bp = Blueprint("tlog", __name__, url_prefix="/tlog")

MODULE_INFO = {
    "name": "TLog Handler",
    "url": "/tlog",
    "desc": "Create msg5 requests per BU: import the BU docs, edit fields, items and tenders, copy the string for Offset Explorer.",
    "icon": "📨",
}


@bp.route("/")
def index():
    return render_template("tlog/index.html",
                           config=store.load_config(),
                           entries=store.list_entries(),
                           field_types=store.FIELD_TYPES)


@bp.route("/api/config", methods=["GET", "POST"])
def config():
    if request.method == "POST":
        data = request.get_json(force=True) or {}
        cfg = store.load_config()
        if data.get("reset_fields"):
            cfg["fields"] = json.loads(json.dumps(store.DEFAULT_FIELDS))
        for k in ("auto_increment", "auto_timestamp", "auto_recalc", "pretty", "fields"):
            if k in data:
                cfg[k] = data[k]
        return jsonify({"ok": True, "config": store.save_config(cfg)})
    return jsonify({"ok": True, "config": store.load_config()})


@bp.route("/api/library", methods=["GET", "POST"])
def library():
    if request.method == "POST":
        data = request.get_json(force=True) or {}
        text = data.get("json", "")
        if not isinstance(text, str) or not text.strip():
            return jsonify({"ok": False, "error": "nothing to save — load or generate a message first"}), 400
        try:
            if not isinstance(json.loads(text), dict):
                raise ValueError("must be one JSON object")
        except ValueError as e:
            return jsonify({"ok": False, "error": f"not valid JSON: {e}"}), 400
        e = store.save_entry(data.get("id", ""), data.get("name", ""), text,
                             bu_code=data.get("bu_code", ""), kind=data.get("kind", "request"),
                             notes=data.get("notes", ""))
        return jsonify({"ok": True, "entry": {k: e[k] for k in ("id", "name", "bu_code", "kind", "updated")},
                        "entries": store.list_entries()})
    return jsonify({"ok": True, "entries": store.list_entries()})


@bp.route("/api/library/<eid>", methods=["GET", "DELETE"])
def library_entry(eid):
    if request.method == "DELETE":
        if not store.delete_entry(eid):
            return jsonify({"ok": False, "error": "not found"}), 404
        return jsonify({"ok": True, "entries": store.list_entries()})
    e = store.get_entry(eid)
    if e is None:
        return jsonify({"ok": False, "error": "not found"}), 404
    return jsonify({"ok": True, "entry": e})


@bp.route("/api/import", methods=["POST"])
def import_files():
    """Multipart 'files': .docx / .json / .txt BU documents -> templates."""
    added, errors = [], []
    for f in request.files.getlist("files"):
        if not f.filename:
            continue
        try:
            found = store.read_upload(f.filename, f.read())
        except Exception as e:  # not a docx / unreadable
            errors.append(f"{f.filename}: could not read ({e})")
            continue
        if not found:
            errors.append(f"{f.filename}: no message with a playloadJson found")
            continue
        for m in found:
            e = store.save_entry("", m["name"], m["json"], bu_code=m["bu_code"],
                                 kind="template", notes=f"imported from {f.filename}")
            added.append({"id": e["id"], "name": e["name"], "bu_code": e["bu_code"]})
    return jsonify({"ok": bool(added) or not errors, "added": added, "errors": errors,
                    "entries": store.list_entries()})
