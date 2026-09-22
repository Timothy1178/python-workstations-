"""JSON storage for test plans and the test-case template schema.

The builder's columns come from data/template.json, so when the user's own
test case template arrives we only replace that file (or edit it in the UI)
— no code changes needed.
"""
import json
import re
import time
import uuid
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PLANS_DIR = DATA_DIR / "plans"
TEMPLATE_FILE = DATA_DIR / "template.json"

# Schema matching the CCASIA / AIMAS test plan template
# (CCASIA-44 UAT Test Plan.xlsx). type: text | textarea | select
DEFAULT_TEMPLATE = {
    "name": "AIMAS Test Plan (CCASIA)",
    "fields": [
        {"key": "testing_bu", "label": "Testing BU", "type": "text", "width": "narrow"},
        {"key": "title", "label": "Case", "type": "text", "width": "medium"},
        {"key": "steps", "label": "Steps", "type": "textarea", "width": "wide"},
        {"key": "expected", "label": "Expected results", "type": "textarea", "width": "wide"},
        {"key": "test_data", "label": "Test Data", "type": "textarea", "width": "medium"},
        {"key": "campaign_id", "label": "Campaign ID", "type": "text", "width": "narrow"},
        {"key": "remark", "label": "Remark", "type": "textarea", "width": "medium"},
    ],
    # Fields filled in during execution (the viewer), not the builder.
    "run_fields": [
        {"key": "result", "label": "Testing Results", "type": "select",
         "options": ["Not Run", "Pass", "Fail", "Blocked", "N/A"]},
        {"key": "actual", "label": "Actual Results", "type": "textarea"},
    ],
}


# ---------- current case (what the screen cap plugin sends to) ----------

CURRENT_FILE = DATA_DIR / "current_case.json"


def get_current():
    if not CURRENT_FILE.exists():
        return None
    cur = json.loads(CURRENT_FILE.read_text(encoding="utf-8"))
    plan = load_plan(cur.get("plan_id", ""))
    if plan is None or not any(c["uid"] == cur.get("case_uid") for c in plan["cases"]):
        return None  # plan or case was deleted since
    return cur


def set_current(plan_id, case_uid):
    plan = load_plan(plan_id)
    if plan is None:
        return None
    for i, case in enumerate(plan["cases"], start=1):
        if case["uid"] == case_uid:
            f = case.get("fields", {})
            label = " ".join(x for x in (f.get("testing_bu", "").strip(),
                                         f.get("title", "").strip()) if x)
            cur = {
                "plan_id": plan_id,
                "plan_name": plan.get("name", plan_id),
                "case_uid": case_uid,
                "case_no": i,
                "label": label or f"case {i}",
                "set_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            DATA_DIR.mkdir(exist_ok=True)
            CURRENT_FILE.write_text(json.dumps(cur, ensure_ascii=False), encoding="utf-8")
            return cur
    return None


# ---------- screenshots (one folder per case) ----------

def shots_dir(plan_id, case_uid):
    return PLANS_DIR / f"{plan_id}_shots" / case_uid


def list_shots(plan_id, case_uid):
    d = shots_dir(plan_id, case_uid)
    if not d.exists():
        return []
    return sorted(p.name for p in d.iterdir()
                  if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif"))


def save_shot(plan_id, case_uid, data, ext=".png"):
    d = shots_dir(plan_id, case_uid)
    d.mkdir(parents=True, exist_ok=True)
    name = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}{ext}"
    (d / name).write_bytes(data)
    return name


def delete_shot(plan_id, case_uid, filename):
    # filename comes from the URL — never let it escape the shots folder
    if "/" in filename or "\\" in filename or filename.startswith("."):
        return
    path = shots_dir(plan_id, case_uid) / filename
    if path.exists():
        path.unlink()


def load_template():
    if TEMPLATE_FILE.exists():
        return json.loads(TEMPLATE_FILE.read_text(encoding="utf-8"))
    return DEFAULT_TEMPLATE


def save_template(template):
    DATA_DIR.mkdir(exist_ok=True)
    TEMPLATE_FILE.write_text(
        json.dumps(template, indent=2, ensure_ascii=False), encoding="utf-8")


def _slug(name):
    s = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
    return s or "plan"


def _plan_path(plan_id):
    return PLANS_DIR / f"{plan_id}.json"


def load_plan(plan_id):
    path = _plan_path(plan_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_plan(plan):
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    plan["updated"] = time.strftime("%Y-%m-%d %H:%M")
    _plan_path(plan["id"]).write_text(
        json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    return plan


def create_plan(name, description=""):
    plan_id = f"{_slug(name)}-{uuid.uuid4().hex[:6]}"
    plan = {
        "id": plan_id,
        "name": name,
        "description": description,
        "created": time.strftime("%Y-%m-%d %H:%M"),
        "cases": [],
    }
    return save_plan(plan)


def delete_plan(plan_id):
    path = _plan_path(plan_id)
    if path.exists():
        path.unlink()
    shots = PLANS_DIR / f"{plan_id}_shots"
    if shots.exists():
        import shutil
        shutil.rmtree(shots)


def list_plans():
    if not PLANS_DIR.exists():
        return []
    plans = [json.loads(p.read_text(encoding="utf-8"))
             for p in sorted(PLANS_DIR.glob("*.json"))]
    plans.sort(key=lambda p: p.get("updated", ""), reverse=True)
    return plans


def plan_summaries():
    out = []
    for p in list_plans():
        cases = p.get("cases", [])
        done = sum(1 for c in cases
                   if c.get("run", {}).get("result") not in (None, "", "Not Run"))
        out.append({
            "id": p["id"], "name": p["name"], "updated": p.get("updated", ""),
            "total": len(cases), "done": done,
        })
    return out


def new_case(fields):
    return {"uid": uuid.uuid4().hex[:10], "fields": fields, "run": {}}
