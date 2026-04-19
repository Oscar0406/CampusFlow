from repositories.base import BaseRepository


class TicketService:
    def __init__(self, repo: BaseRepository):
        self.repo = repo

    def create(self, dept: str, data: dict) -> dict:
        return self.repo.save_ticket(dept, data)

    def list_by_dept(self, dept: str) -> list[dict]:
        return self.repo.get_tickets(dept)

    def find(self, ticket_id: str, departments: list[str]) -> dict | None:
        for dept in departments:
            for t in self.repo.get_tickets(dept):
                if t.get("ticket_id") == ticket_id:
                    return t
        return None
