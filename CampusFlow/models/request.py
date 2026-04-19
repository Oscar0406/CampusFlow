from dataclasses import dataclass, field


@dataclass
class IncomingRequest:
    message: str
    user_id: str = ""
    session_id: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class RoutingDecision:
    departments: list[str]
    confidence: float
    is_followup: bool = False
    extracted_data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "departments":    self.departments,
            "confidence":     self.confidence,
            "is_followup":    self.is_followup,
            "extracted_data": self.extracted_data,
        }
