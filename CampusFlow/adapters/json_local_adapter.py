"""
Development / demo adapter — reads from local JSON files.
Used when adapters.type = json_local in the university config.
Replace with RestAdapter for production.
"""
import json
import os

from adapters.base import UniversityAdapter


class JsonLocalAdapter(UniversityAdapter):
    def __init__(self, ctx):
        self.path = ctx.ticket_path

    def _load(self, dept: str) -> dict | list:
        fpath = os.path.join(self.path, f"{dept}.json")
        if not os.path.exists(fpath):
            return {}
        with open(fpath) as f:
            return json.load(f)

    def get_student(self, student_id: str) -> dict:
        return {}

    def get_courses(self, filters: dict) -> list[dict]:
        data = self._load("academic")
        courses = data.get("courses", []) if isinstance(data, dict) else []
        if filters.get("available_only"):
            courses = [c for c in courses if c.get("available_seats", 0) > 0]
        return courses

    def get_rooms(self, filters: dict) -> list[dict]:
        data = self._load("accommodation")
        rooms = data.get("rooms", []) if isinstance(data, dict) else []
        if filters.get("status"):
            rooms = [r for r in rooms if r.get("status") == filters["status"]]
        if filters.get("gender"):
            rooms = [r for r in rooms if r.get("gender") == filters["gender"]]
        if filters.get("room_type"):
            rooms = [r for r in rooms if r.get("type") == filters["room_type"]]
        if filters.get("max_monthly_rate_myr"):
            rooms = [r for r in rooms if r.get("monthly_rate_myr", 0) <= filters["max_monthly_rate_myr"]]
        return rooms

    def get_finances(self, student_id: str) -> dict:
        data = self._load("finance")
        if not isinstance(data, dict):
            return {}
        return {
            "scholarships":  data.get("scholarships", []),
            "bursaries":     data.get("bursaries", []),
            "payment_plans": data.get("payment_plans", {}),
            "fee_structure": data.get("fee_structure", {}),
        }

    def read_dept_data(self, dept: str) -> dict | list:
        return self._load(dept)
