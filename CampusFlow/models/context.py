from dataclasses import dataclass, field


@dataclass
class TenantContext:
    university_id: str
    config: dict = field(default_factory=dict)

    @property
    def llm_config(self) -> dict:
        return self.config.get("llm", {})

    @property
    def departments(self) -> list:
        return self.config.get("departments", [])

    @property
    def ticket_path(self) -> str:
        return self.config.get("ticket_store", {}).get("path", f"./data/{self.university_id}/")
