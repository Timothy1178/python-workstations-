"""Web Plugins module — browser extensions for QA work (Chrome & Edge).

Each plugin lives in plugins/<slug>/ as an unpacked Manifest V3
extension plus a plugin.json describing it for this page. The page
lists them with install steps and a zip download; installing is
"load unpacked" (or drop the zip) via chrome://extensions /
edge://extensions with Developer mode on.
"""
import io
import json
import zipfile
from pathlib import Path

from flask import Blueprint, render_template, send_file, abort

PLUGINS_DIR = Path(__file__).resolve().parents[2] / "plugins"

bp = Blueprint("plugins", __name__, url_prefix="/plugins")

MODULE_INFO = {
    "name": "Web Plugins",
    "url": "/plugins",
    "desc": "Browser extensions for QA work — download and load into Chrome or Edge.",
    "icon": "🧩",
}


def list_plugins():
    plugins = []
    if PLUGINS_DIR.exists():
        for meta_file in sorted(PLUGINS_DIR.glob("*/plugin.json")):
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            meta["slug"] = meta.get("slug") or meta_file.parent.name
            plugins.append(meta)
    return plugins


@bp.route("/")
def index():
    return render_template("plugins/index.html", plugins=list_plugins())


@bp.route("/<slug>/download")
def download(slug):
    folder = PLUGINS_DIR / slug
    if not folder.is_dir() or not (folder / "plugin.json").exists():
        abort(404)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(folder.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts and f.name != ".DS_Store":
                zf.write(f, f.relative_to(folder))
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"{slug}.zip",
                     mimetype="application/zip")
