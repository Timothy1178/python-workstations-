"""QA Workstation — local Flask server.

Each feature lives in modules/<name>/ as a Flask blueprint. Any module that
exposes `bp` (blueprint) and `MODULE_INFO` (dict) is auto-registered and
appears on the main page and sidebar — add a folder, get a tool.
"""
import importlib
import pkgutil
from pathlib import Path

from flask import Flask, render_template

import modules
from version import __version__

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "qa-workstation-local"
    app.config["DATA_DIR"] = DATA_DIR
    DATA_DIR.mkdir(exist_ok=True)

    registered = []
    for m in pkgutil.iter_modules(modules.__path__):
        mod = importlib.import_module(f"modules.{m.name}")
        bp = getattr(mod, "bp", None)
        if bp is None:
            continue
        app.register_blueprint(bp)
        info = getattr(mod, "MODULE_INFO", {})
        registered.append({
            "name": info.get("name", m.name.title()),
            "url": info.get("url", f"/{m.name}"),
            "desc": info.get("desc", ""),
            "icon": info.get("icon", "🔧"),
        })
    registered.sort(key=lambda i: i["name"])
    app.config["MODULES"] = registered

    app.config["VERSION"] = __version__

    @app.context_processor
    def inject_modules():
        return {"nav_modules": registered, "app_version": __version__}

    @app.route("/")
    def home():
        from modules.testcases.store import plan_summaries
        from modules.agents.store import load_agents
        return render_template(
            "index.html",
            modules=registered,
            plans=plan_summaries()[:5],
            agents=load_agents(),
        )

    return app


if __name__ == "__main__":
    import os
    app = create_app()
    # The debug reloader runs this file twice; only the serving child
    # (WERKZEUG_RUN_MAIN) should run scheduled Mailer jobs.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        from modules.mailer import scheduler
        scheduler.start()
    print("\n  QA Workstation running at http://127.0.0.1:5010\n")
    app.run(host="127.0.0.1", port=5010, debug=True)
