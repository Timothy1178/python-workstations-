"""Timestamp Converter — UTC+8 (Hong Kong / Taiwan / Malaysia) ⇄ UTC ⇄ epoch.

Everything runs in the browser: paste an epoch (seconds / milliseconds /
microseconds), an ISO date or a `YYYY-MM-DD HH:mm[:ss]` string and every
other representation is shown with a copy button. Quick buttons give the
current time, today / tomorrow / yesterday at midnight, end of day and
±1h / ±1d nudges; display settings (seconds, milliseconds, 12/24 h,
separators, zone suffix, zone offset) and custom format presets are kept
in the browser's localStorage, so nothing is stored on the server.
"""
from flask import Blueprint, render_template

bp = Blueprint("timestamp", __name__, url_prefix="/timestamp")

MODULE_INFO = {
    "name": "Timestamp Converter",
    "url": "/timestamp",
    "desc": "UTC+8 ⇄ UTC ⇄ epoch seconds / milliseconds, with now / today quick buttons, format presets and batch mode.",
    "icon": "⏱",
}


@bp.route("/")
def index():
    return render_template("timestamp/index.html")
