"""Import test cases from an Excel workbook (.xlsx) or CSV into a plan.

Two-step flow so the tester can check what lands in the table:

1. ``preview(raw, filename, template)`` reads the file, picks the sheet and
   header row automatically, suggests a column -> template field mapping
   (by header name, with the usual aliases: "Test Steps" -> steps,
   "Expected Result" -> expected ...) and returns everything the import
   dialog needs. Workbooks exported by this workstation (SIT sheet, header
   on row 8) round-trip without any manual mapping.
2. ``build_cases(rows, mapping, ...)`` turns the chosen rows into case
   dicts (``fields`` + optional ``run`` results) for the builder table.

Uploaded files are parked under data/uploads/imports/<token> between the
two steps so re-previewing another sheet does not need a re-upload.
"""
import csv
import io
import re
import time
import uuid
from pathlib import Path

IMPORT_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads" / "imports"
MAX_PREVIEW_ROWS = 300

# Header spellings commonly seen in test plan spreadsheets, per field key.
ALIASES = {
    "testing_bu": ["testing bu", "bu", "business unit", "module", "area", "function", "component"],
    "case_id": ["#", "no", "no.", "id", "case id", "tc id", "test case id", "tc", "seq", "s/n"],
    "title": ["case", "test case", "title", "scenario", "test scenario", "case name",
              "test case name", "name", "summary", "description", "test case description"],
    "steps": ["steps", "test steps", "step", "procedure", "test procedure", "action",
              "actions", "test step"],
    "expected": ["expected results", "expected result", "expected", "expected outcome",
                 "expected output", "expected behaviour", "expected behavior"],
    "test_data": ["test data", "data", "input", "input data", "testdata"],
    "campaign_id": ["campaign id", "campaign", "campaign no"],
    "remark": ["remark", "remarks", "notes", "note", "comment", "comments"],
    "result": ["testing results", "testing result", "result", "results", "test result",
               "status", "pass/fail", "pass / fail"],
    "actual": ["actual results", "actual result", "actual", "actual outcome"],
    "pre_condition": ["pre-condition", "precondition", "pre condition", "prerequisite",
                      "prerequisites", "setup"],
    "priority": ["priority", "severity"],
}

RESULT_WORDS = {
    "pass": "Pass", "passed": "Pass", "p": "Pass", "ok": "Pass", "success": "Pass",
    "fail": "Fail", "failed": "Fail", "f": "Fail", "ng": "Fail", "error": "Fail",
    "blocked": "Blocked", "block": "Blocked",
    "n/a": "N/A", "na": "N/A", "not applicable": "N/A", "skip": "N/A", "skipped": "N/A",
    "not run": "Not Run", "notrun": "Not Run", "not executed": "Not Run", "pending": "Not Run",
}


def _norm(s):
    s = str(s or "").strip().lower()
    s = re.sub(r"[\s_\-]+", " ", s)
    return s.strip(" :*")


def _cell_text(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if hasattr(v, "strftime"):
        return v.strftime("%Y-%m-%d") if not getattr(v, "hour", 0) else v.strftime("%Y-%m-%d %H:%M")
    return str(v).replace("\r\n", "\n").replace("\r", "\n").strip()


# ---------- reading ----------

def read_sheets(raw, filename):
    """{sheet name: [[cell text, ...], ...]} — .xlsx/.xlsm via openpyxl,
    .csv/.txt via the csv module (one sheet named after the file)."""
    ext = (filename.rsplit(".", 1)[-1].lower() if "." in filename else "")
    if ext in ("csv", "txt", "tsv"):
        text = raw.decode("utf-8-sig", errors="replace")
        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        rows = [[_cell_text(c) for c in r] for r in csv.reader(io.StringIO(text), dialect)]
        return {Path(filename).stem or "CSV": rows}
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True, read_only=True)
    sheets = {}
    for ws in wb.worksheets:
        rows = []
        for r in ws.iter_rows(values_only=True):
            rows.append([_cell_text(c) for c in r])
        # trim trailing empty rows/columns
        while rows and not any(rows[-1]):
            rows.pop()
        width = max((len(r) - _trailing_blanks(r) for r in rows), default=0)
        sheets[ws.title] = [r[:width] + [""] * (width - len(r[:width])) for r in rows]
    wb.close()
    return sheets


def _trailing_blanks(row):
    n = 0
    for c in reversed(row):
        if c:
            break
        n += 1
    return n


# ---------- detection ----------

def field_aliases(template):
    """{field key: set of normalised header spellings} for the template's
    builder fields, run fields, plus the built-in aliases."""
    out = {}
    for f in template.get("fields", []) + template.get("run_fields", []):
        key = f["key"]
        names = {_norm(f.get("label", "")), _norm(key)}
        names |= {_norm(a) for a in ALIASES.get(key, [])}
        out[key] = {n for n in names if n}
    if "case_id" not in out:
        out["case_id"] = {_norm(a) for a in ALIASES["case_id"]}
    return out


def _match_key(header, aliases):
    h = _norm(header)
    if not h:
        return None
    for key, names in aliases.items():
        if h in names:
            return key
    # loose: header contains an alias word (e.g. "Expected Result (UAT)")
    for key, names in aliases.items():
        for n in sorted(names, key=len, reverse=True):
            if len(n) >= 4 and n in h:
                return key
    return None


def detect_header_row(rows, aliases, limit=40):
    """Index of the row that looks most like the header (most alias
    matches); falls back to the first non-empty row."""
    best, best_score = None, 0
    for i, row in enumerate(rows[:limit]):
        score = sum(1 for c in row if _match_key(c, aliases))
        if score > best_score:
            best, best_score = i, score
    if best is not None and best_score >= 2:
        return best
    for i, row in enumerate(rows[:limit]):
        if any(c.strip() for c in row):
            return i
    return 0


def suggest_mapping(headers, aliases):
    mapping, used = {}, set()
    for i, h in enumerate(headers):
        key = _match_key(h, aliases)
        if key and key not in used:
            mapping[str(i)] = key
            used.add(key)
    return mapping


def pick_sheet(sheets, aliases):
    """Prefer the sheet whose best header row matches the most fields."""
    best, best_score = None, -1
    for name, rows in sheets.items():
        if not rows:
            continue
        hi = detect_header_row(rows, aliases)
        score = len(suggest_mapping(rows[hi], aliases))
        if score > best_score:
            best, best_score = name, score
    return best or next(iter(sheets), None)


# ---------- the two steps ----------

def park_upload(raw, filename):
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    ext = (filename.rsplit(".", 1)[-1].lower() if "." in filename else "xlsx")
    ext = re.sub(r"[^a-z0-9]", "", ext)[:6] or "xlsx"
    token = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    (IMPORT_DIR / f"{token}.{ext}").write_bytes(raw)
    # housekeeping: forget parked uploads older than a day
    cutoff = time.time() - 86400
    for p in IMPORT_DIR.iterdir():
        if p.is_file() and p.stat().st_mtime < cutoff and p.name != f"{token}.{ext}":
            try:
                p.unlink()
            except OSError:
                pass
    return token


def parked_file(token):
    if not re.fullmatch(r"[0-9]{8}-[0-9]{6}-[0-9a-f]{8}", token or ""):
        return None
    for p in IMPORT_DIR.glob(f"{token}.*"):
        return p
    return None


def discard(token):
    p = parked_file(token)
    if p:
        try:
            p.unlink()
        except OSError:
            pass


def preview(raw, filename, template, sheet=None, header_row=None):
    """Everything the import dialog shows. header_row is 1-based."""
    sheets = read_sheets(raw, filename)
    if not sheets:
        return {"error": "no sheets found in the file"}
    aliases = field_aliases(template)
    if sheet not in sheets:
        sheet = pick_sheet(sheets, aliases)
    rows = sheets[sheet]
    if not rows:
        return {"error": f"sheet '{sheet}' is empty", "sheets": list(sheets)}
    if header_row is None or not (1 <= int(header_row) <= len(rows)):
        hi = detect_header_row(rows, aliases)
    else:
        hi = int(header_row) - 1
    headers = rows[hi]
    data = rows[hi + 1:]
    mapping = suggest_mapping(headers, aliases)
    return {
        "sheets": list(sheets),
        "sheet": sheet,
        "header_row": hi + 1,
        "headers": [h or f"Column {i + 1}" for i, h in enumerate(headers)],
        "mapping": mapping,
        "rows": data[:MAX_PREVIEW_ROWS],
        "total": len(data),
        "truncated": len(data) > MAX_PREVIEW_ROWS,
    }


def build_cases(rows, mapping, template, fill_down=True, skip_blank=True):
    """Rows (lists of cell text) + {col index: field key} -> list of
    {"fields": {...}, "run": {...}}. Blank Testing BU / Case cells are
    filled from the row above when fill_down is on (Excel merged cells
    read back as blanks)."""
    field_keys = [f["key"] for f in template.get("fields", [])]
    run_keys = [f["key"] for f in template.get("run_fields", [])]
    result_field = next((f for f in template.get("run_fields", [])
                         if f.get("type") == "select"), None)
    col_map = {int(k): v for k, v in mapping.items() if v}
    cases, prev = [], {}
    for row in rows:
        fields = {k: "" for k in field_keys}
        run = {}
        got_any = False
        for ci, key in col_map.items():
            val = row[ci] if ci < len(row) else ""
            if val.strip():
                got_any = True
            if key in run_keys:
                if key == (result_field or {}).get("key"):
                    val = normalise_result(val, result_field.get("options", []))
                run[key] = val
            elif key == "case_id":
                continue  # numbered on save, in row order
            else:
                fields[key] = val
        if skip_blank and not got_any:
            continue
        if fill_down:
            for k in ("testing_bu", "title"):
                if k in fields and not fields[k].strip():
                    fields[k] = prev.get(k, "")
        # a row that only carries the group label (no steps etc.) is not a case
        if skip_blank and not any(v.strip() for k, v in fields.items()
                                  if k not in ("testing_bu", "title")) \
                and not any(v.strip() for v in run.values()) \
                and not fields.get("title", "").strip():
            continue
        prev = fields
        case = {"fields": fields}
        if any(v.strip() for v in run.values()):
            case["run"] = run
        cases.append(case)
    return cases


def normalise_result(value, options):
    v = _norm(value)
    if not v:
        return ""
    for opt in options:
        if _norm(opt) == v:
            return opt
    word = RESULT_WORDS.get(v)
    if word and word in options:
        return word
    return value.strip()
