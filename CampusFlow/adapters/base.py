from abc import ABC, abstractmethod


class UniversityAdapter(ABC):
    @abstractmethod
    def get_student(self, student_id: str) -> dict: ...

    @abstractmethod
    def get_courses(self, filters: dict) -> list[dict]: ...

    @abstractmethod
    def get_rooms(self, filters: dict) -> list[dict]: ...

    @abstractmethod
    def get_finances(self, student_id: str) -> dict: ...

    @abstractmethod
    def read_dept_data(self, dept: str) -> dict | list: ...
