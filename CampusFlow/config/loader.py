import os
import yaml

_CACHE: dict[str, dict] = {}
_CONFIG_DIR = os.path.join(os.path.dirname(__file__), "universities")


def load_university_config(university_id: str) -> dict | None:
    if university_id in _CACHE:
        return _CACHE[university_id]
    path = os.path.join(_CONFIG_DIR, f"{university_id}.yaml")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        cfg = yaml.safe_load(f)
    _CACHE[university_id] = cfg
    return cfg


def list_universities() -> list[str]:
    return [f.replace(".yaml", "") for f in os.listdir(_CONFIG_DIR) if f.endswith(".yaml")]
