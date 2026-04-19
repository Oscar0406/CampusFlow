"""
orchestrator/dispatcher.py
Wires together a single chat turn:
  1. Resolve tenant config → build LLMService, Repository, Adapter
  2. Inject dependencies into tools (one-time per request)
  3. Orchestrate → route to departments
  4. Call each matched agent with session context
  5. Compose unified reply
"""
from langsmith import traceable

from adapters.factory import get_adapter
from agents import AGENT_REGISTRY
from core.tools import init_tools
from models.context import TenantContext
from models.session import Session
from orchestrator.orchestrator import OrchestratorService
from repositories.json_repo import JsonRepository
from services.llm_service import LLMService


@traceable(name="chat_turn")
def chat_turn(user_input: str, session: Session, ctx: TenantContext) -> dict:
    """
    Process one user message within an ongoing session.
    Mutates session in-place and returns the full response dict.
    """
    # 1. Build services for this tenant
    llm     = LLMService.from_config(ctx.llm_config)
    repo    = JsonRepository(ctx.ticket_path)
    adapter = get_adapter(ctx)

    # 2. Inject dependencies into the tool registry
    init_tools(repo, adapter)

    # 3. Record user turn
    session.add_user(user_input)

    # 4. Route
    orch     = OrchestratorService(llm, ctx.departments)
    decision = orch.route(user_input, session)

    if not decision:
        reply = "Sorry, I couldn't understand that. Could you rephrase?"
        session.add_assistant(reply)
        return {"reply": reply, "departments_contacted": []}

    departments    = decision.departments
    extracted_data = decision.extracted_data
    session.last_departments = departments

    # 5. Call each matched agent
    agent_responses: dict[str, dict] = {}
    for dept in departments:
        agent_fn = AGENT_REGISTRY.get(dept)
        if not agent_fn:
            agent_responses[dept] = {"error": f"No agent registered for: {dept}"}
            continue
        try:
            agent_responses[dept] = agent_fn(extracted_data, session, llm)
        except Exception as e:
            agent_responses[dept] = {"error": str(e)}

    # 6. Compose reply from all agent messages
    parts = [
        resp.get("message") or resp.get("error", "")
        for resp in agent_responses.values()
        if resp.get("message") or resp.get("error")
    ]
    assistant_reply = "\n\n".join(parts) or "Done!"
    session.add_assistant(assistant_reply)

    return {
        "reply": assistant_reply,
        "routing": {
            "departments": departments,
            "confidence":  decision.confidence,
            "is_followup": decision.is_followup,
            "summary":     extracted_data.get("summary", ""),
        },
        "responses": agent_responses,
    }
