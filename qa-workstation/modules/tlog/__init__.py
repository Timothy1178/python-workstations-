"""TLog Handler — editor for the "create msg5" function call messages.

Import the BU documents (one UPDATE_TRANSACTION_STOCK_FROM_MSG5 message
each) as templates, pick one, edit the fields / items / tenders, and
copy the one-line string to send through Offset Explorer. Editing runs
in the browser; this module keeps the library and the field config
under data/tlog/ (gitignored).
"""
import json
import time

from flask import Blueprint, render_template, request, jsonify, send_file

from . import store, csvset
from modules import msgfiles

bp = Blueprint("tlog", __name__, url_prefix="/tlog")

MODULE_INFO = {
    "name": "TLog Handler",
    "url": "/tlog",
    "desc": "Create msg5 requests per BU: import the BU docs, edit fields, items and tenders, copy the string for Offset Explorer.",
    "icon": "📨",
}


@bp.route("/")
def index():
    store.migrate_msg5()
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


@bp.route("/api/read-file", methods=["POST"])
def read_file():
    """Multipart 'file' -> every message found in it (Excel cell, CSV
    cell, Word paragraph, .json / .txt) without saving anything; the
    page loads one into the editor or saves them all as templates."""
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"ok": False, "error": "no file"}), 400
    try:
        found = msgfiles.read_upload(f.filename, f.read())
    except Exception as e:
        return jsonify({"ok": False, "error": f"could not read {f.filename}: {e}"}), 400
    if not found:
        return jsonify({"ok": False, "error": f"{f.filename}: no message with a playloadJson found"}), 400
    return jsonify({"ok": True, "filename": f.filename, "messages": found})


@bp.route("/api/library/bulk", methods=["POST"])
def library_bulk():
    data = request.get_json(force=True) or {}
    n = 0
    for m in data.get("messages", []):
        if isinstance(m, dict) and isinstance(m.get("json"), str) and m["json"].strip():
            store.save_entry("", str(m.get("name", "")), m["json"], bu_code=str(m.get("bu_code", "")),
                             kind="template" if data.get("kind") == "template" else "request",
                             notes=str(m.get("notes", "")))
            n += 1
    return jsonify({"ok": True, "saved": n, "entries": store.list_entries()})


# ---------- CSV set (ORDER / PAYMENT / ITEMS / PROMOTION + .ok) ----------

@bp.route("/csv")
def csv_page():
    lay = csvset.load_layout()
    return render_template("tlog/csvset.html", layout=lay, shared=csvset.shared_names(lay),
                           sets=csvset.list_sets(), entries=store.list_entries(),
                           file_types=csvset.FILE_TYPES, child_of=csvset.CHILD_OF,
                           formats=csvset.FORMATS, autos=csvset.AUTOS)


@bp.route("/api/csv/layout", methods=["GET", "POST"])
def csv_layout():
    if request.method == "POST":
        data = request.get_json(force=True) or {}
        if data.get("reset"):
            lay = csvset.save_layout(csvset.DEFAULT_LAYOUT)
        else:
            lay = csvset.load_layout()
            for k in ("name_format", "ref_base"):
                if k in data:
                    lay[k] = data[k]
            if isinstance(data.get("files"), dict):
                for ft, cols in data["files"].items():
                    if ft in csvset.FILE_TYPES and isinstance(cols, list):
                        lay["files"][ft] = cols
            lay = csvset.save_layout(lay)
        return jsonify({"ok": True, "layout": lay, "shared": csvset.shared_names(lay)})
    lay = csvset.load_layout()
    return jsonify({"ok": True, "layout": lay, "shared": csvset.shared_names(lay)})


@bp.route("/api/csv/sets", methods=["GET", "POST"])
def csv_sets():
    if request.method == "POST":
        data = request.get_json(force=True) or {}
        s = csvset.save_set(data.get("id", ""), data)
        return jsonify({"ok": True, "set": {k: s[k] for k in ("id", "name", "bu", "date", "seq", "updated")},
                        "sets": csvset.list_sets()})
    return jsonify({"ok": True, "sets": csvset.list_sets()})


@bp.route("/api/csv/sets/<sid>", methods=["GET", "DELETE"])
def csv_set(sid):
    if request.method == "DELETE":
        if not csvset.delete_set(sid):
            return jsonify({"ok": False, "error": "not found"}), 404
        return jsonify({"ok": True, "sets": csvset.list_sets()})
    s = csvset.get_set(sid)
    if s is None:
        return jsonify({"ok": False, "error": "not found"}), 404
    return jsonify({"ok": True, "set": s})


@bp.route("/api/csv/import", methods=["POST"])
def csv_import():
    """Multipart 'files': the 4 CSVs (and/or .ok, or a zip) -> transactions."""
    ups = [(f.filename, f.read()) for f in request.files.getlist("files") if f.filename]
    if not ups:
        return jsonify({"ok": False, "error": "no files"}), 400
    try:
        result = csvset.import_set(csvset.load_layout(), ups)
    except Exception as e:
        return jsonify({"ok": False, "error": f"could not read the files: {e}"}), 400
    if "error" in result:
        return jsonify({"ok": False, **result}), 400
    return jsonify({"ok": True, **result})


@bp.route("/api/csv/export", methods=["POST"])
def csv_export():
    """JSON {bu, date, seq, files: {TYPE: [[cell,...],...]}} -> zip of
    4 CSV + 4 empty .ok files named per the template."""
    data = request.get_json(force=True) or {}
    lay = csvset.load_layout()
    bu = str(data.get("bu", "")).strip().upper() or "BU"
    date = (str(data.get("date", "")).strip() or time.strftime("%Y%m%d"))[:8]
    seq = str(data.get("seq", "")).strip() or "1"
    files = data.get("files") if isinstance(data.get("files"), dict) else {}
    buf = csvset.build_zip(lay, bu, date, seq, files)
    return send_file(buf, as_attachment=True, mimetype="application/zip",
                     download_name=f"TLOG_{bu}_{date}_{seq}.zip")
