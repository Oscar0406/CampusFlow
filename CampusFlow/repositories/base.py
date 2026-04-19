from abc import ABC, abstractmethod


class BaseRepository(ABC):
    @abstractmethod
    def save_ticket(self, dept: str, ticket: dict) -> dict: ...

    @abstractmethod
    def get_tickets(self, dept: str) -> list[dict]: ...

    @abstractmethod
    def read_reference_data(self, dept: str) -> dict | list: ...
