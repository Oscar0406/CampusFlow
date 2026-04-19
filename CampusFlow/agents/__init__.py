from agents.maintenance  import maintenance_agent
from agents.academic     import academic_agent
from agents.finance      import finance_agent
from agents.it_support   import it_support_agent
from agents.library      import library_agent
from agents.procurement  import procurement_agent
from agents.accommodation      import accommodation_agent

AGENT_REGISTRY: dict[str, object] = {
    "maintenance":      maintenance_agent,
    "academic":         academic_agent,
    "finance":          finance_agent,
    "it_support":       it_support_agent,
    "library":          library_agent,
    "procurement":      procurement_agent,
    "accommodation":    accommodation_agent,
}
