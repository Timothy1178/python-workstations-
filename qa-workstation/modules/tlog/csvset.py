"""TLog CSV set: ORDER / ORDER_PAYMENT / ORDERITEMS / ORDERITEMS_PROMOTION.

A "set" is a list of transactions. Each transaction is one ORDER row
plus its item, payment and promotion rows; columns that carry the same
name in several files (member card, date-time, store, till, transaction
number, receipt, BU) are entered once per transaction and copied into
every file on export. The layout (column names per file, defaults,
number formats, Msg5 mapping) lives in data/tlog/csv_layout.json and is
edited in the page; the file format itself is fixed by the template:
every field double-quoted, no header, CRLF between rows, no trailing
newline, an empty file is a single CRLF, and a same-named empty .ok
file beside each CSV.
"""
import csv
import io
import json
import re
import time
import uuid
import zipfile
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "tlog"
LAYOUT_FILE = DATA_DIR / "csv_layout.json"
SETS_DIR = DATA_DIR / "sets"

FILE_TYPES = ["ORDER", "ORDER_PAYMENT", "ORDERITEMS", "ORDERITEMS_PROMOTION", "ORDER_XM"]
# ORDER_XM (TSR / Lucky Draw account values) is part of the spec but only sent when a transaction has account lines
OPTIONAL_FILES = ("ORDER_XM",)
CHILD_OF = {"ORDER_PAYMENT": "payments", "ORDERITEMS": "items", "ORDERITEMS_PROMOTION": "promotions", "ORDER_XM": "accounts"}
# per-column spec notes carried from tlog_spec.json (read-only in the layout editor)
NOTE_KEYS = ("desc", "guide", "sample", "pos", "spec_seq", "spec_type")
NAME_FORMAT = "{TYPE}_{BU}_{YYYYMMDD}_{SEQ}"
FORMATS = ("", "dec3", "dec4", "dec9")
# auto rules — every auto is a *suggestion*: it fills the cell when it is left blank; typed values win
AUTOS = ("", "lineno", "txnref", "sum_items_net", "sum_items_qty", "count_items", "sum_payments",
         "line_net", "total_if_blank", "bu", "bu_member", "program", "member_no", "store_name", "erp_if_blank")
TYPES = ("text", "number", "datetime", "flag")
SPEC_FILE = Path(__file__).resolve().parent / "tlog_spec.json"
BUS = ["WTCTW", "MBHK", "WTCSG", "WTCTH", "WWHK", "WTCPH", "WTCVN", "WTCMY", "WTCID", "LOOKPH", "FTRHK"]


def _spec_layout():
    """Default layout = the RetailHK Sales_Transactions v1.3 field spec
    (names, types, lengths, required, LOVs) in the column order of the
    WWHK sample set, with defaults, auto rules and Msg5 mapping."""
    return json.loads(SPEC_FILE.read_text(encoding="utf-8"))


DEFAULT_LAYOUT = _spec_layout()


def _clean_lov(v):
    """LOV name (PAYMENT_TYPE_CODE) or an inline fixed list ("=PromotionID", "=Y|N")."""
    v = str(v or "").strip()
    if v.startswith("="):
        return "=" + "|".join(x.strip() for x in v[1:].split("|") if x.strip())
    return re.sub(r"[^A-Z0-9_]", "", v.upper())


def clean_col(c):
    if not isinstance(c, dict):
        return dict(E)
    name = re.sub(r"[^A-Za-z0-9_]", "", str(c.get("name", "")).strip())
    out = {
        "name": name,
        "label": str(c.get("label", "")).strip() or name,
        "default": str(c.get("default", "")),
        "format": c.get("format") if c.get("format") in FORMATS else "",
        "auto": c.get("auto") if c.get("auto") in AUTOS else "",
        "msg5": re.sub(r"[^A-Za-z0-9_.:\-]", "", str(c.get("msg5", "")).strip()),
        "type": c.get("type") if c.get("type") in TYPES else "text",
        "max": re.sub(r"\D", "", str(c.get("max", "")))[:4],
        "required": bool(c.get("required", False)),
        "lov": _clean_lov(c.get("lov", "")),
        "hint": str(c.get("hint", ""))[:400],
    }
    for k in NOTE_KEYS:
        if c.get(k):
            out[k] = str(c[k])[:600]
    ref = re.sub(r"[^0-9A-Za-z]", "", str(c.get("ref", "")).strip())
    if ref:
        out["ref"] = ref
    return out


def load_layout():
    lay = json.loads(json.dumps(DEFAULT_LAYOUT))
    if LAYOUT_FILE.exists():
        try:
            saved = json.loads(LAYOUT_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            saved = {}
        if saved.get("name_format"):
            lay["name_format"] = str(saved["name_format"])
        if "ref_base" in saved:
            lay["ref_base"] = str(saved["ref_base"])
        if isinstance(saved.get("bus"), list):
            lay["bus"] = [str(b).strip().upper() for b in saved["bus"] if str(b).strip()]
        if isinstance(saved.get("payment_maps"), list):
            lay["payment_maps"] = saved["payment_maps"]
        if isinstance(saved.get("lovs"), dict):
            lay["lovs"] = {k: [str(v) for v in vals] for k, vals in saved["lovs"].items() if isinstance(vals, list)}
        files = saved.get("files")
        if isinstance(files, dict):
            for ft in FILE_TYPES:
                if isinstance(files.get(ft), list):
                    lay["files"][ft] = [clean_col(c) for c in files[ft]]
    return lay


def save_layout(lay):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "name_format": str(lay.get("name_format") or NAME_FORMAT),
        "ref_base": str(lay.get("ref_base", "")),
        "bus": [str(b).strip().upper() for b in (lay.get("bus") or BUS) if str(b).strip()],
        "lovs": {k: [str(v) for v in vals] for k, vals in (lay.get("lovs") or DEFAULT_LAYOUT["lovs"]).items() if isinstance(vals, list)},
        "payment_maps": lay.get("payment_maps") or DEFAULT_LAYOUT.get("payment_maps", []),
        "files": {ft: [clean_col(c) for c in (lay.get("files", {}).get(ft) or [])] for ft in FILE_TYPES},
    }
    LAYOUT_FILE.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    return out


def shared_names(lay):
    """Transaction-level columns: names present in ORDER that also appear
    in at least one child file — entered once per transaction and copied
    into every row of every file. ORDER column order."""
    child = {c["name"] for ft in CHILD_OF for c in lay["files"][ft] if c["name"]}
    out = []
    for c in lay["files"]["ORDER"]:
        if c["name"] and c["name"] in child and c["name"] not in out:
            out.append(c["name"])
    return out


# ---------- saved sets ----------

def _path(sid):
    return SETS_DIR / f"{sid}.json"


def list_sets():
    if not SETS_DIR.exists():
        return []
    out = []
    for p in SETS_DIR.glob("*.json"):
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        out.append({k: s.get(k, "") for k in ("id", "name", "bu", "date", "seq", "updated")}
                   | {"transactions": len(s.get("transactions", []))})
    out.sort(key=lambda s: s.get("updated", ""), reverse=True)
    return out


def get_set(sid):
    if not re.fullmatch(r"[0-9a-f]{12}", sid or ""):
        return None
    try:
        return json.loads(_path(sid).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_set(sid, data):
    SETS_DIR.mkdir(parents=True, exist_ok=True)
    now = time.strftime("%Y-%m-%d %H:%M")
    existing = get_set(sid) if sid else None
    if existing is None:
        sid = uuid.uuid4().hex[:12]
        existing = {"id": sid, "created": now}
    existing.update({
        "name": str(data.get("name", "")).strip() or existing.get("name") or f"set {sid}",
        "bu": str(data.get("bu", "")).strip().upper(),
        "date": re.sub(r"\D", "", str(data.get("date", "")))[:8],
        "seq": str(data.get("seq", "")).strip(),
        "ref_base": str(data.get("ref_base", "")).strip(),
        "transactions": data.get("transactions", []) if isinstance(data.get("transactions"), list) else [],
        "updated": now,
    })
    _path(sid).write_text(json.dumps(existing, ensure_ascii=False), encoding="utf-8")
    return existing


def delete_set(sid):
    s = get_set(sid)
    if s:
        _path(sid).unlink()
    return s is not None


# ---------- files ----------

def file_name(lay, ftype, bu, date, seq, ext="csv"):
    fmt = lay.get("name_format") or NAME_FORMAT
    if not str(seq).strip():
        fmt = fmt.replace("_{SEQ}", "").replace("{SEQ}", "")
    base = fmt.format(TYPE=ftype, BU=bu, YYYYMMDD=date, SEQ=seq)
    base = re.sub(r"[^\w\-.]", "", base)
    return f"{base}.{ext}"


def csv_bytes(rows):
    """Template format: every field quoted, CRLF between rows, no trailing
    newline; an empty file is one CRLF."""
    if not rows:
        return b"\r\n"
    buf = io.StringIO()
    w = csv.writer(buf, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
    for r in rows:
        w.writerow(["" if v is None else str(v) for v in r])
    text = buf.getvalue()
    if text.endswith("\r\n"):
        text = text[:-2]
    return text.encode("utf-8")


def zip_files(files, include=None):
    """The file types that go into the zip: the 4 mandatory ones plus an
    optional one (ORDER_XM) when it is asked for or has rows."""
    include = set(include or ())
    return [ft for ft in FILE_TYPES if ft not in OPTIONAL_FILES or ft in include or files.get(ft)]


def build_zip(lay, bu, date, seq, files, include=None):
    """files: {ftype: [[cell, ...], ...]} -> zip bytes with one csv + one
    empty ok per file type (4 mandatory + ORDER_XM when used)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for ft in zip_files(files, include):
            z.writestr(file_name(lay, ft, bu, date, seq, "csv"), csv_bytes(files.get(ft) or []))
            z.writestr(file_name(lay, ft, bu, date, seq, "ok"), b"")
    buf.seek(0)
    return buf


# ---------- import an existing set ----------

def parse_name(filename):
    """ORDER_PAYMENT_WWHK_20240829_54.csv -> (type, bu, date, seq);
    the _SEQ part is optional (ORDER_WTCID_20261102.csv -> seq "")."""
    stem = Path(filename).stem
    for ft in sorted(FILE_TYPES, key=len, reverse=True):
        m = re.fullmatch(re.escape(ft) + r"_([A-Za-z0-9]+)_(\d{8})(?:_(\w+))?", stem)
        if m:
            return ft, m.group(1).upper(), m.group(2), m.group(3) or ""
    return None


def read_rows(raw):
    text = raw.decode("utf-8-sig", errors="replace")
    return [r for r in csv.reader(io.StringIO(text, newline="")) if any(c.strip() for c in r)]


def rows_to_dicts(lay, ftype, rows):
    cols = lay["files"][ftype]
    out = []
    for r in rows:
        d = {}
        for i, c in enumerate(cols):
            if c["name"] and i < len(r) and c["name"] not in d:
                d[c["name"]] = r[i]
        out.append(d)
    return out


def import_set(lay, uploads):
    """uploads: [(filename, bytes)] (csv files and/or a zip of them) ->
    {bu, date, seq, transactions, warnings}."""
    files = {}
    meta = None
    warnings = []
    for name, raw in uploads:
        if name.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                for info in z.infolist():
                    if info.filename.lower().endswith(".csv"):
                        uploads_inner = (Path(info.filename).name, z.read(info))
                        p = parse_name(uploads_inner[0])
                        if p:
                            files[p[0]] = read_rows(uploads_inner[1])
                            meta = meta or p[1:]
            continue
        if name.lower().endswith(".ok"):
            continue
        p = parse_name(name)
        if not p:
            warnings.append(f"{name}: name does not match {NAME_FORMAT}.csv (the _SEQ part is optional) — skipped")
            continue
        files[p[0]] = read_rows(raw)
        meta = meta or p[1:]
    if "ORDER" not in files:
        return {"error": "no ORDER_<BU>_<YYYYMMDD>[_<SEQ>].csv in the upload", "warnings": warnings}
    shared = shared_names(lay)
    orders = rows_to_dicts(lay, "ORDER", files["ORDER"])
    children = {CHILD_OF[ft]: rows_to_dicts(lay, ft, files.get(ft, [])) for ft in CHILD_OF}
    key_names = [n for n in ("CustomerOrderNumber", "ERPOrderNumber", "StoreID", "POSNumber", "CardNumber") if n in shared] or shared
    def key(d):
        return tuple(d.get(n, "") for n in key_names)
    txns = []
    for o in orders:
        t = {"order": o, **{kind: [] for kind in CHILD_OF.values()}}
        for kind in CHILD_OF.values():
            t[kind] = [{k: v for k, v in c.items() if k not in shared} for c in children[kind] if key(c) == key(o)]
        txns.append(t)
    matched = sum(len(t[k]) for t in txns for k in CHILD_OF.values())
    total = sum(len(v) for v in children.values())
    if matched < total:
        warnings.append(f"{total - matched} child rows did not match any ORDER row on {', '.join(key_names)}")
    bu, date, seq = meta or ("", "", "")
    return {"bu": bu, "date": date, "seq": seq, "transactions": txns, "warnings": warnings}
