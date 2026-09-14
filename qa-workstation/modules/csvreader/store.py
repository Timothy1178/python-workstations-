"""Storage for the CSV reader.

Files live in data/csv/<file_id>.json as {name, headers, rows, uploaded}.
Field display settings are saved per header signature (a hash of the
column names), so re-uploading a CSV with the same structure reuses them.
"""
import csv
import hashlib
import io
import json
import re
import time
import uuid
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CSV_DIR = DATA_DIR / "csv"
SETTINGS_FILE = DATA_DIR / "csv_settings.json"

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
DATE_RES = [
    re.compile(r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?$"),
    re.compile(r"^\d{2}/\d{2}/\d{4}( \d{2}:\d{2}(:\d{2})?)?$"),
]


def signature(headers):
    return hashlib.sha1("\x1f".join(headers).encode("utf-8")).hexdigest()[:16]


def detect_type(header, values):
    """Guess a field's type from its non-empty sample values."""
    sample = [v for v in values if v.strip()][:50]
    if sample and all(UUID_RE.match(v) for v in sample):
        return "uuid"
    if sample and all(any(rx.match(v) for rx in DATE_RES) for v in sample):
        return "date"
    lower = header.lower()
    if not sample:  # empty column — fall back to the header name
        if "uuid" in lower or lower.endswith("_id") and "guid" in lower:
            return "uuid"
        if "date" in lower or "time" in lower:
            return "date"
    return "text"


def parse_csv(name, raw_bytes):
    text = raw_bytes.decode("utf-8-sig", errors="replace")
    return _from_table(name, csv.reader(io.StringIO(text)))


DELIMITERS = [",", "\t", ";", "|"]
_DELIM_NAMES = {"comma": ",", "tab": "\t", "semicolon": ";", "pipe": "|"}


def sniff_delimiter(text):
    """Pick the delimiter that appears on every line, preferring the one
    with a consistent count per line (a clean grid beats stray commas)."""
    lines = [ln for ln in text.splitlines() if ln.strip()][:20]
    best, best_score = None, 0
    for d in DELIMITERS:
        counts = [ln.count(d) for ln in lines]
        if not counts or min(counts) == 0:
            continue
        score = min(counts) * (2 if len(set(counts)) == 1 else 1)
        if score > best_score:
            best, best_score = d, score
    return best


def parse_pasted(name, text, delimiter="auto", has_header=True):
    """Convert pasted text (comma/tab/semicolon/pipe separated) to a doc."""
    text = text.replace("﻿", "").strip("\n\r")
    if not text.strip():
        return None
    delim = _DELIM_NAMES.get(delimiter) or sniff_delimiter(text)
    if delim:
        table = list(csv.reader(io.StringIO(text), delimiter=delim))
    else:  # no separator found — one column, a record per line
        table = [[ln.strip()] for ln in text.splitlines()]
    if not has_header and table:
        width = max(len(r) for r in table)
        table.insert(0, [f"column_{i+1}" for i in range(width)])
    return _from_table(name, table)


def _from_table(name, reader):
    table = [row for row in reader if any(c.strip() for c in row)]
    if not table:
        return None
    headers = [h.strip() or f"column_{i+1}" for i, h in enumerate(table[0])]
    rows = []
    for r in table[1:]:
        r = list(r) + [""] * (len(headers) - len(r))
        rows.append(r[:len(headers)])
    file_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    doc = {
        "id": file_id,
        "name": name,
        "uploaded": time.strftime("%Y-%m-%d %H:%M"),
        "headers": headers,
        "rows": rows,
    }
    save_file(doc)
    return doc


def save_file(doc):
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    (CSV_DIR / f"{doc['id']}.json").write_text(
        json.dumps(doc, ensure_ascii=False), encoding="utf-8")


def load_file(file_id):
    path = CSV_DIR / f"{file_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def delete_file(file_id):
    path = CSV_DIR / f"{file_id}.json"
    if path.exists():
        path.unlink()


def list_files():
    if not CSV_DIR.exists():
        return []
    docs = []
    for p in sorted(CSV_DIR.glob("*.json"), reverse=True):
        d = json.loads(p.read_text(encoding="utf-8"))
        docs.append({"id": d["id"], "name": d["name"],
                     "uploaded": d["uploaded"], "rows": len(d["rows"]),
                     "cols": len(d["headers"])})
    return docs


def default_settings(doc):
    fields = {}
    cols = list(zip(*doc["rows"])) if doc["rows"] else [[] for _ in doc["headers"]]
    for i, h in enumerate(doc["headers"]):
        values = list(cols[i]) if i < len(cols) else []
        fields[h] = {"mode": "show", "type": detect_type(h, values)}
    return {"fields": fields}


def load_settings(doc):
    sig = signature(doc["headers"])
    all_settings = {}
    if SETTINGS_FILE.exists():
        all_settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    saved = all_settings.get(sig)
    base = default_settings(doc)
    if saved:
        for h, cfg in saved.get("fields", {}).items():
            if h in base["fields"]:
                base["fields"][h].update(
                    {k: v for k, v in cfg.items() if k in ("mode", "type")})
    return base


def save_settings(doc, settings):
    sig = signature(doc["headers"])
    all_settings = {}
    if SETTINGS_FILE.exists():
        all_settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    clean = {"fields": {}}
    for h in doc["headers"]:
        cfg = settings.get("fields", {}).get(h, {})
        clean["fields"][h] = {
            "mode": cfg.get("mode") if cfg.get("mode") in ("show", "star", "hide") else "show",
            "type": cfg.get("type") if cfg.get("type") in ("text", "uuid", "date") else "text",
        }
    all_settings[sig] = clean
    SETTINGS_FILE.write_text(
        json.dumps(all_settings, indent=2, ensure_ascii=False), encoding="utf-8")
    return clean


def to_csv_bytes(doc):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(doc["headers"])
    w.writerows(doc["rows"])
    return buf.getvalue().encode("utf-8-sig")
