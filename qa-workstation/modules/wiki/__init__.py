"""QA Wiki module — organised knowledge base with an agent-assisted editor.

Pages are Markdown, grouped by category, tagged, and searchable. The
editor embeds the shared chat box (static/chatbox.js): paste a real
document or introduction and the selected agent — local Claude CLI or a
connected Copilot agent — drafts or improves the wiki page.
"""
from flask import (Blueprint, jsonify, render_template, request, redirect,
                   url_for)
from markupsafe import escape

from modules.agents import service

from . import store

try:
    import markdown as _markdown

    def render_md(text):
        return _markdown.markdown(text or "", extensions=["extra", "sane_lists"])
except ImportError:  # keep the wiki readable without the package
    def render_md(text):
        return f"<pre class=\"wiki-fallback\">{escape(text or '')}</pre>"

bp = Blueprint("wiki", __name__, url_prefix="/wiki")

MODULE_INFO = {
    "name": "QA Wiki",
    "url": "/wiki",
    "desc": "Team knowledge base — searchable Markdown pages with agent-assisted writing.",
    "icon": "📚",
}

store.ensure_seeds()


@bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    cat = request.args.get("category", "").strip()
    pages = store.list_pages()
    all_categories = store.categories(pages)
    shown = store.search(pages, q)
    if cat:
        shown = [p for p in shown if p["category"] == cat]
    grouped = {}
    for p in shown:
        grouped.setdefault(p["category"], []).append(p)
    for plist in grouped.values():
        plist.sort(key=lambda p: p["title"].lower())
    return render_template(
        "wiki/index.html",
        q=q, cat=cat,
        categories=all_categories,
        grouped=sorted(grouped.items(), key=lambda kv: kv[0].lower()),
        recent=pages[:5] if not q and not cat else [],
        total=len(pages), shown_count=len(shown),
        snippet=store.snippet,
    )


@bp.route("/new")
def new():
    return render_template("wiki/edit.html", page=None,
                           categories=[c for c, _ in store.categories(store.list_pages())])


@bp.route("/create", methods=["POST"])
def create():
    title = request.form.get("title", "").strip()
    if not title:
        return redirect(url_for("wiki.index"))
    page = store.create_page(
        title=title,
        category=request.form.get("category", ""),
        tags=store.parse_tags(request.form.get("tags", "")),
        content=request.form.get("content", ""),
    )
    return redirect(url_for("wiki.view", page_id=page["id"]))


@bp.route("/<page_id>")
def view(page_id):
    page = store.get_page(page_id)
    if page is None:
        return redirect(url_for("wiki.index"))
    return render_template("wiki/view.html", page=page,
                           html=render_md(page["content"]))


@bp.route("/<page_id>/edit")
def edit(page_id):
    page = store.get_page(page_id)
    if page is None:
        return redirect(url_for("wiki.index"))
    return render_template("wiki/edit.html", page=page,
                           categories=[c for c, _ in store.categories(store.list_pages())])


@bp.route("/<page_id>/save", methods=["POST"])
def save(page_id):
    title = request.form.get("title", "").strip()
    page = store.update_page(
        page_id,
        title=title or "Untitled",
        category=request.form.get("category", ""),
        tags=store.parse_tags(request.form.get("tags", "")),
        content=request.form.get("content", ""),
    )
    if page is None:
        return redirect(url_for("wiki.index"))
    return redirect(url_for("wiki.view", page_id=page_id))


@bp.route("/<page_id>/delete", methods=["POST"])
def delete(page_id):
    store.delete_page(page_id)
    return redirect(url_for("wiki.index"))


@bp.route("/preview", methods=["POST"])
def preview():
    content = (request.get_json(force=True) or {}).get("content", "")
    return jsonify({"html": render_md(content)})


# ---------- AI assistants ----------

@bp.route("/ask", methods=["POST"])
def ask():
    """Q&A over the whole wiki, for the chat box on the index page."""
    data = request.get_json(force=True)
    pages = store.list_pages()
    parts, total = [], 0
    for p in pages:
        body = p["content"][:3000]
        block = (f"=== {p['title']} (category: {p['category']}; "
                 f"tags: {', '.join(p['tags'])}; updated {p['updated']}) ===\n{body}")
        total += len(block)
        if total > 45000:
            parts.append("[... more pages omitted — knowledge base truncated]")
            break
        parts.append(block)
    convo = ""
    history = data.get("history", [])
    if history:
        convo = "Conversation so far:\n" + "\n".join(
            f'{m["role"]}: {m["text"]}' for m in history[-8:]) + "\n\n"
    prompt = f"""You are the QA team's knowledge assistant. Answer the tester's question using ONLY the wiki pages below (and any documents attached to the message). Answer in plain text, concise and practical. Name the wiki page(s) you used. If the wiki doesn't contain the answer, say so and suggest which page should be created or updated.

Wiki pages:
{chr(10).join(parts) if parts else "(the wiki is empty)"}

{convo}Tester's question: {data.get("message", "")}
"""
    try:
        raw = service.complete_with_attachments(
            data.get("provider"), prompt, data.get("attachments"))
    except service.ProviderError as exc:
        return jsonify({"reply": str(exc), "error": exc.code})
    return jsonify({"reply": raw[:6000] or "(no reply)"})

def _build_prompt(draft, message, history):
    convo = ""
    if history:
        convo = "Conversation so far:\n" + "\n".join(
            f'{m["role"]}: {m["text"]}' for m in history[-8:]) + "\n\n"
    tags = ", ".join(draft.get("tags", [])) or "(none)"
    return f"""You are the QA team's knowledge librarian embedded in the QA workstation wiki editor. The tester chats with you to create and improve wiki documentation from real documents, specs, tickets and introductions they paste.

Respond with ONLY one JSON object — no markdown fences, no text outside it — with these keys:
- "reply": short plain-text message to the tester (what you did / open questions)
- optionally "title", "category", "tags" (list of short lowercase strings), "content" — include a key ONLY when you want to change that field. "content" must be the COMPLETE new Markdown for the page; it replaces the draft.

Guidelines:
- Structure "content" as clean Markdown: a one-line summary first, then only the sections that apply — ## Purpose, ## Scope, ## Details, ## Steps, ## FAQ, ## Glossary, ## Related, ## Sources.
- When the tester pastes a document or introduction, distil it into documentation: factual, concise, deduplicated. Keep exact values (URLs, IDs, versions, environment names, owners) verbatim, and record the source document's name under ## Sources.
- When asked to improve or reorganise, restructure without inventing facts; put anything unclear in "reply" as questions instead of guessing.
- "category" is one short noun (e.g. Process, Environments, AIMAS, Tools); pick from the team's existing categories when one fits.

Current draft:
title: {draft.get("title") or "(empty)"}
category: {draft.get("category") or "(empty)"}
tags: {tags}
content:
<<<
{draft.get("content") or "(empty)"}
>>>

{convo}Tester's message: {message}
"""


@bp.route("/assist", methods=["POST"])
def assist():
    data = request.get_json(force=True)
    draft = data.get("draft", {})
    prompt = _build_prompt(draft, data.get("message", ""),
                           data.get("history", []))
    try:
        raw = service.complete_with_attachments(
            data.get("provider"), prompt, data.get("attachments"))
    except service.ProviderError as exc:
        return jsonify({"reply": str(exc), "error": exc.code})

    parsed = service.extract_json(raw)
    if parsed is None:  # prose answer — show it, no field changes
        return jsonify({"reply": raw[:4000] or "(no reply)"})
    out = {"reply": str(parsed.get("reply", "")).strip() or "Done."}
    for key in ("title", "category", "content"):
        value = parsed.get(key)
        if isinstance(value, str) and value.strip():
            out[key] = value
    tags = parsed.get("tags")
    if isinstance(tags, list):
        out["tags"] = [str(t).strip().lower() for t in tags if str(t).strip()]
    return jsonify(out)
