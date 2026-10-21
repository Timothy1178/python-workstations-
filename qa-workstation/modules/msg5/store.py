"""Storage for the Msg5 Json editor.

- data/msg5/messages/<id>.json — saved transaction strings {id, name,
  json (the raw string), notes, created, updated}
- data/msg5/config.json — editor settings: the editable fields (which
  payload XML tags show up as inputs, with label / type / options) and
  the auto-increment toggle. The built-in fields from the original
  Transaction String Editor are the defaults; testers add their own
  from any tag found in a loaded payload.
"""
import json
import re
import time
import uuid
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "msg5"
MSG_DIR = DATA_DIR / "messages"
CONFIG_FILE = DATA_DIR / "config.json"

FIELD_TYPES = ("text", "number", "date", "datetime")

DEFAULT_FIELDS = [
    {"key": "transactionNumber", "tag": "TransactionNumber", "label": "Transaction number",
     "type": "number", "required": True, "all": True, "hint": ""},
    {"key": "businessDate", "tag": "BusinessDate", "label": "Business date",
     "type": "date", "required": True, "all": True,
     "hint": "Updates every <BusinessDate> in the payload."},
    {"key": "clubCard", "tag": "ClubCard", "label": "Club card",
     "type": "text", "required": False, "all": True, "insert_after": "CashierID",
     "hint": "If absent, a non-empty ClubCard is inserted after CashierID."},
    {"key": "startDateTime", "tag": "StartDateTime", "label": "Start date and time",
     "type": "datetime", "required": True, "all": True, "hint": ""},
    {"key": "endDateTime", "tag": "EndDateTime", "label": "End date and time",
     "type": "datetime", "required": True, "all": True, "hint": ""},
]

DEFAULT_CONFIG = {
    "auto_increment": True,     # New UUID -> transaction number + 1
    "increment_tag": "TransactionNumber",
    "pretty": False,
    "fields": DEFAULT_FIELDS,
}


# ---------- config ----------

def load_config():
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if CONFIG_FILE.exists():
        try:
            saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            saved = {}
        for k in ("auto_increment", "pretty"):
            if k in saved:
                cfg[k] = bool(saved[k])
        if saved.get("increment_tag"):
            cfg["increment_tag"] = str(saved["increment_tag"])
        if isinstance(saved.get("fields"), list):
            cfg["fields"] = [clean_field(f) for f in saved["fields"] if clean_field(f)]
    return cfg


def save_config(cfg):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "auto_increment": bool(cfg.get("auto_increment", True)),
        "increment_tag": str(cfg.get("increment_tag") or "TransactionNumber"),
        "pretty": bool(cfg.get("pretty", False)),
        "fields": [],
    }
    seen = set()
    for f in cfg.get("fields", []):
        f = clean_field(f)
        if f and f["key"] not in seen:
            seen.add(f["key"])
            out["fields"].append(f)
    CONFIG_FILE.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def clean_field(f):
    if not isinstance(f, dict):
        return None
    tag = re.sub(r"[^A-Za-z0-9_.\-:]", "", str(f.get("tag", "")).strip())
    if not tag:
        return None
    key = re.sub(r"[^A-Za-z0-9_]", "", str(f.get("key", "")).strip()) or key_for(tag)
    ftype = f.get("type") if f.get("type") in FIELD_TYPES else "text"
    out = {
        "key": key,
        "tag": tag,
        "label": str(f.get("label", "")).strip() or tag,
        "type": ftype,
        "required": bool(f.get("required", False)),
        "all": bool(f.get("all", True)),
        "hint": str(f.get("hint", "")).strip(),
    }
    ins = re.sub(r"[^A-Za-z0-9_.\-:]", "", str(f.get("insert_after", "")).strip())
    if ins:
        out["insert_after"] = ins
    return out


def key_for(tag):
    t = re.sub(r"[^A-Za-z0-9]", "", tag)
    return (t[:1].lower() + t[1:]) if t else "field"


# ---------- saved messages ----------

def _path(mid):
    return MSG_DIR / f"{mid}.json"


def _read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def list_messages():
    if not MSG_DIR.exists():
        return []
    out = []
    for p in MSG_DIR.glob("*.json"):
        m = _read(p)
        if m:
            out.append({k: m.get(k, "") for k in ("id", "name", "notes", "created", "updated")}
                       | {"size": len(m.get("json", ""))})
    out.sort(key=lambda m: m.get("updated", ""), reverse=True)
    return out


def get_message(mid):
    if not re.fullmatch(r"[0-9a-f]{12}", mid or ""):
        return None
    return _read(_path(mid))


def save_message(mid, name, json_text, notes=""):
    """Create (mid empty) or overwrite a saved message."""
    MSG_DIR.mkdir(parents=True, exist_ok=True)
    now = time.strftime("%Y-%m-%d %H:%M")
    existing = get_message(mid) if mid else None
    if existing is None:
        mid = uuid.uuid4().hex[:12]
        existing = {"id": mid, "created": now}
    existing.update({
        "name": name.strip() or existing.get("name") or f"message {mid}",
        "json": json_text,
        "notes": notes.strip(),
        "updated": now,
    })
    _path(mid).write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    return existing


def delete_message(mid):
    m = get_message(mid)
    if m:
        _path(mid).unlink()
    return m is not None
