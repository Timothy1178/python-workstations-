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

FILE_TYPES = ["ORDER", "ORDER_PAYMENT", "ORDERITEMS", "ORDERITEMS_PROMOTION"]
CHILD_OF = {"ORDER_PAYMENT": "payments", "ORDERITEMS": "items", "ORDERITEMS_PROMOTION": "promotions"}
NAME_FORMAT = "{TYPE}_{BU}_{YYYYMMDD}_{SEQ}"
FORMATS = ("", "dec3", "dec4", "dec9")
AUTOS = ("", "lineno", "txnref", "sum_items_net", "sum_items_qty", "count_items", "sum_payments",
         "line_net", "total_if_blank")


def col(name="", label="", default="", fmt="", auto="", msg5="", ref=""):
    c = {"name": name, "label": label or name, "default": default, "format": fmt, "auto": auto, "msg5": msg5}
    if ref:
        c["ref"] = ref
    return c


E = col()  # always-empty column

# Best-guess names for the header-less template (editable in the page).
DEFAULT_LAYOUT = {
    "name_format": NAME_FORMAT,
    "ref_base": "0006957324",
    "files": {
        "ORDER": [
            col("BUCode", "BU code", "WWHK", msg5="json:buCode"),
            col("ProgramName", "Program name", "WWHK Membership"),
            col("OrderBU", "Order BU", "WWHK", msg5="json:buCode"),
            col("MemberCard", "Member card", msg5="ClubCard"),
            col("ProgramDesc", "Program description", "WWHK Membership"),
            E, E,
            col("VoidFlag", "Void flag", "N"),
            col("TotalAmount", "Total amount", fmt="dec4", auto="sum_items_net"),
            E,
            col("TransactionDateTime", "Transaction date-time", msg5="StartDateTime"),
            col("SettleDateTime", "Settlement date-time", msg5="EndDateTime"),
            col("StoreID", "Store ID", msg5="StoreID"),
            col("CashierCode", "Cashier code", "05530", msg5="CashierID"),
            col("TransactionNumber", "Transaction number", msg5="TransactionNumber"),
            col("ReceiptNo", "Receipt no", msg5="TransactionNumber"),
            col("TillID", "Till ID", msg5="TillID"),
            col("ItemCount", "Item line count", auto="count_items"),
            E,
            col("MemberCard", "Member card", msg5="ClubCard"),
            col("Points", "Points"),
            col("DiscountAmount", "Discount amount", "0.0000", fmt="dec4"),
            col("TaxAmount", "Tax amount", "0.0000", fmt="dec4"),
            col("OrderRef", "Order reference", auto="txnref", ref="05"),
            E, E, E, E, E, E,
            col("RefundFlag", "Refund flag", "N"),
            E, E, E,
            col("ExtraAmount1", "Extra amount 1", "0.0000", fmt="dec4"),
            E, E, E,
            col("ExtraAmount2", "Extra amount 2", "0.0000", fmt="dec4"),
            E, E, E,
            col("ExtraAmount3", "Extra amount 3", "0.0000", fmt="dec4"),
            E, E, E,
            col("ExtraAmount4", "Extra amount 4", "0.0000", fmt="dec4"),
            E, E, E,
            col("ExtraAmount5", "Extra amount 5", "0.0000", fmt="dec4"),
            E, E, E,
            col("ExtraAmount6", "Extra amount 6", "0.0000", fmt="dec4"),
        ],
        "ORDER_PAYMENT": [
            col("MemberCard", "Member card", msg5="ClubCard"),
            col("TransactionDateTime", "Transaction date-time", msg5="StartDateTime"),
            col("StoreID", "Store ID", msg5="StoreID"),
            col("TillID", "Till ID", msg5="TillID"),
            col("TransactionNumber", "Transaction number", msg5="TransactionNumber"),
            col("ReceiptNo", "Receipt no", msg5="TransactionNumber"),
            col("BUCode", "BU code", "WWHK", msg5="json:buCode"),
            col("TenderType", "Tender type", "Credit Card"),
            col("LineNo", "Line no", auto="lineno"),
            col("TenderName", "Tender name", "VISA", msg5="TenderID"),
            col("Amount", "Amount", fmt="dec3", auto="total_if_blank", msg5="Amount"),
            col("PaymentRef", "Payment reference", auto="txnref", ref="07"),
        ],
        "ORDERITEMS": [
            col("MemberCard", "Member card", msg5="ClubCard"),
            col("TransactionDateTime", "Transaction date-time", msg5="StartDateTime"),
            col("StoreID", "Store ID", msg5="StoreID"),
            col("TillID", "Till ID", msg5="TillID"),
            col("TransactionNumber", "Transaction number", msg5="TransactionNumber"),
            col("ReceiptNo", "Receipt no", msg5="TransactionNumber"),
            col("BUCode", "BU code", "WWHK", msg5="json:buCode"),
            col("ItemID", "Item ID", msg5="ItemID"),
            col("LineNo", "Line no", auto="lineno"),
            col("Quantity", "Quantity", "1", fmt="dec9", msg5="Quantity"),
            E, E,
            col("LineDiscount", "Line discount", "0.0000", fmt="dec4"),
            E, E,
            col("EntryMethod", "Entry method", "Manual"),
            col("UnitPrice", "Unit price", fmt="dec4", msg5="UnitSalesPrice"),
            E,
            col("Weight", "Weight", "0E-9"),
            col("LineTax", "Line tax", "0.0000", fmt="dec4"),
            col("NetAmount", "Net amount", fmt="dec4", auto="line_net", msg5="ExtendedAmount"),
            E, E, E,
            col("LineRef", "Line reference", auto="txnref", ref="07"),
            E, E, E, E,
        ],
        "ORDERITEMS_PROMOTION": [
            col("MemberCard", "Member card", msg5="ClubCard"),
            col("TransactionDateTime", "Transaction date-time", msg5="StartDateTime"),
            col("StoreID", "Store ID", msg5="StoreID"),
            col("TillID", "Till ID", msg5="TillID"),
            col("TransactionNumber", "Transaction number", msg5="TransactionNumber"),
            col("ReceiptNo", "Receipt no", msg5="TransactionNumber"),
            col("BUCode", "BU code", "WWHK", msg5="json:buCode"),
            col("ItemID", "Item ID", msg5="MarkdownItemID"),
            col("LineNo", "Line no", auto="lineno"),
            col("PromotionID", "Promotion ID", msg5="PromotionID"),
            col("PromotionName", "Promotion name"),
            col("PromoDiscount", "Promotion discount", fmt="dec4", msg5="Amount"),
            col("PromoRef", "Promotion reference", auto="txnref", ref="07"),
        ],
    },
}


# ---------- layout ----------

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
    }
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
    base = (lay.get("name_format") or NAME_FORMAT).format(TYPE=ftype, BU=bu, YYYYMMDD=date, SEQ=seq)
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


def build_zip(lay, bu, date, seq, files):
    """files: {ftype: [[cell, ...], ...]} -> zip bytes with 4 csv + 4 ok."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for ft in FILE_TYPES:
            z.writestr(file_name(lay, ft, bu, date, seq, "csv"), csv_bytes(files.get(ft) or []))
            z.writestr(file_name(lay, ft, bu, date, seq, "ok"), b"")
    buf.seek(0)
    return buf


# ---------- import an existing set ----------

def parse_name(filename):
    """ORDER_PAYMENT_WWHK_20240829_54.csv -> (type, bu, date, seq)."""
    stem = Path(filename).stem
    for ft in sorted(FILE_TYPES, key=len, reverse=True):
        m = re.fullmatch(re.escape(ft) + r"_([A-Za-z0-9]+)_(\d{8})_(\w+)", stem)
        if m:
            return ft, m.group(1).upper(), m.group(2), m.group(3)
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
            warnings.append(f"{name}: name does not match {NAME_FORMAT}.csv — skipped")
            continue
        files[p[0]] = read_rows(raw)
        meta = meta or p[1:]
    if "ORDER" not in files:
        return {"error": "no ORDER_<BU>_<YYYYMMDD>_<SEQ>.csv in the upload", "warnings": warnings}
    shared = shared_names(lay)
    orders = rows_to_dicts(lay, "ORDER", files["ORDER"])
    children = {CHILD_OF[ft]: rows_to_dicts(lay, ft, files.get(ft, [])) for ft in CHILD_OF}
    key_names = [n for n in ("TransactionNumber", "ReceiptNo", "StoreID", "TillID", "MemberCard") if n in shared] or shared
    def key(d):
        return tuple(d.get(n, "") for n in key_names)
    txns = []
    for o in orders:
        t = {"order": o, "items": [], "payments": [], "promotions": []}
        for kind in ("items", "payments", "promotions"):
            t[kind] = [{k: v for k, v in c.items() if k not in shared} for c in children[kind] if key(c) == key(o)]
        txns.append(t)
    matched = sum(len(t[k]) for t in txns for k in ("items", "payments", "promotions"))
    total = sum(len(v) for v in children.values())
    if matched < total:
        warnings.append(f"{total - matched} child rows did not match any ORDER row on {', '.join(key_names)}")
    bu, date, seq = meta or ("", "", "")
    return {"bu": bu, "date": date, "seq": seq, "transactions": txns, "warnings": warnings}
