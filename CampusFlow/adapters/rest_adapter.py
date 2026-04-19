"""
Production REST adapter — calls the university's real SIS, Finance, and accommodation APIs.
Field name mismatches are resolved via the schema mappings in the university YAML.
Used when adapters.type = generic_rest in the university config.
"""
import os
import httpx

from adapters.base import UniversityAdapter


class RestAdapter(UniversityAdapter):
    def __init__(self, ctx):
        cfg = ctx.config.get("adapters", {})
        self._sis_base = cfg.get("sis", {}).get("base_url", "")
        self._fin_base = cfg.get("finance", {}).get("base_url", "")
        self._hsg_base = cfg.get("accommodation", {}).get("base_url", "")
        self._sis_key  = os.environ.get(cfg.get("sis", {}).get("api_key_env", ""), "")
        self._fin_key  = os.environ.get(cfg.get("finance", {}).get("api_key_env", ""), "")
        self._hsg_key  = os.environ.get(cfg.get("accommodation", {}).get("api_key_env", ""), "")
        self._sis_map  = cfg.get("sis", {}).get("schema", {})
        self._fin_map  = cfg.get("finance", {}).get("schema", {})
        self._hsg_map  = cfg.get("accommodation", {}).get("schema", {})

    def _map(self, raw: dict, schema: dict) -> dict:
        return {k: raw.get(v, raw.get(k)) for k, v in schema.items()}

    def _hdr(self, key: str) -> dict:
        return {"Authorization": f"Bearer {key}"}

    def get_student(self, student_id: str) -> dict:
        r = httpx.get(f"{self._sis_base}/students/{student_id}", headers=self._hdr(self._sis_key))
        r.raise_for_status()
        return self._map(r.json(), self._sis_map)

    def get_courses(self, filters: dict) -> list[dict]:
        r = httpx.get(f"{self._sis_base}/courses", params=filters, headers=self._hdr(self._sis_key))
        r.raise_for_status()
        return [self._map(c, self._sis_map) for c in r.json()]

    def get_rooms(self, filters: dict) -> list[dict]:
        r = httpx.get(f"{self._hsg_base}/rooms", params=filters, headers=self._hdr(self._hsg_key))
        r.raise_for_status()
        return [self._map(room, self._hsg_map) for room in r.json()]

    def get_finances(self, student_id: str) -> dict:
        r = httpx.get(
            f"{self._fin_base}/students/{student_id}/finances",
            headers=self._hdr(self._fin_key),
        )
        r.raise_for_status()
        return self._map(r.json(), self._fin_map)

    def read_dept_data(self, dept: str) -> dict:
        return {}
