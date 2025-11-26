from typing_extensions import TypedDict

class State(TypedDict):
    user_message: str
    context: str
    awareness: float
    journey: float
    willingness: float
    segment: float
    intervention: float
    validation: float
    total_nodes: int
    node_order: list[str]





