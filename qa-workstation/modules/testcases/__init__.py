"""Test Cases module — builder (author cases) and viewer (run tests)."""
import re

from flask import (Blueprint, render_template, request, redirect, url_for,
                   jsonify, send_file, send_from_directory)

from . import store

bp = Blueprint("testcases", __name__, url_prefix="/testcases")

MODULE_INFO = {
    "name": "Test Cases",
    "url": "/testcases",
    "desc": "Build test cases from your template and run them in the viewer.",
    "icon": "📋",
}


@bp.route("/")
def index():
    return render_template(
        "testcases/index.html",
        plans=store.plan_summaries(),
        template=store.load_template(),
    )


@bp.route("/create", methods=["POST"])
def create():
    name = request.form.get("name", "").strip()
    if not name:
        return redirect(url_for("testcases.index"))
    plan = store.create_plan(name, request.form.get("description", "").strip())
    return redirect(url_for("testcases.builder", plan_id=plan["id"]))


@bp.route("/plan/<plan_id>/delete", methods=["POST"])
def delete(plan_id):
    store.delete_plan(plan_id)
    return redirect(url_for("testcases.index"))


# ---------- Builder ----------

@bp.route("/plan/<plan_id>")
def builder(plan_id):
    plan = store.load_plan(plan_id)
    if plan is None:
        return redirect(url_for("testcases.index"))
    return render_template(
        "testcases/builder.html", plan=plan, template=store.load_template())


@bp.route("/plan/<plan_id>/cases", methods=["POST"])
def save_cases(plan_id):
    """Replace the plan's cases with the builder's current table (JSON)."""
    plan = store.load_plan(plan_id)
    if plan is None:
        return jsonify({"ok": False, "error": "plan not found"}), 404
    incoming = request.get_json(force=True).get("cases", [])
    existing = {c["uid"]: c for c in plan.get("cases", [])}
    cases = []
    for item in incoming:
        uid = item.get("uid")
        if uid and uid in existing:
            case = existing[uid]
            case["fields"] = item.get("fields", {})
        else:
            case = store.new_case(item.get("fields", {}))
        cases.append(case)
    # Case IDs follow row order, numbered 1..x within each Testing BU +
    # Case pair — reordering or editing either field renumbers them.
    counters = {}
    for case in cases:
        f = case["fields"]
        key = (f.get("testing_bu", "").strip(), f.get("title", "").strip())
        counters[key] = counters.get(key, 0) + 1
        f["case_id"] = str(counters[key])
    plan["cases"] = cases
    store.save_plan(plan)
    return jsonify({"ok": True, "count": len(cases),
                    "uids": [c["uid"] for c in cases]})


# ---------- Viewer / test runner ----------

@bp.route("/plan/<plan_id>/run")
def viewer(plan_id):
    plan = store.load_plan(plan_id)
    if plan is None:
        return redirect(url_for("testcases.index"))
    return render_template(
        "testcases/viewer.html", plan=plan, template=store.load_template())


@bp.route("/plan/<plan_id>/run/<case_uid>", methods=["POST"])
def save_run(plan_id, case_uid):
    plan = store.load_plan(plan_id)
    if plan is None:
        return jsonify({"ok": False, "error": "plan not found"}), 404
    data = request.get_json(force=True)
    for case in plan["cases"]:
        if case["uid"] == case_uid:
            case["run"] = data.get("run", {})
            store.save_plan(plan)
            return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "case not found"}), 404


# ---------- AI assistant ----------

@bp.route("/plan/<plan_id>/assist", methods=["POST"])
def assist_chat(plan_id):
    plan = store.load_plan(plan_id)
    if plan is None:
        return jsonify({"ok": False, "error": "plan not found"}), 404
    data = request.get_json(force=True)
    from . import assist
    result = assist.run_assist(
        plan=plan,
        template=store.load_template(),
        table=data.get("table", []),
        message=data.get("message", ""),
        history=data.get("history", []),
        provider_id=data.get("provider"),
        attachments=data.get("attachments"),
    )
    return jsonify({"ok": "error" not in result, **result})


# ---------- current case + screen cap plugin API ----------

@bp.after_request
def _allow_plugin(resp):
    # The QA Multi Screen Cap extension talks to these endpoints from its
    # own origin; the workstation is local-only, so a permissive CORS
    # policy on this blueprint is fine.
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@bp.route("/api/current", methods=["GET", "POST"])
def current_case():
    """Which case evidence should go to: set by the builder / run viewer
    as the tester moves around, read by the screen cap plugin."""
    if request.method == "POST":
        data = request.get_json(force=True) or {}
        cur = store.set_current(data.get("plan_id", ""), data.get("case_uid", ""))
        if cur is None:
            return jsonify({"ok": False, "error": "unknown plan or case"}), 404
        return jsonify({"ok": True, "current": cur})
    cur = store.get_current()
    if cur:
        cur = {**cur, "shots": len(store.list_shots(cur["plan_id"], cur["case_uid"]))}
    return jsonify({"current": cur})


# ---------- screenshots ----------

@bp.route("/plan/<plan_id>/shots/<case_uid>", methods=["GET", "POST"])
def shots(plan_id, case_uid):
    if request.method == "POST":
        saved = []
        for f in request.files.getlist("shots"):
            ext = "." + (f.filename.rsplit(".", 1)[-1].lower()
                         if "." in f.filename else "png")
            if ext not in (".png", ".jpg", ".jpeg", ".gif"):
                ext = ".png"
            saved.append(store.save_shot(plan_id, case_uid, f.read(), ext))
        return jsonify({"ok": True, "saved": saved,
                        "shots": store.list_shots(plan_id, case_uid)})
    return jsonify({"shots": store.list_shots(plan_id, case_uid)})


@bp.route("/plan/<plan_id>/shots/<case_uid>/<path:filename>")
def shot_file(plan_id, case_uid, filename):
    return send_from_directory(store.shots_dir(plan_id, case_uid), filename)


@bp.route("/plan/<plan_id>/shots/<case_uid>/<path:filename>/delete",
          methods=["POST"])
def shot_delete(plan_id, case_uid, filename):
    store.delete_shot(plan_id, case_uid, filename)
    return jsonify({"ok": True, "shots": store.list_shots(plan_id, case_uid)})


# ---------- Excel export ----------

@bp.route("/plan/<plan_id>/export")
def export(plan_id):
    plan = store.load_plan(plan_id)
    if plan is None:
        return redirect(url_for("testcases.index"))
    # importlib avoids the name clash with this view function
    import importlib
    xl = importlib.import_module(f"{__name__}.export")
    buf = xl.export_plan(plan)
    safe = re.sub(r"[^\w\- ]", "", plan["name"]).strip() or plan_id
    return send_file(
        buf, as_attachment=True, download_name=f"{safe} Test Plan.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument"
                 ".spreadsheetml.sheet")
