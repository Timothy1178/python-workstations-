"""Mailer module — send Excel tables by email through Outlook, on demand
or on a schedule.

Jobs pair a data source (a table captured by the QA Table Mailer plugin,
a local/OneDrive-synced .xlsx, or a download URL) with an HTML template
and a receiver group. The plugin talks to /mailer/api/* (CORS-open, the
workstation is local-only); people use the pages under /mailer/.
"""
import json

from flask import (Blueprint, jsonify, redirect, render_template, request,
                   url_for)

from . import outlook, scheduler, store

bp = Blueprint("mailer", __name__, url_prefix="/mailer")

MODULE_INFO = {
    "name": "Mailer",
    "url": "/mailer",
    "desc": "Email Excel tables through Outlook — templates, receivers, schedules.",
    "icon": "📧",
}

DAYS = [(0, "Mon"), (1, "Tue"), (2, "Wed"), (3, "Thu"), (4, "Fri"), (5, "Sat"), (6, "Sun")]


@bp.after_request
def _allow_plugin(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


# ---------- pages ----------

@bp.route("/")
def index():
    return render_template("mailer/index.html", jobs=store.list_items("jobs"),
                           templates=store.list_items("templates"),
                           receivers=store.list_items("receivers"),
                           log=store.recent_log(), settings=store.settings(), days=dict(DAYS))


@bp.route("/job/new")
@bp.route("/job/<job_id>")
def job_edit(job_id=None):
    job = store.get_item("jobs", job_id) if job_id else None
    if job_id and job is None:
        return redirect(url_for("mailer.index"))
    return render_template("mailer/job.html", job=job, templates=store.list_items("templates"),
                           receivers=store.list_items("receivers"), days=DAYS)


@bp.route("/job/save", methods=["POST"])
def job_save():
    f = request.form
    src_type = f.get("source_type", "table")
    try:
        table = json.loads(f.get("table_json") or "{}")
    except json.JSONDecodeError:
        table = {}
    job = {
        "id": f.get("id", ""),
        "name": f.get("name", "").strip() or "Untitled job",
        "subject": f.get("subject", "").strip(),
        "template_id": f.get("template_id", ""),
        "receivers_id": f.get("receivers_id", ""),
        "to": f.get("to", "").strip(), "cc": f.get("cc", "").strip(), "bcc": f.get("bcc", "").strip(),
        "source": {
            "type": src_type,
            "table": table if src_type == "table" else (store.get_item("jobs", f.get("id", "")) or {}).get("source", {}).get("table"),
            "path": f.get("path", "").strip(), "url": f.get("url", "").strip(),
            "sheet": f.get("sheet", "").strip(), "range": f.get("range", "").strip().upper(),
            "header_row": f.get("header_row") == "on",
        },
        "schedule": {
            "enabled": f.get("sched_enabled") == "on",
            "time": f.get("sched_time") or "09:00",
            "days": [int(d) for d in f.getlist("sched_days")] or [0, 1, 2, 3, 4],
        },
    }
    existing = store.get_item("jobs", job["id"]) if job["id"] else None
    if existing:
        job["last_run"], job["last_status"] = existing.get("last_run"), existing.get("last_status")
    store.upsert("jobs", job)
    return redirect(url_for("mailer.index"))


@bp.route("/job/<job_id>/run", methods=["POST"])
def job_run(job_id):
    job = store.get_item("jobs", job_id)
    if job:
        scheduler.run_job(job, review=store.settings().get("review_before_send", False))
    return redirect(url_for("mailer.index"))


@bp.route("/job/<job_id>/delete", methods=["POST"])
def job_delete(job_id):
    store.delete_item("jobs", job_id)
    return redirect(url_for("mailer.index"))


@bp.route("/job/<job_id>/preview")
def job_preview(job_id):
    job = store.get_item("jobs", job_id)
    if job is None:
        return "job not found", 404
    template = store.get_item("templates", job.get("template_id", "")) or {}
    try:
        table = store.resolve_table(job)
    except Exception as exc:
        return f"<p style='color:#b91c1c;font-family:sans-serif'>Cannot load data: {exc}</p>"
    subject, body = store.render(template, job, table)
    return f"<p style='font-family:sans-serif;color:#6b7280'>Subject: <b>{subject}</b></p>{body}"


@bp.route("/templates")
@bp.route("/templates/<template_id>")
def templates(template_id=None):
    current = store.get_item("templates", template_id) if template_id else None
    return render_template("mailer/templates.html", templates=store.list_items("templates"),
                           current=current, default_html=store.DEFAULT_TEMPLATE_HTML)


@bp.route("/templates/save", methods=["POST"])
def template_save():
    f = request.form
    t = store.upsert("templates", {
        "id": f.get("id", ""), "name": f.get("name", "").strip() or "Untitled template",
        "subject": f.get("subject", "").strip(), "html": f.get("html", ""),
    })
    return redirect(url_for("mailer.templates", template_id=t["id"]))


@bp.route("/templates/<template_id>/delete", methods=["POST"])
def template_delete(template_id):
    store.delete_item("templates", template_id)
    return redirect(url_for("mailer.templates"))


@bp.route("/templates/preview", methods=["POST"])
def template_preview():
    data = request.get_json(force=True) or {}
    sample = {"headers": ["Case", "Status", "Owner"],
              "rows": [["Login SIT-01", "Pass", "Alice"], ["Payment SIT-07", "Fail", "Bob"]]}
    subject, body = store.render({"html": data.get("html", ""), "subject": data.get("subject", "")},
                                 {"name": "Sample job"}, sample)
    return jsonify({"subject": subject, "html": body})


@bp.route("/receivers")
def receivers():
    return render_template("mailer/receivers.html", groups=store.list_items("receivers"))


@bp.route("/receivers/save", methods=["POST"])
def receivers_save():
    f = request.form
    store.upsert("receivers", {
        "id": f.get("id", ""), "name": f.get("name", "").strip() or "Untitled group",
        "to": store.parse_email_list(f.get("to")), "cc": store.parse_email_list(f.get("cc")),
        "bcc": store.parse_email_list(f.get("bcc")),
    })
    return redirect(url_for("mailer.receivers"))


@bp.route("/receivers/<group_id>/delete", methods=["POST"])
def receivers_delete(group_id):
    store.delete_item("receivers", group_id)
    return redirect(url_for("mailer.receivers"))


@bp.route("/settings", methods=["GET", "POST"])
def settings():
    result = None
    if request.method == "POST":
        f = request.form
        cfg = store.save_settings({
            "transport": f.get("transport", "outlook"), "smtp_host": f.get("smtp_host", ""),
            "smtp_port": int(f.get("smtp_port") or 587), "smtp_user": f.get("smtp_user", ""),
            "smtp_password": f.get("smtp_password") or store.settings().get("smtp_password", ""),
            "from_name": f.get("from_name", ""), "review_before_send": f.get("review_before_send") == "on",
        })
        if f.get("test_to"):
            try:
                result = "✓ " + outlook.send(cfg, store.parse_email_list(f["test_to"]), [], [],
                                             "QA Workstation Mailer — test", "<p>It works 🎉</p>")
            except Exception as exc:
                result = "✕ " + str(exc)
    return render_template("mailer/settings.html", settings=store.settings(), result=result)


# ---------- plugin API ----------

@bp.route("/api/options")
def api_options():
    return jsonify({
        "templates": [{"id": t["id"], "name": t["name"]} for t in store.list_items("templates")],
        "receivers": [{"id": g["id"], "name": g["name"], "to": g.get("to", [])} for g in store.list_items("receivers")],
        "jobs": [{"id": j["id"], "name": j["name"], "source": (j.get("source") or {}).get("type")} for j in store.list_items("jobs")],
        "transport": store.settings().get("transport"),
    })


@bp.route("/api/send", methods=["POST"])
def api_send():
    """One-off send from the plugin: {table, template_id, receivers_id, to, cc, subject, name}."""
    d = request.get_json(force=True) or {}
    job = {"id": "", "name": d.get("name") or "Table from Excel", "subject": d.get("subject", ""),
           "template_id": d.get("template_id", ""), "receivers_id": d.get("receivers_id", ""),
           "to": d.get("to", ""), "cc": d.get("cc", ""), "bcc": "",
           "source": {"type": "table", "table": d.get("table") or {}}}
    template = store.get_item("templates", job["template_id"]) or {}
    try:
        subject, body = store.render(template, job, job["source"]["table"])
        to, cc, bcc = store.recipients_for(job)
        msg = outlook.send(store.settings(), to, cc, bcc, subject, body,
                           review=bool(d.get("review")) or store.settings().get("review_before_send", False))
        store.log({"job": job["name"], "ok": True, "message": msg, "to": to, "subject": subject})
        return jsonify({"ok": True, "message": msg, "to": to, "subject": subject})
    except Exception as exc:
        store.log({"job": job["name"], "ok": False, "message": str(exc)})
        return jsonify({"ok": False, "error": str(exc)})


@bp.route("/api/jobs", methods=["POST"])
def api_job_create():
    """Save a captured table as a job (unscheduled until edited): the
    plugin's '💾 Save as job'. If job_id is given, only its table is updated."""
    d = request.get_json(force=True) or {}
    if d.get("job_id"):
        job = store.get_item("jobs", d["job_id"])
        if job is None:
            return jsonify({"ok": False, "error": "job not found"}), 404
        job.setdefault("source", {})["type"] = "table"
        job["source"]["table"] = d.get("table") or {}
    else:
        job = {"id": "", "name": d.get("name") or "Table from Excel", "subject": d.get("subject", ""),
               "template_id": d.get("template_id", ""), "receivers_id": d.get("receivers_id", ""),
               "to": d.get("to", ""), "cc": d.get("cc", ""), "bcc": "",
               "source": {"type": "table", "table": d.get("table") or {}},
               "schedule": {"enabled": False, "time": "09:00", "days": [0, 1, 2, 3, 4]}}
    job = store.upsert("jobs", job)
    return jsonify({"ok": True, "job": {"id": job["id"], "name": job["name"]},
                    "url": url_for("mailer.job_edit", job_id=job["id"], _external=True)})
