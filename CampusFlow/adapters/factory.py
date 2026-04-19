from adapters.base import UniversityAdapter
from adapters.json_local_adapter import JsonLocalAdapter
from adapters.rest_adapter import RestAdapter

_REGISTRY: dict[str, type[UniversityAdapter]] = {
    "json_local":   JsonLocalAdapter,
    "generic_rest": RestAdapter,
}


def get_adapter(ctx) -> UniversityAdapter:
    kind = ctx.config.get("adapters", {}).get("type", "json_local")
    cls = _REGISTRY.get(kind, JsonLocalAdapter)
    return cls(ctx)
