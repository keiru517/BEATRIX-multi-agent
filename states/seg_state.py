from typing import TypedDict

class SEGState(TypedDict):
    segment_label: str
    activation_score: float
    key_drivers: list[str]
    comment: str