from typing_extensions import TypedDict
from states.utility_state import UtilityState

class State(TypedDict):
    user_message: str
    context: str
    utilities: UtilityState
    awareness: float
    journey: float
    willingness: float
    segment: float
    intervention: float
    validation: float
    total_nodes: int
    node_order: list[str]





