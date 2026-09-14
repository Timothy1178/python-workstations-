"""Storage for the QA wiki.

Pages live in data/wiki/<id>.json as
{id, title, category, tags, content, created, updated} — content is
Markdown. Category and tags drive the index grouping and search.
"""
import json
import re
import time
import uuid
from pathlib import Path

WIKI_DIR = Path(__file__).resolve().parents[2] / "data" / "wiki"


def _path(page_id):
    return WIKI_DIR / f"{page_id}.json"


def _write(page):
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    _path(page["id"]).write_text(
        json.dumps(page, indent=2, ensure_ascii=False), encoding="utf-8")


def list_pages():
    if not WIKI_DIR.exists():
        return []
    pages = [json.loads(p.read_text(encoding="utf-8"))
             for p in WIKI_DIR.glob("*.json")]
    pages.sort(key=lambda p: p.get("updated", ""), reverse=True)
    return pages


def get_page(page_id):
    p = _path(page_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def create_page(title, category="", tags=None, content=""):
    now = time.strftime("%Y-%m-%d %H:%M")
    page = {
        "id": f"{time.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}",
        "title": title,
        "category": category.strip() or "General",
        "tags": tags or [],
        "content": content,
        "created": now,
        "updated": now,
    }
    _write(page)
    return page


def update_page(page_id, title, category, tags, content):
    page = get_page(page_id)
    if page is None:
        return None
    page.update({
        "title": title,
        "category": category.strip() or "General",
        "tags": tags,
        "content": content,
        "updated": time.strftime("%Y-%m-%d %H:%M"),
    })
    _write(page)
    return page


def delete_page(page_id):
    p = _path(page_id)
    if p.exists():
        p.unlink()


def parse_tags(raw):
    return [t.strip().lower() for t in re.split(r"[,;]", raw or "") if t.strip()]


def categories(pages):
    counts = {}
    for p in pages:
        counts[p["category"]] = counts.get(p["category"], 0) + 1
    return sorted(counts.items(), key=lambda kv: kv[0].lower())


def snippet(content, limit=150):
    """First words of the page with the Markdown noise stripped."""
    text = re.sub(r"```.*?```", " ", content or "", flags=re.S)
    text = re.sub(r"[#>*_`\[\]|-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def search(pages, q):
    q = (q or "").strip().lower()
    if not q:
        return pages
    hits = []
    for p in pages:
        hay = " ".join([p["title"], p["category"], " ".join(p["tags"]),
                        p["content"]]).lower()
        if all(w in hay for w in q.split()):
            hits.append(p)
    return hits
