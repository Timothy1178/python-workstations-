import json
import time
import uuid
from pathlib import Path

AGENTS_FILE = Path(__file__).resolve().parents[2] / "data" / "agents.json"


def load_agents():
    if AGENTS_FILE.exists():
        return json.loads(AGENTS_FILE.read_text(encoding="utf-8"))
    return []


def get_agent(agent_id):
    return next((a for a in load_agents() if a["id"] == agent_id), None)


def _save(agents):
    AGENTS_FILE.parent.mkdir(exist_ok=True)
    AGENTS_FILE.write_text(
        json.dumps(agents, indent=2, ensure_ascii=False), encoding="utf-8")


def add_agent(name, role="", notes="", environment_id="", schema_name="",
              tenant_id="", app_client_id="", direct_connect_url=""):
    agents = load_agents()
    agents.append({
        "id": uuid.uuid4().hex[:8],
        "name": name,
        "role": role,
        "notes": notes,
        "environment_id": environment_id,
        "schema_name": schema_name,
        "direct_connect_url": direct_connect_url,
        "tenant_id": tenant_id,
        "app_client_id": app_client_id,
        "status": "not connected",
        "added": time.strftime("%Y-%m-%d"),
    })
    _save(agents)


def set_status(agent_id, status):
    agents = load_agents()
    for a in agents:
        if a["id"] == agent_id:
            a["status"] = status
    _save(agents)


def delete_agent(agent_id):
    _save([a for a in load_agents() if a["id"] != agent_id])
