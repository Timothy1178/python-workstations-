"""Find transaction messages ({"id", ..., "playloadJson": "..."} JSON
objects) inside uploaded files: .xlsx/.xlsm (every text cell of every
sheet), .csv, .docx (paragraph text), .json / .txt.

Shared by the Msg5 Json page and the TLog Handler library. Not a
blueprint — app.py skips modules without `bp`.
"""
import csv
import io
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
PAYLOAD_KEYS = ("playloadJson", "payloadJson")


def find_messages(text):
    """Every top-level JSON object in the text that carries a payload."""
    dec = json.JSONDecoder()
    out, i = [], 0
    while True:
        i = text.find("{", i)
        if i < 0:
            break
        try:
            obj, end = dec.raw_decode(text, i)
        except ValueError:
            i += 1
            continue
        if isinstance(obj, dict) and any(isinstance(obj.get(k), str) for k in PAYLOAD_KEYS):
            out.append(obj)
        i = end
    return out


def docx_text(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    paras = []
    for p in root.iter(W + "p"):
        txt = "".join(t.text or "" for t in p.iter(W + "t"))
        if txt.strip():
            paras.append(txt)
    return "\n".join(paras)


def _label(obj):
    bits = [str(obj.get(k)) for k in ("buCode", "type") if obj.get(k)]
    if obj.get("id"):
        bits.append(str(obj["id"])[:13])
    return " · ".join(bits)


def _entry(name, obj, where=""):
    return {
        "name": name,
        "where": where,
        "bu_code": str(obj.get("buCode", "") or "").upper(),
        "label": _label(obj),
        "json": json.dumps(obj, ensure_ascii=False),
    }


def xlsx_messages(stem, raw):
    """Messages from every text cell; the name is taken from the first
    other text cell in the same row (a title column), else sheet!cell."""
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True, read_only=True)
    found = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            texts = [(c.coordinate, c.value) for c in row if isinstance(c.value, str) and c.value.strip()]
            labels = [v.strip() for _, v in texts if "{" not in v][:1]
            for coord, v in texts:
                if "{" not in v:
                    continue
                for n, obj in enumerate(find_messages(v), start=1):
                    where = f"{ws.title}!{coord}"
                    name = labels[0] if labels else f"{stem} {where}"
                    if n > 1:
                        name += f" ({n})"
                    found.append(_entry(name, obj, where))
    wb.close()
    return found


def csv_messages(stem, raw):
    text = raw.decode("utf-8-sig", errors="replace")
    found = []
    for r, row in enumerate(csv.reader(io.StringIO(text)), start=1):
        labels = [c.strip() for c in row if c.strip() and "{" not in c][:1]
        for c in row:
            for n, obj in enumerate(find_messages(c), start=1):
                name = labels[0] if labels else f"{stem} row {r}"
                found.append(_entry(name + (f" ({n})" if n > 1 else ""), obj, f"row {r}"))
    return found


def read_upload(filename, raw):
    """-> list of {name, where, bu_code, label, json}."""
    stem, ext = Path(filename).stem, Path(filename).suffix.lower()
    if ext in (".xlsx", ".xlsm"):
        return xlsx_messages(stem, raw)
    if ext == ".csv":
        return csv_messages(stem, raw)
    text = docx_text(raw) if ext == ".docx" else raw.decode("utf-8-sig", errors="replace")
    msgs = find_messages(text)
    return [_entry(stem if len(msgs) == 1 else f"{stem} ({n})", obj)
            for n, obj in enumerate(msgs, start=1)]
