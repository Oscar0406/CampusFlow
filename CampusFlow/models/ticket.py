from dataclasses import dataclass, field
from enum import Enum


class TicketStatus(str, Enum):
    OPEN        = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED    = "resolved"
    CLOSED      = "closed"


@dataclass
class Ticket:
    ticket_id:     str
    department:    str
    university_id: str
    status: TicketStatus = TicketStatus.OPEN
    timestamp:     str = ""
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "ticket_id":     self.ticket_id,
            "department":    self.department,
            "university_id": self.university_id,
            "status":        self.status.value,
            "timestamp":     self.timestamp,
            **self.data,
        }
