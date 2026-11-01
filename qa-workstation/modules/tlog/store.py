"""Storage + file reading for the TLog Handler editor.

- data/tlog/library/<id>.json — BU templates (imported from the BU
  docs) and saved requests: {id, name, bu_code, kind, notes, json,
  created, updated}
- data/tlog/config.json — editable fields (tag -> input) and toggles.

The messages are the UPDATE_TRANSACTION_STOCK_FROM_MSG5 Kafka payloads
sent through Offset Explorer: {"id", "type", "buCode", "timestamp",
"playloadJson": "<entity-encoded ActiveStore_SalesTransaction XML>"}.
"""
import json
import re
import time
import uuid
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "tlog"
LIB_DIR = DATA_DIR / "library"
CONFIG_FILE = DATA_DIR / "config.json"

FIELD_TYPES = ("text", "number", "date", "datetime", "flag", "epochms")
KINDS = ("template", "request")

# source "json" = top-level key of the message; "xml" = payload tag.
DEFAULT_FIELDS = [
    {"key": "type", "source": "json", "tag": "type", "label": "Type", "type": "text", "group": "Message", "required": True},
    {"key": "buCode", "source": "json", "tag": "buCode", "label": "BU code", "type": "text", "group": "Message", "required": True},
    {"key": "timestamp", "source": "json", "tag": "timestamp", "label": "Timestamp (epoch ms)", "type": "epochms", "group": "Message", "required": True},
    {"key": "storeID", "source": "xml", "tag": "StoreID", "label": "Store ID", "type": "number", "group": "Transaction", "all": True, "required": True},
    {"key": "retailerId", "source": "xml", "tag": "RetailerId", "label": "Retailer ID", "type": "number", "group": "Transaction", "all": True, "required": True,
     "attr_of": "ActiveStore_SalesTransaction_1.70", "hint": "Also sets the RetailerId attribute on the transaction element."},
    {"key": "businessDate", "source": "xml", "tag": "BusinessDate", "label": "Business date", "type": "date", "group": "Transaction", "all": True, "required": True},
    {"key": "periodBusinessDate", "source": "xml", "tag": "PeriodBusinessDate", "label": "Period business date", "type": "date", "group": "Transaction", "all": True},
    {"key": "transactionNumber", "source": "xml", "tag": "TransactionNumber", "label": "Transaction number", "type": "number", "group": "Transaction", "all": True, "required": True},
    {"key": "externalReferenceId", "source": "xml", "tag": "ExternalReferenceId", "label": "External reference ID", "type": "number", "group": "Transaction", "all": False},
    {"key": "tillID", "source": "xml", "tag": "TillID", "label": "Till ID", "type": "number", "group": "Transaction", "all": True},
    {"key": "cashierID", "source": "xml", "tag": "CashierID", "label": "Cashier ID", "type": "number", "group": "Transaction", "all": True},
    {"key": "startDateTime", "source": "xml", "tag": "StartDateTime", "label": "Start date and time", "type": "datetime", "group": "Transaction", "all": True, "required": True},
    {"key": "endDateTime", "source": "xml", "tag": "EndDateTime", "label": "End date and time", "type": "datetime", "group": "Transaction", "all": True, "required": True},
    {"key": "lpeServerName", "source": "xml", "tag": "LPEServerName", "label": "LPE server name", "type": "text", "group": "Transaction", "all": True},
    {"key": "clubCard", "source": "xml", "tag": "ClubCard", "label": "Club card", "type": "text", "group": "Customer", "all": True,
     "insert_after": "CashierID", "hint": "If absent, inserted after CashierID."},
    {"key": "clubId", "source": "xml", "tag": "ClubId", "label": "Club ID", "type": "number", "group": "Customer", "all": True},
    {"key": "refundFlag", "source": "xml", "tag": "RefundFlag", "label": "Refund flag", "type": "flag", "group": "Flags", "all": True},
    {"key": "transactionVoid", "source": "xml", "tag": "TransactionVoid", "label": "Transaction void", "type": "flag", "group": "Flags", "all": True},
    {"key": "cancelFlag", "source": "xml", "tag": "CancelFlag", "label": "Cancel flag", "type": "flag", "group": "Flags", "all": True},
    {"key": "trainingModeFlag", "source": "xml", "tag": "TrainingModeFlag", "label": "Training mode", "type": "flag", "group": "Flags", "all": True},
    {"key": "offlineFlag", "source": "xml", "tag": "OfflineFlag", "label": "Offline flag", "type": "flag", "group": "Flags", "all": True},
]

DEFAULT_CONFIG = {
    "auto_increment": True,   # New UUID -> TransactionNumber + 1
    "auto_timestamp": True,   # Generate -> timestamp = now
    "auto_recalc": True,      # Generate -> ExtendedAmount / TotalAmount / ItemsNumber / single tender
    "pretty": False,
    "fields": DEFAULT_FIELDS,
}


# ---------- config ----------

def clean_field(f):
    if not isinstance(f, dict):
        return None
    tag = re.sub(r"[^A-Za-z0-9_.\-:]", "", str(f.get("tag", "")).strip())
    if not tag:
        return None
    source = "json" if f.get("source") == "json" else "xml"
    key = re.sub(r"[^A-Za-z0-9_]", "", str(f.get("key", "")).strip()) or key_for(tag)
    out = {
        "key": key, "source": source, "tag": tag,
        "label": str(f.get("label", "")).strip() or tag,
        "type": f.get("type") if f.get("type") in FIELD_TYPES else "text",
        "group": str(f.get("group", "")).strip() or ("Message" if source == "json" else "Extra"),
        "required": bool(f.get("required", False)),
        "all": bool(f.get("all", True)),
        "hint": str(f.get("hint", "")).strip(),
    }
    for k in ("insert_after", "attr_of"):
        v = re.sub(r"[^A-Za-z0-9_.\-:]", "", str(f.get(k, "")).strip())
        if v:
            out[k] = v
    return out


def key_for(tag):
    t = re.sub(r"[^A-Za-z0-9]", "", tag)
    return (t[:1].lower() + t[1:]) if t else "field"


def load_config():
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if CONFIG_FILE.exists():
        try:
            saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            saved = {}
        for k in ("auto_increment", "auto_timestamp", "auto_recalc", "pretty"):
            if k in saved:
                cfg[k] = bool(saved[k])
        if isinstance(saved.get("fields"), list):
            cfg["fields"] = [clean_field(f) for f in saved["fields"] if clean_field(f)]
    return cfg


def save_config(cfg):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = {k: bool(cfg.get(k, DEFAULT_CONFIG[k]))
           for k in ("auto_increment", "auto_timestamp", "auto_recalc", "pretty")}
    out["fields"], seen = [], set()
    for f in cfg.get("fields", []):
        f = clean_field(f)
        if f and f["key"] not in seen:
            seen.add(f["key"])
            out["fields"].append(f)
    CONFIG_FILE.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


# ---------- library ----------

def _path(eid):
    return LIB_DIR / f"{eid}.json"


def _read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def list_entries():
    if not LIB_DIR.exists():
        return []
    out = []
    for p in LIB_DIR.glob("*.json"):
        e = _read(p)
        if e:
            out.append({k: e.get(k, "") for k in ("id", "name", "bu_code", "kind", "notes", "created", "updated")}
                       | {"size": len(e.get("json", ""))})
    out.sort(key=lambda e: (e.get("kind") != "template", e.get("bu_code", ""), e.get("name", "").lower()))
    return out


def get_entry(eid):
    if not re.fullmatch(r"[0-9a-f]{12}", eid or ""):
        return None
    return _read(_path(eid))


def save_entry(eid, name, json_text, bu_code="", kind="request", notes=""):
    LIB_DIR.mkdir(parents=True, exist_ok=True)
    now = time.strftime("%Y-%m-%d %H:%M")
    entry = get_entry(eid) if eid else None
    if entry is None:
        eid = uuid.uuid4().hex[:12]
        entry = {"id": eid, "created": now}
    entry.update({
        "name": name.strip() or entry.get("name") or f"{bu_code or 'message'} {eid}",
        "bu_code": (bu_code or entry.get("bu_code") or bu_from_json(json_text)).strip().upper(),
        "kind": kind if kind in KINDS else entry.get("kind", "request"),
        "notes": notes.strip(),
        "json": json_text,
        "updated": now,
    })
    _path(eid).write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")
    return entry


def delete_entry(eid):
    e = get_entry(eid)
    if e:
        _path(eid).unlink()
    return e is not None


def bu_from_json(text):
    try:
        return str(json.loads(text).get("buCode", "") or "")
    except (ValueError, AttributeError):
        return ""


# ---------- reading the BU docs ----------

from modules import msgfiles  # noqa: E402


def read_upload(filename, raw):
    """-> list of {name, bu_code, json} found in a .docx / .xlsx / .csv /
    .json / .txt (any cell or paragraph holding the message)."""
    return msgfiles.read_upload(filename, raw)


# ---------- one-time migration from the retired Msg5 Json page ----------

MSG5_DIR = Path(__file__).resolve().parents[2] / "data" / "msg5"
MIGRATED = DATA_DIR / ".msg5_migrated"


def migrate_msg5():
    """Saved messages -> library requests; custom edit-box fields -> the
    TLog config (group "Msg5"); auto-increment toggle. Runs once."""
    if MIGRATED.exists() or not MSG5_DIR.exists():
        return None
    moved = {"messages": 0, "fields": 0}
    for p in sorted((MSG5_DIR / "messages").glob("*.json")) if (MSG5_DIR / "messages").exists() else []:
        m = _read(p)
        if m and isinstance(m.get("json"), str) and m["json"].strip():
            save_entry("", m.get("name", p.stem), m["json"], kind="request",
                       notes=(m.get("notes", "") + " · from Msg5 Json").strip(" ·"))
            moved["messages"] += 1
    cfg_file = MSG5_DIR / "config.json"
    if cfg_file.exists():
        old = _read(cfg_file) or {}
        cfg = load_config()
        have = {(f.get("source", "xml"), f["tag"]) for f in cfg["fields"]}
        for f in old.get("fields", []):
            f = clean_field({**f, "group": "Msg5"})
            if f and (f["source"], f["tag"]) not in have:
                cfg["fields"].append(f)
                have.add((f["source"], f["tag"]))
                moved["fields"] += 1
        if "auto_increment" in old:
            cfg["auto_increment"] = bool(old["auto_increment"])
        save_config(cfg)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MIGRATED.write_text(json.dumps(moved), encoding="utf-8")
    return moved
