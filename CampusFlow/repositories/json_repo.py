import json
import os
import random
import string
from datetime import datetime

from repositories.base import BaseRepository

DEPT_PREFIX = {
    "maintenance": "MNT", "academic": "ACA", "finance": "FIN",
    "it_support":  "ITS", "library":  "LIB", "procurement": "PRO",
    "accommodation":     "HSG",
}


class JsonRepository(BaseRepository):
    def __init__(self, base_path: str):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _path(self, dept: str) -> str:
        return os.path.join(self.base_path, f"{dept}.json")

    def _load(self, dept: str) -> dict | list:
        path = self._path(dept)
        if not os.path.exists(path):
            return {}
        with open(path) as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def _save_raw(self, dept: str, data: dict | list) -> None:
        with open(self._path(dept), "w") as f:
            json.dump(data, f, indent=2)

    def _new_id(self, dept: str) -> str:
        prefix = DEPT_PREFIX.get(dept, dept[:3].upper())
        return f"{prefix}-{''.join(random.choices(string.digits, k=6))}"

    def save_ticket(self, dept: str, ticket: dict) -> dict:
        data = self._load(dept)
        is_list = isinstance(data, list)
        tickets = data if is_list else data.setdefault("tickets", [])
        ticket["ticket_id"] = self._new_id(dept)
        ticket["timestamp"] = datetime.utcnow().isoformat() + "Z"
        ticket.setdefault("status", "open")
        tickets.append(ticket)
        self._save_raw(dept, data if not is_list else tickets)
        return ticket

    def get_tickets(self, dept: str) -> list[dict]:
        data = self._load(dept)
        return data if isinstance(data, list) else data.get("tickets", [])

    def read_reference_data(self, dept: str) -> dict | list:
        return self._load(dept)
