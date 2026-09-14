"""CSV Reader module — upload a CSV and browse records as a form.

Per-field settings (show / star / hide, plus type override) are saved per
column signature, so the same kind of file keeps its layout. UUID fields
get a regenerate button; date fields get a picker defaulting to now.
"""
import io

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


@bp.route("/<file_id>/download")
def download(file_id):
    doc = store.load_file(file_id)
    if doc is None:
        return redirect(url_for("csvreader.index"))
    return send_file(io.BytesIO(store.to_csv_bytes(doc)),
                     as_attachment=True, download_name=doc["name"],
                     mimetype="text/csv")
