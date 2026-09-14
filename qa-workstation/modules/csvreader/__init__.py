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
    raw = f.read()
    if f.filename.lower().endswith(".json"):
        doc = store.parse_json_file(f.filename, raw)
    else:
        doc = store.parse_csv(f.filename, raw)
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


CLEAN_CONTRACT = """
When the tester asks you to CLEAN, FIX, or CONVERT data, respond with ONLY one JSON object — no markdown fences, no text outside it:
{"reply": "<short summary of every change you made>", "cleaned": [["header1", "header2", ...], ["row1col1", ...], ...]}
- "cleaned" is the COMPLETE table including the header row as the first list; every cell a string.
- Typical cleaning: trim whitespace, normalise casing and date formats (YYYY-MM-DD), unify inconsistent values of the same thing, remove exact duplicate records, fill derivable blanks — never invent data you cannot derive.
For questions and analysis, answer in plain text only (no JSON)."""


@bp.route("/ask", methods=["POST"])
def ask_general():
    """CSV assistant on the index page — clean/convert pasted or attached
    data into a new file, or answer general CSV questions."""
    return _run_chat(None)


@bp.route("/<file_id>/ask", methods=["POST"])
def ask(file_id):
    """Data chat over one file: analysis Q&A, plus cleaning into a new file."""
    doc = store.load_file(file_id)
    if doc is None:
        return jsonify({"reply": "File not found.", "error": "not_found"}), 404
    return _run_chat(doc)


def _run_chat(doc):
    from modules.agents import service
    data = request.get_json(force=True)
    convo = ""
    history = data.get("history", [])
    if history:
        convo = "Conversation so far:\n" + "\n".join(
            f'{m["role"]}: {m["text"]}' for m in history[-8:]) + "\n\n"

    if doc is not None:
        lines = [",".join(doc["headers"])]
        total, shown = len(lines[0]), 0
        for row in doc["rows"]:
            line = ",".join(row)
            total += len(line)
            if shown >= 500 or total > 45000:
                break
            lines.append(line)
            shown += 1
        truncated = shown < len(doc["rows"])
        trunc_note = (f"\n[... {len(doc['rows']) - shown} more records not shown "
                      "— the data is TRUNCATED: refuse cleaning requests and "
                      "explain the file is too large to clean in chat; "
                      "analysis covers the shown records only]" if truncated else "")
        clean_part = "" if truncated else CLEAN_CONTRACT
        prompt = f"""You are a QA data analyst embedded in a CSV record viewer. The tester asks about the data below (and any attached documents): counts, filters, duplicates, anomalies, format problems, summaries — answer precisely, quote exact values, reference records by 1-based record number.
{clean_part}

File: {doc["name"]} — {len(doc["rows"])} records, {len(doc["headers"])} fields.
Data (CSV, first line is the header):
{chr(10).join(lines)}{trunc_note}

{convo}Tester's message: {data.get("message", "")}
"""
    else:
        prompt = f"""You are a QA data assistant on the CSV reader page. The tester pastes messy text or attaches documents/Excel and you convert and clean them into proper CSV data; you also answer general CSV questions.
{CLEAN_CONTRACT}

{convo}Tester's message: {data.get("message", "")}
"""

    try:
        raw = service.complete_with_attachments(
            data.get("provider"), prompt, data.get("attachments"))
    except service.ProviderError as exc:
        return jsonify({"reply": str(exc), "error": exc.code})

    parsed = service.extract_json(raw)
    cleaned = parsed.get("cleaned") if isinstance(parsed, dict) else None
    if isinstance(cleaned, list) and len(cleaned) >= 2:
        table = [[str(c) for c in r] for r in cleaned if isinstance(r, list)]
        if doc is not None:
            base = doc["name"][:-4] if doc["name"].lower().endswith(".csv") else doc["name"]
            name = f"{base}-cleaned.csv"
        else:
            name = f"cleaned-{time.strftime('%Y%m%d-%H%M')}.csv"
        newdoc = store.create_from_table(name, table)
        if newdoc is not None:
            return jsonify({
                "reply": str(parsed.get("reply", "")).strip() or "Cleaned file created.",
                "cleaned_file": {"id": newdoc["id"], "name": newdoc["name"],
                                 "url": url_for("csvreader.viewer", file_id=newdoc["id"])},
            })
    if isinstance(parsed, dict) and parsed.get("reply"):
        return jsonify({"reply": str(parsed["reply"])[:6000]})
    return jsonify({"reply": (raw or "(no reply)")[:6000]})


@bp.route("/<file_id>/download")
def download(file_id):
    doc = store.load_file(file_id)
    if doc is None:
        return redirect(url_for("csvreader.index"))
    name = doc["name"]
    if not name.lower().endswith(".csv"):
        name = name.rsplit(".", 1)[0] + ".csv"
    return send_file(io.BytesIO(store.to_csv_bytes(doc)),
                     as_attachment=True, download_name=name,
                     mimetype="text/csv")


@bp.route("/<file_id>/download.json")
def download_json(file_id):
    doc = store.load_file(file_id)
    if doc is None:
        return redirect(url_for("csvreader.index"))
    name = doc["name"]
    if not name.lower().endswith(".json"):
        name = name.rsplit(".", 1)[0] + ".json"
    return send_file(io.BytesIO(store.to_json_bytes(doc)),
                     as_attachment=True, download_name=name,
                     mimetype="application/json")
