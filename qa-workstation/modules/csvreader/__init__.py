"""CSV Reader module — upload a CSV and browse records as a form.

Per-field settings (show / star / hide, plus type override) are saved per
column signature, so the same kind of file keeps its layout. UUID fields
get a regenerate button; date fields get a picker defaulting to now.
"""
import io
import time

from flask import (Blueprint, render_template, request, redirect, url_for,
                   jsonify, send_file)

from . import store

bp = Blueprint("csvreader", __name__, url_prefix="/csv")

MODULE_INFO = {
    "name": "CSV Reader",
    "url": "/csv",
    "desc": "Open CSV files as record forms — show, star or hide fields.",
    "icon": "📄",
}


@bp.route("/")
def index():
    return render_template("csvreader/index.html", files=store.list_files())


@bp.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("csvfile")
    if not f or not f.filename:
        return redirect(url_for("csvreader.index"))
    doc = store.parse_csv(f.filename, f.read())
    if doc is None:
        return redirect(url_for("csvreader.index"))
    return redirect(url_for("csvreader.viewer", file_id=doc["id"]))


@bp.route("/paste", methods=["POST"])
def paste():
    """Convert pasted text (comma/tab/semicolon/pipe separated) to a CSV doc."""
    name = request.form.get("name", "").strip() \
        or f"pasted-{time.strftime('%Y%m%d-%H%M')}"
    if not name.lower().endswith(".csv"):
        name += ".csv"
    doc = store.parse_pasted(
        name,
        request.form.get("pasted", ""),
        delimiter=request.form.get("delimiter", "auto"),
        has_header=request.form.get("has_header") == "on",
    )
    if doc is None:
        return redirect(url_for("csvreader.index"))
    return redirect(url_for("csvreader.viewer", file_id=doc["id"]))


@bp.route("/<file_id>")
def viewer(file_id):
    doc = store.load_file(file_id)
    if doc is None:
        return redirect(url_for("csvreader.index"))
    return render_template("csvreader/viewer.html", doc=doc,
                           settings=store.load_settings(doc))


@bp.route("/<file_id>/delete", methods=["POST"])
def delete(file_id):
    store.delete_file(file_id)
    return redirect(url_for("csvreader.index"))


@bp.route("/<file_id>/settings", methods=["POST"])
def settings(file_id):
    doc = store.load_file(file_id)
    if doc is None:
        return jsonify({"ok": False, "error": "file not found"}), 404
    clean = store.save_settings(doc, request.get_json(force=True))
    return jsonify({"ok": True, "settings": clean})


@bp.route("/<file_id>/row/<int:idx>", methods=["POST"])
def save_row(file_id, idx):
    doc = store.load_file(file_id)
    if doc is None:
        return jsonify({"ok": False, "error": "file not found"}), 404
    if not 0 <= idx < len(doc["rows"]):
        return jsonify({"ok": False, "error": "row out of range"}), 404
    values = request.get_json(force=True).get("values", [])
    row = doc["rows"][idx]
    for i, v in enumerate(values[:len(row)]):
        row[i] = str(v)
    store.save_file(doc)
    return jsonify({"ok": True})


@bp.route("/<file_id>/ask", methods=["POST"])
def ask(file_id):
    """Data Q&A over this file, for the viewer's chat box."""
    from modules.agents import service
    doc = store.load_file(file_id)
    if doc is None:
        return jsonify({"reply": "File not found.", "error": "not_found"}), 404
    data = request.get_json(force=True)
    lines = [",".join(doc["headers"])]
    total = len(lines[0])
    shown = 0
    for row in doc["rows"]:
        line = ",".join(row)
        total += len(line)
        if shown >= 500 or total > 45000:
            lines.append(f"[... {len(doc['rows']) - shown} more records truncated]")
            break
        lines.append(line)
        shown += 1
    convo = ""
    history = data.get("history", [])
    if history:
        convo = "Conversation so far:\n" + "\n".join(
            f'{m["role"]}: {m["text"]}' for m in history[-8:]) + "\n\n"
    prompt = f"""You are a QA data analyst embedded in a CSV record viewer. Answer the tester's question about the data below (and any attached documents): counts, filters, duplicates, anomalies, format problems, summaries, comparisons. Answer in plain text; be precise with numbers, quote exact values, and reference records by their 1-based record number. If the data was truncated, say your answer covers the shown records only.

File: {doc["name"]} — {len(doc["rows"])} records, {len(doc["headers"])} fields.
Data (CSV, first line is the header):
{chr(10).join(lines)}

{convo}Tester's question: {data.get("message", "")}
"""
    try:
        raw = service.complete_with_attachments(
            data.get("provider"), prompt, data.get("attachments"))
    except service.ProviderError as exc:
        return jsonify({"reply": str(exc), "error": exc.code})
    return jsonify({"reply": raw[:6000] or "(no reply)"})


@bp.route("/<file_id>/download")
def download(file_id):
    doc = store.load_file(file_id)
    if doc is None:
        return redirect(url_for("csvreader.index"))
    return send_file(io.BytesIO(store.to_csv_bytes(doc)),
                     as_attachment=True, download_name=doc["name"],
                     mimetype="text/csv")
