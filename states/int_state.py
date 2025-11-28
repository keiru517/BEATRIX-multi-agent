from typing import TypedDict


class INTState(TypedDict):
    intervention_effect_index: float
    reactance_index: float
    complementarity_score: float
    intervention_state: str
    intervention_comment: str
