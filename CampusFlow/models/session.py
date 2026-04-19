"""
models/session.py
Holds multi-turn conversation history and persistent user facts
for a single chat session. Serialisable to/from dict for API storage.
"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Session:
    # Full conversation (role: user | assistant)
    conversation: list[dict] = field(default_factory=list)

    # Facts extracted and accumulated across turns
    # e.g. {"gender": "female", "student_id": "STU-001", "budget_myr": 250}
    user_context: dict = field(default_factory=dict)

    # Tickets raised this session {dept: ticket_id}
    tickets: dict = field(default_factory=dict)

    # Which departments were involved last turn (for follow-up routing)
    last_departments: list[str] = field(default_factory=list)

    session_id: str = field(default_factory=lambda: datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def add_user(self, text: str) -> None:
        self.conversation.append({"role": "user", "content": text})

    def add_assistant(self, text: str) -> None:
        self.conversation.append({"role": "assistant", "content": text})

    def update_context(self, new_facts: dict) -> None:
        """Merge non-None facts into user_context."""
        self.user_context.update({k: v for k, v in new_facts.items() if v is not None})

    def history_for_llm(self, max_turns: int = 10) -> list[dict]:
        """Return the last N user+assistant pairs for LLM context."""
        return self.conversation[-(max_turns * 2):]

    def to_dict(self) -> dict:
        return {
            "session_id":       self.session_id,
            "created_at":       self.created_at,
            "user_context":     self.user_context,
            "tickets":          self.tickets,
            "last_departments": self.last_departments,
            "conversation":     self.conversation,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        s = cls()
        s.session_id        = data.get("session_id", s.session_id)
        s.created_at        = data.get("created_at", s.created_at)
        s.user_context      = data.get("user_context", {})
        s.tickets           = data.get("tickets", {})
        s.last_departments  = data.get("last_departments", [])
        s.conversation      = data.get("conversation", [])
        return s
