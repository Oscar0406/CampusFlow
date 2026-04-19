"""
services/session_store.py
In-memory session store. In production, swap the backend for Redis
by replacing _store with a Redis client and serialising via Session.to_dict().
"""
from models.session import Session


class SessionStore:
    def __init__(self):
        self._store: dict[str, Session] = {}

    def get(self, session_id: str) -> Session | None:
        return self._store.get(session_id)

    def get_or_create(self, session_id: str) -> Session:
        if session_id not in self._store:
            s = Session()
            s.session_id = session_id
            self._store[session_id] = s
        return self._store[session_id]

    def save(self, session: Session) -> None:
        self._store[session.session_id] = session

    def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)

    def list_ids(self) -> list[str]:
        return list(self._store.keys())


# Module-level singleton used by the gateway
_default_store = SessionStore()


def get_session_store() -> SessionStore:
    return _default_store
