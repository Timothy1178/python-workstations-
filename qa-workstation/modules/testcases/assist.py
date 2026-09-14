"""AI assistant for the test case builder.

Runs the locally installed Claude Code CLI (`claude -p`) so no API key is
needed — it uses the user's existing Claude Code login. Designed so a
Copilot Studio provider can be added later behind the same run_assist()
contract.

Contract with the model: it must return one JSON object
  {"reply": str, "updates": [{"row": int, "fields": {...}}], "new_cases": [{...}]}
row numbers are 1-based positions in the builder table.
"""
import json
import os
import shutil
import subprocess

CLAUDE_PATHS = ["claude", "/opt/homebrew/bin/claude", "/usr/local/bin/claude"]
TIMEOUT = 240


def _clean_env():
    """Minimal environment for the CLI.

    If this server was launched from inside a Claude Code session, the
    inherited CLAUDE_*/ANTHROPIC_* variables point the nested CLI at that
    session's plumbing and it hangs — so start from scratch instead.
    """
    keep = ("PATH", "HOME", "USER", "SHELL", "TERM", "LANG", "TMPDIR")
    return {k: os.environ[k] for k in keep if k in os.environ}


def _claude_bin():
    for p in CLAUDE_PATHS:
        found = shutil.which(p) if "/" not in p else (p if shutil.which(p) else None)
        if found:
            return found
    return None


def _build_prompt(plan, template, table, message, history):
    fields = [f for f in template["fields"]]
    field_doc = "\n".join(f'- "{f["key"]}" ({f["label"]})' for f in fields)

    if table:
        rows = "\n".join(f"{i}. {json.dumps(r, ensure_ascii=False)}"
                         for i, r in enumerate(table, start=1))
    else:
        rows = "(the table is empty)"

    convo = ""
    if history:
        convo = "Conversation so far:\n" + "\n".join(
            f'{m["role"]}: {m["text"]}' for m in history[-8:]) + "\n\n"

    return f"""You are a QA test case assistant embedded in a test-plan builder used for AIMAS/CRM system testing (SIT/UAT). The tester chats with you to draft or complete test cases.

Respond with ONLY one JSON object — no markdown fences, no text outside it — with exactly these keys:
- "reply": short plain-text message to the tester (what you did / questions)
- "updates": list of {{"row": <1-based row number>, "fields": {{...}}}} — changes to EXISTING rows; include only the field keys you are changing
- "new_cases": list of {{...}} field objects — NEW rows to append to the table

Field keys you may use inside "fields" / "new_cases":
{field_doc}

Rules:
- Do NOT include "case_id" — numbering is automatic (1..x per Testing BU + Case pair).
- "steps" is a numbered list separated by newlines ("1. ...\\n2. ...").
- Write concise, executable test cases in the style of AIMAS test plans (concrete steps, verifiable expected results).
- If the tester pastes a requirement/ticket/spec, derive test cases from it (cover positive and negative paths).
- If the tester asks you to fill gaps, use "updates" on the existing rows.
- If information is missing (e.g. Testing BU), make a sensible draft and mention the assumption in "reply".

Test plan: {plan.get("name", "")} — {plan.get("description", "") or "no description"}
Current table rows:
{rows}

{convo}Tester's message: {message}
"""


def run_assist(plan, template, table, message, history):
    binary = _claude_bin()
    if not binary:
        return {"reply": "Claude CLI not found on this machine — install "
                         "Claude Code or configure another agent provider.",
                "updates": [], "new_cases": [], "error": "no_provider"}

    prompt = _build_prompt(plan, template, table, message, history)
    try:
        proc = subprocess.run(
            [binary, "-p", prompt],
            capture_output=True, text=True, timeout=TIMEOUT,
            stdin=subprocess.DEVNULL, env=_clean_env(), cwd=os.path.expanduser("~"))
    except subprocess.TimeoutExpired:
        return {"reply": "The agent took too long to answer — try again.",
                "updates": [], "new_cases": [], "error": "timeout"}

    raw = (proc.stdout or "").strip()
    _log_debug(proc.returncode, raw, proc.stderr)
    if proc.returncode != 0:
        detail = (raw or proc.stderr or "unknown error").strip()
        if "authenticate" in detail.lower() or "401" in detail:
            return {"reply": "The Claude CLI on this Mac is not logged in. "
                             "Open Terminal, run `claude`, and complete the "
                             "login once — then I'll be able to answer here.",
                    "updates": [], "new_cases": [], "error": "auth"}
        return {"reply": f"Agent error: {detail[:300]}",
                "updates": [], "new_cases": [], "error": "cli_failed"}

    data = _extract_json(raw)
    if data is None:
        # Model answered in prose — still show it rather than fail.
        return {"reply": raw[:2000], "updates": [], "new_cases": []}

    allowed = {f["key"] for f in template["fields"]}
    updates = []
    for u in data.get("updates", []) or []:
        try:
            row = int(u.get("row"))
        except (TypeError, ValueError):
            continue
        flds = {k: str(v) for k, v in (u.get("fields") or {}).items()
                if k in allowed}
        if row >= 1 and flds:
            updates.append({"row": row, "fields": flds})
    new_cases = [{k: str(v) for k, v in (c or {}).items() if k in allowed}
                 for c in data.get("new_cases", []) or []]
    new_cases = [c for c in new_cases if any(v.strip() for v in c.values())]

    return {"reply": str(data.get("reply", "")).strip() or "Done.",
            "updates": updates, "new_cases": new_cases}


def _log_debug(rc, stdout, stderr):
    from pathlib import Path
    log = Path(__file__).resolve().parents[2] / "data" / "assist_debug.log"
    log.write_text(f"rc={rc}\n--- stdout ---\n{stdout[:4000]}\n"
                   f"--- stderr ---\n{(stderr or '')[:2000]}\n",
                   encoding="utf-8")


def _extract_json(text):
    """Parse the model's JSON, tolerating code fences or stray prose."""
    for candidate in (text, text.strip("`").lstrip("json")):
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            return None
    return None
