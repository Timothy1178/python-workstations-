"""AI assistant for the test case builder.

Builds the prompt and parses the reply; the completion itself goes
through the shared provider service (modules/agents/service.py), so the
tester can pick the local Claude CLI or any connected Copilot agent in
the chat box.

Contract with the model: it must return one JSON object
  {"reply": str, "updates": [{"row": int, "fields": {...}}], "new_cases": [{...}]}
row numbers are 1-based positions in the builder table. A provider that
answers in prose (e.g. a Copilot agent without these instructions) still
works — the reply is shown in the chat, just without table edits.
"""
import json

from modules.agents import service


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


def run_assist(plan, template, table, message, history, provider_id=None,
               attachments=None):
    prompt = _build_prompt(plan, template, table, message, history)
    try:
        raw = service.complete_with_attachments(provider_id, prompt, attachments)
    except service.ProviderError as exc:
        return {"reply": str(exc), "updates": [], "new_cases": [],
                "error": exc.code}

    data = _extract_json(raw)
    if data is None:
        # Model answered in prose — still show it rather than fail.
        return {"reply": raw[:2000] or "(no reply)",
                "updates": [], "new_cases": []}

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


_extract_json = service.extract_json
