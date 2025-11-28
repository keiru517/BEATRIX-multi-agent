from typing import TypedDict


class WTXState(TypedDict):
    behavior_probability: float
    risk_factor: float
    uncertainty_factor: float
    behavior_state: str
    behavior_comment: str
