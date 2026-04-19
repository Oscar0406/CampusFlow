"""
orchestrator/orchestrator.py
Context-aware orchestrator — sees the full conversation history so
follow-up messages ("I prefer single room") are routed correctly.
"""
from langsmith import traceable

from core.json_parser import extract_json
from models.request import RoutingDecision
from models.session import Session
from services.llm_service import LLMService

_PROMPT = """\
You are the CampusFlow Orchestrator — an intelligent routing agent for a university helpdesk.

You receive the FULL conversation history so you can understand follow-up messages in context.
Example: if the student already asked about hostel and now says "I prefer single room",
that is still a accommodation request — do not re-route to a different department.

Your job:
1. Read the LATEST user message IN CONTEXT of the conversation.
2. Identify ALL departments that need to be involved (can be more than one).
3. Extract structured data so each agent can act immediately.
4. Carry forward facts already known (gender, student_id, preferences, tickets).

Available departments:
- "maintenance"  — repairs, broken equipment, HVAC, plumbing, electrical, cleanliness
- "academic"     — course registration, grades, transcripts, dean letters, appeals
- "finance"      — fees, scholarships, refunds, payment plans, financial aid
- "it_support"   — network, Wi-Fi, computers, software, portal, passwords, printers
- "library"      — book reservations, fines, study rooms, academic databases
- "procurement"  — purchasing, equipment orders, vendor approvals, budget estimates
- "accommodation"      — hostel, room availability, assignments, dorm maintenance, hostel fees

Rules:
- Include EVERY relevant department. One message can involve 2-3.
- is_followup: true if this message continues a topic from an earlier turn.
- urgency: low | medium | high | critical
- confidence: 0.0 to 1.0

Respond ONLY with valid JSON, no markdown fences:
{
  "departments": ["dept1"],
  "confidence": 0.95,
  "is_followup": false,
  "extracted_data": {
    "summary": "",
    "urgency": "low",
    "location": null,
    "issue_type": "",
    "requester_type": "student|staff|unknown",
    "gender": null,
    "student_id": null,
    "preferred_room_type": null,
    "budget_myr": null,
    "additional_context": ""
  }
}"""


class OrchestratorService:
    def __init__(self, llm: LLMService, allowed_departments: list[str]):
        self.llm = llm
        self.allowed = set(allowed_departments)

    @traceable(name="orchestrator")
    def route(self, user_input: str, session: Session) -> RoutingDecision | None:
        messages = [{"role": "system", "content": _PROMPT}]

        # Inject known user context as a silent system note
        if session.user_context:
            ctx_note = (
                "Known facts about this user from earlier in the conversation:\n"
                + "\n".join(f"  {k}: {v}" for k, v in session.user_context.items())
            )
            messages.append({"role": "system", "content": ctx_note})

        messages.extend(session.history_for_llm())
        messages.append({"role": "user", "content": user_input})

        raw = self.llm.complete(messages)
        parsed = extract_json(raw)

        if not parsed or "departments" not in parsed:
            return None

        depts = [d for d in parsed["departments"] if d in self.allowed]

        # Persist any newly extracted user facts back into the session
        ed = parsed.get("extracted_data", {})
        session.update_context({
            "gender":              ed.get("gender"),
            "student_id":          ed.get("student_id"),
            "preferred_room_type": ed.get("preferred_room_type"),
            "budget_myr":          ed.get("budget_myr"),
        })

        return RoutingDecision(
            departments=depts,
            confidence=parsed.get("confidence", 0.0),
            is_followup=parsed.get("is_followup", False),
            extracted_data=ed,
        )
